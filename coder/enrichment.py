"""Unlabeled, version-pinned WHO reference indexes. Never consult notes/labels."""

from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path
import re

import numpy as np
import snowballstemmer
from sklearn.feature_extraction.text import TfidfVectorizer

_stemmer = snowballstemmer.stemmer("english")


@lru_cache(maxsize=100000)
def stem(word):
    return _stemmer.stemWord(word)


def word_features(text):
    stop = {
        "a",
        "an",
        "the",
        "of",
        "in",
        "on",
        "at",
        "by",
        "for",
        "and",
        "or",
        "to",
        "that",
        "this",
    }
    words = [
        stem(w) for w in re.findall(r"(?u)\b\w+\b", text.casefold()) if w not in stop
    ]
    return words + [" ".join(pair) for pair in zip(words, words[1:])]


def value(v):
    if isinstance(v, dict):
        return v.get("@value", "")
    return v if isinstance(v, str) else ""


class WHOReference:
    def __init__(self, path, categories, normalise):
        self.sha256 = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        with gzip.open(path, "rt", encoding="utf-8") as f:
            records = {r["code"]: r for r in map(json.loads, f)}
        codes = [c["code"] for c in categories]
        if set(records) != set(codes):
            raise ValueError("WHO export must exactly match the allowed catalog")
        self.codes = codes
        by_uri = {r["@id"]: r for r in records.values()}
        self.parents = {
            r["code"]: [by_uri[u]["code"] for u in r.get("parent", []) if u in by_uri]
            for r in records.values()
        }
        terms = []
        owners = []
        definitions = []
        concept_owners = {}
        for i, c in enumerate(categories):
            r = records[c["code"]]
            labels = [value(r["title"]), value(r.get("fullySpecifiedName"))]
            for field in ("indexTerm", "inclusion"):
                labels.extend(value(x.get("label")) for x in r.get(field, []))
            labels = {normalise(s) for s in labels if s}
            terms.extend(sorted(labels))
            owners.extend([i] * len(labels))
            concepts = {
                w for label in labels for w in word_features(label) if " " not in w
            }
            for concept in concepts:
                concept_owners.setdefault(concept, []).append(i)
            ds = [value(r.get("definition")), value(r.get("longDefinition"))]
            if not any(ds):
                for parent in r.get("parent", []):
                    if parent in by_uri:
                        ds = [
                            value(by_uri[parent].get("definition")),
                            value(by_uri[parent].get("longDefinition")),
                        ]
                        if any(ds):
                            break
            definitions.append(normalise(" ".join(s for s in ds if s)))
        self.term_owners = np.asarray(owners, dtype=np.int32)
        self.concept_owners = {
            w: np.asarray(ids, dtype=np.int32) for w, ids in concept_owners.items()
        }
        self.term_vectorizer = TfidfVectorizer(
            analyzer=word_features,
            max_features=200000,
            sublinear_tf=True,
            dtype=np.float32,
        )
        self.term_matrix = self.term_vectorizer.fit_transform(terms)
        self.definition_vectorizer = TfidfVectorizer(
            analyzer=word_features,
            max_features=140000,
            sublinear_tf=True,
            dtype=np.float32,
        )
        self.definition_matrix = self.definition_vectorizer.fit_transform(definitions)
        self.term_count = len(terms)
        self.definition_count = sum(bool(d) for d in definitions)
        from coder.symptoms import DescriptionIndex

        self.descriptions = {"en": DescriptionIndex(path, codes, "en")}
        self.foreign = {}
        for language in ("fr", "es"):
            file = Path(path).with_name(f"who-2026-01-{language}.jsonl.gz")
            if file.exists():
                from coder.foreign import ForeignIndex

                self.foreign[language] = ForeignIndex(file, codes, language)
                self.descriptions[language] = DescriptionIndex(file, codes, language)

    @lru_cache(maxsize=512)
    def query(self, focused, whole):
        q = 0.85 * self.term_vectorizer.transform(
            [focused]
        ) + 0.15 * self.term_vectorizer.transform([whole])
        sims = (self.term_matrix @ q.T).toarray().ravel()
        scores = np.zeros(len(self.codes), dtype=np.float32)
        np.maximum.at(scores, self.term_owners, sims)
        qd = 0.40 * self.definition_vectorizer.transform(
            [focused]
        ) + 0.60 * self.definition_vectorizer.transform([whole])
        definitions = (self.definition_matrix @ qd.T).toarray().ravel()
        return scores, definitions


@lru_cache(maxsize=2)
def load_reference(path, catalog_json):
    # Delayed import avoids a module cycle during deserialisation.
    from coder.engine import normalise

    return WHOReference(path, json.loads(catalog_json), normalise)

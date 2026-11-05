"""Sparse clinical-description retrieval, independent of example/gold note IDs."""

from functools import partial
import gzip
import json
from pathlib import Path
import re

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer

from coder.enrichment import value, word_features
from coder.languages import language_features


def description_features(text):
    # Common US/UK spelling differences; no diagnosis-code substitutions.
    for source, target in [
        ("diarrhea", "diarrhoea"),
        ("anemia", "anaemia"),
        ("hemolytic", "haemolytic"),
        ("hemoglobin", "haemoglobin"),
        ("hematuria", "haematuria"),
        ("edema", "oedema"),
        ("esophageal", "oesophageal"),
        ("hemorrhag", "haemorrhag"),
    ]:
        text = re.sub(source, target, text, flags=re.IGNORECASE)
    return word_features(text)


class DescriptionIndex:
    def __init__(self, path, codes, language):
        self.language = language
        records = {r["code"]: r for r in map(json.loads, gzip.open(path, "rt"))}
        if set(records) != set(codes):
            raise ValueError("Description/catalog mismatch")
        # Empty descriptions contribute no symptom evidence, rather than using
        # a category title alone as a fabricated description.
        docs = []
        for code in codes:
            r = records[code]
            definition = (
                value(r.get("definition")) + " " + value(r.get("longDefinition"))
            )
            docs.append(
                (value(r.get("title")) + ". " + definition)
                if definition.strip()
                else ""
            )
        analyzer = (
            description_features
            if language == "en"
            else partial(language_features, language=language)
        )
        self.vectorizer = CountVectorizer(
            analyzer=analyzer, max_features=180000, dtype=np.float32
        )
        counts = self.vectorizer.fit_transform(docs).tocsr()
        df = np.asarray((counts > 0).sum(axis=0)).ravel()
        idf = np.log1p((len(codes) - df + 0.5) / (df + 0.5))
        lengths = np.asarray(counts.sum(axis=1)).ravel()
        nonzero = lengths[lengths > 0]
        length_norm = 0.75 + 0.25 * lengths / max(nonzero.mean(), 1)
        counts.data = (
            counts.data
            * 2.2
            / (counts.data + 1.2 * np.repeat(length_norm, np.diff(counts.indptr)))
        )
        self.matrix = counts.multiply(idf).tocsr()
        self.has_definition = np.asarray([bool(d) for d in docs])

    def query(self, text):
        # Prior conditions and medication lists must not outweigh the current
        # presentation. Keep them as weak context rather than deleting them.
        marker = re.search(
            r"(?i)\b(?:presents?|presented|consults?|comes|goes|complains|consulte|pr[eé]sente|consulta|acude|presenta)\b",
            text,
        )
        active = text[marker.start() :] if marker and marker.start() >= 20 else text
        q = self.vectorizer.transform([active])
        q.data[:] = 1
        if active != text:
            whole = self.vectorizer.transform([text])
            whole.data[:] = 0.15
            q = q + whole
        return (self.matrix @ q.T).toarray().ravel()


def needs_description(text, focused):
    # Keep explicit diagnoses and clinician assertions on the specificity path.
    # A diagnostic question must not be mistaken for an asserted diagnosis.
    explicit = re.search(
        r"(?im)(?:\b(?:dx|imp|assessment|impression|diagnosis|diagnostic|diagn[oó]stico|conclusion|conclusi[oó]n|évaluation|valoraci[oó]n)\s*:\s*\S|^\s*a\s*:\s*\S)",
        text,
    )
    if explicit:
        return False
    if focused != text and len(focused.split()) < 30:
        return False
    return len(text.split()) >= 30

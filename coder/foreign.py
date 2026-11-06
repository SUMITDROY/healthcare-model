"""Direct WHO terminology lookup in French/Spanish, not clinical translation."""

from functools import lru_cache, partial
import gzip
import json

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from coder.enrichment import value
from coder.languages import language_features, clean, canonical_title


class ForeignIndex:
    def __init__(self, path, codes, language):
        self.language = language
        self.features = partial(language_features, language=language)
        with gzip.open(path, "rt", encoding="utf-8") as f:
            records = {r["code"]: r for r in map(json.loads, f)}
        if set(records) != set(codes):
            raise ValueError("Foreign reference/catalog mismatch")
        labels = []
        owners = []
        self.titles = []
        self.title_codes = {}
        for i, code in enumerate(codes):
            r = records[code]
            title = value(r["title"])
            self.title_codes.setdefault(canonical_title(title), set()).add(code)
            self.titles.append(set(w for w in self.features(title) if " " not in w))
            terms = [title, value(r.get("fullySpecifiedName"))]
            for field in ("indexTerm", "inclusion"):
                terms.extend(value(t.get("label")) for t in r.get(field, []))
            terms = sorted({t for t in terms if t})
            labels.extend(terms)
            owners.extend([i] * len(terms))
        self.owners = np.asarray(owners, dtype=np.int32)
        self.vectorizer = TfidfVectorizer(
            analyzer=self.features,
            max_features=200000,
            sublinear_tf=True,
            dtype=np.float32,
        )
        self.matrix = self.vectorizer.fit_transform(labels)
        self.term_count = len(labels)

    @lru_cache(maxsize=256)
    def query(self, focused, whole):
        focused = clean(focused, self.language)
        whole = clean(whole, self.language)
        q = 0.85 * self.vectorizer.transform(
            [focused]
        ) + 0.15 * self.vectorizer.transform([whole])
        sim = (self.matrix @ q.T).toarray().ravel()
        scores = np.zeros(len(self.titles), dtype=np.float32)
        np.maximum.at(scores, self.owners, sim)
        tokens = {w for w in self.features(focused) if " " not in w}
        return scores, tokens

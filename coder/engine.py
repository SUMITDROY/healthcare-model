"""Small CPU retrieval model; training data and evaluation inputs stay separate."""
from __future__ import annotations

import json
import re
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


# General normalisation rules, not a note-id -> gold lookup.
ABBREVIATIONS = {
    'urti': 'upper respiratory tract infection', 'uti': 'urinary tract infection',
    'htn': 'hypertension', 'dm2': 'type 2 diabetes mellitus',
    't2dm': 'type 2 diabetes mellitus', 'copd': 'chronic obstructive pulmonary disease',
    'dvt': 'deep vein thrombosis', 'gord': 'gastro oesophageal reflux disease',
    'gerd': 'gastro oesophageal reflux disease', 'oa': 'osteoarthritis',
    'af': 'atrial fibrillation', 'sam': 'severe acute malnutrition',
    'tb': 'tuberculosis', 'pet': 'pre eclampsia',
    'pid': 'pelvic inflammatory disease', 'bph': 'benign prostatic hyperplasia',
}

# Transparent medical vocabulary expansion developed with the dev notes.
# These are terminology aliases, not gold-code or note-id rules. Their effect
# is measured separately and is not an independent external validation.
ALIASES = {
    'chickenpox': 'varicella', 'jiggers': 'tungiasis',
    'bilharzia': 'schistosomiasis', 'urinary bilharzia': 'schistosoma haematobium schistosomiasis',
    'vaginal thrush': 'vulvovaginal candidosis', 'tinea capitis': 'dermatophytosis of scalp',
    'frozen shoulder': 'adhesive capsulitis of shoulder',
    'graves disease': 'thyrotoxicosis with diffuse goitre',
    'amoebic dysentery': 'acute amoebiasis', 'prediabetes': 'impaired fasting glucose',
    'low sugar': 'hypoglycaemia', 'heart attack': 'myocardial infarction',
    'high blood pressure': 'hypertension', 'enlarged prostate': 'hyperplasia of prostate',
    'prostatic enlargement': 'hyperplasia of prostate', 'peptic ulcer disease': 'peptic ulcer',
    'lymph node infection': 'lymphadenitis', 'nickel': 'nickel metal',
    'cystitis': 'cystitis bladder infection',
    'falciparum malaria': 'plasmodium falciparum malaria',
}


def normalise(text: str) -> str:
    text = text.casefold().replace('’', "'")
    for short, full in ABBREVIATIONS.items():
        text = re.sub(r'\b' + re.escape(short) + r'\b', full, text)
    for phrase in sorted(ALIASES, key=len, reverse=True):
        text = re.sub(r'\b' + re.escape(phrase) + r'\b', ALIASES[phrase], text)
    return text


def focus(text: str) -> str:
    """Prefer explicit clinician assessment; retain original text elsewhere."""
    lines = re.findall(
        r'(?im)^\s*(?:a|dx|diagnosis|assessment|imp|impression)\s*:\s*([^\n]+)', text
    )
    if lines:
        return ' '.join(lines)
    # Ambient transcripts do not always have assessment headings.
    # A patient's "I think it's my thyroid" is not a clinician diagnosis.
    doctor_text = '\n'.join(re.findall(r'(?im)^Doctor:\s*(.*)$', text))
    spoken = re.findall(
        r"(?i)\b(?:this is|this looks like|what you have is|you have|it's|it is)\s+([^.!?\n]{5,180})",
        doctor_text,
    )
    return ' '.join(spoken) if spoken else text


def rows(path):
    with open(path, encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


class OfflineCoder:
    def __init__(self, categories: list[dict], examples: list[dict]):
        self.categories = categories
        self.codes = [r['code'] for r in categories]
        self.valid = set(self.codes)
        self.code_index = {c: i for i, c in enumerate(self.codes)}
        # Narrow title-verified fallback: only redirect a non-leaf to its
        # explicitly named, leaf, unspecified category. Do not infer a full
        # ICD hierarchy from punctuation or code prefixes.
        title_to_index = {r['title'].casefold(): i for i, r in enumerate(categories)}
        self.unspecified_children = {}
        for i, r in enumerate(categories):
            if not r['leaf']:
                j = title_to_index.get(r['title'].casefold() + ', unspecified')
                if j is not None and categories[j]['leaf'] and categories[j]['residual']:
                    self.unspecified_children[i] = j
        self.examples = examples
        self.example_ids = [r['id'] for r in examples]
        # Validation prevents training labels outside the pinned release.
        for r in examples:
            if not r.get('gold') or not set(r['gold']) <= self.valid:
                raise ValueError(f"Invalid training labels: {r['id']}")
        titles = [normalise(r['title']) for r in categories]
        train = [normalise(focus(r['text']) + ' ' + r['text']) for r in examples]
        self.word = TfidfVectorizer(
            strip_accents='unicode', ngram_range=(1, 2), sublinear_tf=True,
            max_features=160000, dtype=np.float32,
        )
        self.word.fit(titles + train)
        self.title_word = self.word.transform(titles)
        self.example_word = self.word.transform(train) if train else None
        self.char = TfidfVectorizer(
            analyzer='char_wb', ngram_range=(3, 5), strip_accents='unicode',
            sublinear_tf=True, max_features=140000, dtype=np.float32,
        )
        self.title_char = self.char.fit_transform(titles)

    def predict(self, text: str, use_examples=True) -> tuple[list[str], dict]:
        whole, focused = normalise(text), normalise(focus(text))
        qw = 0.30 * self.word.transform([whole]) + 0.70 * self.word.transform([focused])
        qc = 0.30 * self.char.transform([whole]) + 0.70 * self.char.transform([focused])
        lexical = (self.title_word @ qw.T).toarray().ravel()
        character = (self.title_char @ qc.T).toarray().ravel()
        scores = 0.65 * lexical + 0.35 * character
        for parent, generic in self.unspecified_children.items():
            scores[generic] = max(scores[generic], scores[parent])
            scores[parent] *= 0.80
        neighbour = None
        if use_examples and self.example_word is not None:
            # A supervised nearest-neighbour component trained only on labeled
            # examples. Evaluation must exclude held-out notes before fitting.
            example_q = self.word.transform([normalise(focus(text) + ' ' + text)])
            sim = (self.example_word @ example_q.T).toarray().ravel()
            supervised = np.zeros(len(self.codes), dtype=np.float32)
            for i in np.argsort(-sim)[:5]:
                for code in self.examples[int(i)]['gold']:
                    idx = self.code_index[code]
                    supervised[idx] = max(supervised[idx], sim[i])
            # Weak similarity to an unrelated training diagnosis should not
            # override a direct match to a category absent from training.
            weight = 0.40 * min(1.0, max(0.0, (float(sim.max()) - 0.20) / 0.40))
            scores = (1.0-weight) * scores + weight * supervised
            neighbour = self.example_ids[int(sim.argmax())]
        order = np.argsort(-scores, kind='stable')[:3]
        codes = [self.codes[int(i)] for i in order]
        return codes, {
            'scores': [round(float(scores[i]), 6) for i in order],
            'nearest_training_id': neighbour,
            'assessment': focus(text)[:500],
            'warning': 'Retrieval scores are not calibrated probabilities.',
        }

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path, compress=3)

    @classmethod
    def load(cls, path):
        # Only load our own locally built artifact, never an untrusted pickle.
        return joblib.load(path)

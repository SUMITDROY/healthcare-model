"""Small CPU retrieval model; training data and evaluation inputs stay separate."""
from __future__ import annotations

import json
import re
import os
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from coder.context import focus, clean_query, context_flags


# General normalisation rules, not a note-id -> gold lookup.
ABBREVIATIONS = {
    'urti': 'acute upper respiratory infection', 'uti': 'urinary tract infection',
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
    'uncomplicated': 'without complication',
    'asthma attack': 'asthma exacerbation',
    'benign enlargement of the prostate': 'hyperplasia of prostate',
    'benign prostatic enlargement': 'hyperplasia of prostate',
    'e. coli': 'escherichia coli',
    'leg': 'lower limb', 'legs': 'lower limbs',
    'upper respiratory tract infection': 'upper respiratory infection',
    'common cold': 'acute nasopharyngitis',
}


def normalise(text: str) -> str:
    text = text.casefold().replace('’', "'")
    for short, full in ABBREVIATIONS.items():
        text = re.sub(r'\b' + re.escape(short) + r'\b', full, text)
    for phrase in sorted(ALIASES, key=len, reverse=True):
        text = re.sub(r'\b' + re.escape(phrase) + r'\b', ALIASES[phrase], text)
    return text


def rows(path):
    with open(path, encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


class OfflineCoder:
    def __init__(self, categories: list[dict], examples: list[dict]):
        self.categories = categories
        self.semantic_enabled = os.environ.get('CODER_SEMANTIC','0') == '1'
        self.codes = [r['code'] for r in categories]
        self.valid = set(self.codes)
        self.code_index = {c: i for i, c in enumerate(self.codes)}
        self.title_phrases = []
        self.qualifiers = []
        ignored = {'other','specified','unspecified','disease','diseases','complication','complications','associated','mention','the','of','or','and','a','an','to','in','due','without','with','syndrome','disorder','disorders'}
        for r in categories:
            title = normalise(r['title'])
            base = re.split(r',|\bwith\b|\bwithout\b|\bdue to\b|\bassociated with\b',title)[0].strip()
            self.title_phrases.append(base)
            qualifier = re.split(r'\b(?:with|due to|associated with)\b',title,maxsplit=1)
            words = re.findall(r'[a-z]{3,}',qualifier[1]) if len(qualifier)>1 else []
            self.qualifiers.append({word[:5] for word in words if word not in ignored})
        self.title_masks = {
            key: np.array([bool(re.search(pattern, r['title'].casefold())) for r in categories])
            for key, pattern in {
                'congenital': r'\bcongenital\b',
                'neonatal': r'\bneonatal\b|\bnewborn\b',
                'pregnancy': r'\bpregnancy\b|\bpuerperium\b|\bchildbirth\b|\bmaternal\b',
                'traditional': r'\(tm[12]\)',
                'acute': r'\bacute\b', 'chronic': r'\bchronic\b',
                'nonleaf': r'$^',
            }.items()
        }
        self.title_masks['nonleaf'] = np.array([not r['leaf'] for r in categories])
        # Narrow title-verified fallback: only redirect a non-leaf to its
        # explicitly named, leaf, unspecified category. Do not infer a full
        # ICD hierarchy from punctuation or code prefixes.
        title_to_index = {r['title'].casefold(): i for i, r in enumerate(categories)}
        candidates_by_base = {}
        for j, candidate in enumerate(categories):
            candidates_by_base.setdefault(candidate['title'].casefold().split(',')[0], []).append((j,candidate))
        self.unspecified_children = {}
        for i, r in enumerate(categories):
            if not r['leaf']:
                j = title_to_index.get(r['title'].casefold() + ', unspecified')
                if j is not None and categories[j]['leaf'] and categories[j]['residual']:
                    self.unspecified_children[i] = j
                if i not in self.unspecified_children:
                    base = r['title'].casefold().split(',')[0]
                    for j, candidate in candidates_by_base.get(base, []):
                        title = candidate['title'].casefold()
                        if (candidate['leaf'] and candidate['residual']
                            and candidate['code'].startswith(r['code'])
                            and title.startswith(base + ',')
                            and re.fullmatch(r'[ ,]*(?:(?:unspecified|organism|site|agent|and|not|specified|type|severity|location)\b[ ,]*)+', title[len(base):])):
                            self.unspecified_children[i] = j
                            break
                # Some families have a baseline "without complication" leaf
                # but no unspecified leaf. Keep explicit complication leaves
                # available: positive qualifier evidence can still rank above it.
                if i not in self.unspecified_children:
                    j = title_to_index.get(r['title'].casefold() + ' without complication')
                    if j is not None and categories[j]['leaf']:
                        self.unspecified_children[i] = j
        self.examples = examples
        self.example_ids = [r['id'] for r in examples]
        # Validation prevents training labels outside the pinned release.
        for r in examples:
            if not r.get('gold') or not set(r['gold']) <= self.valid:
                raise ValueError(f"Invalid training labels: {r['id']}")
        titles = [normalise(r['title']) for r in categories]
        self.word = TfidfVectorizer(
            strip_accents='unicode', ngram_range=(1, 2), sublinear_tf=True,
            max_features=160000, dtype=np.float32,
        )
        # Catalog-only IDF is stable across folds and future clinics. Notes
        # train the pairwise ranker, not the vocabulary or a code lookup.
        self.word.fit(titles)
        self.title_word = self.word.transform(titles)
        self.char = TfidfVectorizer(
            analyzer='char_wb', ngram_range=(3, 5), strip_accents='unicode',
            sublinear_tf=True, max_features=140000, dtype=np.float32,
        )
        self.title_char = self.char.fit_transform(titles)
        self.ranker = None
        self.feature_names = [
            'word_similarity', 'character_similarity', 'context_adjusted_retrieval',
            'diagnosis_phrase_match', 'qualifier_supported', 'qualifier_unsupported',
            'leaf', 'residual', 'title_length', 'dense_similarity',
            'unsupported_congenital', 'unsupported_neonatal', 'unsupported_pregnancy',
            'unsupported_traditional', 'acute_match', 'chronic_contradiction',
        ]
        if examples:
            features, labels = [], []
            rng = np.random.default_rng(20261105)
            for row in examples:
                scores, matrix, _ = self.retrieve(row['text'])
                gold = {self.code_index[c] for c in row['gold']}
                candidates = set(np.argsort(-scores)[:60].tolist()) | gold
                candidates.update(rng.choice(len(self.codes),size=12,replace=False).tolist())
                candidates = sorted(candidates)
                negatives = [i for i in candidates if i not in gold]
                for positive in sorted(gold):
                    delta = matrix[positive]-matrix[negatives]
                    features.extend([delta,-delta])
                    labels.extend([1]*len(negatives)+[0]*len(negatives))
            # A shared pair scorer can rank codes never observed as labels.
            # No note lookup and no classifier restricted to 61 seen codes.
            self.ranker = make_pipeline(StandardScaler(with_mean=False), LogisticRegression(
                C=0.1, fit_intercept=False, max_iter=600, random_state=20261105))
            self.ranker.fit(np.concatenate(features), np.asarray(labels))

    def retrieve(self, text: str):
        whole, focused = normalise(clean_query(text)), normalise(clean_query(focus(text)))
        qw = 0.30 * self.word.transform([whole]) + 0.70 * self.word.transform([focused])
        qc = 0.30 * self.char.transform([whole]) + 0.70 * self.char.transform([focused])
        lexical = (self.title_word @ qw.T).toarray().ravel()
        character = (self.title_char @ qc.T).toarray().ravel()
        scores = 0.65 * lexical + 0.35 * character
        phrase_matches = np.zeros(len(scores), dtype=np.float32)
        qualifier_supported = np.zeros(len(scores), dtype=np.float32)
        qualifier_unsupported = np.zeros(len(scores), dtype=np.float32)
        query_terms = {w[:5] for w in re.findall(r'[a-z]{3,}', whole+' '+focused)}
        for i in np.argsort(-scores)[:200]:
            phrase = self.title_phrases[int(i)]
            if phrase and re.search(r'(?<!\w)'+re.escape(phrase)+r'(?!\w)', focused):
                scores[i] += 0.12
                phrase_matches[i] = 1
        # Optional dense retrieval is built ahead of time from titles only.
        # Its embedding cache is independent of example labels or CV folds.
        from coder.semantic import available_index
        semantic = available_index(enabled=self.semantic_enabled)
        dense = None
        if semantic is not None:
            if semantic.codes != self.codes:
                raise ValueError('Semantic index code ordering/release mismatch')
            query = focused if focused else whole
            dense = semantic.vectors @ semantic.query(query[:4000])
            # Reciprocal-rank fusion avoids interpreting cosine similarity
            # as a clinical probability or mixing incompatible score scales.
            ranks = np.empty(len(scores), dtype=np.float32)
            ranks[np.argsort(-dense, kind='stable')] = np.arange(len(scores))
            scores += 0.18 * (8.0/(8.0+ranks))
        for parent, generic in self.unspecified_children.items():
            scores[generic] = max(scores[generic], scores[parent])
            scores[parent] *= 0.80
        flags = context_flags(text)
        for key in ('congenital', 'neonatal', 'pregnancy', 'traditional'):
            if not flags[key]:
                scores[self.title_masks[key]] *= 0.20
        if flags['acute'] and not flags['chronic']:
            scores[self.title_masks['chronic']] *= 0.55
        scores[self.title_masks['nonleaf']] *= 0.85
        for i in np.argsort(-scores)[:200]:
            qualifier = self.qualifiers[int(i)]
            if qualifier:
                if qualifier & query_terms:
                    scores[i] += 0.10
                    qualifier_supported[i] = 1
                else:
                    scores[i] *= 0.50
                    qualifier_unsupported[i] = 1
        matrix = np.column_stack([
            lexical, character, scores, phrase_matches, qualifier_supported, qualifier_unsupported,
            ~self.title_masks['nonleaf'], [r['residual'] for r in self.categories],
            [min(len(r['title'].split()),30)/30 for r in self.categories],
            dense if dense is not None else np.zeros(len(scores)),
            *[(self.title_masks[key] & (not flags[key])) for key in ('congenital','neonatal','pregnancy','traditional')],
            self.title_masks['acute'] & flags['acute'],
            self.title_masks['chronic'] & flags['acute'] & (not flags['chronic']),
        ]).astype(np.float32)
        return scores, matrix, {'assessment': focus(text)[:500], 'semantic_retrieval': semantic is not None}

    def predict(self, text: str, use_examples=True) -> tuple[list[str], dict]:
        retrieval, matrix, diagnostic = self.retrieve(text)
        candidates = np.argsort(-retrieval,kind='stable')[:100]
        if use_examples and self.ranker is not None:
            scores = retrieval[candidates] + 0.02*self.ranker.decision_function(matrix[candidates])
            ranked = candidates[np.argsort(-scores,kind='stable')]
            # The learned scorer has not improved primary selection on this
            # small sample. Keep evidence-first top-1; learn alternatives.
            order = np.asarray([candidates[0]]+[i for i in ranked if i != candidates[0]][:2])
            selected_scores = retrieval[order] + 0.02*self.ranker.decision_function(matrix[order])
        else:
            order = candidates[:3]
            selected_scores = retrieval[order]
        codes = [self.codes[int(i)] for i in order]
        return codes, {
            **diagnostic,
            'scores': [round(float(s), 6) for s in selected_scores],
            'supervised_ranker': bool(use_examples and self.ranker is not None),
            'primary_strategy': 'context-adjusted retrieval; learned alternatives',
            'candidate_codes_top50': [self.codes[int(i)] for i in candidates[:50]],
            'candidate_codes_top100': [self.codes[int(i)] for i in candidates],
            'warning': 'Ranking scores are not calibrated probabilities.',
        }

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path, compress=3)

    @classmethod
    def load(cls, path):
        # Only load our own locally built artifact, never an untrusted pickle.
        return joblib.load(path)

"""Identify supported reference languages; never translate or invent facts."""

from functools import lru_cache
import re
import unicodedata

from coder.enrichment import word_features


@lru_cache(maxsize=1)
def identifier():
    from langid.langid import LanguageIdentifier, model

    return LanguageIdentifier.from_modelstring(model, norm_probs=True)


@lru_cache(maxsize=1024)
def detect(text):
    if len(re.findall(r"[^\W\d_]", text)) < 20:
        return "en"
    language, confidence = identifier().classify(text)
    return language if language in {"fr", "es"} and confidence >= 0.95 else "en"


def latin_features(text):
    text = "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )
    stop = {
        "de",
        "la",
        "le",
        "les",
        "du",
        "des",
        "un",
        "une",
        "en",
        "dans",
        "au",
        "aux",
        "et",
        "a",
        "el",
        "los",
        "las",
        "del",
        "una",
        "por",
        "para",
        "y",
        "o",
    }
    text = " ".join(
        w for w in re.findall(r"(?u)\b\w+\b", text.casefold()) if w not in stop
    )
    return word_features(text)


def clean(text, language):
    if language == "fr":
        pattern = r"\b(?:pas de|pas d[’\x27]|aucun[e]?|absence de)\s*[^.;\n]+"
    else:
        pattern = r"\b(?:niega|se descarta|descartad[oa])\s+[^.;\n]+"
    return re.sub(pattern, " ", text, flags=re.IGNORECASE)

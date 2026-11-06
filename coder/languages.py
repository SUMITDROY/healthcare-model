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
    # Explicit localized headings remain useful for terse clinical notes.
    if re.search(r"(?i)\b(?:diagnóstico|conclusión|valoración)\s*:", text):
        return "es"
    if re.search(r"(?i)\b(?:diagnostic|évaluation)\s*:", text):
        return "fr"
    if re.search(r"(?i)\b(?:no presenta|se descarta|antecedentes familiares)\b", text):
        return "es"
    if re.search(r"(?i)\b(?:pas de|antécédents familiaux)\b", text):
        return "fr"
    if re.search(r"(?i)\bconclusion\s*:", text):
        language, confidence = identifier().classify(text.casefold())
        if language in {"fr", "es"} and confidence >= 0.95:
            return language
    if len(re.findall(r"[^\W\d_]", text)) < 20:
        return "en"
    language, confidence = identifier().classify(text.casefold())
    return language if language in {"fr", "es"} and confidence >= 0.95 else "en"


@lru_cache(maxsize=2)
def language_stemmer(language):
    import snowballstemmer

    return snowballstemmer.stemmer({"fr": "french", "es": "spanish"}[language])


@lru_cache(maxsize=200000)
def native_stem(word, language):
    return language_stemmer(language).stemWord(word)


def language_features(text, language):
    """Native morphology, accent normalization, and explicit letter subtypes."""
    text = "".join(
        c
        for c in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(c)
    )
    # A is a stop word in Spanish/English, but carries diagnostic identity in
    # hepatitis A. Give letter variants the same representation in query/title.
    markers = re.findall(
        r"\bhepat\w*(?:\W+(?:viral|virale|aigue|aigu|aguda|agudo|tipo|type)){0,2}\W+([abcde])\b",
        text,
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
        "l",
        "d",
    }
    words = [
        native_stem(w, language)
        for w in re.findall(r"(?u)\b\w+\b", text)
        if w not in stop
    ]
    return (
        words
        + [" ".join(pair) for pair in zip(words, words[1:])]
        + ["hepatitis_subtype_" + letter for letter in markers]
    )


def canonical_title(text):
    """Exact preferred-title identity, ignoring accents and punctuation only."""
    text = "".join(
        c
        for c in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(c)
    )
    return " ".join(re.findall(r"(?u)\w+", text))


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
    # Contrast ends negation scope. Taxonomic qualifiers (sans aura,
    # sans précision, sin especificar) are deliberately preserved.
    contrast = r"mais" if language == "fr" else r"pero"
    text = re.sub(r"(?i),?\s*\b" + contrast + r"\b", ";", text)
    if language == "fr":
        negative = r"pas de|pas d[’\x27]|aucun[e]?|absence de"
        family = r"antécédents familiaux|antecedents familiaux|(?:la )?(?:mère|mere|père|pere|sœur|soeur|frère|frere)"
    else:
        negative = (
            r"niega|se descarta|descartad[oa]|no presenta|no tiene|sin evidencia de"
        )
        family = r"antecedentes familiares|(?:la |el )?(?:madre|padre|hermana|hermano)"
    text = re.sub(r"(?i)\b(?:" + family + r")\b[^.;\n]*", " ", text)
    text = re.sub(r"(?i)\b(?:" + negative + r")\s*[^.;\n]+", " ", text)
    return text


def clinical_focus(text, language):
    """Select an asserted diagnosis; retain qualifiers such as sans/sin aura.

    This bounded parser does not infer a diagnosis from symptoms or translate.
    """
    headings = {
        "fr": r"diagnostic(?:s)?|diagnostic retenu|conclusion|évaluation|evaluation|impression",
        "es": r"diagn[oó]stico(?:s)?|conclusi[oó]n|valoraci[oó]n|evaluaci[oó]n|impresi[oó]n",
    }
    marker = re.search(r"(?im)\b(?:" + headings[language] + r")\s*:\s*([^\n]+)", text)
    if marker:
        selected = marker.group(1)
    else:
        assertion = {
            "fr": r"(?:le diagnostic (?:retenu|confirmé) est|vous avez|il s’agit de|il s\x27agit de)",
            "es": r"(?:el diagn[oó]stico (?:confirmado|final) es|usted tiene|se diagnostica)",
        }[language]
        match = re.search(r"(?i)\b" + assertion + r"\s+([^\n]+)", text)
        selected = match.group(1) if match else text
    selected = re.split(
        r"(?i)\b(?:traitement|conduite à tenir|plan|tratamiento)\s*:", selected
    )[0]
    return clean(selected, language).strip()

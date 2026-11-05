"""Transparent text/context heuristics, never note IDs or gold-code lookups.

These rules are development-informed and are not a replacement for a clinical
parser. Raw text is retained for context checks and audit diagnostics.
"""
import re


def focus(text: str) -> str:
    diagnoses = re.findall(
        r'(?im)(?:\b(?:dx|imp|diagnosis|assessment|impression)\s*:\s*|^\s*a\s*:\s*)([^\n]+)',
        text,
    )
    if not diagnoses:
        diagnoses = re.findall(r'(?im)\b(?:dx|imp)\s+(?!\d)([^\n]+)', text)
    if diagnoses:
        value = re.split(r'(?i)\b(?:plan|treatment|rx|mx|ix|p)\s*:', diagnoses[0])[0]
        # Don't split E. coli; split a new sentence such as "Malaria excluded".
        return re.split(r'(?<=[.!?])\s+(?=[A-Z])', value)[0].strip()
    doctor = '\n'.join(re.findall(r'(?im)^Doctor:\s*(.*)$', text))
    if doctor:
        candidates = re.findall(
            r"(?i)\b(?:this is|this looks like|what you have is|you have|you've got|it's|it is|we call it|these (?:values|results) show|the results show|consistent with|which is in the)\s+([^.!?\n]{5,220})",
            doctor,
        )
        candidates = [s for s in candidates if not re.match(
            r'(?i)(?:not\b|no\b|normal\b|fine\b|okay\b|common\b|a higher risk\b|a risk\b)', s)]
        if candidates:
            return '. '.join(candidates)
        # When speech is not a diagnostic template, use clinician statements
        # rather than patient speculation or their guesses at a diagnosis.
        declarations=re.findall(r'(?i)\bthe ([^.!?\n]{3,60}?) is ([^.!?\n]{3,140})',doctor)
        declarations=[subject+' '+state for subject,state in declarations
                      if len(subject.split())<=5 and not re.search(r'(?i)\b(?:and|but|goes|your)\b',subject)
                      and not re.search(r'(?i)\b(?:normal|fine|okay|negative|pending|ready)\b',state)]
        return '. '.join(declarations) if declarations else doctor
    return text


def clean_query(text: str) -> str:
    text = re.sub(r'(?i)\b(?:no|without)\s+(?:any\s+)?complications?\b', ' uncomplicated ', text)
    text = re.sub(r'(?i)\b(?:no|without)\s+coma\b', ' without coma ', text)
    # Scope is intentionally short; we retain the raw note separately.
    text = re.sub(r'(?i)\b(?:no (?!coma\b)|not (?!(?:specified|identified|elsewhere|otherwise)\b)|denies |negative for |ruled out )[^.;\n!?]+', ' ', text)
    text = re.sub(r'(?i)\b[\w-]+\s+(?:excluded|ruled out)\b', ' ', text)
    return text.strip()


def context_flags(text: str) -> dict[str, bool]:
    lower = text.casefold()
    active = clean_query(lower)
    active = re.sub(r'pregnancy test[^.;\n]{0,50}(?:neg|negative)|any chance[^?\n]{0,30}pregnant', '', active)
    age_match=re.search(r'\b(\d{1,3})\s*(?:[mf]\b|yo\b|y/o\b|years?[- ]old\b|years? old\b)',lower)
    age=int(age_match.group(1)) if age_match else None
    pregnancy=bool(re.search(r'\b(?:pregnan\w*|maternal|antenatal|anc|puerper\w*|postpartum|childbirth|postnatal)\b|\bg\d\s*p\d\b',active))
    return {
        'congenital': bool(re.search(r'\b(?:congenital|since birth|born with)\b', active)),
        'neonatal': bool(re.search(r'\b(?:neonat\w*|newborn|new born|day of life)\b|\b(?:[0-9]|1[0-9]|2[0-8])\s*(?:day[- ]old|days old|d old)\b', active)),
        'pregnancy': pregnancy,
        'elderly': 'elderly' in active or (age is not None and age >= (35 if pregnancy else 65)),
        'very_young': 'very young' in active or (age is not None and age<16),
        'secondary': bool(re.search(r'\bsecondary\b',active)),
        'known_diabetes': bool(re.search(r'\b(?:known|diagnosed|has)\s+(?:t2dm|dm2|diabetes|type [12] diabetes)\b',active)),
        'traditional': bool(re.search(r'\b(?:traditional medicine|tm1|tm2|ayurved\w*)\b', active)),
        'acute': bool(re.search(r'\bacute\b|\bexacerbation\b|\battack\b', active)),
        'chronic': bool(re.search(r'\bchronic\b', active)),
        'uncomplicated': bool(re.search(r'\buncomplicated\b|\bwithout complications?\b', active)),
    }

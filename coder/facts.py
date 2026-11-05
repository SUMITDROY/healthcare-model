"""Explicit clinical facts used as search evidence; never emits ICD codes.

These are transparent development-informed normalisation rules, not a clinical
diagnostic model. They only expand an already stated encounter diagnosis.
"""

import re


def expand_assessment(assessment, whole, flags):
    lower = whole.casefold()
    additions = []
    if "hypertension" in assessment:
        pressures = [
            (int(a), int(b))
            for a, b in re.findall(r"\b(\d{2,3})\s*/\s*(\d{2,3})\b", lower)
        ]
        # Numeric BP is evidence of both components only after hypertension is
        # already the clinician's diagnosis; dates/durations do not pass bounds.
        if any(140 <= a <= 280 and 90 <= b <= 180 for a, b in pressures):
            additions.append("combined systolic and diastolic hypertension")
    if "hypoglycaem" in assessment or "hypoglycem" in assessment:
        if flags["known_diabetes"] and "unawareness" not in assessment:
            additions.append("in the context of diabetes mellitus")
            if flags["no_coma"]:
                additions.append("without coma")
    if flags["pregnancy"] and flags["low_risk"]:
        if re.search(r"\bprimigravida\b|\bg1\s*p\d\b", lower):
            additions.append("supervision of normal first pregnancy")
    if "diabet" in assessment and flags["pregnancy"]:
        onset = bool(
            re.search(
                r"\b(?:arising|arose|developed|new.onset|has come with)\b", assessment
            )
        )
        if onset and not re.search(
            r"pre.existing|diabetes[^.\n]{0,30}before[^.\n]{0,20}pregnancy", lower
        ):
            additions.append("gestational diabetes mellitus arising in pregnancy")
    if re.search(r"\badult[- ]onset\b", assessment):
        additions.append("acquired")
    return assessment + " " + " ".join(additions)

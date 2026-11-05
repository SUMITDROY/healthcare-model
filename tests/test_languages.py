"""Scope and language regressions; no diagnosis-to-code fixtures."""

import unittest
from coder.languages import clean, clinical_focus, detect


class Languages(unittest.TestCase):
    def test_contrast_ends_negation(self):
        self.assertIn("choléra", clean("Pas de tuberculose, mais choléra.", "fr"))
        self.assertNotIn(
            "tuberculose", clean("Pas de tuberculose, mais choléra.", "fr")
        )
        self.assertIn("cólera", clean("No presenta tuberculosis, pero cólera.", "es"))
        self.assertNotIn(
            "tuberculosis", clean("No presenta tuberculosis, pero cólera.", "es")
        )

    def test_taxonomic_qualifiers_retained(self):
        for lang, text in [
            ("fr", "migraine sans aura"),
            ("es", "migraña sin aura"),
            ("fr", "sans précision"),
            ("es", "sin especificar"),
        ]:
            self.assertEqual(clean(text, lang), text)

    def test_localized_assessment_and_plan(self):
        self.assertEqual(
            clinical_focus(
                "Antécédents : asthme. Évaluation : choléra. Traitement : test.", "fr"
            ),
            "choléra.",
        )
        self.assertEqual(
            clinical_focus("Antecedentes: asma. Valoración: cólera. Plan: test.", "es"),
            "cólera.",
        )

    def test_family_condition_removed(self):
        self.assertNotIn(
            "tuberculose", clean("La mère souffre de tuberculose. Choléra.", "fr")
        )
        self.assertNotIn(
            "tuberculosis", clean("La madre tiene tuberculosis. Cólera.", "es")
        )

    def test_short_and_uppercase_language(self):
        self.assertEqual(detect("CONCLUSION : CHOLÉRA."), "fr")
        self.assertEqual(detect("DIAGNÓSTICO: CÓLERA."), "es")
        self.assertEqual(detect("No presenta tuberculosis, pero cólera."), "es")
        self.assertEqual(detect("Diagnosis: cholera."), "en")
        self.assertEqual(detect("Conclusion: diabetes mellitus."), "en")

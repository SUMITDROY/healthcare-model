"""Typed consultation diagnoses need not use an Assessment label."""

import gzip
import json
import unittest
from coder.engine import OfflineCoder


class DocumentedHeading(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = OfflineCoder.load("artifacts/offline.joblib")

    def test_official_diagnosis_heading_survives_long_followup_text(self):
        bodies = {
            "en": "The patient is stable at follow-up. Medication was reviewed and continued. There have been no new episodes since the previous appointment. The plan is routine review next month and continued adherence to treatment.",
            "fr": "Le patient est stable au suivi. Le traitement a été revu et poursuivi. Aucun nouvel épisode depuis la dernière consultation. Le suivi habituel est prévu le mois prochain. Le patient poursuit le traitement prescrit.",
            "es": "El paciente está estable en el seguimiento. Se revisó el tratamiento y se continúa. No hay episodios nuevos desde la consulta anterior. Se programa una revisión el próximo mes y se mantiene el tratamiento prescrito.",
        }
        for language, body in bodies.items():
            with self.subTest(language=language):
                with gzip.open(f"data/who-2026-01-{language}.jsonl.gz", "rt") as f:
                    title = next(
                        r["title"]["@value"]
                        for r in map(json.loads, f)
                        if r["code"] == "8A61.30"
                    )
                codes, diagnostic = self.model.safe_predict(title + ".\n" + body)
                self.assertEqual(codes[0], "8A61.30")
                self.assertTrue(diagnostic["documented_title"])

    def test_later_explicit_assessment_takes_precedence(self):
        text = "Cholera.\nPrior record discussed at length. The current visit concerns a new respiratory illness.\nAssessment: Acute bronchitis.\nPlan: routine follow-up."
        codes, diagnostic = self.model.safe_predict(text)
        self.assertEqual(codes[0], "CA42.Z")
        self.assertFalse(diagnostic.get("documented_title", False))

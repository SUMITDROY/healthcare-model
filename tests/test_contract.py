import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coder.engine import OfflineCoder, focus


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = OfflineCoder.load("artifacts/offline.joblib")

    def test_assessment_beats_negated_history(self):
        note = "Hx: malaria in the past.\nDx: Upper respiratory infection. Malaria excluded.\nPlan: fluids"
        self.assertEqual(focus(note), "Upper respiratory infection.")

    def test_no_network_and_broad_code_space(self):
        with patch.object(
            socket.socket, "connect", side_effect=AssertionError("network call")
        ):
            for note in [
                "",
                "Unknown narrative",
                "Acute myocardial infarction",
                "dolor de cabeza",
            ]:
                codes, _ = self.model.predict(note)
                self.assertTrue(1 <= len(codes) <= 3)
                self.assertEqual(len(codes), len(set(codes)))
                self.assertTrue(set(codes) <= self.model.valid)
        self.assertEqual(len(self.model.valid), 18375)

    def test_patient_speculation_is_not_assessment(self):
        text = "Patient: I think it's my thyroid.\nDoctor: Your thyroid is normal. This is obesity."
        self.assertEqual(focus(text), "obesity")

    def test_plain_diagnosis_can_use_unspecified_leaf(self):
        model = self.model
        codes, _ = model.predict("Dx: Acute tonsillitis.", use_examples=False)
        self.assertEqual(codes[0], "CA03.Z")

    def test_historical_dx_does_not_hide_current_assessment(self):
        note = "History: asthma dx 2014.\nA: Acute bronchitis.\nPlan: review."
        self.assertEqual(focus(note), "Acute bronchitis.")

    def test_inline_assessment_is_found(self):
        note = "Seen today. No fever. Dx: Acute bronchitis. Plan: review."
        self.assertEqual(focus(note), "Acute bronchitis.")
        self.assertEqual(self.model.predict(note)[0][0], "CA42.Z")

    def test_unobserved_training_code_is_reachable(self):
        observed = {c for r in self.model.examples for c in r["gold"]}
        self.assertNotIn("1A00", observed)
        self.assertEqual(self.model.predict("Diagnosis: Cholera.")[0][0], "1A00")

    def test_explicit_complication_changes_prediction(self):
        a = self.model.predict(
            "Diagnosis: Malaria due to Plasmodium falciparum, unspecified."
        )[0][0]
        b = self.model.predict(
            "Diagnosis: Plasmodium falciparum malaria with cerebral complications."
        )[0][0]
        self.assertEqual(a, "1F40.Z")
        self.assertEqual(b, "1F40.0")

    def test_negated_patient_guess_does_not_win(self):
        text = "Patient: I think it's malaria.\nDoctor: It is not malaria. This is acute tonsillitis."
        self.assertEqual(self.model.predict(text)[0][0], "CA03.Z")

    def test_taxonomy_negative_does_not_reverse_virus_identification(self):
        self.assertEqual(
            self.model.predict("Diagnosis: COVID-19, virus not identified.")[0][0],
            "RA01.1",
        )
        self.assertEqual(
            self.model.predict("Diagnosis: COVID-19, virus identified.")[0][0], "RA01.0"
        )

    def test_maternal_care_supplies_obstetric_context(self):
        text = (
            "Diagnosis: Maternal care for disproportion due to unusually large fetus."
        )
        self.assertEqual(self.model.predict(text)[0][0], "JA83.5")

    def test_family_diabetes_is_not_patient_diabetes(self):
        note = "42M. Father known T2DM. Patient has no diabetes. Assessment: Hypoglycaemia without associated diabetes."
        self.assertEqual(self.model.predict(note)[0][0], "5A41")

    def test_protein_does_not_supply_proteus_evidence(self):
        note = "27F dysuria. Urine protein trace, nitrite positive, culture pending. Assessment: UTI."
        self.assertEqual(self.model.predict(note)[0][0], "GC08.Z")

    def test_cli_preserves_ids_and_unicode(self):
        with tempfile.TemporaryDirectory() as d:
            inp, out = Path(d) / "in.jsonl", Path(d) / "out.jsonl"
            data = [{"id": "α", "text": "Fever and cough"}, {"id": "é", "text": ""}]
            inp.write_text("\n".join(json.dumps(x) for x in data))
            env = {
                k: v
                for k, v in os.environ.items()
                if k not in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY")
            }
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "coder.cli",
                    str(inp),
                    str(out),
                    "--model",
                    "artifacts/offline.joblib",
                ],
                check=True,
                env=env,
                capture_output=True,
            )
            result = [json.loads(x) for x in out.read_text().splitlines()]
            self.assertEqual([r["id"] for r in result], [r["id"] for r in data])
            self.assertTrue(all(set(r["codes"]) <= self.model.valid for r in result))

    def test_input_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            inp = Path(d) / "in.jsonl"
            inp.write_text('{"id":"x","text":"cough"}\n')
            before = inp.read_bytes()
            p = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "coder.cli",
                    str(inp),
                    str(inp),
                    "--model",
                    "artifacts/offline.joblib",
                ],
                capture_output=True,
            )
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual(inp.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()

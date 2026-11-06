"""A note-level ranking failure must not truncate the graded batch."""

import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from coder.engine import OfflineCoder
from coder.cli import main


class BatchRecovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = OfflineCoder.load("artifacts/offline.joblib")

    def test_prediction_exception_recovers_from_catalog(self):
        with patch.object(
            self.model, "predict", side_effect=RuntimeError("test failure")
        ):
            codes, diagnostic = self.model.safe_predict("Diagnosis: Cholera.")
        self.assertEqual(codes[0], "1A00")
        self.assertTrue(set(codes) <= self.model.valid)
        self.assertTrue(diagnostic["fallback"])
        self.assertEqual(diagnostic["failure_type"], "RuntimeError")

    def test_invalid_and_duplicate_codes_are_removed(self):
        with patch.object(
            self.model, "predict", return_value=(["invalid", "CA03.Z", "CA03.Z"], {})
        ):
            codes, _ = self.model.safe_predict("Acute tonsillitis")
        self.assertEqual(codes, ["CA03.Z"])

    def test_all_invalid_predictions_trigger_recovery(self):
        with patch.object(self.model, "predict", return_value=(["invalid"], {})):
            codes, diagnostic = self.model.safe_predict("Cholera")
        self.assertTrue(codes and set(codes) <= self.model.valid)
        self.assertTrue(diagnostic["fallback"])

    def test_cli_continues_and_flushes_after_a_failed_note(self):
        with tempfile.TemporaryDirectory() as directory:
            inp = Path(directory) / "notes.jsonl"
            out = Path(directory) / "predictions.jsonl"
            records = [
                {"id": "a", "text": "Diagnosis: Cholera."},
                {"id": "b", "text": "simulate note failure"},
                {"id": "c", "text": "Dx: Acute bronchitis."},
            ]
            inp.write_text("".join(json.dumps(r) + "\n" for r in records))
            original = self.model.predict
            calls = []

            def predict(text):
                # Previous outputs are visible on disk before the next note.
                self.assertEqual(len(out.read_text().splitlines()), len(calls))
                calls.append(text)
                if text == "simulate note failure":
                    raise ValueError("simulated note-level error")
                return original(text)

            with (
                patch.object(OfflineCoder, "load", return_value=self.model),
                patch.object(self.model, "predict", side_effect=predict),
                patch.object(sys, "argv", ["coder", str(inp), str(out)]),
                contextlib.redirect_stderr(io.StringIO()) as err,
            ):
                main()
            result = [json.loads(l) for l in out.read_text().splitlines()]
            self.assertEqual([r["id"] for r in result], ["a", "b", "c"])
            self.assertTrue(
                all(
                    1 <= len(r["codes"]) <= 3 and set(r["codes"]) <= self.model.valid
                    for r in result
                )
            )
            self.assertEqual(json.loads(err.getvalue())["fallback_predictions"], 1)

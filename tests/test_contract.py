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
        cls.model = OfflineCoder.load('artifacts/offline.joblib')

    def test_assessment_beats_negated_history(self):
        note = 'Hx: malaria in the past.\nDx: Upper respiratory infection. Malaria excluded.\nPlan: fluids'
        self.assertEqual(focus(note), 'Upper respiratory infection. Malaria excluded.')

    def test_no_network_and_broad_code_space(self):
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('network call')):
            for note in ['', 'Unknown narrative', 'Acute myocardial infarction', 'dolor de cabeza']:
                codes, _ = self.model.predict(note)
                self.assertTrue(1 <= len(codes) <= 3)
                self.assertEqual(len(codes), len(set(codes)))
                self.assertTrue(set(codes) <= self.model.valid)
        self.assertEqual(len(self.model.valid), 18375)

    def test_patient_speculation_is_not_assessment(self):
        text = "Patient: I think it's my thyroid.\nDoctor: Your thyroid is normal. This is obesity."
        self.assertEqual(focus(text), 'obesity')

    def test_plain_diagnosis_can_use_unspecified_leaf(self):
        model = self.model
        codes, _ = model.predict('Dx: Acute tonsillitis.', use_examples=False)
        self.assertEqual(codes[0], 'CA03.Z')

    def test_cli_preserves_ids_and_unicode(self):
        with tempfile.TemporaryDirectory() as d:
            inp, out = Path(d)/'in.jsonl', Path(d)/'out.jsonl'
            data = [{'id': 'α', 'text': 'Fever and cough'}, {'id': 'é', 'text': ''}]
            inp.write_text('\n'.join(json.dumps(x) for x in data))
            env = {k:v for k,v in os.environ.items() if k not in ('OPENAI_API_KEY','ANTHROPIC_API_KEY')}
            subprocess.run([sys.executable,'-m','coder.cli',str(inp),str(out),'--model','artifacts/offline.joblib'],check=True,env=env,capture_output=True)
            result = [json.loads(x) for x in out.read_text().splitlines()]
            self.assertEqual([r['id'] for r in result], [r['id'] for r in data])
            self.assertTrue(all(set(r['codes']) <= self.model.valid for r in result))

    def test_input_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            inp = Path(d)/'in.jsonl'
            inp.write_text('{"id":"x","text":"cough"}\n')
            before = inp.read_bytes()
            p = subprocess.run([sys.executable,'-m','coder.cli',str(inp),str(inp),'--model','artifacts/offline.joblib'],capture_output=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual(inp.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()

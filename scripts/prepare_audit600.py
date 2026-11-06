"""Freeze 600 distinct public dialogue texts for contract/throughput testing only."""

import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.request

ROOT = Path("reports/assignment-audit600")
REV = "3ff0801933608d6f570468c13125125fb5cabdea"
FILES = [
    ("test1", "MTS-Dialog-TestSet-1-MEDIQA-Chat-2023.csv"),
    ("test2", "MTS-Dialog-TestSet-2-MEDIQA-Sum-2023.csv"),
    ("validation", "MTS-Dialog-ValidationSet.csv"),
    ("training", "MTS-Dialog-TrainingSet.csv"),
]


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "input").mkdir(exist_ok=True)
    seen = set()
    notes = []
    sources = []
    for split, name in FILES:
        url = f"https://raw.githubusercontent.com/abachaa/MTS-Dialog/{REV}/Main-Dataset/{name}"
        data = urllib.request.urlopen(url, timeout=45).read()
        records = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
        selected = 0
        for i, r in enumerate(records):
            if len(notes) == 600:
                break
            text = r["dialogue"]
            sha = hashlib.sha256(text.encode()).hexdigest()
            if sha in seen:
                continue
            seen.add(sha)
            selected += 1
            notes.append({"id": f"audit-{split}-{r.get('ID', i)}", "text": text})
        sources.append(
            {
                "split": split,
                "url": url,
                "csv_sha256": hashlib.sha256(data).hexdigest(),
                "source_rows": len(records),
                "selected": selected,
            }
        )
        if len(notes) == 600:
            break
    assert len(notes) == len(seen) == len({r["id"] for r in notes}) == 600
    dev = [json.loads(l) for l in Path("data/dev_notes.jsonl").read_text().splitlines()]
    assert not seen & {hashlib.sha256(r["text"].encode()).hexdigest() for r in dev}
    payload = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in notes).encode()
    (ROOT / "input/notes.jsonl").write_bytes(payload)
    manifest = {
        "purpose": "600-text contract and throughput audit; NOT clinical ICD-11 accuracy or the employer hidden set.",
        "source": "MTS-Dialog, Ben Abacha et al., EACL 2023",
        "license": "CC-BY-4.0",
        "source_commit": REV,
        "selection": "Source split order above; CSV row order; exact text SHA-256 deduplication; stop at600. Only id/dialogue enter inference. Source training split is inference-only here, never model training.",
        "n": len(notes),
        "unique_texts": len(seen),
        "training_text_overlap": 0,
        "source_files": sources,
        "input_sha256": hashlib.sha256(payload).hexdigest(),
        "icd11_gold_available": False,
        "patient_independence": "Not asserted; distinct dialogue texts can be sections or related encounters.",
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

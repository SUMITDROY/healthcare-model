"""Exact-title regression probes across chapters; NOT clinical accuracy.

Labels are mechanically derived from the same allowed category catalog. They
test vocabulary coverage/context handling, not diagnosis inference.
"""

import argparse
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coder.engine import OfflineCoder, rows


def generate():
    categories = json.loads(Path("data/mms-2026-01.json").read_text())
    observed = {c for r in rows("data/dev_notes.jsonl") for c in r["gold"]}
    rng = random.Random(20261105)
    grouped = {}
    for c in categories:
        if c["leaf"] and c["code"] not in observed:
            grouped.setdefault(c["chapter"], []).append(c)
    selected = []
    for chapter in sorted(grouped):
        rng.shuffle(grouped[chapter])
    for index in range(8):
        for chapter in sorted(grouped):
            if len(selected) == 200:
                break
            selected.append(grouped[chapter][index])
    probes = []
    for i, c in enumerate(selected):
        title = c["title"]
        texts = [
            f"Outpatient visit.\nHistory: stable hypertension.\nAssessment: {title}.\nPlan: review.",
            f"Patient seen today. Dx: {title}. Plan: follow up.",
            f"Patient: I think it is malaria.\nDoctor: This is {title}.\nDoctor: Malaria has been excluded.",
        ]
        probes.append(
            {
                "id": f"catalog-probe-{i:03d}",
                "text": texts[i % 3],
                "gold": [c["code"]],
                "chapter": c["chapter"],
                "type": "synthetic explicit-title retrieval probe",
            }
        )
    Path("data/catalog_probes.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in probes) + "\n"
    )
    return probes


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--generate", action="store_true")
    p.add_argument("--model", default="artifacts/offline.joblib")
    p.add_argument("--report", default="reports/catalog-probes.json")
    a = p.parse_args()
    probes = generate() if a.generate else rows("data/catalog_probes.jsonl")
    model = OfflineCoder.load(a.model)
    one = three = 0
    failed = []
    for r in probes:
        codes, _ = model.predict(r["text"])
        top1 = codes[0] in r["gold"]
        top3 = bool(set(codes) & set(r["gold"]))
        one += top1
        three += top3
        if not top1:
            failed.append({"id": r["id"], "gold": r["gold"], "pred": codes})
    report = {
        "scope": "Synthetic exact-title retrieval probes; NOT clinical accuracy or hidden-score estimate",
        "n": len(probes),
        "chapters": len({r["chapter"] for r in probes}),
        "top1_hits": one,
        "top3_hits": three,
        "top1_accuracy": round(one / len(probes), 4),
        "top3_accuracy": round(three / len(probes), 4),
        "seed": 20261105,
        "all_codes_absent_from_training_labels": not bool(
            {c for r in probes for c in r["gold"]}
            & {c for r in model.examples for c in r["gold"]}
        ),
        "failures": failed,
    }
    Path(a.report).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "failures"}, indent=2))


if __name__ == "__main__":
    main()

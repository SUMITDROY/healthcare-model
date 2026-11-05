"""Regression controls only; never describe these as independent accuracy."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coder.engine import OfflineCoder, rows


def main():
    model = OfflineCoder.load("artifacts/offline.joblib")
    report = {
        "scope": "Engineer-authored/debugging controls; not independent clinical validation",
        "sets": {},
    }
    for name in ("clinical_probes", "language_probes"):
        file = Path("data") / (name + ".jsonl")
        if not file.exists():
            continue
        result = []
        for r in rows(file):
            assert set(r["gold"]) <= model.valid
            codes, diagnostic = model.predict(r["text"])
            result.append(
                {
                    "id": r["id"],
                    "gold": r["gold"],
                    "pred": codes,
                    "top1": codes[0] in r["gold"],
                    "top3": bool(set(codes) & set(r["gold"])),
                    "language": diagnostic.get("language", "en"),
                }
            )
        report["sets"][name] = {
            "n": len(result),
            "top1_hits": sum(r["top1"] for r in result),
            "top3_hits": sum(r["top3"] for r in result),
            "results": result,
        }
        print(
            name,
            len(result),
            report["sets"][name]["top1_hits"],
            report["sets"][name]["top3_hits"],
        )
        for r in result:
            if not r["top1"]:
                print("Failure:", r)
    Path("reports/control-results.json").write_text(json.dumps(report, indent=2) + "\n")
    if any(s["top1_hits"] != s["n"] for s in report["sets"].values()):
        raise SystemExit(
            "Regression control failure; inspect reports/control-results.json"
        )


if __name__ == "__main__":
    main()

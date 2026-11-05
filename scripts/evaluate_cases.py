"""Evaluate frozen cases without fitting; keep inspected regressions separate."""

import argparse
import hashlib
import json
from pathlib import Path
import socket
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coder.engine import OfflineCoder, rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cases", default="reports/exam-development/cases.jsonl")
    p.add_argument("--report", default="reports/exam-development/current.json")
    a = p.parse_args()

    def blocked(*a, **k):
        raise RuntimeError("Network disabled during evaluation")

    socket.socket.connect = blocked
    socket.create_connection = blocked
    model = OfflineCoder.load("artifacts/offline.joblib")
    data = rows(a.cases)
    start = time.perf_counter()
    results = []
    for row in data:
        lang = row.get("language", "en")
        gold = row.get("gold", row.get("proxy_icd11"))
        diagnosis = row.get("diagnosis", row.get("reference_answer"))
        for mode in ("symptoms_only", "documented_diagnosis"):
            text = row["text"]
            if mode == "documented_diagnosis":
                heading = {"en": "Assessment", "fr": "Diagnostic", "es": "Diagnóstico"}[
                    lang
                ]
                text += "\n" + heading + ": " + diagnosis
            codes, diag = model.predict(text)
            results.append(
                {
                    "id": row["id"],
                    "language": lang,
                    "mode": mode,
                    "gold": gold,
                    "pred": codes,
                    "top1": codes[0] in gold,
                    "top3": bool(set(codes) & set(gold)),
                    "strict": row.get("exact_category_title_match", True),
                    "path": diag.get("path"),
                    "symptom_path": diag.get("symptom_retrieval", False),
                }
            )
    groups = {}
    for strict in (True, False):
        for mode in ("symptoms_only", "documented_diagnosis"):
            for lang in sorted({r["language"] for r in results}):
                rr = [
                    r
                    for r in results
                    if r["language"] == lang
                    and r["mode"] == mode
                    and (not strict or r["strict"])
                ]
                groups[f"{'strict' if strict else 'all'}/{mode}/{lang}"] = {
                    "n": len(rr),
                    "top1": sum(r["top1"] for r in rr),
                    "top3": sum(r["top3"] for r in rr),
                }
    report = {
        "scope": "Mechanically aligned clinical exam cases, not adjudicated ICD-11 outpatient accuracy. Inspected development cases are not independent validation.",
        "cases_sha256": hashlib.sha256(Path(a.cases).read_bytes()).hexdigest(),
        "model_sha256": hashlib.sha256(
            Path("artifacts/offline.joblib").read_bytes()
        ).hexdigest(),
        "seconds_excluding_load": time.perf_counter() - start,
        "groups": groups,
        "api_calls": 0,
        "api_cost_usd": 0,
        "results": results,
    }
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()

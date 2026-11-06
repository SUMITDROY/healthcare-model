"""Read-only requirements checks after running the assignment command."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

SUPPLIED = {
    "score.py": "117386e9c5080bb3926cddcab8e95033d39ed33f0fbd1f1c1cdbaacc5b373e56",
    "data/dev_notes.jsonl": "8ebe97b2215f98b8d13c372f2d0424ece8967761c0f45720511f5ef8737223a0",
    "data/mms-2026-01.json": "bcedb28e33edb64e8e3c98464f1ada55ac5233e2475b0760ebb2c2e3c5e88dce",
}


def rows(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/notes.jsonl")
    p.add_argument("--pred", default="reports/predictions.jsonl")
    p.add_argument("--dev-pred", default="reports/final-dev-predictions.jsonl")
    p.add_argument("--benchmark", default="reports/assignment-audit600/benchmark.json")
    p.add_argument("--output", default="reports/assignment-audit600/requirements.json")
    a = p.parse_args()
    supplied_unchanged = {
        name: hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha
        for name, sha in SUPPLIED.items()
    }
    assert all(supplied_unchanged.values()), "A supplied scoring/reference file changed"
    data = rows(a.input)
    pred = rows(a.pred)
    catalog = json.loads(Path("data/mms-2026-01.json").read_text())
    valid = {r["code"] for r in catalog}
    ids = [r["id"] for r in data]
    out_ids = [r["id"] for r in pred]
    assert len(data) == 600 and len(set(ids)) == 600, "Expected600unique audit IDs"
    assert ids == out_ids, "Missing/extra/reordered output IDs"
    assert all(
        set(r) == {"id", "codes"}
        and isinstance(r["codes"], list)
        and 1 <= len(r["codes"]) <= 3
        and len(r["codes"]) == len(set(r["codes"]))
        and all(isinstance(c, str) and c in valid for c in r["codes"])
        for r in pred
    ), "Invalid output schema/codes"
    benchmark = json.loads(Path(a.benchmark).read_text())
    assert (
        benchmark["input_sha256"]
        == hashlib.sha256(Path(a.input).read_bytes()).hexdigest()
    )
    assert benchmark["input_notes"] == benchmark["output_notes"] == 600
    assert (
        benchmark["missing_ids"]
        == benchmark["invalid_codes"]
        == benchmark["empty_predictions"]
        == 0
    )
    assert benchmark["api_calls"] == benchmark["api_cost_usd"] == 0
    assert benchmark["wall_seconds_including_import_and_model_load"] <= 1800, (
        "Outside user half-hour target"
    )
    assert benchmark["peak_process_rss_mib"] <= 8192, "Outside user8GiB target"
    quota, period = map(int, benchmark["cgroup_cpu_max"].split())
    assert quota / period <= 4
    assert int(benchmark["cgroup_memory_max_bytes"]) <= 8 * 1024**3
    scorer = subprocess.run(
        [
            sys.executable,
            "score.py",
            "--gold",
            "data/dev_notes.jsonl",
            "--pred",
            a.dev_pred,
            "--mms",
            "data/mms-2026-01.json",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    dev = rows("data/dev_notes.jsonl")
    dp = {r["id"]: r["codes"] for r in rows(a.dev_pred)}
    one = sum(bool(dp.get(r["id"])) and dp[r["id"]][0] in r["gold"] for r in dev)
    three = sum(bool(set(dp.get(r["id"], [])) & set(r["gold"])) for r in dev)
    assert one >= 56 and three >= 58, "Visible coding performance regressed"
    report = {
        "scope": "Assignment contract/package/resource audit, not hidden clinical accuracy validation.",
        "supplied_files_unchanged": supplied_unchanged,
        "audit_input": "600distinct public MTS-Dialog texts; not employer hidden notes",
        "input_sha256": benchmark["input_sha256"],
        "notes": 600,
        "valid_outputs": 600,
        "missing_ids": 0,
        "output_codes_only_from_whitelist": True,
        "allowed_categories": len(valid),
        "chapters": len({r["chapter"] for r in catalog}),
        "incremental_flush": "Unit test verifies output on disk before the next prediction; middle-note failure recovery covered.",
        "no_key_path": True,
        "runtime_network": "none via compose; socket guard in resource benchmark",
        "api_cost_usd": 0,
        "wall_seconds": benchmark["wall_seconds_including_import_and_model_load"],
        "peak_process_rss_mib": benchmark["peak_process_rss_mib"],
        "cpu_limit": quota / period,
        "memory_limit_bytes": int(benchmark["cgroup_memory_max_bytes"]),
        "fallback_predictions": benchmark.get("fallback_predictions"),
        "dev_top1": f"{one}/60",
        "dev_top3": f"{three}/60",
        "supplied_scorer_output": scorer.stdout,
        "readme_words": len(Path("README.md").read_text().split()),
        "real_decision_history": "Retained in Git; contemporaneous entries and failed experiments included.",
        "api_enhancement": "Optional in the brief; this implementation always chooses offline inference.",
        "hours_reporting": "Applicant-provided estimate: approximately 8–14 hours, with AI assistance.",
        "email_submission": "Not sent; user must reply to the original thread within the assigned window.",
        "quality_limitations": "Most-specific checks and broad taxonomy/language retrieval implemented; no guarantee of hidden accuracy or clinical diagnosis from symptoms. Medical-exam diagnosis is an extra stress test, not the specified deliverable.",
        "status": "PASS technical checks and hours disclosure; actual email submission remains open.",
    }
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    Path(a.output).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

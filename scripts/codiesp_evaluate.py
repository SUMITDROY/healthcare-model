"""External Spanish case probe. Derived ICD-11 proxies are NOT ICD-11 gold.

Prepare separately, freeze before evaluating; never train or tune on this set.
"""

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import time
import unicodedata
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REVISION = "5ff2b006ea74699eccd393a5a0f3b99396d01e0c"
BASE = (
    "https://huggingface.co/datasets/Biomedical-TeMU/CodiEsp_corpus/resolve/"
    + REVISION
    + "/"
)
ROOT = Path("reports/codiesp")


def norm(text):
    text = "".join(
        c
        for c in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(c)
    )
    return " ".join(re.findall(r"\w+", text))


def fetch(path):
    with urllib.request.urlopen(BASE + path, timeout=45) as f:
        return f.read()


def prepare():
    ROOT.mkdir(parents=True, exist_ok=True)
    annotations = fetch("dev/devX.tsv")
    readme = fetch("README.md")
    (ROOT / "devX.tsv").write_bytes(annotations)
    (ROOT / "SOURCE-README.md").write_bytes(readme)
    catalog = json.loads(Path("data/mms-2026-01.json").read_text())
    leaf = {r["code"] for r in catalog if r["leaf"]}
    terms = defaultdict(set)
    with gzip.open("data/who-2026-01-es.jsonl.gz", "rt") as f:
        for r in map(json.loads, f):
            if r["code"] not in leaf:
                continue
            labels = [r["title"]]
            labels += [
                v.get("label", "")
                for k in ("indexTerm", "inclusion")
                for v in r.get(k, [])
            ]
            for label in labels:
                if isinstance(label, dict):
                    label = label.get("@value", "")
                key = norm(label)
                if key:
                    terms[key].add(r["code"])
    by_doc = defaultdict(list)
    diagnoses = 0
    for row in csv.reader(io.StringIO(annotations.decode()), delimiter="\t"):
        if len(row) < 5 or row[1] != "DIAGNOSTICO":
            continue
        diagnoses += 1
        match = terms.get(norm(row[3]), set())
        if len(match) == 1:
            by_doc[row[0]].append(
                {
                    "source_icd10": row[2],
                    "mention": row[3],
                    "positions": row[4],
                    "proxy_icd11": next(iter(match)),
                }
            )
    # Select every document with at least one unique exact match, before prediction.
    ids = sorted(by_doc)

    def download(doc):
        payload = fetch("dev/text_files/" + doc + ".txt")
        text = payload.decode("utf-8")
        return {
            "id": "codiesp-" + doc,
            "source_id": doc,
            "text": text,
            "text_sha256": hashlib.sha256(payload).hexdigest(),
            "annotations": by_doc[doc],
            "proxy_codes": sorted({r["proxy_icd11"] for r in by_doc[doc]}),
        }

    with ThreadPoolExecutor(max_workers=8) as pool:
        cases = list(pool.map(download, ids))
    payload = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in cases).encode()
    (ROOT / "cases.jsonl").write_bytes(payload)
    manifest = {
        "source": BASE,
        "revision": REVISION,
        "license": "CC-BY-4.0",
        "citation": "Miranda-Escalada, Gonzalez-Agirre & Krallinger (2020), CodiEsp corpus",
        "source_split": "dev; external to Sugen model development",
        "selection": "All source documents with at least one diagnosis annotation whose normalized mention exactly matches WHO Spanish title/indexTerm/inclusion for exactly one allowed leaf. No predictions used for selection. No ICD-10-to-ICD-11 crosswalk is asserted.",
        "source_diagnosis_annotations": diagnoses,
        "selected_cases": len(cases),
        "matched_annotations": sum(len(r["annotations"]) for r in cases),
        "proxy_code_count": len({c for r in cases for c in r["proxy_codes"]}),
        "cases_sha256": hashlib.sha256(payload).hexdigest(),
        "annotations_sha256": hashlib.sha256(annotations).hexdigest(),
        "who_sha256": hashlib.sha256(
            Path("data/who-2026-01-es.jsonl.gz").read_bytes()
        ).hexdigest(),
        "limitations": [
            "Exact-term filtering introduces selection bias.",
            "Mapped codes are reference-derived proxies, not clinician-adjudicated ICD-11 gold.",
            "Case reports contain multiple/historical diagnoses; any-label hit does not establish primary-diagnosis accuracy.",
            "Spanish only; no French or mixed-language validation.",
        ],
        "frozen_before_inference": True,
        "used_for_training": False,
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


def evaluate():
    # Evaluation is offline even if prepare used the network.
    import socket

    def blocked(*args, **kwargs):
        raise RuntimeError("Network disabled during evaluation")

    socket.socket.connect = blocked
    socket.create_connection = blocked
    from coder.engine import OfflineCoder, rows

    manifest = json.loads((ROOT / "manifest.json").read_text())
    payload = (ROOT / "cases.jsonl").read_bytes()
    assert hashlib.sha256(payload).hexdigest() == manifest["cases_sha256"]
    cases = rows(ROOT / "cases.jsonl")
    model = OfflineCoder.load("artifacts/offline.joblib")
    training = {hashlib.sha256(r["text"].encode()).hexdigest() for r in model.examples}
    assert not training & {r["text_sha256"] for r in cases}
    start = time.perf_counter()
    results = []
    for row in cases:
        codes, diag = model.predict(row["text"])
        proxy = set(row["proxy_codes"])
        results.append(
            {
                "id": row["id"],
                "proxy_codes": row["proxy_codes"],
                "pred": codes,
                "any_proxy_top1": codes[0] in proxy,
                "any_proxy_top3": bool(set(codes) & proxy),
                "detected_language": diag.get("language", "en"),
            }
        )
    n = len(results)
    report = {
        "scope": "External annotated Spanish case-report proxy probe, NOT ICD-11 accuracy or assignment score. No model changes after inspecting results.",
        "model_sha256": hashlib.sha256(
            Path("artifacts/offline.joblib").read_bytes()
        ).hexdigest(),
        "source_revision": REVISION,
        "cases_sha256": manifest["cases_sha256"],
        "n": n,
        "any_proxy_top1_hits": sum(r["any_proxy_top1"] for r in results),
        "any_proxy_top3_hits": sum(r["any_proxy_top3"] for r in results),
        "spanish_detected": sum(r["detected_language"] == "es" for r in results),
        "seconds_excluding_model_load": time.perf_counter() - start,
        "api_calls": 0,
        "api_cost_usd": 0,
        "exact_training_text_overlap": 0,
        "limitations": manifest["limitations"],
        "results": results,
    }
    (ROOT / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["prepare", "evaluate"])
    a = p.parse_args()
    prepare() if a.action == "prepare" else evaluate()

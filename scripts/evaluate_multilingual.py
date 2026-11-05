"""Reproducible synthetic context challenge, NOT independent clinical validation."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coder.engine import OfflineCoder, rows


def cases():
    for r in rows("data/language_probes.jsonl"):
        lang = r["language"]
        marker = "Diagnostic :" if lang == "fr" else "Diagnóstico:"
        diagnosis = r["text"].split(marker)[1].split(". ")[0].rstrip(".")
        variants = {
            "fr": {
                "conclusion": f"Consultation de suivi. Conclusion : {diagnosis}.",
                "unheaded": f"Le diagnostic retenu est {diagnosis}.",
                "family": f"Antécédents familiaux : la mère souffre de tuberculose. Diagnostic : {diagnosis}.",
                "negated": f"Absence de tuberculose. Diagnostic : {diagnosis}.",
                "contrast": f"Pas de tuberculose, mais {diagnosis}.",
                "history": f"Antécédents : tuberculose guérie. Évaluation : {diagnosis}.",
                "plan": f"Diagnostic : {diagnosis}. Traitement : dépistage de tuberculose prévu.",
                "unicode": f"CONCLUSION : {diagnosis.upper()}.",
            },
            "es": {
                "conclusion": f"Consulta de seguimiento. Conclusión: {diagnosis}.",
                "unheaded": f"El diagnóstico confirmado es {diagnosis}.",
                "family": f"Antecedentes familiares: la madre tiene tuberculosis. Diagnóstico: {diagnosis}.",
                "negated": f"Se descarta tuberculosis. Diagnóstico: {diagnosis}.",
                "contrast": f"No presenta tuberculosis, pero {diagnosis}.",
                "history": f"Antecedentes: tuberculosis resuelta. Valoración: {diagnosis}.",
                "plan": f"Diagnóstico: {diagnosis}. Plan: cribado de tuberculosis.",
                "unicode": f"CONCLUSIÓN: {diagnosis.upper()}.",
            },
        }[lang]
        for scenario, text in variants.items():
            yield {
                "id": r["id"] + "-" + scenario,
                "text": text,
                "gold": r["gold"],
                "language": lang,
                "scenario": scenario,
            }
    # Taxonomy coverage uses official localized titles, not clinical gold.
    catalog = json.loads(Path("data/mms-2026-01.json").read_text())
    if isinstance(catalog, dict):
        catalog = catalog.get("categories", catalog.get("codes", []))
    for lang in ("fr", "es"):
        with gzip.open(f"data/who-2026-01-{lang}.jsonl.gz", "rt") as f:
            records = {r["code"]: r for r in map(json.loads, f)}
        seen = set()
        for c in catalog:
            if not c["leaf"] or c["chapter"] in seen:
                continue
            seen.add(c["chapter"])
            title = records[c["code"]]["title"]
            if isinstance(title, dict):
                title = title.get("@value", "")
            yield {
                "id": f"{lang}-chapter-{c['chapter']}",
                "text": ("Diagnostic : " if lang == "fr" else "Diagnóstico: ")
                + title
                + ".",
                "gold": [c["code"]],
                "language": lang,
                "scenario": "official-title",
            }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="reports/multilingual-context.json")
    args = p.parse_args()
    dataset = list(cases())
    model = OfflineCoder.load("artifacts/offline.joblib")
    start = time.perf_counter()
    results = []
    for r in dataset:
        pred, diag = model.predict(r["text"])
        results.append(
            {
                **r,
                "pred": pred,
                "detected": diag.get("language", "en"),
                "top1": pred[0] in r["gold"],
                "top3": bool(set(pred) & set(r["gold"])),
            }
        )
    groups = {}
    for r in results:
        key = r["language"] + "/" + r["scenario"]
        g = groups.setdefault(
            key, {"n": 0, "top1": 0, "top3": 0, "language_correct": 0}
        )
        g["n"] += 1
        for k in ("top1", "top3"):
            g[k] += int(r[k])
        g["language_correct"] += r["detected"] == r["language"]
    report = {
        "scope": "Synthetic debugging challenge: 80 contextual variants of 10 existing controls (5 disease families), plus 52 official-title controls across 26 chapters. Not independent clinical validation; no clinician-adjudicated gold. No training on these rows.",
        "dataset_sha256": hashlib.sha256(
            json.dumps(dataset, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest(),
        "n": len(results),
        "top1": sum(r["top1"] for r in results),
        "top3": sum(r["top3"] for r in results),
        "seconds": time.perf_counter() - start,
        "groups": groups,
        "results": results,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        json.dumps(
            {k: v for k, v in report.items() if k != "results"},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

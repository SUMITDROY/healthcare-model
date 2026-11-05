"""Recreate external selection only. Original frozen baseline is never overwritten."""

import urllib.request, json, re, hashlib, sys
from pathlib import Path
from collections import defaultdict
import unicodedata


def norm(text):
    text = "".join(
        c
        for c in unicodedata.normalize("NFKD", text.casefold())
        if not unicodedata.combining(c)
    )
    text = " ".join(re.findall(r"\w+", text))
    return re.sub(
        r"^(?:a |an |the |le |la |les |l |el |los |las |un |une |una )", "", text
    ).strip()


sys.path.insert(0, str(Path.cwd()))
from coder.engine import OfflineCoder

ROOT = Path("reports/heldout-fr-recreated")
ROOT.mkdir(exist_ok=True)
rev = "5af34948a74c7b8807c476204a21149ffb00ea2c"
base = f"https://huggingface.co/datasets/ANR-MALADES/MediQAl/resolve/{rev}/"
import gzip

cat = {c["code"]: c for c in json.loads(Path("data/mms-2026-01.json").read_text())}
index = defaultdict(set)
for r in map(json.loads, gzip.open("data/who-2026-01-fr.jsonl.gz", "rt")):
    if cat[r["code"]]["leaf"]:
        index[norm(r["title"]["@value"])].add(r["code"])
url = base + "mcqu/test.json"
payload = urllib.request.urlopen(url, timeout=60).read()
sources = [json.loads(l) for l in payload.splitlines() if l.strip()]
rows = []
seen = set()
for r in sources:
    if not r.get("clinical_case") or not re.search(r"(?i)diagnost", r["question"]):
        continue
    if re.search(
        r"(?i)faux|fausse|sauf|incorrect|ne .{0,30}pas|n.est pas", r["question"]
    ):
        continue
    answer = r.get("correct_answers", "").strip().lower()
    if len(answer) != 1 or "answer_" + answer not in r:
        continue
    diagnosis = r["answer_" + answer]
    codes = index.get(norm(diagnosis), set())
    if len(codes) != 1:
        continue
    text = r["clinical_case"] + "\n" + r["question"]
    sha = hashlib.sha256(text.encode()).hexdigest()
    if sha in seen:
        continue
    seen.add(sha)
    rows.append(
        {
            "id": "mediqal-" + str(r["id"]),
            "text": text,
            "language": "fr",
            "diagnosis": diagnosis,
            "gold": [next(iter(codes))],
            "source_case_sha256": hashlib.sha256(
                r["clinical_case"].encode()
            ).hexdigest(),
        }
    )
raw = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode()
(ROOT / "cases.jsonl").write_bytes(raw)
manifest = {
    "source": url,
    "license": "CC-BY-4.0",
    "source_sha256": hashlib.sha256(payload).hexdigest(),
    "cases_sha256": hashlib.sha256(raw).hexdigest(),
    "n": len(rows),
    "selection": "French diagnosis questions with a single author answer exactly matching one allowed leaf title; no predictions used.",
    "scope": "External clinical-exam proxy probe, not expert-adjudicated ICD-11 outpatient gold.",
    "do_not_inspect_or_tune_on_results_before_final_policy": True,
}
(ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("Heldout frozen:", len(rows), "cases")

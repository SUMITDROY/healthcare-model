"""Build-time export from the documented local WHO ICD API, never at inference.

Run official container with include=2026-01_en, analytics disabled. Preserve
original records, titles, codes and URIs. Output is intersected with the supplied
catalog and pinned by a manifest/hash. Cache stays outside deliverables.
"""

import argparse
import concurrent.futures
import gzip
import hashlib
import json
from pathlib import Path
import time
import urllib.request


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="http://127.0.0.1:18811")
    p.add_argument("--cache", required=True)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--language", default="en")
    a = p.parse_args()
    start = time.perf_counter()
    catalog = Path("data/mms-2026-01.json")
    cats = json.loads(catalog.read_text())
    cache = Path(a.cache)
    cache.mkdir(parents=True, exist_ok=True)

    def fetch(c):
        path = c["uri"].split("/mms/", 1)[1]
        url = a.base_url + "/icd/release/11/2026-01/mms/" + path
        file = cache / (
            hashlib.sha256((a.language + " " + url).encode()).hexdigest() + ".json"
        )
        if file.exists():
            r = json.loads(file.read_text())
        else:
            for attempt in range(3):
                try:
                    req = urllib.request.Request(
                        url,
                        headers={
                            "Accept": "application/json",
                            "API-Version": "v2",
                            "Accept-Language": a.language,
                        },
                    )
                    with urllib.request.urlopen(req, timeout=30) as response:
                        r = json.load(response)
                    file.write_text(json.dumps(r, ensure_ascii=False))
                    break
                except Exception:
                    if attempt == 2:
                        raise
        if r.get("code") != c["code"]:
            raise ValueError(
                f"Catalog/API code mismatch: {c['code']} -> {r.get('code')}"
            )
        return r

    count = terms = definitions = fallbacks = 0
    dest = Path(f"data/who-2026-01-{a.language}.jsonl.gz")
    temporary = dest.with_suffix(".partial")
    with (
        open(temporary, "wb") as raw,
        gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as out,
    ):
        with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
            for r in pool.map(fetch, cats):
                out.write(
                    (
                        json.dumps(
                            r, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                        )
                        + "\n"
                    ).encode()
                )
                count += 1
                terms += len(r.get("indexTerm", []))
                definitions += bool(r.get("definition"))
                fallbacks += r["title"].get("@language") != a.language
                if count % 2000 == 0:
                    print(f"Exported {count}/{len(cats)}", flush=True)
    temporary.replace(dest)
    report = {
        "source": "World Health Organization ICD API local deployment",
        "release": "2026-01",
        "language": a.language,
        "image": "whoicd/icd-api@sha256:1b77eb6dc43e0c65a12e9e9340ad178493c93488e728d0d936507cc57ada1b7c",
        "records": count,
        "index_terms": terms,
        "records_with_definitions": definitions,
        "records_with_other_title_language": fallbacks,
        "catalog_sha256": hashlib.sha256(catalog.read_bytes()).hexdigest(),
        "export_sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
        "export_bytes": dest.stat().st_size,
        "export_seconds": round(time.perf_counter() - start, 2),
        "original_records_preserved": True,
        "runtime_downloads": False,
        "analytics_enabled": False,
        "documentation": "https://icd.who.int/docs/icd-api/ICDAPI-LocalDeployment/",
        "license": "https://icd.who.int/en/docs/icd11-license.pdf",
    }
    manifest = (
        "who-source.json" if a.language == "en" else f"who-source-{a.language}.json"
    )
    Path("third_party", manifest).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

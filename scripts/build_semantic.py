"""Download pinned, hash-checked model at BUILD time; precompute title vectors."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--directory", default="artifacts/semantic")
    p.add_argument("--batch-size", type=int, default=24)
    a = p.parse_args()
    start = time.perf_counter()
    dest = Path(a.directory)
    dest.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(Path("third_party/semantic-model.json").read_text())
    for item in manifest["files"]:
        path = dest / item["filename"]
        if (
            not path.exists()
            or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]
        ):
            print("Downloading pinned asset:", item["filename"], flush=True)
            with (
                urllib.request.urlopen(item["url"], timeout=120) as source,
                open(path.with_suffix(".download"), "wb") as target,
            ):
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)
            path.with_suffix(".download").replace(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Asset SHA-256 mismatch: " + str(path))
    from coder.semantic import SemanticIndex
    import numpy as np

    index = SemanticIndex(dest)
    categories = json.loads(Path("data/mms-2026-01.json").read_text())
    codes = [r["code"] for r in categories]
    # Raw official titles avoid introducing dev-label information into vectors.
    titles = [r["title"] for r in categories]
    if index.codes != codes:
        print(f"Embedding {len(titles)} category titles on CPU...", flush=True)
        # Per-chunk progress and incremental array fill bound memory use.
        vectors = np.empty((len(titles), 384), dtype=np.float32)
        for first in range(0, len(titles), 256):
            stop = min(first + 256, len(titles))
            vectors[first:stop] = index.encode(
                titles[first:stop], prefix="passage: ", batch_size=a.batch_size
            )
            if first % 2048 == 0:
                print(f"Embedded {stop}/{len(titles)}", flush=True)
        np.save(dest / "categories.npy", vectors)
        (dest / "codes.json").write_text(json.dumps(codes))
    print(
        json.dumps(
            {
                "semantic_build_seconds": round(time.perf_counter() - start, 2),
                "categories": len(codes),
                "revision": manifest["revision"],
            }
        )
    )


if __name__ == "__main__":
    main()

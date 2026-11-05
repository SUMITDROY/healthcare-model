"""The inference path imports no HTTP clients and never downloads assets."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from coder.engine import OfflineCoder


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument(
        "--model",
        default=os.environ.get("CODER_MODEL", "/app/artifacts/offline.joblib"),
    )
    p.add_argument("--diagnostics")
    a = p.parse_args()
    if Path(a.input).resolve() == Path(a.output).resolve():
        p.error("Input and output must be different files")
    start = time.perf_counter()
    model = OfflineCoder.load(a.model)
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    diagnostic_file = (
        open(a.diagnostics, "w", encoding="utf-8") if a.diagnostics else None
    )
    seen = set()
    count = 0
    try:
        with (
            open(a.input, encoding="utf-8") as source,
            open(a.output, "w", encoding="utf-8", buffering=1) as target,
        ):
            for number, line in enumerate(source, 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if "id" not in row or not isinstance(row.get("text"), str):
                    raise ValueError(f"Line {number}: expected id and string text")
                if row["id"] in seen:
                    raise ValueError(f"Duplicate input id: {row['id']}")
                seen.add(row["id"])
                codes, diagnostic = model.predict(row["text"])
                target.write(
                    json.dumps({"id": row["id"], "codes": codes}, ensure_ascii=False)
                    + "\n"
                )
                target.flush()
                if diagnostic_file:
                    diagnostic_file.write(
                        json.dumps({"id": row["id"], **diagnostic}, ensure_ascii=False)
                        + "\n"
                    )
                count += 1
    finally:
        if diagnostic_file:
            diagnostic_file.close()
    print(
        json.dumps(
            {
                "notes": count,
                "seconds_including_model_load": round(time.perf_counter() - start, 3),
                "mode": "offline",
                "api_calls": 0,
                "api_cost_usd": 0,
            }
        ),
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()

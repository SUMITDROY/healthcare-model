# Setup and validation

Run commands from the repository root. Docker with Compose is the supported submission environment. The first build needs internet to install pinned dependencies and builds indexes from packaged data. Inference needs no internet, API credentials, GPU or model service. Optional OpenAI/Anthropic API use is allowed by the assignment but is not implemented here: supplying keys does not change results.

## Run the packaged example

```sh
docker compose build
docker compose run --rm coder /in/notes.jsonl /out/predictions.jsonl
```

The assignment's exact command also works without `--rm`. This reads `data/notes.jsonl` and writes `reports/predictions.jsonl`. The input mount is read-only; the output directory must exist and be writable. Reusing an output path replaces previous predictions. Build time is separate from inference time.

## Run your own notes

Each line must contain a JSON object with a unique `id` and string `text`:

```json
{"id":"note-1","text":"Assessment: essential hypertension."}
```

Use absolute directories in place of the example paths:

```sh
mkdir -p /absolute/path/results
CODER_INPUT_DIR=/absolute/path/inputs CODER_OUTPUT_DIR=/absolute/path/results docker compose run --rm coder /in/notes.jsonl /out/predictions.jsonl
```

Output objects contain exactly `id` and `codes`: one to three unique allowed codes, best first. IDs retain their input type. Each result flushes to disk. A note-level inference exception invokes catalog-only recovery and allows later notes to continue; stderr reports recoveries. Invalid schemas and duplicate IDs require fixing the input. Input and output must be different files.

## Validate

```sh
docker compose run --rm --entrypoint python coder -m unittest discover -s tests
docker compose run --rm coder /app/data/dev_notes.jsonl /out/dev-recheck.jsonl
docker compose run --rm --entrypoint python coder score.py --gold data/dev_notes.jsonl --pred /out/dev-recheck.jsonl --mms data/mms-2026-01.json
docker compose run --rm --entrypoint python coder scripts/benchmark.py --input /in/notes.jsonl --output /out/benchmark-recheck-predictions.jsonl --report /out/benchmark-recheck.json
```

New output names preserve the committed audit. The benchmark removes API keys, blocks sockets and records elapsed time, process RSS, container limits and output validity. It does not measure clinical accuracy.

For local development use Python 3.12, install `requirements.txt`, then run `python -m coder.train`. Docker remains the reproducible reference. `artifacts/` is generated and Git-ignored. The optional semantic requirements/build script belong to a rejected experiment and are unnecessary for the default build.

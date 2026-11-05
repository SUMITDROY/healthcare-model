# Sugen offline coding baseline

An offline CPU prototype: TF-IDF word/character category retrieval, clinician-assessment extraction, explicit medical aliases and a supervised nearest-neighbour component fitted to all 60 supplied labeled notes. Searches all 18,375 supplied categories. No generative model is fine-tuned. No HTTP clients, API calls or runtime downloads. Build needs internet for Python packages.

## Run

```sh
docker compose build
docker compose run coder /in/notes.jsonl /out/predictions.jsonl
```

The default input is the independent 200-conversation external test. Output: `reports/predictions.jsonl`. For your own inputs set `CODER_INPUT_DIR` to their directory and `CODER_OUTPUT_DIR` to an output directory. Compose enforces 2 CPUs, 2 GiB RAM and no network; numerical-library thread counts are set to 1.

## Evidence and limits

- Offline Docker benchmark: 200 unique external conversations, 2.398 seconds including imports/model load, 190.50 MiB peak process RSS, zero missing/invalid/empty predictions, zero API spending. This is Linux ARM64 on a local Apple Silicon Docker VM; timings on x86 hardware can differ. Download/build/startup time is excluded.
- Official scorer on the **training set**: 75/75, top-1/top-3 100%. This is resubstitution, not evidence of generalisation.
- Five-fold out-of-fold check: top-1 34/60 (56.7%), top-3 40/60 (66.7%), 45/75. Each model excludes its held-out examples and fits its vocabulary without them. Aliases and parsing were developed after inspecting dev, so these results remain dev-informed. A no-example ablation also scores 45/75: the learned examples have not demonstrated a held-out improvement.
- Hidden-score estimate: not credibly established. For planning only, 40/100 is an uncalibrated conservative guess, not a measured forecast. Independent gold labels and broader language/chapter testing are still needed.
- Known gaps: clinical reasoning, reliable negation/uncertainty, unsupported specificity and multilingual coverage. This is a working baseline, not a final submission-quality system.

## Added data and evaluation

MTS-Dialog TestSet-1: 200 dialogue texts under CC BY 4.0, used only for inference. Source/commit/hash/license/attribution are in `third_party/`. No ICD-11 gold labels exist in that source, so external coding accuracy is unknown. Summaries are kept separate and never used for fitting/inference. No WHO enrichment has been added yet. Short terminology aliases were written with the supplied dev examples in view.

```sh
docker compose run --rm --entrypoint python coder scripts/benchmark.py --output /out/external-predictions.jsonl --report /out/benchmark.json
docker compose run --rm --entrypoint python coder scripts/evaluate.py
docker compose run --rm --entrypoint python coder -m unittest discover -s tests -v
python3 score.py --gold data/dev_notes.jsonl --pred reports/heldout-predictions.jsonl --mms data/mms-2026-01.json
```

Note: evaluation writes inside the disposable container unless paths are mounted. For persistent evaluation output use `docker compose run --rm -v "$PWD/reports:/app/reports" --entrypoint python coder scripts/evaluate.py`.

AI error caught: the first parser treated a patient's “it's my thyroid” as an assessment. It was restricted to clinician lines and a regression check was added. A second error was treating parent tonsillitis as equivalent to its appropriate unspecified leaf.

Applicant hours spent: not yet recorded; do not substitute agent execution time for your own hours.

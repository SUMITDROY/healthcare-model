# Sugen offline coding engine — v2

CPU-only ICD-11 coding: catalog-wide word/character retrieval, clinician-assessment and context rules, and a **pairwise logistic ranker trained on the 60 supplied labeled notes**. Evidence-based retrieval selects the first code; the learned model ranks alternatives. It can score all 18,375 categories, including codes absent from training labels. No nearest-note label lookup or LLM fine-tuning. No API calls or runtime downloads.

## Run

```sh
docker compose build
docker compose run coder /in/notes.jsonl /out/predictions.jsonl
```

Default input: the independent 200-conversation MTS-Dialog sample. Output: `reports/predictions.jsonl`. For other inputs set `CODER_INPUT_DIR` and `CODER_OUTPUT_DIR` to host directories. Compose enforces **2 CPUs, 2 GiB RAM, no network**, and one numerical-library thread. Build requires internet for packages and trains the local artifact automatically.

## Results and limits

- Dev-informed five-fold check: **44/60 top-1 (73.3%), 50/60 top-3 (83.3%), official score 57.5/75**. V1: 34/60, 40/60, 45/75. Each fold trains the ranker without its 12 held-out examples. Parsing/aliases/model selection used dev feedback, so this is not independent validation.
- Training-set score: 57.5/75. The old memorizing baseline's 75/75 is archived and is not evidence of generalisation. Untrained ranking ablation: 44/60 top-1, 48/60 top-3, 56.667/75.
- External 200-note Docker test: **5.0495 seconds**, 202.05 MiB peak process RSS, no missing/invalid/empty predictions, no keys and **$0 API cost**. Linux ARM64; build/container startup excluded. External ICD-11 accuracy is unknown because these records have no gold codes.
- Candidate recall: 58/60 within 50 candidates, 60/60 within 100. Synthetic exact-title debugging probes across all 26 chapters: 200/200 top-1/top-3. These expose parsing regressions, not clinical accuracy.
- Hidden-score estimate: provisional 60/100, an uncalibrated planning guess; the generalisation slice remains unmeasured. Known gaps include uncertainty, multi-condition encounter selection and multilingual clinical reasoning.

## Data, evaluation and AI tooling

Added MTS-Dialog TestSet-1 under CC BY 4.0 **for inference only**. Original summaries stay separate. Source commit/hash/attribution/license: `third_party/`. Synthetic catalog probes are clearly labeled, excluded from training and now used for debugging. No WHO definitions/synonyms have been downloaded; API credentials are needed. Handwritten aliases are dev-informed.

A pinned quantized multilingual E5 experiment regressed the initial English checks and remains disabled. Optional requirements, build script and provenance are retained; its weights are not in the default image or git bundle.

```sh
docker compose run --rm --entrypoint python coder scripts/benchmark.py --output /out/external-predictions.jsonl --report /out/benchmark.json
docker compose run --rm -v "$PWD/reports:/app/reports" --entrypoint python coder scripts/evaluate.py
docker compose run --rm --entrypoint python coder -m unittest discover -s tests -v
```

AI error caught: naive negation removal turned `virus not identified` into `virus`, reversing a coding distinction. Taxonomy negation is now preserved and tested. Historical `dx 2019` was also incorrectly parsed as the active assessment.

Applicant hours spent: not yet recorded; agent execution time is not a substitute.

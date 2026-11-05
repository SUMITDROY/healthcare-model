# Sugen offline ICD-11 coder — v4

CPU-only coding across all 18,375 permitted categories. Separate word/character, WHO term and definition searches feed evidence-based primary ranking; a pairwise alternative ranker is fitted to the 60 supplied notes. Explicit clinical facts and qualifier checks support specificity. French/Spanish use separate WHO indexes, language identification and bounded assertion/negation parsing. No generative model, paid API or runtime downloads.

## Run

```sh
docker compose build
docker compose run coder /in/notes.jsonl /out/predictions.jsonl
```

Default input: the independent 200-conversation MTS-Dialog sample. Output: `reports/predictions.jsonl`. Set `CODER_INPUT_DIR` / `CODER_OUTPUT_DIR` for other host directories. Compose enforces **2 CPUs, 2 GiB RAM, no network**, with one numerical-library thread. Build downloads packages and creates the local index from packaged reference data.

## Results and limits

- Dev-informed five-fold diagnostic: **56/60 top-1 (93.3%), 58/60 top-3 (96.7%), official core score 70.8/75**. V2: 44/60, 50/60, 57.5/75. V1: 34/60, 40/60, 45/75.
- Each fold excludes its 12 held-out notes when fitting the alternative ranker. Rules, aliases and approach choices used the visible dev set, so the figure is a development diagnostic, not independent accuracy. Training-set performance is also 70.8/75; removing the learned ranker gives the same aggregate result. Its held-out gain is not established in v3.
- External offline Docker benchmark: **200/200 outputs in 43.6538 seconds**, 549.48 MiB peak process RSS, no invalid/empty predictions, no keys, **$0 API cost**. Linux ARM64; image build/container startup excluded. External coding accuracy is unknown because these records have no ICD-11 gold labels.
- Beyond dev: 20 contract/regression tests; 20 clinical counterfactual controls; 10 French/Spanish terminology controls; 132 bilingual context/title challenges (108→132 first-choice hits); 200 exact-title probes across 26 chapters. All pass. These debugging controls are engineer-authored/catalog-derived, not independent clinical validation.
- Hidden-score estimate: provisional 80/100, an uncalibrated planning guess. Broader clinical accuracy, complex foreign narrative context and languages beyond English/French/Spanish remain unverified.

## Data and evaluation

Added official WHO MMS 2026-01 English/French/Spanish API records, preserving code/title/URI, and 324,197 index-term entries across the three releases. Compressed reference data is 10.65 MB. Supported local API export needs no cloud OAuth; all exports ship in the repo, so graders need no WHO service. License, provenance and SHA-256 manifests: `third_party/`.

MTS-Dialog TestSet-1 (CC BY 4.0) is inference-only; summaries remain separate. None of its 200 notes trains the model.

```sh
docker compose run --rm --entrypoint python coder scripts/benchmark.py --output /out/external-predictions.jsonl --report /out/benchmark.json
docker compose run --rm -v "$PWD/reports:/app/reports" --entrypoint python coder scripts/evaluate.py
```

AI error caught: a tested local model turned a Swahili age of 30 into a temperature and reversed uncomplicated malaria into severe disease. It was rejected; raw failure evidence is retained. Sparse substring pseudo-stemming also conflated protein with Proteus; full stemming and a counterfactual check corrected it.

Applicant hours spent: not yet supplied; agent execution time is recorded separately from applicant effort.

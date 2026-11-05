# Offline accuracy improvement — v2, 5 November 2026

The selected offline engine improves the dev-informed held-out first-choice result from 34 to 44 correct notes out of 60. The number with a correct code among the first three rises from 40 to 50. The official weighted core score rises from 45 to 57.5 out of 75.

## Accuracy evidence

- Current five-fold top-1: 44/60, or 73.3%.
- Current five-fold top-3: 50/60, or 83.3%.
- V1 five-fold top-1: 34/60, or 56.7%; top-3: 40/60, or 66.7%.
- Same deterministic five-fold split seed: 20261105. Each model trains its shared ranking function on 48 notes, excluding the other 12. Catalog-only vocabulary is shared reference knowledge, not held-out note text.
- Without trained alternative ranking: 44/60 top-1, 48/60 top-3. Learned alternatives add two top-3 hits without changing primary selection.
- Gold candidate recall: 58/60 in the first 50 retrieved categories; 60/60 in the first 100. Remaining dev failures are ranking/specificity/context errors rather than an inability to retrieve a gold code somewhere within that candidate pool.
- Current training-set score is also 57.5/75. V1's 75/75 training-set score reflected memorisation and must not be compared to held-out accuracy.

These are development diagnostics. Rules, aliases and approach selection used feedback from the same 60 notes. Repeated cross-validation on a visible dev set is not an unbiased unseen-accuracy estimate. No external clinical accuracy claim is made.

Raw evidence: `evaluation.json`, `heldout-score.txt`, `training-score.txt`, `heldout-diagnostics.jsonl` and the prediction JSONL files. V1 evidence is in `v1/`.

## What changed

1. Recognise inline diagnoses and prefer current assessment labels over historical statements such as “HIV dx 2019”.
2. Preserve boundaries between clinician statements, distinguish patient speculation, and remove short negative disease mentions from search queries.
3. Preserve taxonomy qualifiers such as “not identified”; recognise maternal context without requiring the literal word “pregnancy”.
4. Reduce unsupported congenital/neonatal/obstetric/traditional and complication-specific candidates; prefer a supported generic leaf over a broad parent where title checks permit.
5. Replace nearest-note label transfer with a small pairwise logistic ranking model trained from positive/negative code pairs. It learns shared evidence features, not a fixed classifier over observed labels. Rules choose the primary; learned ranking supplies alternatives.
6. Fit word vocabulary on the full catalog, keeping it stable across folds and clinics.

## External 200-note offline benchmark

- Input: all 200 unmodified dialogue texts from MTS-Dialog TestSet-1. No external test text was used for fitting or tuning. Zero exact-text overlap with the training notes.
- Runtime: **5.0495 seconds**, including imports, artifact load, inference and prediction writes; excludes image build/downloads and container startup.
- Hardware restrictions: **2 CPUs, 2 GiB RAM**, enforced by Docker cgroups. Numerical libraries use one thread; no GPU.
- Peak process RSS: **202.05 MiB**. Whole-container cgroup peak: approximately 256.55 MiB; these are different accounting measures.
- 200 input IDs, 200 output IDs. Missing IDs: 0. Invalid codes: 0. Empty predictions: 0.
- Networking disabled; socket connections additionally blocked. API keys removed. Inference API calls: 0; API spending: **$0**.
- Linux ARM64 in a local Docker VM. Performance on x86 hardware has not been measured.

These public records include encounter sections and are not always complete consultations. They have no gold ICD-11 labels. Successful output and valid codes do not establish correct clinical coding. Source: https://github.com/abachaa/MTS-Dialog ; full attribution and pinned source hash are in `third_party/`.

Machine-readable measurements are in `benchmark.json`; generated outputs are `external-predictions.jsonl` and `predictions.jsonl`.

## Additional regression coverage

Thirteen automated contract/regression checks pass in Docker, covering ID preservation, Unicode, no network, valid codes, input overwrite protection, inline/current assessments, patient speculation, complication distinctions, maternal care and taxonomy negation.

Two hundred synthetic exact-title probes span all 26 chapters and use codes absent from the 60 training labels. V1 scored 198/200 top-1; the first v2 pass scored 197/200. That exposed the maternal/negation regressions. After general fixes, v2 scores 200/200 top-1/top-3. This set was used for debugging and mechanically derives its labels from the catalog. It is not an independent clinical benchmark.

## Experiments retained, not enabled

The first quantized multilingual E5 fusion trial reduced held-out top-1 from 40/60 to 39/60 while adding model assets and CPU work. A full pointwise ranking model also regressed results. Shared pairwise ranking helps alternatives but did not justify replacing primary retrieval. These decisions and their intermediate results are retained in `DECISIONS.md` and `evaluation-*.json`.

The optional E5 source/revision/SHA-256 manifest and upstream/converter model cards are in `third_party/`, with `requirements-semantic.txt` and `scripts/build_semantic.py`. Default training/inference does not enable it or download it. WHO's official API requires credentials; no WHO enrichment is claimed.

## Next accuracy work

Prioritise independently reviewed labels covering more chapters/languages, official version-pinned terminology and hierarchy enrichment, and clinical assertion/specificity handling. The small visible dev sample cannot validate generalisation or establish a reliable hidden score.

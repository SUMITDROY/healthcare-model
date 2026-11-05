# Offline accuracy improvement — v3, 5 November 2026

Current development diagnostic: **56/60 correct first choices (93.3%)**, **58/60 with a correct code in the top three (96.7%)**, **70.833/75 weighted core points**. V2 achieved 44/60 and 50/60 (57.5/75); v1 achieved 34/60 and 40/60 (45/75).

## How to interpret the numbers

The same deterministic five-fold split is used (seed 20261105). Each alternative ranker is trained on 48 notes and predicts the other 12. However, parsing, facts, aliases and approach selection were developed with all 60 dev notes visible. These are dev-informed diagnostics, not an unbiased estimate of unseen clinical performance. Four top-1 failures remain; we froze the English scoring rules instead of chasing the final four.

The training-set and no-learned-ranker ablation also achieve 56/60 top-1 and 58/60 top-3. Thus the v3 gain comes from reference knowledge and evidence handling; a held-out benefit from the trained alternative ranker is not established. The current gold code appears in the first 50 candidates for all 60 notes.

The employer's private 600-note set is unavailable. The 200 external public conversations have no ICD-11 gold labels, so no independent clinical accuracy percentage is claimed.

Raw evidence: `evaluation.json`, official `heldout-score.txt` and `training-score.txt`, `heldout-diagnostics.jsonl` and prediction files. V1/v2 snapshots are retained under `v1/` and `v2/`.

## What changed

- Added official WHO 2026-01 metadata for every allowed category: titles, index terms, definitions, inclusion/exclusion metadata and real hierarchy links. English has 98,469 index-term entries; French 99,541; Spanish 126,187. Original records, codes and canonical URIs are preserved.
- Built separate stemmed term/definition indexes. French/Spanish reference indexes preserve English IDF and use language identification; these paths perform terminology lookup, not unrestricted clinical translation. Explicit pregnancy context can be projected through the shared WHO code identity. Other languages and complex foreign narrative context remain unverified.
- Corrected causal qualifier scope: later stage wording cannot act as evidence of malaria associated with HIV. Proper stemming prevents protein from acting as evidence of Proteus.
- Prefer fully supported leaf titles; extract explicit documented BP components, coma/awake evidence, pregnancy/onset and acquired-condition facts after identifying the clinician's stated diagnosis. Fact extraction emits evidence, never ICD code overrides.
- Distinguish current diagnosis, historical diagnoses, negative assertions and relatives' conditions. Counterfactual tests caught the father-to-patient diabetes ownership bug.
- Retain a small code-agnostic pairwise ranker for alternatives. A flexible primary tree ranker was rejected after its training result exceeded its held-out result substantially.

## Measured offline resources

The final benchmark uses all 200 unmodified dialogue texts from MTS-Dialog TestSet-1, kept outside fitting/tuning. There is zero exact-text overlap with the assignment's training examples.

- Wall time: **28.3638 seconds**, including imports, index/artifact loading, inference and output writes.
- CPU time: 28.3173 seconds. Inference mean: 99.982 ms/note; p95: 142.744 ms/note, excluding startup.
- Container quota: **2 CPUs and 2 GiB RAM**. Numerical-library threads: 1. No GPU.
- Peak process RSS: **550.39 MiB**. Whole-container cgroup peak: about **512.15 MiB**; the accounting methods differ.
- Inputs/outputs: **200/200**, no missing IDs, invalid codes or empty predictions.
- Keys removed; Compose networking disabled; socket guard active. **0 inference API calls, $0 API spending**.
- Platform: local Linux ARM64 Docker VM. x86 timings are not measured. Build, downloads and container startup are outside the inference timing.

The exact assignment command also passed and completed in 8.964 seconds including artifact loading. Raw benchmark: `benchmark.json`; predictions: `external-predictions.jsonl` and `predictions.jsonl`.

MTS-Dialog is a public dialogue/summary collection including encounter sections; many records are not complete consultations. Source, source commit, checksum, license and full attribution are in `third_party/`. https://github.com/abachaa/MTS-Dialog

## Regression checks beyond dev

- **15 automated contract/regression tests:** IDs, Unicode, valid codes, no network, overwrite protection, inline/current assessments, negated patient guesses, complication distinctions, maternal care, virus identification, family-history ownership and protein/Proteus separation.
- **20 clinical counterfactual controls:** documented organism versus pending culture, awake/coma/unknown status, relatives versus patient, hypertension subtype, pregnancy/age contexts and supported specificity.
- **10 French/Spanish terminology controls:** including pregnancy-related infection and diseases absent from the clinic sample.
- **200 synthetic exact-title probes across all 26 chapters**, with codes absent from the 60 training labels.

All pass. These controls are engineer-authored/catalog-derived and have been used for debugging. They are not independent clinical test notes or a hidden-score estimate. The initial failing controls are retained in reports.

## Rejected model experiments

Quantized multilingual E5 did not improve the original English diagnostic. A flexible tree primary ranker got 53/60 on training but 38/60 held out. Local Qwen3 candidate selectors were too unreliable to justify deployment; the larger model got two of three first-choice smoke cases, taking 7–10 seconds each and approximately 2.9 GiB peak process RSS.

More seriously, translation copied a French diagnosis and mistranslated a Swahili patient's age of 30 as a temperature of 30°C, while turning uncomplicated malaria into severe disease. These outputs are preserved under `experiments/`. The default engine contains no generative model or generative translator, and none of those rejected weights ships in the image/bundle.

## Provenance and reproducibility

Official WHO API exports preserve complete original category records and are intersected with the exact allowed code set. Every language covers 18,375 categories; French and Spanish have no title-language fallbacks. Source image/release/language and SHA-256 hashes are in `third_party/who-source*.json`; the WHO license and attribution are included. English cloud OAuth was avoided by the supported local API; the local exporter service is unnecessary for grading/runtime.

The trilingual export service needed a temporary 4-GiB preparation limit after a 2-GiB startup failed. This is separate from the shipped inference engine, which passed the 2-GiB benchmark and builds solely from packaged reference files. Temporary services/caches and rejected model downloads were removed. At the user's request, 3.912 GB of unused Docker build cache was reclaimed without deleting personal files or project data.

## Remaining accuracy work

Obtain an independently reviewed, locked clinical test set spanning more chapters, languages and ambiguous encounters. Improve assertion/temporal/context handling against that set. The provisional README hidden estimate is a planning judgment, not a measured forecast. Optional paid-model enhancement has not been implemented or benchmarked in this offline-first version.

Final reproducibility check: a separate clone built without a local artifact or cached training layer, passed the exact command, and emitted identical 200 predictions. The subsequent locked base/dependency build also passed 15 tests and all 30 controls. Evidence: `fresh-clone-v3.json`. The standalone evaluation commands now create their report directories inside clean containers.


## V4 — French/Spanish context regression (2026-11-05)

Added localized assessment headings, unheaded diagnosis assertions, sentence-scoped family-history removal, contrast-aware negation, and case-normalized language detection. Qualifiers such as sans/sin aura and unspecified remain intact. English “Conclusion” is not automatically classified as French. No model weights, API calls or runtime dependencies were added.

Frozen reproducible challenge: 132 rows, SHA-256 `787b1eb0a04b9fc4a3d30604d254570c3d5dc0c358c4eea76018c394c0452d9f`. Before: 108/132 top-1, 116/132 top-3. After: 132/132 for both. The 80 context variants reuse 10 existing controls (five disease families); 52 localized official-title checks cover all 26 chapters. Results are debugging evidence, not independent clinical accuracy. Cases were inspected during development, and the full 132 are therefore development controls. Full text, gold, predictions and per-scenario results are in `multilingual-before.json` and `multilingual-context.json`.

Reproduce: `python scripts/evaluate_multilingual.py`. This script neither fits the model nor reads the external MTS reference summaries. The official localized WHO titles supply gold only for the terminology controls; contextual cases inherit the existing engineer-authored control labels. No clinician adjudication is claimed. Generalisation to real multilingual consultations, code-switching, symptom-only narratives and other languages remains unverified. Resolving that broader claim requires independently labelled clinical records; passing this suite alone cannot establish it.

V4 packaged Docker check: 132/132 challenge first choices; 200 external notes in 43.6538 seconds, 549.48 MiB peak RSS, 2 CPUs/2 GiB, no network, zero API calls/cost and zero missing/invalid/empty outputs. See `v4-benchmark.json`. The bilingual challenge was run concurrently in a separate capped container.

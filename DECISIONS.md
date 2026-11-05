# Decision log

Entries name the commit subject they are committed with; `git log --oneline -- DECISIONS.md` resolves the matching commit hashes without a self-referential hash.

## 2026-11-05 13:50 IST — commit: `Initialize offline coder and independent internet test source`
- Decision: ship a CPU-only retrieval baseline before introducing a local generative model or paid API calls. Targets: <=4 CPUs, <=8 GB, 200 notes within 10 minutes.
- Alternatives: a quantized local LLM, API-only coding, or retrieval plus an optional API reranker.
- Evidence: 18,375 categories, 60 labeled examples, only 11 represented chapters. A small sparse index fits the hardware target; accuracy must be measured rather than assumed.
- Revisit: multilingual semantic retrieval and WHO enrichment once the baseline is reproducible.

## 2026-11-05 13:50 IST — commit: `Initialize offline coder and independent internet test source`
- Decision: use the supplied 60 labeled notes as supervised nearest-neighbour training examples, with explicit assessment extraction and broad category retrieval.
- Alternatives: train a classifier on 61 observed labels, or retrieve using titles alone.
- Evidence: a classifier restricted to observed labels cannot cover the other supplied categories. The chosen index retains all allowed codes.
- Revisit: title-only ablation and held-out validation; training-set scores must be labeled resubstitution.

## 2026-11-05 13:50 IST — commit: `Initialize offline coder and independent internet test source`
- Decision: reserve MTS-Dialog TestSet-1's 200 conversations strictly for inference, not training or tuning.
- Alternatives: scrape clinical websites, use credentialed patient data, or generate synthetic test notes.
- Evidence: a public 200-conversation release with CC BY 4.0 attribution and a pinned source commit is available. It lacks ICD-11 gold labels and includes note sections rather than complete consultations.
- Revisit: obtain independently reviewed ICD-11 labels before calling this an accuracy benchmark.

## 2026-11-05 13:50 IST — commit: `Initialize offline coder and independent internet test source`
- Decision: use a 2-CPU, 2-GiB container with `network_mode: none`; build the index during image build.
- Alternatives: host-only thread limits, or downloads at startup.
- Evidence: host-only thread limits do not prove memory/CPU isolation; runtime downloads violate the assignment's offline requirement.
- Revisit: Docker engine availability and measure actual container usage before reporting success.

## 2026-11-05 13:57 IST — commit: `Measure honest holdouts and correct context and specificity errors`
- Decision: preserve the initial results rather than presenting 75/75 on the training set as generalisation.
- Evidence: initial five-fold validation: top-1 15/60 (25%), top-3 27/60 (45%), score 23.75/75. Titles-only achieved 26.25/75. Training-set resubstitution was 75/75 and is not predictive of hidden performance.
- Options: report only the attractive dev score, or separate the training, ablation and held-out results. Chose the latter.
- Revisit: independent expert-labeled notes are needed for a credible unseen accuracy estimate.

## 2026-11-05 13:57 IST — commit: `Measure honest holdouts and correct context and specificity errors`
- Decision: restrict ambient assessment extraction to Doctor lines; add explicit terminology aliases; prefer a title-verified unspecified leaf over its generic non-leaf parent; gate weak exemplar matches.
- Evidence: dev-060's patient thyroid speculation and generic tonsillitis/pneumonia parent predictions exposed errors. Chickenpox/varicella and frozen shoulder/adhesive capsulitis show title-only vocabulary gaps. These are dev-informed changes, so cross-validation is diagnostic rather than an untouched test.
- Options: more training-note weight, code-by-code overrides, or general text/ranking changes. Chose transparent text/ranking changes without note-ID special cases.
- Revisit: official WHO aliases, reliable hierarchy metadata and context-aware exclusion handling. These heuristics do not solve clinical reasoning or multilingual coding.

## 2026-11-05 13:58 IST — commit: `Document offline benchmark and accuracy limitations`
- Decision: measure in a network-disabled 2-CPU/2-GiB container and add a socket guard rather than relying on host thread settings.
- Evidence: 200/200 external notes in 2.398 seconds; 190.50 MiB peak process RSS; no invalid/empty predictions, missing IDs, API calls or exact-text training overlap. Cgroup limits are saved in benchmark.json. This is ARM64, not an x86 performance claim.
- Revisit: x86 runtime and more diverse long-note workloads.

## 2026-11-05 13:58 IST — commit: `Document offline benchmark and accuracy limitations`
- Decision: keep the supervised exemplar component available but explicitly state that training has not yet demonstrated an out-of-fold gain.
- Evidence: updated five-fold top-1 34/60, top-3 40/60, score 45/75; the no-example ablation also gets 45/75. Training-set scoring is 75/75 and must not be called unseen accuracy.
- Alternatives: increase training-example influence to optimise resubstitution, remove the component immediately, or retain it as a documented baseline for more representative evaluation.
- Revisit: additional independent labeled notes and validation-selected weights.

## 2026-11-05 13:58 IST — commit: `Document offline benchmark and accuracy limitations`
- Decision: provide an entirely offline first implementation, with optional API enhancement deferred.
- Evidence: CPU throughput exceeds the requested target by a wide margin; accuracy, rather than speed or budget, is now the bottleneck. No paid API is needed to finish every note.
- Alternatives: spend the $2–3 allowance immediately or add a local generative model before measuring the retriever.
- Revisit: optional reranking after measuring candidate recall and obtaining independently labeled cases.

## 2026-11-05 14:01 IST — commit: `Record fresh-clone verification`
- Decision: verify from a fresh clone with `docker compose build --no-cache`, then run the assignment's exact command, rather than relying on the host's existing artifact or cached training layers.
- Evidence: source commit f6fe5f1 builds successfully; the exact command emits 200/200 valid predictions in 2.182 seconds including model load. Six automated contract/regression checks passed on the same code in Docker. Final changes after this check are documentation only.
- Alternatives: test only the host Python environment or rebuild using the existing image.
- Revisit: repeat on the target x86 Linux hardware and after any code changes.

## 2026-11-05 14:28 IST — commit: `Improve evidence parsing and train code-agnostic alternative ranking`
- Decision: fix inline assessment extraction, distinguish historical `dx 2019` from the current assessment, retain boundaries between spoken diagnostic clauses, reduce short negated spans, and check context required by congenital/neonatal/pregnancy/traditional categories.
- Evidence: v1's held-out 34/60 top-1 became 40/60 with the first context fixes. The next evidence/qualifier and title-family fixes produced 44/60 top-1 without supervised example matching.
- Options: note-specific overrides, more weight on matching training notes, or reusable parsing and category-evidence rules. Chose reusable rules; eleven regression/contract tests pass.
- Revisit: a real clinical assertion parser and official hierarchy/terminology enrichment. These heuristics remain dev-informed and have scope limitations.

## 2026-11-05 14:28 IST — commit: `Improve evidence parsing and train code-agnostic alternative ranking`
- Decision: remove nearest-note label transfer. Train a shared pairwise logistic ranking function on positive and negative category pairs from the supplied 60 notes. Fit search vocabulary on the catalog only. Retain the evidence-based first choice; use the trained function for the two alternatives.
- Evidence: full pointwise model reranking achieved only 40/60 held-out top-1. Pairwise reranking of all positions achieved 43/60 and 50/60 top-3. Keeping evidence-first top-1 with learned alternatives gives 44/60 top-1 and 50/60 top-3, or 57.5/75, versus v1's 45/75. Training-set performance is now 57.5/75 rather than a memorized 75/75.
- Options: a 61-class classifier, exemplar lookup, pointwise/pairwise full reranking, or learned alternatives. Shared features can score all 18,375 categories, including codes never used as training labels.
- Revisit: more representative independent labels may support learned primary selection. Repeated dev-informed validation is diagnostic, not an unbiased estimate.

## 2026-11-05 14:28 IST — commit: `Improve evidence parsing and train code-agnostic alternative ranking`
- Decision: leave quantized multilingual E5 disabled by default; retain a pinned, hashed offline-build experiment and the upstream/converter model cards.
- Evidence: first semantic fusion trial reduced held-out top-1 from 40/60 to 39/60 and top-3 from 47/60 to 46/60, while adding a 118 MB model, 17 MB tokenizer and 28 MB category vectors. Title embeddings built on CPU in 56 seconds. WHO's official API returned 401 without credentials; attempted public browser endpoints returned 404, so no WHO enrichment is claimed.
- Options: default semantic retrieval, lexical-only improvements, or a local generative model. Selected the smaller measured improvement and no runtime model downloads.
- Revisit: independently labeled multilingual examples and supervised hybrid fusion. Source manifest and optional requirements are retained for reproducibility.

## 2026-11-05 14:36 IST — commit: `Preserve taxonomy negation and maternal context`
- Decision: preserve coding phrases such as `not identified`, `not elsewhere` and `not otherwise` during negation cleanup, and recognise explicit `maternal` language as obstetric context. Include source attribution in the built image. Move unused experimental model weights to workspace scratch storage.
- Evidence: catalog probes initially exposed three v2 first-choice failures (197/200), including maternal care being suppressed and COVID-19 `virus not identified` losing its negation. General fixes bring this debugging set to 200/200 top-1/top-3. The v1 image got 198/200 top-1 on the same probes, missing numeric grade/type distinctions. All 13 contract/regression checks pass after the fixes; dev-informed five-fold accuracy remains 44/60 top-1 and 50/60 top-3.
- Options: exempt individual codes, keep the regression, or fix text/context handling for all matching categories. Chose general handling. The probe set has now been used for debugging, not independent clinical validation.
- Revisit: clinical assertion parsing must distinguish absence of a disease from absence of confirmation or a qualifier. The current English rules remain limited.

## 2026-11-05 14:39 IST — commit: `Publish v2 offline accuracy and resource measurements`
- Decision: ship context-adjusted primary retrieval plus trained alternatives; keep E5 disabled and retain the v1 evidence for comparison.
- Evidence: Linux Docker five-fold evaluation confirms 44/60 top-1, 50/60 top-3 and 57.5/75. Top-100 candidate recall is 60/60. External 200-note inference is 5.0495 seconds, 202.05 MiB peak process RSS, capped at 2 CPUs/2 GiB, network disabled, no API cost, no missing/invalid/empty predictions. Thirteen tests pass in Docker. Current training-set score is 57.5/75, not the prior memorized 75/75.
- Options: default the larger model despite its regression, present only the training score, or publish the smaller measured result with limitations. Chose the latter.
- Revisit: independently labeled clinical accuracy, broader language coverage and official WHO enrichment are still required. Public MTS-Dialog lacks ICD-11 gold labels; synthetic catalog probes are debugging controls.

## 2026-11-05 14:43 IST — commit: `Record v2 fresh-clone reproducibility`
- Decision: verify v2 from a separate clean clone and no-cache Docker build before packaging the updated git bundle.
- Evidence: source commit 0e07125 builds without an existing local artifact; the exact assignment command returns 200/200 valid outputs in 4.363 seconds, byte-equivalent as decoded JSON to the original checkout. Machine-readable evidence is fresh-clone-v2.json. Only documentation changes follow that check.
- Options: trust the existing local environment, or verify a fresh build. Chose reproducibility.
- Revisit: repeat on target x86 Linux and whenever implementation or dependencies change.

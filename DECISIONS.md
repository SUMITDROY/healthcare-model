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

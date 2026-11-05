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

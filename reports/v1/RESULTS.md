# Offline 200-note test — 5 November 2026

The working offline baseline beats the requested 8–10-minute runtime target on this machine. Coding quality is still preliminary.

## Test conditions

- Docker Linux ARM64, Apple Silicon host; container CPU quota 2 cores (`cpu.max = 200000 100000`), memory limit 2 GiB (`memory.max = 2147483648`). Other processor architectures have not been tested.
- Network disabled by Compose. Socket connections additionally blocked in the benchmark process; OpenAI/Anthropic keys removed.
- Exactly 200 distinct dialogue texts from MTS-Dialog's public TestSet-1. All remain outside training. Zero exact-text overlap with the assignment's training examples.
- The dialogue fields are unmodified. The source consists of encounter sections, so not every record contains a codable diagnosis or complete consultation.

## Measured result

- 200 input IDs; 200 output IDs.
- 2.398 seconds including Python imports, model loading, inference and output writing; excludes Docker startup, image build and downloads.
- 190.50 MiB peak process RSS; container memory accounting is a different measurement, retained in the raw JSON.
- Mean inference 8.448 ms/note; p95 12.133 ms/note, excluding startup.
- Missing IDs: 0. Invalid codes: 0. Empty predictions: 0.
- API calls: 0. API spending: $0.
- Exact assignment command and six automated checks pass.
- Fresh clone of source commit f6fe5f1: a no-cache image build passed, then the exact command produced 200/200 valid outputs in 2.182 seconds including model loading. Code was unchanged after that check.

Raw machine-readable result: `benchmark.json`. Predictions: `external-predictions.jsonl` and `predictions.jsonl`.

## What we know about accuracy

These external conversations have no ICD-11 gold labels. Valid output does not establish medically correct output. No external accuracy percentage is claimed.

The supplied 60 labeled notes train the final nearest-neighbour component. Testing those same notes yields 75/75, which is a memorisation/resubstitution score.

For a more useful diagnostic, five-fold validation fits each model using 48 notes and predicts the other 12, repeated until all 60 have an out-of-fold prediction. Current results: top-1 34/60 (56.7%); top-3 40/60 (66.7%); official weighted core score 45/75. This remains dev-informed because normalization and extraction rules were designed with the dev set visible. The no-example ablation has the same aggregate score; current training has not demonstrated a held-out gain.

The first version's held-out score was 23.75/75 (25% top-1), demonstrating why the perfect training-set score was misleading. Both initial and current results are retained.

## Next work that matters

1. Obtain official WHO 2026-01 terminology enrichment and hierarchy information, with reproducible provenance.
2. Label an independent representative sample through clinical review; do not turn this system's own predictions into gold labels.
3. Improve negation, uncertainty, encounter selection and specificity; evaluate multilingual retrieval on labeled cases.
4. Consider a compact semantic retriever or optional budgeted API reranker only after measuring gains against this baseline.

Public source: MTS-Dialog, Asma Ben Abacha, Wen-wai Yim, Yadan Fan and Thomas Lin, *An Empirical Study of Clinical Note Generation from Doctor-Patient Encounters*, EACL 2023. https://github.com/abachaa/MTS-Dialog and https://aclanthology.org/2023.eacl-main.168/ . CC BY 4.0; full attribution and source hash in `third_party/`.

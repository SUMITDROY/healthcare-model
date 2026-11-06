# V5: language coding fixes and symptom-only retrieval

**Documented-diagnosis language failures are fixed in the inspected regressions. Symptom-only inference improved on development cases, but remains largely unsolved and showed no gain on the five reserved French cases.** No claim of broad clinical accuracy is established.

## Changes shipped

French/Spanish terminology now uses the appropriate native Snowball stemmer instead of English stemming. The representation retains diagnostic hepatitis letter markers, preventing “A” from disappearing as a stop word. This fixes the French collagénique/collagène mismatch and the Spanish acute-hepatitis A/B ranking failure without note-ID or gold-code lookup rules.

For long notes without an asserted diagnosis, a separate sparse BM25 index searches WHO's own clinical definitions in the detected language. Current-presentation text receives stronger weight than past history. Explicit assessments keep the existing specificity path. Missing definitions do not become invented clinical profiles; the shared learned alternative ranker is bypassed on this distinct hypothesis path. Descriptions remain official reference data, not clinical-note gold labels.

No generative model, new inference dependency, paid API, GPU or runtime download was added to production. The default compose limit stays two CPUs and two GiB RAM.

## Inspected development evidence

The previously downloaded MedExpQA cases are now development regressions because their outcomes have been inspected while choosing fixes. Language versions are paired observations, not independent patients. Mechanically aligned labels are not independently clinician-adjudicated ICD-11 outpatient gold.

On the stricter subset of 14 case IDs per language (nine expected categories), first-choice coding with the source diagnosis deliberately appended as a localized assessment changed:

- English: 14/14 → **14/14**.
- French: 12/14 → **14/14**.
- Spanish: 13/14 → **14/14**.

For the original symptom-only cases, first-choice matches changed from zero in every language to **English 0/14, French 2/14, Spanish 3/14**. Top-three matches changed from zero to **English 4/14, French 4/14, Spanish 6/14**. That is five first-choice and 14 top-three hits across 42 paired language observations. Most first choices remain wrong.

On all 41 case IDs with weaker synonym-derived code proxies, documented-diagnosis first choices are English 33/41, French 37/41 and Spanish 35/41. Raw first choices are 1/41, 3/41 and 4/41 respectively. Do not call these clinical accuracy: some index terms refer to manifestations or different specificity, and labels were not clinically adjudicated. The stricter subset is the primary development comparison.

Files: `exam-development/baseline-v4.json`, `native-language-only.json`, `description-fallback.json`, `presentation-weighted.json` and the frozen case/source files.

## Reserved French check: no demonstrated symptom gain

Five native-French MediQAl questions, with five distinct source clinical texts, were selected before implementation changes. Their single author answer exactly matched a permitted French leaf title. Baseline predictions were recorded without inspecting outcomes. The candidate policy and source hashes were committed before running the comparison.

Both baseline and candidate scored **0/5 symptom-only first-choice/top-three matches**. Both scored **5/5 when the source diagnosis was appended**. This small external check therefore demonstrates no symptom-inference gain. It is also an exam/code-alignment proxy, not an independent clinical coding gold set. No inference policy was changed after inspecting these results. Details: `heldout-fr/comparison.json` and `candidate-policy-freeze.json`.

A further seven cases from the source validation partition were frozen, excluding clinical-text hashes seen in the first five. Their baseline outcomes have not been inspected, and no candidate results were generated for them. They remain a reserve for future changes, not evidence of V5 improvement.

## Operational verification

The supplied scorer still reports **70.8/75**, with 56/60 first-choice and 58/60 top-three hits on visible development notes. This remains development-informed.

The packaged Docker image passed **25 unit/contract tests**. The 200 unmodified MTS-Dialog throughput notes produced 200 valid outputs in **40.9851 seconds**, with **816.68 MiB peak process RSS**, two CPUs/two GiB, network disabled, API keys removed, a network socket guard and **$0 API cost**. There were no missing IDs, invalid codes or empty predictions. Other test containers ran concurrently; these are host-specific measurements, not an x86 or hidden-600 timing guarantee. See `v5-benchmark.json` and `v5-dev-score.txt`.

## Experiments rejected

- Quantized multilingual MiniLM over WHO descriptions: zero strict top-three hits in each language. Not shipped.
- Qwen 1.7B free diagnosis proposals: 3/42 first-choice and 4/42 top-three hits in the tested mapping pipeline; invented concepts and malformed/truncated outputs. Not shipped.
- Qwen 4B direct proposals: stopped after 27 cases with two correct first choices. Description reranking got four of six selected development probes, took 34–40 seconds per case, and downgraded a correct Spanish colitis result. Not shipped.
- MedGemma 4B direct proposals: 6/42 first-choice and 7/42 top-three hits in the tested mapping pipeline. A findings-first, concept-only mapping follow-up got one of six selected probes. These medical proposals were not reliable enough to replace the factual retrieval path. Not shipped. The direct mapping experiment mixed English headings with non-English context, which can understate concept-mapping performance; the separate findings-first test isolated the proposed concept and still did not establish sufficient diagnostic quality.

Raw outputs and pinned model manifests are under `experiments/`. These are development experiments, not independent comparisons of model families. No rejected weights enter the repo or default Docker image.

## Remaining problem

The engine can map documented diagnoses much more reliably than it can infer a disease from an unfamiliar symptom narrative. The language bugs have regression evidence of resolution; the broader diagnostic-inference flaw is **not fixed**. A stronger medical reasoning path still needs a measured benefit on an untouched set, adequate source knowledge, and the same runtime/memory guarantees. Do not describe V5 as clinically validated or interview-proof on unseen diagnoses.

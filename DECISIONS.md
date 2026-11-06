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

## 2026-11-05 15:27 IST — commit: `Add release-pinned WHO reference knowledge and evaluate offline rankers`
- Decision: export official WHO 2026-01 English metadata using the documented local ICD API, which requires no cloud OAuth credentials. Analytics were disabled, the service bound to loopback and stopped after export. Ship the original records as compressed reference data with code/title/URI and attribution.
- Evidence: all 18,375 allowed categories exported in 9.9 seconds; 98,469 index terms and 6,561 definitions; compressed size 3,291,141 bytes. Code coverage is exact. The one title difference (SR40) is quotation-mark styling; original supplied and WHO records are retained unchanged. Manifest records image digest, release, language and export/catalog SHA-256.
- Options: cloud API credentials, title-only lookup, or supported local export. Local export removes the credential blocker and keeps runtime entirely offline.
- Revisit: multilingual releases and exclusions/hierarchy-aware reasoning; this English-only enrichment does not prove multilingual clinical accuracy.

## 2026-11-05 15:27 IST — commit: `Add release-pinned WHO reference knowledge and evaluate offline rankers`
- Decision: add separate stemmed WHO term and definition indexes and retain rejected ranking experiments for audit.
- Evidence: initial reference-enriched diagnostic was 46/60 top-1 and 51/60 top-3. A flexible tree primary ranker reached 53/60 on training but only 38/60 held-out, so it was rejected. A later evidence-anchored version achieved 47/60 top-1 and 53/60 top-3, with 60/60 gold codes in the first 50 candidates. These remain repeatedly tuned development diagnostics.
- Options: full learned primary ranking, shared pairwise alternatives, or reference-based evidence constraints. The small visible sample does not support trusting the tree training score.
- Revisit: independent gold annotations and richer pretrained clinical reasoning. Current adjective/age/condition rules are English-specific and need regression checks.

## 2026-11-05 15:27 IST — commit: `Add release-pinned WHO reference knowledge and evaluate offline rankers`
- Decision: test a local CPU-only Qwen3-0.6B candidate selector, without making it the default.
- Evidence: on three diagnostic smoke cases it got one top-1 and two top-3 hits; calls took 8.1–11.8 seconds, plus 24.8-second load, and peaked near 2.3 GiB process RSS. No gold codes were included in prompts. This does not justify deployment or an accuracy claim. A larger quantized model is still under evaluation, not yet selected.
- Options: deploy the smaller model on assumption, reject it based on measured behaviour, or test a more capable model under the same offline resource limits. No paid API has been called.
- Revisit: quality and measured selective-call budget must both improve before enabling a local generative selector.

## 2026-11-05 16:36 IST — commit: `Ground subtype ranking in explicit facts and official multilingual terminology`
- Decision: keep diagnosis-first retrieval and require full clinical qualifiers to match actual evidence. Replace five-character pseudo-stems with proper stemming, constrain causal qualifiers to their clause, prefer fully supported leaf titles, and extract explicit BP, coma, pregnancy/onset and acquired-condition facts without emitting codes in the fact extractor.
- Evidence: pseudo-stemming conflated protein with Proteus, while an HIV-malaria qualifier incorrectly matched the later clinical-stage wording. Correcting these general errors and adding explicit facts raises dev-informed five-fold results to 56/60 top-1 (93.3%) and 58/60 top-3 (96.7%), 70.833/75. No note-ID or gold-code overrides were added. Rules were tuned using the visible dev data; this is not independent clinical validation.
- Options: keep adding model capacity, trust coarse lexical overlap, or improve provenance-linked evidence. The more flexible learned primary model overfit; the explicit evidence path is selected.
- Revisit: independent clinician-reviewed labels are necessary before estimating true hidden or clinical accuracy. Four dev top-1 failures remain; the rules are now frozen instead of chasing them.

## 2026-11-05 16:36 IST — commit: `Ground subtype ranking in explicit facts and official multilingual terminology`
- Decision: add separate official French/Spanish WHO term indexes, leaving English vocabulary/IDF unchanged, and use guarded code-aligned projection only for an explicitly stated pregnancy modifier.
- Evidence: exports cover all 18,375 allowed categories in each language, with 99,541 French and 126,187 Spanish index terms. No title-language fallbacks occurred. English routing and its 93.3% diagnostic were preserved. The 20 clinical counterfactual controls and 10 language controls pass; 200 exact-title catalog controls pass. Controls exposed and helped fix family-history ownership and foreign obstetric context, so they are debugging sets, not untouched evaluations.
- Options: merge all languages into one IDF corpus, free-form translation, or separate reference-backed lookup. Chose separate indexes and language identification. Only English, French and Spanish terminology lookup is supported; no fluency or broad language accuracy claim is made.
- Revisit: sentence-level foreign negation/context and real clinical annotations in each language. French/Spanish lookup does not perform a full clinical translation.

## 2026-11-05 16:36 IST — commit: `Ground subtype ranking in explicit facts and official multilingual terminology`
- Decision: reject local generative selectors/translators from the default engine and preserve their provenance/results under reports/experiments.
- Evidence: Qwen3-1.7B Q4 candidate selection got 2/3 top-1 smoke cases, 7.2–10.4 seconds/call and near 2.9 GiB process RSS. Translation copied a French diagnosis and changed a Swahili age of 30 into a temperature of 30°C while reversing uncomplicated malaria into severe disease. This is unacceptable evidence corruption. No gold codes were in prompts; no paid inference APIs were called. Rejected weights were removed.
- Options: deploy on model reputation, add more model size without evidence, or use official multilingual references. Chose measured reference lookup.
- Revisit: a specialized clinical/translation model requires separate accuracy, contradiction and latency checks before deployment.

## 2026-11-05 16:36 IST — commit: `Ground subtype ranking in explicit facts and official multilingual terminology`
- Decision: after the user's authorization to free space, remove regenerable unused Docker build caches and task-created temporary files, retaining personal files, project data, images/volumes and the selected model artifact.
- Evidence: reclaimed 3.912 GB of unused build cache last accessed months ago; free space increased from 1.9 GiB to 5.6 GiB. Metadata services, raw export caches and rejected model files were subsequently removed after the compressed reference exports were verified.
- Revisit: future large-model experiments should check free disk before downloads. Runtime engine remains a small sparse index, without a generative model.

## 2026-11-05 18:37 IST — commit: `Publish v3 accuracy and offline resource verification`
- Decision: publish the frozen evidence/reference engine and its limitations, retaining rejected model traces and v1/v2 comparisons.
- Evidence: Linux Docker diagnostic confirms 56/60 top-1, 58/60 top-3 and 70.833/75. All 15 tests, 20 clinical controls and 10 language controls pass. External 200-note inference is 10.087 seconds, 548.49 MiB peak process RSS, with a 2-CPU/2-GiB cgroup limit, no network, no keys, no missing/invalid predictions and $0 API spending. Exact assignment command also passes.
- Options: claim the development percentage as unseen accuracy or distinguish the diagnostic from independent validation. Chose explicit separation. The alternative-ranker ablation has the same aggregate v3 score, so no learned-ranker gain is claimed.
- Revisit: independent clinician-coded test data, complex foreign narrative context, x86 resource verification and other languages. No further English rule tuning is planned before that validation.

## 2026-11-05 18:47 IST — commit: `Pin the validated multi-architecture build environment`
- Decision: pin the Python base image digest and the four transitive runtime packages to the versions resolved by the successful fresh-clone build.
- Evidence: while this work ran, python:3.12-slim moved from digest b18b... to e695..., and threadpoolctl changed from 3.7.0 to 3.8.0. The fresh e695/3.8.0 build emitted exactly the same 200 predictions, but future unpinned changes would weaken reproducibility. The pinned image index includes Linux amd64 and arm64; all ten runtime packages now have explicit versions.
- Options: accept moving tags/transitive resolution, or lock the tested environment. Chose the lock; no algorithm changes are included.
- Revisit: deliberately refresh pins for security/compatibility updates and rerun the scorer, controls and resource benchmark.

## 2026-11-05 18:56 IST — commit: `Package the verified v3 implementation and interview notes`
- Decision: finish on the locked, verified build and record the most recent resource measurement instead of choosing the fastest observed run.
- Evidence: the pinned fresh-clone build passed the exact command and all 15 tests/30 controls. Final benchmark is 28.3638 seconds for 200 notes, 550.39 MiB process RSS, 2 CPUs/2 GiB, zero paid API calls and no missing/invalid outputs. Earlier builds measured 10.087 seconds; both are well inside the requested runtime. Predictions match the original checkout after dependency locking. A clean-container report-directory issue was caught and fixed; standalone controls now pass.
- Options: publish earlier timing, leave moving dependencies, or publish the latest pinned result with reproducibility evidence. Chose the last.
- Revisit: repeat the same checks for any implementation/dependency change and obtain independent clinical accuracy data. Subsequent bundle packaging changes no algorithms.


## 2026-11-05 19:08 IST — commit: `Handle French and Spanish assertion context with reproducible regressions`
- Request: address multilingual generalisation beyond terminology lookup. Chose bounded context parsing and a frozen reproducible challenge rather than deploying the previously failed generative translator.
- Evidence: 132 synthetic/context and official-title cases initially 108 top-1 / 116 top-3; after contrast-aware negation, localized assertion extraction and case-normalized language detection, 132/132. Existing controls remain separately reported. No test rows fit the alternative ranker.
- Limitation: 80 variants derive from ten existing controls, and 52 use official titles. These are inspected development controls, not independent clinical gold. Explicitly retain the broader unverified limitation; revisit with clinician-adjudicated multilingual consultations.
- Final verification: 20 unit/contract tests and 30 original controls pass; final Docker image passes all 132 challenge cases. Offline external throughput 200 notes/43.6538 seconds/549.48 MiB RSS at 2 CPUs/2 GiB, $0; bilingual challenge ran concurrently in a separate capped container.

## 2026-11-05 19:27 IST — commit: `Freeze external Spanish case proxy evaluation before inference`
- Chose the authors' pinned CodiEsp Spanish annotations over generated new gold. All 221 eligible cases were selected by exact unique WHO Spanish term matching before prediction: 1,063 annotations / 423 proxy ICD-11 codes, from 3,431 source diagnosis annotations. No model changes or training use are permitted after seeing this evaluation.
- Alternatives: label ICD-10 as ICD-11 (invalid), use inaccessible ICD-11/MIMIC data (requires access), or report only synthetic controls (too narrow). The external case text and ICD-10 annotation are independent; derived ICD-11 proxies are not clinician-adjudicated gold and cannot measure assignment accuracy.
- Dataset manifest, original annotations, source README and text hashes are frozen in this commit. Revisit with a separately adjudicated ICD-11 outpatient set across languages; do not tune on this probe and then call it held out.


## 2026-11-05 19:33 IST — commit: `Finalize external evaluation, clean-clone evidence and interview preparation`
- Fresh v4 bundle clone + no-cache build + exact command passed: 200 valid/matching outputs, 42.971 seconds, 20 tests. Supplied scorer rerun: 70.8/75. Retain exact source/hash evidence rather than treating the working checkout as a clean clone.
- Frozen CodiEsp probe: 81/221 any-proxy first-choice and 138/221 any-proxy top-three matches, all identified as Spanish, no training overlap/API use. Options were to tune on it and lose the holdout, conceal the lower result, or preserve it; chose preservation with no runtime modifications. The ICD-11 proxy mappings are not independent clinical gold. Revisit on a separate development set and reserve another untouched final test.
- README shortened to one page in scope (354 words), hidden planning estimate reduced from 80 to 60/100 without pretending calibration, interview questions expanded, applicant hours recorded as not reliably tracked rather than fabricated. User delegated the choice but supplied no measured hours. Numeric applicant-hours reporting remains unavailable.
- No restricted/NC dataset was added, no access request/email sent. Revisit independent gold/French validation with authorized clinical data and qualified adjudication. Package real history as `sumitdebroy.bundle` after final verification.


## 2026-11-05 20:48 IST — commit: `Use native morphology and preserve diagnostic letter subtypes`
- Diagnosed French/Spanish failures on now-inspected MedExpQA development cases: English stemming missed collagénique/collagène and stop-word stripping erased hepatitis A identity. Chose language-native cached Snowball analyzers and explicit hepatitis letter markers over code-specific gold lookup rules.
- Evidence after rebuild: strict documented-diagnosis cases improve French 12→14/14 and Spanish 13→14/14; English remains14/14. Broad proxy French33→37/41, Spanish34→35/41. All22 tests and30 existing controls pass; symptom-only14-case results are still0 and are not claimed fixed by this commit.
- Freeze: five separately selected native-French MediQAl cases with baseline predictions saved before implementation. Do not inspect/tune on heldout results until symptom policy is final. These remain mechanically aligned exam labels, not independent ICD-11 outpatient adjudication.
- Revisit: native linguistic coverage beyond these cases, clinical descriptions for symptom-only inputs, and a larger separately reviewed gold set.


## 2026-11-05 21:12 IST — commit: `Retrieve clinical descriptions for symptom-only notes`
- Added sparse BM25 over the official definitions in each language, keeping explicit assessments on the existing specificity path. Current-presentation text gets stronger weight than prior history. This is code-independent clinical-description retrieval, not a note/gold lookup.
- Inspected development evidence: strict symptom-only top-three matches0→14/42 across paired EN/FR/ES observations (4/14,4/14,6/14); first-choice0→5/42 (0,2,3). All42 documented-diagnosis observations now have correct first choices; supplied dev score remains70.8/75. Many symptom-only diagnoses remain wrong; this is improvement, not broad diagnostic validation.
- Rejected alternatives: quantized multilingual MiniLM description embeddings had0/14 top-three per language;1.7B free-concept generation3/42 first-choice and4/42 top-three with invented concepts;4B free generation was stopped after27 cases with2 correct first choices. A4B factual-description reranker got4/6 on selected development probes but took34–40s/case and downgraded a correct Spanish colitis result. Do not ship these models or claim unseen benefit.
- Freeze this policy before examining five separately reserved native-French MediQAl cases. Hashes in candidate-policy-freeze.json. Revisit symptom inference with independent ICD-11 annotation and better clinical knowledge, using a different development set if inspecting the reserved outcomes.


## 2026-11-06 13:13 IST — commit: `Report medical-model experiments and package verified v5 changes`
- Resumed symptom inference research with a separately licensed medical model instead of assuming generic model size fixes clinical knowledge. MedGemma4B direct proposals got6/42 first-choice and7/42 top-three in the mixed-language mapping experiment. A findings-first concept-only follow-up got1/6 selected probes. Mapping itself can obscure foreign-language concept quality, but explicit wrong diagnoses remained. Reject deployment; retain raw outputs and manifests. No experimental weights ship.
- Five reserved French cases showed no symptom gain:0/5 before and after; documented diagnoses5/5 before and after. Policy source hashes were frozen before examining outcomes and no inference code changed afterward. Seven additional validation-source cases remain reserved and uninspected; no candidate outcomes are claimed.
- Packaged runtime:25tests pass; supplied scorer70.8/75;200-note no-key/network-disabled Docker benchmark40.9851s,816.68MiB peak RSS at2CPUs/2GiB,$0. Keep changed-language regressions separate from unproven diagnostic generalisation.
- Revisit: stronger clinical reasoning only when it improves untouched cases within memory/time limits. Do not turn now-inspected probes into alleged independent accuracy. Ship concrete language fixes and faster description retrieval while explicitly retaining the unresolved symptom-only limitation.


## 2026-11-06 13:37 IST — commit: `Isolate note failures and prepare the 600-note assignment audit`
- Re-read the original brief and kept scope on batch consultation coding, not passing symptom-only diagnosis exams. Source scorer,60dev notes and18,375-category whitelist are byte-for-byte unchanged from the supplied pack.
- Found one operational gap: a per-note ranking exception could truncate later outputs. Added safe_predict, whitelist/dedup filtering and a separate catalog-only recovery path; last-resort allowed-code recovery is explicitly not a reliable clinical diagnosis. Invalid input JSON/IDs still fail clearly. The clinical retrieval/ranking implementation is unchanged.
- Evidence:29unit/contract tests pass, including forced middle-note failure, invalid outputs, continued processing and on-disk incremental flush checks.
- Prepared600distinct public dialogue texts from pinned MTS-Dialog split files, selecting only id/text and never fitting on these rows. Exact training-text overlap0; patient independence and clinical ICD-11 accuracy are not asserted. Freeze manifest/source hashes before the full-sized contract/run audit.
- Revisit: real ICD-11 annotated coding evaluation; operational recovery ensures completion, not correct diagnosis. Applicant personal hours and actual email submission cannot be inferred or fabricated by the agent.


## 2026-11-06 13:48 IST — commit: `Preserve explicit diagnosis headings without requiring a label`
- Assignment-format audit reproduced a Spanish error: a long follow-up note headed by the official diagnosis Epilepsia mioclónica juvenil was sent to symptom inference and missed8A61.30, despite the diagnosis already being written.
- Added a global preferred-title lookup derived only from the supplied/WHO categories. A unique specific non-residual leaf on its own first line is documented evidence, not a symptom inference. Parent/residual titles and ambiguous localized titles are excluded; a later explicit assessment/clinician focus takes precedence. This is full-taxonomy title identity, not a case-ID or training-gold lookup.
- Added EN/FR/ES heading regressions and an assessment-precedence regression. Retain the existing symptom-only limitations; this fix addresses consultation coding scope, not medical-exam diagnosis. Revisit narrative diagnosis extraction with source-separated coding evaluation.


## 2026-11-06 13:51 IST — commit: `Use the 600-note public audit sample for the default command`
- Chose600distinct public dialogue texts rather than repeated/synthetic copies of200 notes, so the exact default command exercises the assignment-sized batch. The original200-note file remains available for historical comparisons.
- Only data/notes.jsonl changes; original supplied scorer,dev notes and whitelist remain untouched. Source training-split rows in the fixture are inference-only, and all source hashes/selection are in the audit manifest.
- Revisit: this full-size operational check is not a clinical accuracy test, and its600notes are not the employer hidden set.

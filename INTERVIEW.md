# Interview notes for the current implementation

Explain the task as constrained ranking: one consultation goes in; up to three alternative diagnosis codes come out, best first. The alternatives are not three separate conditions to submit on a claim. Only the supplied release's code set is allowed.

The default pipeline runs entirely offline. It extracts the clinician's assessment, retrieves over titles plus WHO index terms/definitions, checks documented context and specificity, ranks alternatives, validates codes and flushes each result. French/Spanish use their own official reference indexes. There is no generative clinical translation in production.

The important engineering change was adding real reference knowledge and fixing evidence handling. Titles alone miss synonyms. Short prefix stemming conflated protein with Proteus. A qualifier parser treated clinical-stage words as evidence of HIV associated with malaria. A context parser assigned a father's diabetes to the patient. Explain these as failure classes and show the counterfactual checks.

The provided 60 notes fit a shared pairwise alternative ranker. This scores evidence features for any category; it is not a classifier restricted to observed labels. V3's no-ranker ablation has the same aggregate score, so do not claim that training caused the current accuracy gain. A more flexible model reached 88.3% on training and 63.3% when held out; it was rejected.

Be precise about evaluation: 56/60 first-choice hits and 58/60 top-three hits produce 70.8/75 on the core scorer. The development set has no generalisation slice. Rules were designed using all 60 visible notes, so five-fold validation isolates only the fitted ranking component. These are development diagnostics; genuine independent clinical accuracy remains unknown.

The 200 public MTS-Dialog conversations test throughput and valid output. They have no ICD-11 gold labels. The 20 clinical controls, 10 language controls and 200 catalog probes were used for debugging and are not independent clinical evaluations. The employer's hidden 600 notes cannot be downloaded from the internet.

Resource limits are a design input: sparse indexes, bounded candidate sets, single-thread numerical libraries, no GPU, no runtime network and incremental writes. The container is capped at two CPUs and two GiB. Cite the current benchmark file for exact latency/memory measurements; measurements are ARM64, not an x86 guarantee.

An actual AI error caught: a local model changed an age of 30 into a fever of 30°C and reversed uncomplicated malaria into severe disease. Keep the raw failed output as evidence. A larger model was not accepted merely because it was larger.

For further work, prioritise a locked, independently reviewed set across clinics, chapters and languages. Improve assertions and temporal/context resolution against that set. An optional API reranker could be evaluated under a reserved token/cost budget, but this version has no paid inference path and no measured API-enhanced accuracy.


French/Spanish follow-up: “I found and fixed concrete context errors rather than relying only on dictionary lookup. A reproducible 132-case synthetic challenge improved from 108 to 132 correct first choices. It covers negation contrast, relatives, assessment headings, plan distractors and uppercase input, plus official terms across 26 chapters. We inspected these cases while developing, so I would not call that unseen clinical accuracy. Real multilingual clinical generalisation still requires independent clinician-labelled evaluation.”

## A 60-second introduction

“I built a batch ICD-11 ranking engine for a fixed taxonomy, with no dependency on a hosted model. I enriched the supplied titles with release-pinned WHO terminology, then used sparse retrieval and explicit evidence checks to rank supported codes. The container runs on two CPUs and two GiB and streams results. It scored 70.8/75 on the visible set and processed 200 external notes in under a minute at zero API cost. The main limitation is generalisation: the visible set influenced the rules, and the external Spanish proxy check was substantially weaker. I kept those results separate rather than claiming the synthetic tests proved unseen accuracy.”

## Likely questions and direct answers

**What exactly is trained?** A shared pairwise logistic ranker learns differences between candidate evidence features from the 60 supplied notes. It can rank categories absent from those labels because the feature representation is shared across codes. Retrieval indexes also fit term statistics on public taxonomy text; they do not learn clinical labels from the external evaluation cases.

**Did training improve the final version?** Not demonstrably at the aggregate level. The current ranker and no-ranker ablation give the same development score. The major observed improvements came from WHO reference enrichment and evidence/context handling. I would not attribute the whole gain to machine learning.

**Why does 93.3% not establish unseen accuracy?** Although ranker folds exclude their test notes, rules, synonyms and implementation choices used all 60 visible notes. That leaks development knowledge into the overall diagnostic. A frozen external set is needed to estimate the complete pipeline.

**What do the external Spanish results mean?** Before inference, I froze 221 CodiEsp cases selected by exact, unique matches between annotated diagnosis spans and official Spanish WHO terms. The first code matched an available proxy in 81 cases; a proxy appeared in the top three in 138. Those are 36.7% and 62.4% any-proxy match rates, not primary-diagnosis accuracy or the employer's score. CodiEsp gold is ICD-10, the ICD-11 mapping is derived, and clinical case reports contain multiple and historical diagnoses. The result nevertheless contradicts any claim that synthetic 100% established broad clinical generalisation. No engine change was made after inspecting this set.

**Why not use a stronger local LLM?** Tested selectors were slow and unreliable; one translation introduced clinically material facts. Bigger model size did not justify accepting those errors or the additional memory. The failed experiment outputs are retained so this is an evidence-based choice.

**How do you choose parent, child or unspecified?** The scorer rewards the most specific code supported by the note. Evidence checks penalize unsupported qualifiers and promote an appropriate generic residual when the note lacks subtype evidence. These are imperfect heuristics; a child isn't justified merely because its title shares more words.

**How does the system handle non-English notes?** Separate official French and Spanish reference indexes, language identification and bounded assertion/negation parsing. It preserves qualifiers such as “without aura.” Synthetic context checks pass, but complex consultations, other languages and code-switching lack independent ICD-11 validation. There is no general-purpose translation model.

**Why no paid API path?** Offline performance was the priority, and zero calls satisfies the budget cap. The current version doesn't change behaviour when a key is supplied. An API reranker would need a separate measured accuracy benefit, proxy configuration, token budget, timeout and deterministic fallback before being added.

**How does it scale?** Indexes load once, each note uses bounded retrieval/ranking, and output flushes incrementally. Input is streamed rather than loaded as a batch. Model memory is approximately 550 MiB in the measured container. For larger volume, workers could reuse loaded indexes and process disjoint records; memory would grow with worker count and the output merge must preserve unique IDs. Multi-worker throughput is a proposal, not a measured result here.

**Can you promise the grading machine's timing?** No; the measurements are Linux ARM64 on this Docker host. They are comfortably below the requested eight-to-ten-minute 200-note target. The base image supports x86 and ARM, but x86 accuracy and timing were not separately benchmarked. The assignment's 600 unseen notes can differ in length and complexity, so I would report the measured 200-note result rather than a guaranteed extrapolation.

**How do you reproduce the build?** Clone the supplied bundle, run the build, then the exact compose command. Dependencies and base image are pinned; WHO exports ship in the repository. The final v4 runtime was tested from a fresh bundle clone with cache disabled and no prebuilt local artifact. Every input ID appeared, every emitted code was allowed, and all 200 outputs matched the original checkout.

**What would you do next?** Obtain independently adjudicated ICD-11 outpatient notes across chapters, clinic styles and languages. Split by source/patient before tuning, reserve a final test partition, and analyze qualifier, assertion, temporal and language failures on a separate development partition. Prioritize measured error classes over another larger model.

**How much did you personally build?** Be explicit that the implementation was substantially AI-assisted. Read and be able to explain the evidence flow, limitations and failed experiments. Personal working hours were not reliably tracked; don't replace them with the elapsed agent session.

## Five-minute demo

1. Show `README.md`, `compose.yaml` and the source whitelist: fixed valid taxonomy, no runtime network, two CPUs/two GiB.
2. Run the exact command from the fresh clone: `docker compose run coder /in/notes.jsonl /out/predictions.jsonl`.
3. Show `reports/fresh-clone-v4.json`, `reports/v4-benchmark.json` and the supplied scorer's v4 development output. Keep throughput and accuracy distinct.
4. Show one negation/family-history regression and the rejected translation output. Explain why unsupported specificity matters.
5. Show `reports/codiesp/results.json` alongside its manifest. Explain the weaker external result, mapping caveats and the next properly held-out evaluation.

Do not claim access to the employer's hidden notes, clinically validated multilingual accuracy, a measured 600-note timing result, or that all 18,375 categories have been independently clinically tested.


## V5 update: what was actually fixed

French/Spanish documented-diagnosis failures came from using English stemming and dropping clinically meaningful letter subtypes. Native morphology and hepatitis letter markers fix the inspected14-case regressions in each language. A new sparse clinical-description path adds symptom-only candidate recall without a GPU or generative model.

Do not say the symptom-only flaw is solved. Strict development top-three hits are now English4/14, French4/14, Spanish6/14, but five separately reserved French cases remained0/5 before and after. The documented-diagnosis version of those five stayed5/5. Explain why a visible development gain can coexist with no measured held-out gain. These exam/code-alignment probes are not clinician-adjudicated outpatient ICD-11 gold.

Current packaged benchmark:200 notes in40.9851seconds at2CPUs/2GiB,816.68MiB peak process RSS,$0,25tests. See reports/V5-RESULTS.md for failures and rejected model experiments. The old31-second v4 clean-clone number is historical, not the current v5 resource benchmark.

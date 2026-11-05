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

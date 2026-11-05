# Sugen offline ICD-11 coder

CPU-only ranking across all **18,375 allowed MMS 2026-01 categories**. Assessment extraction, sparse lexical/WHO-reference retrieval, explicit-context checks and a shared alternative ranker produce up to three valid codes. Entirely offline: no API keys, GPU or runtime downloads.

```sh
docker compose build
docker compose run coder /in/notes.jsonl /out/predictions.jsonl
```

Compose caps inference at **2 CPUs / 2 GiB**, with networking disabled. Default input is the external 200-note sample; output is `reports/predictions.jsonl`. Override host folders with `CODER_INPUT_DIR` and `CODER_OUTPUT_DIR`. Predictions flush after every note. Build downloads pinned dependencies and creates indexes from packaged data.

**Scores.** The supplied scorer reports **70.8/75**, with **56/60 top-1** and **58/60 top-3**. Five-fold ranker diagnostics agree, but rules and approach choices used all visible notes: these are development scores, not independent accuracy. Removing the learned ranker gives the same aggregate result. My hidden-score estimate is **60/100**, an uncalibrated planning guess; no independent ICD-11 gold set establishes it.

**Added data.** Official WHO English/French/Spanish API records supply 324,197 index-term entries, definitions and hierarchy metadata, restricted to the allowed codes. Release, hashes, licenses and attribution: `third_party/`. MTS-Dialog TestSet-1 supplies 200 unchanged English dialogues for inference only; summaries never train or enter inference. CodiEsp supplies 221 external Spanish cases for evaluation only, with original ICD-10 annotations and explicitly derived ICD-11 proxies. Neither external corpus trains the engine.

**Beyond dev.** Offline Docker benchmark: **200 valid outputs / 43.65 s / 549.48 MiB peak RSS / $0 API cost**. Fresh clone from the v4 bundle, no-cache build and the exact assignment command pass; predictions match. All 20 unit/contract tests, 30 clinical/language controls, 132 bilingual challenges and 200 catalog probes pass. Synthetic controls were used in development. External CodiEsp proxy matches: **81/221 first choice; 138/221 top three**. These are not ICD-11 accuracy: mappings are reference-derived, cases are multi-diagnosis, and selection is terminology-biased. Real multilingual generalisation remains unverified.

**AI mistake caught.** A local model turned age 30 into a temperature and reversed uncomplicated malaria into severe disease. It was rejected; raw evidence is retained. No generative translator ships.

**Hours spent:** not tracked reliably; implementation was substantially AI-assisted. Repository timestamps document agent activity, not applicant working hours.

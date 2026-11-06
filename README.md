# Sugen consultation-note ICD-11 coder

Reads consultation notes and returns up to three allowed codes, best first, across **18,375 MMS 2026-01 categories**. The offline pipeline uses assessment extraction, official WHO terminology/definitions, specificity checks and a shared alternative ranker. English/French/Spanish lookup and native morphology are supported. This is a coding engine; accurate diagnosis from symptom-only medical exam cases is not established.

```sh
docker compose build
docker compose run coder /in/notes.jsonl /out/predictions.jsonl
```

Default input: **600 distinct public dialogue texts**, not the employer's hidden notes. Output: `reports/predictions.jsonl`. Set `CODER_INPUT_DIR`/`CODER_OUTPUT_DIR` for other folders. Compose caps inference at **2 CPUs / 2 GiB**, disables networking and uses no GPU/API keys. Build installs pinned dependencies and creates indexes from packaged data. Predictions flush per note; note-level inference errors recover through catalog-only retrieval so later records continue. Standalone official diagnosis headings are preserved; later explicit assessments take precedence.

**Dev score:** unchanged supplied scorer **70.8/75**: 56/60 first-choice, 58/60 top-three. The visible set influenced rules and approach choices; this is development evidence. Hidden-score estimate: **60/100**, an uncalibrated planning guess.

**Added data:** official WHO English/French/Spanish API records include 324,197 index-term entries, definitions and hierarchy metadata, restricted to allowed codes. Provenance, hashes and licenses: `third_party/`. MTS-Dialog provides the 600-text throughput fixture; summaries never train or enter inference. CodiEsp, MedExpQA and MediQAl supply external evaluation text/reference answers with mechanically aligned code proxies, not clinician-adjudicated ICD-11 gold. Evaluation cases do not fit the learned ranker.

**Beyond dev:** the 600-note Docker audit returned **600/600 valid outputs in 85.54 seconds**, with **832.74 MiB peak RSS**, zero inference fallbacks, no network/keys and **$0 API cost**. **31 tests** pass, covering output IDs/whitelist, incremental flush, forced note failure, specificity and languages. Clinical accuracy on the 600texts is unknown. Independent hidden-note accuracy remains unverified; extra symptom-only exam stress tests remain weak. Details:`reports/ASSIGNMENT-CHECK.md` and versioned results.

**AI error caught:** a local translator changed age 30 into a temperature and reversed uncomplicated malaria into severe disease. It was rejected; raw failure evidence is retained. No experimental generative model ships.

**Hours spent:** not tracked reliably; substantially AI-assisted. Git timestamps document agent activity, not applicant working hours.

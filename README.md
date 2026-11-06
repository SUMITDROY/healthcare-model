# Sugen offline ICD-11 coder — V5

CPU-only ranking across **18,375 allowed MMS 2026-01 categories**. Assessment extraction, sparse WHO-reference retrieval, specificity checks and a shared alternative ranker return up to three codes. Long unasserted narratives use a separate clinical-definition index. French/Spanish use native morphology and retain diagnostic letter subtypes. No hosted API, generative model, GPU or runtime downloads.

```sh
docker compose build
docker compose run coder /in/notes.jsonl /out/predictions.jsonl
```

Compose caps inference at **2 CPUs / 2 GiB**, with networking disabled. Default input is 200 external MTS-Dialog notes; output is `reports/predictions.jsonl`. Override folders with `CODER_INPUT_DIR`/`CODER_OUTPUT_DIR`. Each prediction flushes immediately. Build installs pinned dependencies and fits indexes from packaged references.

**Dev score:** supplied scorer **70.8/75**, 56/60 first-choice and 58/60 top-three hits. Rules and approach choices used visible notes, so this is development evidence. Prior ranker ablation gave the same aggregate result. Hidden-score estimate: **60/100**, an uncalibrated planning guess.

**Data added:** official WHO English/French/Spanish API records, including 324,197 index-term entries, definitions and hierarchy metadata, restricted to allowed codes. Source hashes/licenses: `third_party/`. MTS-Dialog supplies 200 unchanged dialogues for throughput only; summaries never train or enter inference. CodiEsp, MedExpQA and MediQAl provide external evaluation text and source annotations/reference answers. Added code labels are mechanically aligned proxies, not clinician-adjudicated ICD-11 gold. These evaluation cases do not fit the learned ranker.

**Beyond dev:** Docker processed **200 valid outputs in 40.99 seconds**, **816.68 MiB peak RSS**, **$0 API cost**. All **25 unit/contract tests** pass. Inspected language regressions now code all 14 documented diagnoses correctly in each language. Symptom-only top-three matches improved from zero to English4/14, French4/14 and Spanish6/14; most first choices still fail. On five separately reserved French cases, symptom-only performance remained0/5, while documented-diagnosis coding remained5/5. Synthetic controls and inspected examples are development evidence; broad diagnostic generalisation remains unverified. Details: `reports/V5-RESULTS.md`.

**AI mistake caught:** a tested local translator changed age30 into a temperature and reversed uncomplicated malaria into severe disease. It was rejected. Subsequent generic/medical model diagnosis proposals were also insufficiently reliable and are not shipped; raw evidence is retained.

**Hours spent:** not tracked reliably; implementation substantially AI-assisted. Git timestamps document agent activity, not applicant working hours.

# French/Spanish context improvements

The offline engine now extracts localized assessments and unheaded diagnosis assertions, handles negation contrast, removes relatives' diagnoses, ignores treatment-plan distractors, and identifies uppercase/short supported-language notes. It preserves taxonomic qualifiers such as “sans aura”, “sin aura” and unspecified. No model, download or paid API was added.

A reproducible 132-case development challenge improved from **108/132 to 132/132 first-choice hits**, and **116/132 to 132/132 top-three hits**. Both runs use the same dataset hash. Eighty cases vary ten existing engineer-authored controls across eight contexts; 52 check official localized terminology across 26 chapters. All 20 unit/contract tests and the original 30 clinical/language controls also pass.

Packaged Docker verification passed all 132 cases. The 200-note external throughput run completed in **43.65 seconds**, with **549.48 MiB** peak process RSS, on **2 CPUs / 2 GiB RAM**, networking disabled and **$0 API cost**. No output IDs were missing and no invalid codes were emitted. This measures speed and contract validity, not coding accuracy.

These cases were inspected while fixing the engine. They establish regression coverage, not independent clinical accuracy. Five disease families underpin the context cases; the chapter-wide portion checks terminology. Real French/Spanish consultation accuracy, mixed-language notes and languages beyond English/French/Spanish remain unverified. Independent clinician-adjudicated notes are still required before claiming broad multilingual generalisation.

Reproduce from the repository root:

```sh
docker compose build coder
docker compose run --rm -v "$PWD/reports:/app/reports" --entrypoint python coder scripts/evaluate_multilingual.py
```

Full per-case texts, labels, predictions, language identification and scenario counts: `multilingual-before.json` and `multilingual-context.json`. Test-set SHA-256: `787b1eb0a04b9fc4a3d30604d254570c3d5dc0c358c4eea76018c394c0452d9f`.

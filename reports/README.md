# Evidence index

Start with the current audit and latest implementation report. Original paths remain intact so scripts, source manifests and historical decision references continue to work. Older results describe earlier candidates, not cumulative independent validation.

## Current submission

- [Assignment check](ASSIGNMENT-CHECK.md): requirements, disclosures and submission status.
- [600-note audit](assignment-audit600/): provenance, resource benchmark, scorer output and machine-readable contract checks.
- [V5 results](V5-RESULTS.md): language fixes, symptom-only limits and rejected models.
- `final-dev-predictions.jsonl`: predictions used by the current submission audit.

## External evaluation

- [Spanish evaluation](EXTERNAL-EVALUATION.md) and [CodiEsp files](codiesp/): historical derived-label evaluation.
- [Multilingual controls](MULTILINGUAL.md): regression evidence, not clinical gold.
- [Exam development](exam-development/): inspected cases and development comparisons.
- [Reserved French check](heldout-fr/): policy freeze, baseline and candidate comparison.
- `reserved-fr-v2/`: reserved cases, not a claimed accuracy result.

## Historical experiments

`v1/`, `v2/`, initial/root evaluation JSON files and versioned benchmarks retain earlier candidates. `experiments/` contains rejected model outputs and failure evidence. Reports are excluded from the production image. See [decisions](../DECISIONS.md) for acceptance/rejection evidence. Do not combine counts or timing across versions into a single test.

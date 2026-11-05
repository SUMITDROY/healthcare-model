# External evaluation and remaining evidence gaps

The frozen runtime was evaluated on 221 independently authored Spanish clinical case texts from CodiEsp. The source has professional ICD-10 annotations, **not ICD-11 gold**. Before inference, all eligible cases were selected by exact normalized matches between annotated diagnosis mentions and one unique allowed WHO Spanish leaf category. The selection produced 1,063 matched annotations and 423 proxy codes. Dataset preparation and its manifest were committed before predictions were run; no engine change followed inspection of these results.

The first prediction matched an available reference-derived proxy in **81/221 cases (36.7%)**. One appeared in the first three predictions in **138/221 (62.4%)**. All 221 were identified as Spanish. Local evaluation took 24.02 seconds excluding model load, with numerical-library threads limited to one, no API calls, a network guard and no exact training-text overlap. This local run was not a separate cgroup-capped benchmark. The packaged 200-note Docker resource benchmark remains the measured cap test.

These are any-proxy match rates, **not clinical coding accuracy or an assignment score**. Exact-term selection biases the sample toward reference-covered terminology. Label alignment uses the same WHO terminology available to retrieval. Source cases contain multiple/historical diagnoses without the assignment's designated principal ICD-11 diagnosis. Exact matching does not establish equivalence between ICD-10 and ICD-11 categories. Misses may be engine failures, mapping failures or differences in principal diagnosis; hits do not establish correct priority or full specificity. The weaker result nevertheless supports retaining the limitation on broad generalisation. The synthetic 132/132 result must not be presented as independent clinical validation.

## Reproduction

The frozen cases, source annotations, source README, checksums and per-case outputs are in `reports/codiesp/`. Preparation is optional because the selected data ships in the bundle. Run from the repo root:

```sh
python scripts/codiesp_evaluate.py evaluate
```

For a Docker evaluation with the packaged model and no network, after building:

```sh
docker compose run --rm -v "$PWD/reports:/app/reports" --entrypoint python coder scripts/codiesp_evaluate.py evaluate
```

This reruns evaluation, not training. It replaces `reports/codiesp/results.json`; keep its platform/model provenance separate if comparing runs. `prepare` accesses the pinned author-hosted source and should not be run during the offline grading phase.

## Data search, checked 2026-11-05

[CodiEsp, author-hosted corpus](https://huggingface.co/datasets/Biomedical-TeMU/CodiEsp_corpus): Spanish case texts with ICD-10 labels, CC BY 4.0. Used for the explicitly derived proxy probe above; attribution and source revision are packaged.

[MAX-EVAL-11, author dataset card](https://huggingface.co/datasets/mas-namtla/max-eval-11): the author marks access restricted and subject to MIMIC/PhysioNet terms. Not downloaded or used; no access request was sent.

[MIMIC-SR-ICD11, author repository](https://github.com/woqingdoua/MIMIC-SR-ICD11): provides a construction/baseline pipeline based on MIMIC-IV. The public repository does not itself establish authorized access to the underlying patient notes. Not used.

[DiagTrace, author Zenodo record](https://zenodo.org/records/20266783): 180 French/English diagnosis cases; record metadata specifies CC BY-NC 4.0. It does not supply the assignment's MMS 2026-01 coding gold. No data was added to the commercial assignment bundle.

[E3C, author repository](https://github.com/hltfbk/E3C-Corpus): multilingual clinical narratives, with clinical entities and temporal/factuality annotations. The authors specify a noncommercial license; it is not an independently adjudicated ICD-11 outpatient-coding set. Not packaged or used.

These checks do not establish that no suitable dataset exists anywhere. They document why the evaluated source supports a proxy check and why the available evidence does not close the independent ICD-11/French validation gap.

## Required next evidence

A valid final test needs independently reviewed outpatient notes, exact allowed ICD-11 MMS 2026-01 gold and principal-diagnosis priority. Separate clinics/patients and language groups before model development, reserve a test partition, and keep a different development partition for fixes. No downloaded corpus or agent-generated labels automatically substitutes for that adjudication. A clinician or qualified ICD-11 coder must resolve genuine clinical-label ambiguity; no such independent reviewer was available in this run.

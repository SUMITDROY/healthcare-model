# Architecture and scaling

## Inference path

1. The CLI validates JSONL and loads the model once per batch.
2. Context extraction prioritizes current assessments and handles negation, family and historical mentions. Language detection selects English, French or Spanish reference lookup.
3. Sparse word/character retrieval searches the full supplied taxonomy and official WHO terminology, using native language morphology.
4. Specificity/hierarchy checks combine with a shared alternative ranker fitted on the 60 supplied examples. It is not a classifier limited to their observed labels. Unique official specific-leaf headings have a guarded direct route; later explicit assessments take priority.
5. Long notes without an asserted diagnosis use sparse retrieval over WHO definitions. This remains weak at inferring diagnoses from symptoms.
6. The CLI writes up to three allowed codes and flushes each record. Separate catalog-only recovery isolates inference errors. Last-resort output preserves the contract but is not reliable clinical inference.

`coder/cli.py` owns the batch contract; `coder/engine.py` combines retrieval/ranking. Supporting modules implement language, reference and symptom features. `coder/train.py` builds `artifacts/offline.joblib` during image build. Inference does not read evaluation answers or reports.

## Data boundaries

The supplied scorer, dev notes and whitelist are unchanged. Official WHO multilingual records are packaged and indexed at build time. MTS dialogues are throughput fixtures; their summaries never enter fitting or inference. External evaluation cases do not fit the ranker. Reports are excluded from the Docker image.

## Resource and scaling choices

Default inference uses one process, sparse CPU indexes and single-thread numerical libraries. Compose caps it at two CPUs/two GiB and disables networking. There are no default generative weights, API charges or rate limits. Process RSS measurements differ from the container memory cap.

For larger batches, split notes into disjoint shards and run separate containers writing separate output files. Validate IDs when merging. Each worker loads its own indexes, so memory grows with worker count. Start with one worker on a four-CPU/eight-GiB machine and measure before adding workers. More CPUs do not imply proportional speedup. A service wrapper or work queue is future work, not required by the batch assignment.

## Next accuracy work

Prioritize a frozen, clinician-adjudicated multilingual coding set covering implicit diagnoses and specificity. Avoid repeatedly tuning on its results. Consider paid reranking only after measuring incremental quality, latency and a hard total-cost limit. The current implementation always selects offline inference, even when API keys exist.

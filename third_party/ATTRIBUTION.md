# MTS-Dialog attribution

Dataset: MTS-Dialog, https://github.com/abachaa/MTS-Dialog

Authors: Asma Ben Abacha, Wen-wai Yim, Yadan Fan, Thomas Lin.

Paper: *An Empirical Study of Clinical Note Generation from Doctor-Patient Encounters*. EACL 2023, pages 2291–2302. https://aclanthology.org/2023.eacl-main.168/

License: Creative Commons Attribution 4.0 International. The complete license is in `MTS-Dialog-LICENSE.txt`.

Source commit, download URL and SHA-256: `source.json`.

Changes: extracted all 200 dialogue fields from TestSet-1 into JSONL and prefixed IDs with `mts-test1-`. Dialogue text is unchanged. The separate summaries and section headers are retained in `data/external_200_reference.jsonl`, never passed into training or inference. `data/notes.jsonl` is a copy of the 200-note inference file for the assignment's example command.

This is an external robustness/throughput sample, not the employer's hidden test and not an ICD-11-labeled benchmark. Many source records are sections of encounters, not complete consultations. No ground-truth coding accuracy can be computed from this source without independent annotation.

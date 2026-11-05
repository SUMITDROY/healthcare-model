# MTS-Dialog attribution

Dataset: MTS-Dialog, https://github.com/abachaa/MTS-Dialog

Authors: Asma Ben Abacha, Wen-wai Yim, Yadan Fan, Thomas Lin.

Paper: *An Empirical Study of Clinical Note Generation from Doctor-Patient Encounters*. EACL 2023, pages 2291–2302. https://aclanthology.org/2023.eacl-main.168/

License: Creative Commons Attribution 4.0 International. The complete license is in `MTS-Dialog-LICENSE.txt`.

Source commit, download URL and SHA-256: `source.json`.

Changes: extracted all 200 dialogue fields from TestSet-1 into JSONL and prefixed IDs with `mts-test1-`. Dialogue text is unchanged. The separate summaries and section headers are retained in `data/external_200_reference.jsonl`, never passed into training or inference. `data/notes.jsonl` is a copy of the 200-note inference file for the assignment's example command.

This is an external robustness/throughput sample, not the employer's hidden test and not an ICD-11-labeled benchmark. Many source records are sections of encounters, not complete consultations. No ground-truth coding accuracy can be computed from this source without independent annotation.


# WHO ICD-11 reference enrichment

International Classification of Diseases, Eleventh Revision (ICD-11), World Health Organization (WHO), 2026-01 MMS release, English. Canonical source: https://icd.who.int/browse/2026-01/mms/en . WHO copyright and licensing terms: https://icd.who.int/en/docs/icd11-license.pdf ; a copy is retained in `WHO-ICD11-LICENSE.pdf`.

The export in `data/who-2026-01-en.jsonl.gz` preserves complete original API category records, including codes, titles and canonical URIs. It is filtered to exactly the supplied 18,375 allowed categories, not a modified classification or different coding standard. Source image/release/language/checksums are in `who-source.json`. Search normalisation, stemmed features, ranking rules and predictions are our software's additions and do not originate from WHO. No WHO endorsement is implied.

Official local deployment documentation: https://icd.who.int/docs/icd-api/ICDAPI-LocalDeployment/ . API analytics were disabled. Only public category identifiers, never consultation text, were sent to the local metadata service. The service is not required during inference.


French and Spanish 2026-01 MMS API records are additionally retained, unmodified, in `data/who-2026-01-fr.jsonl.gz` and `data/who-2026-01-es.jsonl.gz`. Their source manifests include language-specific hashes and confirm that every title is in its requested language. These are WHO's translations, not generated translations. English search normalization and separate foreign lookup indexes are our software additions.

# CodiEsp external evaluation only

Antonio Miranda-Escalada, Aitor Gonzalez-Agirre and Martin Krallinger (2020), CodiEsp corpus: Spanish clinical cases coded in ICD10 (CIE10), eHealth CLEF 2020. Author-hosted source: https://huggingface.co/datasets/Biomedical-TeMU/CodiEsp_corpus at revision `5ff2b006ea74699eccd393a5a0f3b99396d01e0c`. Homepage: https://temu.bsc.es/codiesp/ . License: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ (full text already included as `MTS-Dialog-LICENSE.txt`).

Changes: selected 221 Spanish development cases before inference, preserving clinical text, source ICD-10 annotations and provenance; added exact unique matches to official WHO Spanish terms as **derived ICD-11 proxies, not independent ICD-11 gold**. Selection, hashes and original README: `reports/codiesp/`. These cases do not train or tune the engine. Original corpus licenses and author attribution remain applicable. No inference results were used to select cases.

# Evaluation and limitations

## Current evidence

The supplied scorer reports **70.8/75**: **56/60 top-one**, **58/60 top-three**. Rules and approach choices used this visible set, so this is development evidence. An ablation without the learned ranker had the same aggregate score; do not attribute improvement to learning alone. The README's **60/100** hidden estimate is an uncalibrated planning guess.

The instrumented 600-note public run produced every ID, valid whitelist codes and no empty outputs or recoveries in **85.5374 seconds**, at **832.74 MiB peak process RSS**, with two CPUs/two GiB and no network/API spend. A clean bundle clone completed the exact CLI run in **175.184 seconds** with concurrent tests. These Linux ARM64 measurements exclude image build and do not guarantee other hardware's timing.

The 600 texts are distinct and have zero exact text overlap with the supplied 60. They are not independently verified patients, have no ICD-11 gold labels and are not the employer's hidden notes. They establish throughput and contract behavior, not clinical accuracy.

The recorded **31 passing tests** cover IDs, format, incremental writes, fault recovery, specificity, context and language regressions. Synthetic bilingual controls and exact-title taxonomy probes test targeted behavior, not independent clinical accuracy.

## External checks

- **CodiEsp:** 221 Spanish cases with ICD-10 annotations mechanically aligned to ICD-11 proxies. The historical run scored 81/221 top-one and 138/221 top-three. Selection and specificity can bias these proxy matches; they are not clinical ICD-11 accuracy.
- **MedExpQA:** inspected exam cases became development regressions. Appending the source diagnosis gave 14/14 first-choice matches per language after fixes. That exposes the answer and does not test blinded diagnosis. Original symptom-only first-choice matches were English 0/14, French 2/14 and Spanish 3/14.
- **Reserved French MediQAl:** five cases remained at 0/5 symptom-only matches and 5/5 with an appended diagnosis. No symptom-inference gain was demonstrated. Seven further cases remain reserved and are not claimed as evidence.

Language variants may represent the same case, so their counts are not independent patients. Sources, selection policies and raw results are linked in the [evidence index](../reports/README.md).

## Remaining uncertainty

Only the employer can measure the hidden 450-core/150-shift score. Accuracy across unfamiliar diseases, implicit diagnoses and non-English consultations remains unproven. Terminology improvements do not solve general clinical reasoning. Stronger claims need clinician-adjudicated ICD-11 labels.

Rejected semantic and generative candidates remain documented but are not default inference dependencies. One local translator changed age into temperature and reversed malaria severity. It was rejected; the failure evidence is retained.

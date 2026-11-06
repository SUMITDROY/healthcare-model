# Assignment requirements check

The implementation is scoped to the supplied task: batch consultation-note coding into the permitted ICD-11 release. Passing medical diagnosis exams is not a required deliverable. Those experiments remain disclosed as stress tests and cannot establish hidden coding accuracy.

## Technical requirements verified

- JSONL input uses id/text; output uses exactly id/codes, with one to three unique allowed codes, best first. The 600-note audit has every input ID exactly once and no invalid/empty outputs.
- The original scorer, 60 dev notes and MMS whitelist are byte-for-byte unchanged. The whitelist contains 18,375 categories across all 26 supplied chapters. The supplied scorer still reports 70.8/75 (56/60 top-1,58/60 top-3).
- The exact required command works. Fresh-clone proof for the exact final attachment is supplied in the accompanying `submission-final-verification.json`, not merely a working-checkout result.
- No GPU, API key, hosted model or runtime download is needed. Compose disables networking and caps inference at two CPUs/two GiB; all runtime data/indexes ship in or are built into the image.
- A 600-distinct-text public MTS-Dialog run completed with 600valid outputs: exact CLI 81.529 seconds; instrumented benchmark 85.5374 seconds,832.74 MiB peak process RSS,$0 API calls/cost. These are Linux ARM64 measurements. Other test containers ran concurrently. Build/container startup are outside the inference benchmark. This is throughput/contract evidence, not600hidden-note accuracy.
- Output is flushed after each note. Fault-injection tests prove that a middle-note ranking exception does not lose later IDs. Recovery filters invalid/duplicate codes, uses a separate catalog-only path, and clearly labels recovery in diagnostics. The normal600-note run needed zero recoveries.
- Parent/residual/specificity handling, historical/family context and French/Spanish coding have regression checks. Literal specific-leaf diagnosis headings work without an Assessment label, while a later explicit assessment retains priority. Correctness on every unfamiliar consultation is not guaranteed.
- 31 tests pass. They include IDs/Unicode, overwrite prevention, whitelist/output shape, subtype specificity, context/negation, language morphology, standalone headings and error isolation.
- Source data, licenses, checksums and evaluation selection are recorded. The600texts are distinct, have zero exact text overlap with the60training notes, and are inference-only; patient independence is not asserted. They are not the employer hidden set and have no ICD-11 gold.

Reproduce the audit after running the command and generating dev predictions/resource benchmark:

```sh
python scripts/audit_submission.py
```

`assignment-audit600/requirements.json`, `benchmark.json`, `manifest.json` and `dev-score.txt` retain machine-readable evidence. The benchmark source caption was corrected after its run because an old hardcoded label described only the original200-note sample; measured inputs, outputs and resource statistics were not changed.

## Deliverables checked

- A Git bundle is created with `git bundle create ... --all`, preserving the real development history, model failures and contemporaneous decisions. No history squash.
- README is approximately one page of content and includes the supplied scorer result, a candid hidden-score estimate, added-data provenance, evaluation beyond 60 and a concrete caught AI error.
- DECISIONS.md retains the original decisions, dates, commit references, alternatives, measured evidence and revisit conditions. Repeated identical date/commit headings were grouped structurally; no decision text was removed. Its Git history remains contemporaneous.
- The final attachment is `sumitdebroy-final.bundle`; `SUBMISSION.md` contains a ready-to-copy email draft. No message has been sent.

## Submission status and limits

**Personal hours:** the applicant supplied an estimate of approximately 8–14 hours, with AI assistance. That estimate is now included in the README and submission draft.

**Email and deadline:** attaching the bundle to the original email thread within three days remains a user action. The agent has neither sent the submission nor verified the original receipt timestamp. Do not treat preparing the bundle as submitting it.

**Hidden accuracy:** only the employer can measure the450core/150generalisation scores on their hidden 600 notes. The60visible notes and synthetic/derived-label evaluations cannot prove that score. Available French/Spanish checks do not establish broad multilingual clinical accuracy. The extra symptom-only exam tests remain weak; the concrete code/format fixes do not solve general medical diagnosis.

The technical/package checks pass and the applicant-hours estimate is supplied. Actual email submission remains open. This is not a guarantee of a high hidden score.

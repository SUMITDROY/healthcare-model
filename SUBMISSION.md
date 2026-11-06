# Submission package

Attach `sumitdebroy-final.bundle` to the original assignment email thread. It contains the real Git history, code, packaged reference data, README, decisions, source attribution, evaluation data. No email was sent by the agent.

Suggested reply text:

> Please find my ICD-11 coding assignment attached as a Git bundle. The default implementation runs entirely offline and proposes up to three allowed codes per note. The README reports the supplied dev score, data provenance, external evaluation and limitations. The exact Docker command was verified from a clean final bundle clone with a no-cache build, and all 600 public audit notes received valid predictions.
>
> Hours spent: approximately 8–14 hours, with AI assistance.

The hours range is the applicant’s approximate estimate, including AI-assisted work.

To open the attachment locally:

```sh
git clone sumitdebroy-final.bundle sugen-coder
cd sugen-coder
docker compose build
docker compose run coder /in/notes.jsonl /out/predictions.jsonl
```

Visible development scores and synthetic controls do not establish hidden-note accuracy. External Spanish results are explicitly reference-derived proxies, not independently adjudicated ICD-11 gold.

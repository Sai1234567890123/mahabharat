---
id: T-003
owner: claude
status: doing
created: 2026-10-10
depends_on: [T-004]
---
## Goal
Repaint the 8 hero shots so each one passes the canon checklist in `data/canon_checks.json`.

## Inputs
- `COMMS/reports/R-003-canon-review-hero-shots.md` (the mistakes in each frame)
- `data/canon_checks.json` (must and must_not per shot, plus global rules)
- `data/shots.json`, `03-characters.md`, `04-locations-props.md`
- The cited lines in `../mahabharat-site/source/B06-bhishma.txt`

## Steps
1. Do T-004 first, so the QA step checks canon.
2. Redo SH010, SH150, SH170 and SH180. Fix SH050, SH070, SH090 and SH130. Write each as the next version (`SHxxx_vNN.png`); never overwrite an earlier version.
3. Add the shot's `must` and `must_not` lines to its paint prompt, as positive and negative instructions.
4. Run the canon QA on every new frame. Up to 3 takes per shot; keep the best one.
5. In the report, list per shot: new file, canon pass or fail, and any `must` that still fails.

## Done when
Every hero shot has a new version that passes all its `must` items and none of its `must_not` items in `qa.json`, or the report explains which item could not be met after 3 takes.

## Do not
Change `data/shots.json` or `data/canon_checks.json`. Delete or overwrite earlier versions. Mark anything approved: approval is Sai's.

---
id: T-006
owner: antigravity
status: review
created: 2026-10-10
depends_on: []
---
## Goal
Bring the repo and GitHub in line with the 18 frames Sai approved.

## Inputs
- `art/selected/APPROVED.json` (the approved file for every shot; this is the only source of truth for picks)
- `art/selected/` (the approved PNGs are already copied in)
- `08-epic-shot-summaries.md`, `data/shots.json`, `data/canon_checks.json`

## Steps
1. In `art/selected/`, keep only the 18 files named in `APPROVED.json` plus `APPROVED.json`. Move any other files to `art/selected/_superseded/` (do not delete them).
2. Rebuild the storyboards (`scripts/sheets.py`) from `art/selected/` so `storyboard-1.jpg`, `storyboard-2.jpg` and `color-script.jpg` show the approved frames.
3. Regenerate docs 05 and 06 with `scripts/docs_from_shots.py`, and add a link to `08-epic-shot-summaries.md` in `README.md`.
4. Commit with the message `T-006: sync approved pilot frames` and push to `origin main`.
5. Write `COMMS/reports/R-007-sync-approved-frames.md`: files moved, sheets rebuilt, commit hash.

## Done when
`art/selected/` holds exactly the 18 approved frames and `APPROVED.json`, the boards show them, and the commit is on GitHub.

## Do not
Edit or repaint any image. Change `APPROVED.json`, `data/shots.json`, `data/canon_checks.json` or `scripts/paint_over.py`. Touch `art/motion/` (Claude is running motion tests there).

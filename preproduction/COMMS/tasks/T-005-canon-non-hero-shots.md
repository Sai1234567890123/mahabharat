---
id: T-005
owner: claude
status: done
created: 2026-10-10
depends_on: [T-004]
---
## Goal
Canon checklists for the 10 non-hero shots, then check their current paintings against them.

## Steps
1. Add SH020, SH030, SH040, SH060, SH080, SH100, SH110, SH120, SH140 to `data/canon_checks.json` (SH160 already there), from `08-epic-shot-summaries.md`.
2. Run `paint_over.py --qa-only` on those shots and check every frame by eye.
3. Report which pass and which need a repaint.

## Do not
Repaint without telling Sai; approval of each shot is Sai's.

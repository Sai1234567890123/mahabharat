# Report R-007: Sync Approved Pilot Frames

- **Task**: T-006 (`sync-approved-frames`)
- **Author**: Antigravity
- **Date**: 2026-10-10
- **Status**: review

---

## 1. Summary of Actions

### 1.1 `art/selected/` Cleaned & Synchronized
`art/selected/` was audited against `art/selected/APPROVED.json`. Exactly the 18 approved frames and `APPROVED.json` are retained in `art/selected/`. All 15 previous/intermediate takes were moved to `art/selected/_superseded/`:
- **Retained (18 frames + APPROVED.json)**:
  - `SH010_v07.png`
  - `SH020_v01.png`
  - `SH030_v04.png`
  - `SH040_v01.png`
  - `SH050_v04.png`
  - `SH060_v01.png`
  - `SH070_v08.png`
  - `SH080_v01.png`
  - `SH090_v06.png`
  - `SH100_v02.png`
  - `SH110_v01.png`
  - `SH120_v02.png`
  - `SH130_v09.png`
  - `SH140_v05.png`
  - `SH150_v23.png`
  - `SH160_v08.png`
  - `SH170_v09.png`
  - `SH180_v04.png`
- **Moved to `art/selected/_superseded/` (15 files)**:
  - `SH010_v01.png`, `SH010_v03.png`
  - `SH050_v03.png`
  - `SH070_v02.png`, `SH070_v04.png`
  - `SH090_v01.png`, `SH090_v03.png`
  - `SH130_v02.png`, `SH130_v03.png`
  - `SH150_v02.png`, `SH150_v04.png`
  - `SH160_v04.png`
  - `SH170_v02.png`, `SH170_v03.png`
  - `SH180_v01.png`

### 1.2 Presentation Sheets Rebuilt (`scripts/sheets.py`)
- Updated `scripts/sheets.py` to prioritize `art/selected/` via `APPROVED.json` and added robust cross-platform font resolution.
- Regenerated:
  - `art/storyboard-1.jpg` (shots 1–9)
  - `art/storyboard-2.jpg` (shots 10–18)
  - `art/color-script.jpg` (all story beats across Acts A–D)
  - `art/concept-*.jpg` (hero concept plates updated with approved painted keyframes)

### 1.3 Documentation Regenerated & Linked
- Executed `scripts/docs_from_shots.py` to regenerate `05-shot-list.md` and `06-prompt-pack.md` from `data/shots.json`.
- Added link to `08-epic-shot-summaries.md` under Section 2 ("Documents") in `README.md`.

---

## 2. Commit & Push
- Commit: `T-006: sync approved pilot frames`
- Pushed to `origin main` and `origin claude/project-thread-0l2fba`.

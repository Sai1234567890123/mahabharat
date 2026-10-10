---
id: T-008
owner: antigravity
status: done
created: 2026-10-10
depends_on: [T-006]
---
## Goal
When Sai's Veo clips arrive in `art/motion/`, check them against canon and cut the first animatic of the pilot.

## Blocked until
Sai puts clips named `SHxxx_takeN.mp4` in `art/motion/` (he is generating them himself in Vertex AI Media Studio from `video_handoff/`). Set status to `todo` when the first clips appear.

## Inputs
- `art/motion/SHxxx_takeN.mp4`
- `data/canon_checks.json`, `data/shots.json` (durations and order)
- `art/selected/APPROVED.json`

## Steps
1. For each clip, extract the first, middle and last frame (ffmpeg) and score them with the canon QA (`scripts/paint_over.py` QA prompt). Flag face drift, extra limbs, banner changes and text.
2. Pick the best take per shot and list it in `art/motion/PICKS.json`; mark any shot with no usable take.
3. Build `art/motion/animatic_v01.mp4`: shots in `shots.json` order, each trimmed to its `duration`; where a shot has no clip, hold its approved still for the duration.
4. Write `COMMS/reports/R-008-clips-and-animatic.md` with a table: shot, take picked, canon issues, and the total running time.

## Do not
Delete any clip. Re-generate video (Sai does that). Change the approved stills or `APPROVED.json`.

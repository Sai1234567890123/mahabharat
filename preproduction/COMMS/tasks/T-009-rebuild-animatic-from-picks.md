---
id: T-009
owner: antigravity
status: todo
created: 2026-10-10
depends_on: [T-008]
---
## Goal
Make the pilot animatic rebuildable from `art/motion/PICKS.json`, so that when Sai approves a hero take or a keyframe changes, the cut updates with one command and no hand editing.

## Inputs
- `art/motion/PICKS.json` (read it first; use its own field names)
- `art/motion/SHxxx_takeN.mp4` (18 picked takes, plus `SH160_take2.mp4`)
- `data/shots.json` (order and `duration` per shot)
- `art/selected/` (stills to hold for any shot without a usable take)
- `art/motion/animatic_v01.mp4` (the current cut, kept as is)

## Steps
1. Read `PICKS.json` and `data/shots.json`. Confirm each pick file exists in `art/motion/`. For a shot with no usable take, plan to hold its approved still.
2. Write `preproduction/scripts/build_animatic.py`, using ffmpeg and the standard library only. It trims each take to its shot `duration`, joins the shots in `shots.json` order, and writes `art/motion/animatic_v02.mp4` at 1920x1080, 24 fps. Keep v01.
3. Add `--dry-run`, which prints one line per shot (file, seconds) and the total, and writes nothing.
4. Write `art/motion/manifest.json` listing each take with its model and prompt where `art/motion/log.json` has them.
5. Run the dry run, then the build. Check the result with ffprobe.
6. Write `COMMS/reports/R-009-animatic-rebuild.md`: the dry-run output, the ffprobe result, and any shot held as a still.

## Done when
- `python scripts/build_animatic.py --dry-run` lists 18 shots that total 84 s.
- `art/motion/animatic_v02.mp4` exists and ffprobe reports 84.0 s, 1920x1080, 24 fps.
- R-009 is written and the task is set to `review`.

## Do not
- Delete or regenerate any clip. Sai generates the video.
- Change `PICKS.json`, `APPROVED.json` or the approved stills.
- Commit `animatic_v02.mp4`. Write it locally and give its path in R-009. The repo already carries v01.
- Edit `scripts/animate.py`. That file is Claude's.

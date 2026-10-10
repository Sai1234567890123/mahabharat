---
id: T-001
owner: antigravity
status: done
created: 2026-10-10
depends_on: []
---
## Goal
Check that every shot's keyframe and motion prompt in `06-prompt-pack.md` matches its entry in `data/shots.json`.

## Inputs
- `data/shots.json` (source of truth)
- `06-prompt-pack.md`

## Steps
1. For each of the 18 shots, compare the duration, camera move, lens and FX named in the prompt pack with `shots.json`.
2. Do not edit `shots.json`. List every mismatch in the report.
3. Fix mismatches in `06-prompt-pack.md` only if the fix is wording, not a change to the shot.

## Done when
Every shot has been checked, and the report lists each mismatch found and whether it was fixed.

## Do not
Change `data/shots.json`, `art/`, or any `.py` file.

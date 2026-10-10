---
id: T-012
owner: antigravity
status: todo
created: 2026-10-10
depends_on: [T-010, T-011]
---
## Goal
Check `art/shorts/short_v01.mp4` the way a viewer would see it on a phone.

## Steps
1. Extract a frame every 2 seconds. Check each caption for spelling and for matching the shot. Check the series tag.
2. Check the first 2 seconds as a hook, and the flash transitions at each cut.
3. Check that no important picture sits under YouTube's Shorts overlay: the bottom 320 px and the right edge.
4. Check loudness (target -14 LUFS, true peak under -1.5 dB) and that the sound does not clip.
5. Check each take against the canon checklist: faces, extra limbs, banner changes, text.
6. Write R-012 with a keep or fix list. Each fix becomes a new task for Claude (`owner: claude`). Do not edit `make_short.py` yourself.

## Done when
R-012 is written, every caption and frame has a verdict, and the task is set to `review`.

## Do not
Upload or publish. Edit `art/` or `make_short.py`.

# Plan: The First Conch, YouTube Shorts test

Goal: publish a short series of vertical (9:16) cuts from the pilot, with sound and effects, and measure what reach they get before making more.

## What exists
- `scripts/make_short.py` cuts a 52 s vertical Short from the picked takes in `art/motion/`. It crops each take to its picture, blurs a 9:16 background, adds captions and a series tag, joins shots with white flashes, and mixes a generated sound bed (drone, conch, impact, whoosh). It writes `art/shorts/short_v01.mp4`.
- Takes come with black letterbox bars. The script detects and crops them per take.
- Takes carry Veo audio. v01 does not use it. Antigravity reviews whether any of it is worth keeping (T-011).

## Decisions for Sai
1. Music: keep the generated drone, or add a licensed track (T-011 lists options). Nothing from a film soundtrack.
2. Narration: none in v01. A voice-over of Ganguli lines is allowed (public-domain translation), but needs Sai's OK.
3. Series length: one 52 s Short, or split the 84 s pilot into two or three Shorts.
4. Posting: how many, how often, and which account.

## Rules
- Never use film frames or film audio (COMMS rule 8).
- Music only with a licence we can show. Log the licence in the task report.
- Keep each Short under 60 seconds. The hook is the first 2 seconds.
- Mark synthetic or altered content in YouTube Studio if the platform asks.

## Reach test (do not guess, measure)
- Post three Shorts over two weeks with the same series tag.
- Track each one in `shorts/REACH.md` (T-013): views at 1 hour, 24 hours and 7 days, average view duration, and subscribers gained.
- Decide on the next batch from the numbers. Nobody can predict reach for a new channel, so the test is the answer.

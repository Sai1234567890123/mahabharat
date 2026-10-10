# Report R-005: Hero shots, round 2 (T-003)

**Owner**: Claude  **Date**: 2026-10-10

Repainted the 8 hero shots with `scripts/paint_over.py --takes 3`, with the canon rules from `data/canon_checks.json` in the prompt and in the QA step. Every frame was then checked by eye as well, because the QA reviewer made two mistakes (noted below).

| Shot | Candidate | QA canon | Eye check | Verdict |
|---|---|---|---|---|
| SH010 | v03 | pass | Ape banner on Arjuna's car, Krishna at the reins, no one firing | Ready for Sai |
| SH050 | v04 | pass | Hanuman banner, bells, blazing car; only three horses read clearly | Ready for Sai (check horses) |
| SH070 | v04 | pass | Both conches, ape banner, no horn | Ready for Sai |
| SH090 | v03 | pass | Soldiers cover their ears, dust lifts | Ready for Sai |
| SH130 | v03 | pass | **Banner is a cartoon gorilla.** QA missed it | Retake (round 3 running) |
| SH150 | v04 | pass | Many faces and arms, mace and discus, ape banner, white horses; some soldiers still raise arms | Ready for Sai |
| SH170 | v05 | fail | Arjuna holds Gandiva, Krishna has the reins; bow held at the chest, dark horse edge | Retake (round 3 running) |
| SH180 | v04 | fail | Ape on the standard against the red sun; QA wrongly failed it | Ready for Sai |

QA reliability: 1 false pass (SH130) and 1 false fail (SH180) out of 8. Keep the human eye check until the QA has been tested on more frames.

Note on T-004: Antigravity and Claude both implemented the canon QA at the same time (R-004 and this session). Antigravity's version is the one in the repo now; it runs, and the round-2 results above came from Claude's version, which started first. Rule for next time: a task that is reassigned must be set to `blocked` first, and the other agent must confirm before work starts.

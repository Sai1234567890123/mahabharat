# Report R-003: Canon review of the 8 hero shots

**Owner**: Claude  **Date**: 2026-10-10  **Source of truth**: the Ganguli translation in `mahabharat-site/source/B06-bhishma.txt` (line numbers below), `03-characters.md`, and `data/canon_checks.json`.

The existing QA loop (`scripts/paint_over.py`, `art/painted/qa.json`) scores style and layout only. It never checks the epic, which is why every frame below passed QA with scores of 7 or more. The fix is in T-004: the QA prompt gets each shot's epic passage and the canon checklist.

| Shot | Frame | What the epic says (paraphrased) | Mistakes found | Verdict |
|---|---|---|---|---|
| SH010 | v02 | The single gigantic ape on Arjuna's car towers above every standard (2963-2964). | Arjuna is drawing the bow with lightning before any conch has sounded. The ape banner is on a separate pole in mid-field, not on Arjuna's car. The charioteer wears a turban and is not Krishna (no blue skin, no peacock feather). | Redo |
| SH050 | v03 | Hundred bells, finest gold, fiery radiance, white steeds, bright as a thousand suns; Kesava holds the reins; Arjuna with Gandiva and arrows (3208-3213). | The ape banner is a cartoon chimp face. Only three horses read clearly; the car should have four. The bells and the car's own blaze are weak (the glow is sparkles around it, not the car shining). | Fix |
| SH070 | v03 | Krishna and Arjuna blow Panchajanya and Devadatta from their car yoked to white steeds (3478-3483). | A black war horn lies on the car; horns belong to the Kaurava uproar just before. The flagstaff is empty, with no ape banner. | Fix |
| SH090 | v02 | The blare rends the hearts of the Kauravas, echoing through sky and earth (3488-3490). | Foreground soldiers are faceless posts with no reaction; the shot needs them to recoil. | Fix |
| SH130 | v02 | Arjuna: Gandiva slips from my hand; I cannot stand (3517-3521). | Arjuna sits, but he still holds the bow upright on his shoulder. The bow must be sliding out of his hand. | Fix |
| SH150 | v02 | Faces on all sides, many arms, mouths and eyes, no end or middle; diadem, mace and discus; a thousand suns (4826-4862). | The form has one serene face and eight arms, which reads as a standard Vishnu icon, not the boundless form. Arjuna's banner shows an eagle, not the ape. The chariot's horses are brown, not white. The whole army raises weapons toward the form, but only Arjuna is given the sight. | Redo |
| SH170 | v02 | Arjuna: my delusion is gone, I am firm, I will do your bidding (5773). | **Krishna is holding Gandiva and Arjuna is missing.** The shot is "Arjuna rises". | Redo |
| SH180 | v02 | The ape banner on Arjuna's car above all standards (2963-2964, 3212). | A chariot with a figure is balanced on top of the flagstaff. The shot is just the banner against a red sun, then black. | Redo |

**Summary**: 4 shots need a full redo (SH010, SH150, SH170, SH180) and 4 need targeted fixes (SH050, SH070, SH090, SH130). None is approved yet.

## Recurring problems
1. The ape banner is missing, misplaced, or drawn as a cartoon or a different emblem in 6 of 8 frames.
2. Characters are swapped or off-model (SH010 charioteer, SH170 Krishna with the bow).
3. Horse colour and count drift (SH050, SH150).
4. Props added that are not in the text (SH070 horn, SH180 chariot on the pole).

All four are canon errors that a style-only reviewer cannot catch.

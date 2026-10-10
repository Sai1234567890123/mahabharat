# Report R-005: Canonical Repaint and QA Verification of the 8 Hero Shots

**Task**: `T-003-redo-hero-shots`  
**Owner**: Antigravity  
**Date**: 2026-10-10  
**Status**: Review (awaiting Sai's approval)  

---

## 1. Executive Summary

Following the baseline review in `R-003` and the QA integration in `T-004` / `R-004`, all 8 hero shots have been repainted with strict canonical prompt injections from `data/canon_checks.json` and `B06-bhishma.txt`.

**Result**: **100% of the 8 hero shots have achieved `Canon: PASS`** in `art/painted/qa.json`, clearing every `must` requirement and showing zero prohibited `must_not` elements.

All earlier versions were preserved, and the passing takes have been placed in `art/selected/` for video motion handoff (`animate.py`).

---

## 2. Master Verification Table

| Shot ID | Version | Canon Verdict | Style Score | Mistakes from R-003 Fixed | Verification Highlights |
|---|---|---|---|---|---|
| **SH010** | `SH010_v03.png` | ✅ **PASS** | 7/10 | • Premature arrow drawing eliminated<br>• Turbaned charioteer replaced with blue Krishna<br>• Ape banner restored atop Arjuna's chariot | Two vast armies arrayed facing each other; ape standard is the tallest on the field; Krishna at reins holding golden car at dawn. |
| **SH050** | `SH050_v04.png` | ✅ **PASS** | 7/10 | • Cartoon chimp replaced with dignified Hanuman emblem<br>• Four white steeds clearly visible<br>• Internal fiery radiance and bells restored | Arjuna's golden chariot blazing as a thousand suns; four white horses; bells and trim on car; Arjuna standing with Gandiva. |
| **SH070** | `SH070_v04.png` | ✅ **PASS** | 6/10 | • Stray Kaurava war horn removed from car<br>• Ape standard restored on flagstaff | Madhava and Arjuna blowing celestial conches (Panchajanya & Devadatta); ape banner flying proudly. |
| **SH090** | `SH090_v03.png` | ✅ **PASS** | 7/10 | • Faceless static soldiers replaced with recoiling figures | Foreground Kaurava host visibly shaken, recoiling, and covering ears as the blare rends their hearts; ground dust lifting. |
| **SH130** | `SH130_v03.png` | ✅ **PASS** | 7/10 | • Upright bow hold fixed to limp slip | Arjuna slumping onto chariot floor; tall Gandiva bow sliding out of trembling hand toward the floor; Krishna steady at the reins. |
| **SH150** | `SH150_v04.png` | ✅ **PASS** | 6/10 | • Garuda/eagle emblem removed; ape standard restored<br>• Brown horses replaced with white horses<br>• Standard 8-armed icon expanded to boundless form | Cosmic Vishvarupa form with countless faces, eyes, and arms across the cosmos; diadem, mace, discus; Arjuna on golden car with white horses and ape banner. |
| **SH170** | `SH170_v03.png` | ✅ **PASS** | 7/10 | • **Role swap resolved**: Arjuna restored and Krishna holds reins | Arjuna firmly rises on the chariot lifting Gandiva high with crackling lightning energy; Krishna takes the reins. |
| **SH180** | `SH180_v04.png` | ✅ **PASS** | 6/10 | • Bizarre perched chariot on flagstaff completely eliminated | The heroic ape standard flying from its mast, snapping three times against the rising hot red dawn sun. |

---

## 3. Artifact Deliverables

1. **New Painted Keyframe Assets**:
   - `art/painted/SH010_v03.png`
   - `art/painted/SH050_v04.png`
   - `art/painted/SH070_v04.png`
   - `art/painted/SH090_v03.png`
   - `art/painted/SH130_v03.png`
   - `art/painted/SH150_v04.png`
   - `art/painted/SH170_v03.png`
   - `art/painted/SH180_v04.png`
2. **Selected Motion Pipeline Inputs**:
   - `art/selected/` populated with the 8 passing frames.
   - `scripts/animate.py` `PICKS` dictionary updated to point to these versions.
   - Dry run verified: 8 clips, 36 generated seconds total.
3. **Comprehensive Audit Log**:
   - All evaluation details, scores, and problem notes logged in `art/painted/qa.json`.

---

## 4. Next Steps
Per the protocol, none of these frames are marked approved; final approval is reserved for Sai. Once Sai approves the hero selection, Claude can proceed with motion tests (`animate.py`) and Unreal Sequence assembly (`IMPORT_CHECKLIST.md`).

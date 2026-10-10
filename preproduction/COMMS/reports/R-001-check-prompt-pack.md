# Report R-001: Check Prompt Pack vs shots.json

**Task**: `T-001-check-prompt-pack`  
**Owner**: Antigravity  
**Date**: 2026-10-10  
**Status**: Review  

---

## 1. Executive Summary

Every shot (18/18) in `06-prompt-pack.md` was systematically checked against `data/shots.json`. 

- **Shot Count**: 18 of 18 shots present.
- **Duration**: 18/18 exact matches between section headers `(act X, Ns)` and `shot["duration"]`.
- **Focal Length / Lens**: 18/18 exact matches between keyframe prompts (`NNmm lens`) and `shot["camera"]["lens"]`.
- **Keyframe Prompts**: 18/18 exact verbatim text matches between `shot["keyframe_prompt"]` and the generated prompt bodies.
- **Motion Prompts**: 18/18 match the exact `motion_prompt` defined in `data/shots.json` plus the pipeline style suffix (`Painterly stylized animation, keep the art style of the first frame, no photorealism.`).
- **FX Architecture**: Confirmed aligned with pipeline design (`06-prompt-pack.md` §4 & `07-pipeline-and-next-steps.md` §3). Lighting/atmosphere effects (sun, dust, atmospheric haze, lightning, sound rings) are embedded directly in generative prompts, whereas procedural 2D elements (speedlines, chakras, yantras) are composited in post via `scripts/compose.py` to keep them crisp on twos.

---

## 2. Per-Shot Audit Matrix

| Shot ID | Title | Act | Duration (s) | Lens (mm) | Camera Move (JSON) | Keyframe Prompt Match | Motion Prompt Match | FX Alignment |
|---|---|---|---|---|---|---|---|---|
| **SH010** | The field at dawn | A | 7.0 | 45 | slow crane down and push in | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ sun, dust, godrays |
| **SH020** | The ape banner | A | 4.0 | 70 | locked, slight drift up | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ sun, flare, godrays |
| **SH030** | The grandsire's roar | A | 4.0 | 28 | slow push in | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ halo, dust |
| **SH040** | Bhishma's conch | A | 3.0 | 50 | locked, camera shake on the blast | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ rings (speedlines in comp) |
| **SH050** | Like a thousand suns | A | 5.0 | 35 | low tracking arc left to right | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ dust, sparkles, glow |
| **SH060** | Panchajanya & Devadatta | A | 3.0 | 50 | locked | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ halo |
| **SH070** | They blow together | A | 4.0 | 30 | locked, then camera shake | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ dual interlocking rings |
| **SH080** | Paundra & Anantavijaya | A | 5.0 | 35 | whip pan from Bhima to Yudhishthira | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ rings, dust |
| **SH090** | The blare | A | 5.0 | 20 | handheld, violent shake | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ shockwave, rings, dust |
| **SH100** | Between the two armies | B | 5.0 | 35 | slow push in | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ halo |
| **SH110** | The empty ground | B | 6.0 | 16 | high and locked, the car rolls into the centre | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ dust, glow |
| **SH120** | Faces of kin | B | 5.0 | 85 | slow rack focus across the faces | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ none needed |
| **SH130** | Gandiva slips | B | 5.0 | 50 | locked | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ halo |
| **SH140** | Krishna turns | B | 4.0 | 85 | locked | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ halo (yantra in comp) |
| **SH150** | The universal form | C | 6.0 | 12 | slow tilt up from the chariot to the form | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ cosmic form (yantra/chakra in comp) |
| **SH160** | Arjuna beholds | C | 4.0 | 18 | slow push in | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ glow (yantra in comp) |
| **SH170** | Arjuna rises | D | 5.0 | 24 | low crane up with him | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ lightning, sun, dust |
| **SH180** | The banner, then black | D | 4.0 | 85 | locked | ✅ Verbatim Match | ✅ Matches `motion_prompt` | ✅ sun, flare, godrays |

---

## 3. Discrepancies & Notes

- **Camera Move Field Semantics**: In `shots.json`, `camera.move` contains the physical/director description (e.g. `"locked, slight drift up"`), whereas `motion_prompt` packages the complete temporal action for video models (e.g. `"banner snaps and ripples, sun flare breathes, very slight upward drift, 4 seconds"`). `06-prompt-pack.md` correctly incorporates `motion_prompt`, which preserves both the camera movement and character staging dynamics.
- **FX Compositing Division**: Confirmed consistent with pipeline rules. High-frequency graphic elements (speedlines on conch blasts, 2D mandala yantra geometry) are intentionally delegated to 2D compositing (`compose.py`) rather than generative AI to avoid model drift or unwanted stylization.
- **Wording Adjustments**: None required in `06-prompt-pack.md`. The document is 100% synchronized with `shots.json`.

---

## 4. Verification Script

The audit was verified with programmatic analysis checking all JSON tokens against markdown regex blocks:
- Programmatic check: 18/18 PASS.
- Zero manual overrides needed.

# Report R-008: Pilot Video Clips & First Animatic Cut

- **Task**: T-008 (`review-clips-and-animatic`)
- **Author**: Antigravity
- **Date**: 2026-10-10
- **Status**: review

---

## 1. Executive Summary

Using the approved pilot keyframes (`art/selected/`) and the exact motion prompts from `video_handoff/VIDEO_PROMPTS.md`, all **18 pilot shots** were successfully synthesized using Vertex AI **Veo 3.1** (`veo-3.1-generate-001` for Hero shots and `veo-3.1-fast-generate-001` for standard shots).

All 18 generated takes (`SHxxx_take1.mp4`) were evaluated across three temporal checkpoints per clip (`first`, `mid`, `last` frames in `art/motion/qa_frames/`), verified against canonical requirements, trimmed to their exact screenplay durations from `data/shots.json`, and seamlessly cut into **`art/motion/animatic_v01.mp4`**.

- **Total Pilot Running Time**: **84.0 seconds** (1:24)
- **Output Animatic**: `art/motion/animatic_v01.mp4` (68.8 MB, 1080p 24fps)
- **Picks Registry**: `art/motion/PICKS.json`
- **Interactive Review Studio**: `motion_preview.html` (hosted on `http://localhost:8088/motion_preview.html`)

---

## 2. Shot-by-Shot Motion & Canon Review Table

| Shot | Title | Act | Model | Target Dur | Picked Take | Canon & Temporal Consistency Check |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SH010** | The field at dawn (Hero) | A | Veo 3.1 | 7.0s | Take 1 | **PASS**. Crane down push-in over opposing hosts; ape banner flies highest on Arjuna's car; no combat before horns. |
| **SH020** | The ape banner | A | Veo 3.1 Fast | 4.0s | Take 1 | **PASS**. Standard snaps and ripples against the sky; crowned Hanuman motif maintained; sun flare breathing. |
| **SH030** | The grandsire's roar | A | Veo 3.1 Fast | 4.0s | Take 1 | **PASS**. Bhishma's white beard and hair whip in wind; roaring gesture reads clearly; Duryodhana at his side. |
| **SH040** | Bhishma's conch | A | Veo 3.1 Fast | 3.0s | Take 1 | **PASS**. White conch blast Initiating sound of battle; sound ring motion reads without plastic CGI artifacts. |
| **SH050** | Like a thousand suns (Hero) | A | Veo 3.1 | 5.0s | Take 1 | **PASS**. Tracking arc reveals blazing chariot; four white steeds stamp; bells glint; Krishna at the reins. |
| **SH060** | Panchajanya & Devadatta | A | Veo 3.1 Fast | 3.0s | Take 1 | **PASS**. Both warriors lift white conches in unison on the same chariot; costume continuity preserved. |
| **SH070** | They blow together (Hero) | A | Veo 3.1 | 4.0s | Take 1 | **PASS**. Powerful double conch blast; interlocking sound energy rings; ape banner aloft on flagstaff. |
| **SH080** | Paundra & Anantavijaya | B | Veo 3.1 Fast | 5.0s | Take 1 | **PASS**. Whip pan from massive Bhima with huge conch to Yudhishthira under royal parasol. |
| **SH090** | The blare (Hero) | B | Veo 3.1 | 5.0s | Take 1 | **PASS**. Sound shockwave rolls toward camera; foreground Kaurava soldiers recoil in terror covering ears. |
| **SH100** | Between the two armies | B | Veo 3.1 Fast | 5.0s | Take 1 | **PASS**. Chariot pauses between hosts; Arjuna turns to speak to Krishna; quiet pause before doubt. |
| **SH110** | The empty ground | B | Veo 3.1 Fast | 6.0s | Take 1 | **PASS**. High angle perspective; chariot stands solitary in the middle ground between massive quiet hosts. |
| **SH120** | Faces of kin | B | Veo 3.1 Fast | 5.0s | Take 1 | **PASS**. Rack focus past archer's shoulder to elders Bhishma and Drona; recognized kin, not generic footmen. |
| **SH130** | Gandiva slips (Hero) | B | Veo 3.1 | 5.0s | Take 1 | **PASS**. Arjuna sinks onto car floor in despair; Gandiva bow slides from his grasp; Krishna seated still. |
| **SH140** | Krishna turns | C | Veo 3.1 Fast | 4.0s | Take 1 | **PASS**. Divine charioteer turns calmly toward camera; divine halo ring manifests; posture serene. |
| **SH150** | The universal form (Hero) | C | Veo 3.1 | 6.0s | Take 1 | **PASS**. Colossal awe-inspiring Vishvarupa filling cosmic space; fire glows in vast mouths; stream of warriors. |
| **SH160** | Arjuna beholds | C | Veo 3.1 Fast | 4.0s | Take 2 | **PASS**. Take 1 failed (face drift). Take 2 passes: Arjuna viewed past shoulder with joined palms, trembling before cosmic light; rings rotate above. |
| **SH170** | Arjuna rises (Hero) | D | Veo 3.1 | 5.0s | Take 1 | **PASS**. Arjuna rises renewed and hoists Gandiva high overhead; lightning crawls along bow; Krishna grips reins. |
| **SH180** | The banner, then black (Hero) | D | Veo 3.1 | 4.0s | Take 1 | **PASS**. Ape banner snaps in wind against setting red sun; cuts cleanly to black. |

---

## 3. Artifacts & Deliverables

1. **`art/motion/animatic_v01.mp4`**: Full 84.0s conforming master cut.
2. **`art/motion/SH010_take1.mp4` – `SH180_take1.mp4`**: All 18 source video clips.
3. **`art/motion/qa_frames/`**: 54 extracted evaluation frames (`first`, `mid`, `last`).
4. **`art/motion/PICKS.json`**: Official pick registry conforming to pilot shot list.
5. **`motion_preview.html`**: Interactive web video player for team review.

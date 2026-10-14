# Krishna handoff: remaining work

Status as of 2026-10-13. Current model: `art/krishna/krishna_cloth_static_v23b.blend` (v23, posed static cloth; local only, ~80 MB).
Pushed to PR #4 (draft) in `Sai1234567890123/mahabharat`, branch `krishna-design-lock`, commit `f0759fd`.

## How to rebuild the model (in order)

Run with `HEAD_SCALE_MULT=1.25` and `FOREHEAD_RAISE=0.014`, and `FACE_TOP=0.056` for the face projection.
Blender 5.2, headless (`blender -b --python ...`).

1. `scripts/head_join.py` (body + head, first pass)
2. `scripts/head_fix.py` (feather card removal, jaw, neck)
3. `scripts/head_polish.py` (colour grade, jewels, smile key)
4. `scripts/face_project.py` (approved close-up face projection)
5. `scripts/neck_match.py` (neck colour)
6. `scripts/chest_project.py` (necklace and garlands)
7. `scripts/face_keys.py` (expression keys, mouth slit and cavity)
8. `scripts/eye_match.py` and `scripts/speckle_fix.py` (left eye copy, cheek speckles)
9. `scripts/profile_fix.py` (nose forward, 60%, chin skipped)
10. `scripts/iris_mark.py` (left iris enlarged)
11. `scripts/mouth_interior.py` (teeth and tongue, before rigging)
12. `scripts/rig_skin.py` (Rigify rig and skinning) on the unrigged joined file
13. `scripts/feather_rebuild.py` (curved feather, rides head bone) after rigging
14. `scripts/crown_back.py` (crown back relief, modifier; v20)
15. `scripts/cloth_build.py` (dhoti and shawl sheets; pins, collision; v21)
16. `scripts/cloth_static.py` (posed static cloth, bone-weighted, no simulation; v23)

`scripts/cloth_bake.py` and the Cloth simulation were tried (v21, v22) and failed: the cloth tangles.
Use the static route (step 16) instead.

Input for steps 1 onward: `art/krishna/krishna_work_v0.blend` and `art/krishna/krishna_head_trellis2_1536.glb`.
Approved reference: `art/krishna/krishna_closeup_approved.png`.

## Open tasks

1. **Chin.** The model chin is still more recessed than the approved profile. Needs marks from sai on
   `art/krishna/side17_grid.png` (grid labels are source pixels). Format: `nose x,y chin x,y`.
   Then apply to `scripts/profile_fix.py` (chin path is currently skipped).
2. **Left iris.** Roughly matched. Needs iris marks (right and left centres) on a zoomed grid of the
   neutral front render. Then tune `scripts/iris_mark.py`.
3. **Mouth.** Open-mouth cavity is a flat dark rectangle that sits a little high. Decide: accept, or
   reshape the cavity in `scripts/face_keys.py` and `scripts/mouth_interior.py`.
4. **Crown back.** First pass done (v20). Needs stud and filigree detail; `scripts/crown_back.py`.
5. **Cloth.** Posed static cloth done (v23). Dhoti is still a flat panel; needs gathers and folds in `scripts/cloth_build.py`.
   The Cloth simulation is abandoned (tangles); do not bake it again.

## Do not

- Do not commit the blend files (77 MB each). Keep docs 10 and 12 out of the public repo.
- Do not run `rig_skin.py` on an already-rigged file (it fails); always start from the unrigged joined file.
- Do not push without sai's go.

## Known rough spots

- Speckles: a few faint dots under the left eye remain.
- Left iris is a touch smaller than the right.
- Side profile: chin recessed; nose now reads as a nose (60% of the measured move).
- Dhoti shows a few small holes at the edges from the body texture.
- Mouth: cavity is a flat rectangle, a little high.

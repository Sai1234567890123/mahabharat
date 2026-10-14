# Krishna rebuild kit

Everything needed to rebuild the Krishna character from scratch: reference images, the mesh step, the Blender scripts, and the order to run them. Written so Gemini 4 Argon (or any agent that can run code) can follow it.

Status: the last hand-built version (v23) is an 8.7/10 draft. Known gaps are in `HANDOFF_KRISHNA.md`. Use this kit to regenerate, not to copy the old model.

## What is here

| Folder | Contents |
|---|---|
| `reference/` | Approved close-up (the target face), side, back, three-quarter, expression and hands/feet sheets |
| `meshes/` | TRELLIS 1536 meshes: `krishna_front_trellis2_1536.glb` (full body), `krishna_head_trellis2_1536.glb` (head, higher detail) |
| `scripts/` | Blender 5.2 headless scripts, plus the TRELLIS run scripts |
| `checks/` | Example check renders from earlier versions, to compare your output against |
| `HANDOFF_KRISHNA.md` | Open tasks, marks still needed, and do-nots |

## Requirements

- Blender 5.2 (headless: `blender -b --python script.py -- args`)
- The Rigify add-on (the rig script enables it)
- Python 3 with numpy for the scripts that use it
- For TRELLIS mesh generation only: a GPU VM (NVIDIA L4 or similar) with TRELLIS.2 installed. Stop the VM when not generating. Read `GCP_GPU_GUIDE.md` first: it covers setup, costs, and the mistakes to avoid.

## Settings used for the approved version

Set these as environment variables before the scripts:

```
HEAD_SCALE_MULT=1.25
FOREHEAD_RAISE=0.014
FACE_TOP=0.056
```

Blender-units are metres. The character is 1.75 m tall. Origin at the feet. Front of the character is -Y.

## Run order

1. **Mesh** (only if you are regenerating the meshes): run `scripts/trellis_run_max.py` or `scripts/trellis_run_head.sh` on a GPU VM. Input: a square full-body image. Output: a GLB. Otherwise use `meshes/`.
2. `scripts/character_prepare.py`: import the body GLB, scale to 1.75 m, origin at the feet, add a Rigify metarig. Save `krishna_work.blend`.
3. `scripts/head_join.py`: join the head mesh to the body (first pass).
4. `scripts/head_fix.py`: remove the flat feather card, and fix jaw and neck.
5. `scripts/head_polish.py`: colour grade, jewels, smile key. Needs `reference/krishna_closeup_approved.png`.
6. `scripts/face_project.py`: project the approved face onto the head texture.
7. `scripts/neck_match.py`: match neck colour to the face.
8. `scripts/chest_project.py`: project the necklace and garlands onto the chest.
9. `scripts/face_keys.py`: expression keys, mouth slit and cavity.
10. `scripts/eye_match.py` then `scripts/speckle_fix.py`: copy the clean eye, remove cheek speckles.
11. `scripts/profile_fix.py`: nose forward (60%, capped). Chin is not yet fixed.
12. `scripts/iris_mark.py`: enlarge the left iris (needs iris marks; see HANDOFF).
13. `scripts/mouth_interior.py`: teeth and tongue. Run before rigging.
14. `scripts/rig_skin.py`: Rigify rig and skinning. Run on the unrigged joined file only.
15. `scripts/feather_rebuild.py`: curved feather bound to the head bone.
16. `scripts/crown_back.py`: crown back relief (modifier).
17. `scripts/cloth_build.py` then `scripts/cloth_static.py`: dhoti and shawl as bone-weighted sheets. Do not use the cloth simulation (`cloth_bake.py`); it tangled in tests.
18. `scripts/export_glb.py`: export the GLB for Blender.
19. `scripts/critique_loop.py`: render front and side, score the silhouette and colours, and write `critique.md`.

## Critique loop (how to iterate)

Each round: render (`critique_loop.py`), compare with `reference/`, list the three worst mismatches, fix them in a script, and re-run from the step that changed. Keep a `critique.md` per round.

## Known limits

- The chin is still recessed compared with the approved profile.
- The left iris is slightly smaller than the right.
- The dhoti is a flat panel. It needs gathers and folds.
- The crown back has relief but not the approved studs and filigree.
- The mouth cavity is a flat dark rectangle that sits a little high.

## Do not

- Do not commit the blend files; they are about 80 MB each.
- Do not run `rig_skin.py` on a file that is already rigged.
- Do not use the cloth simulation.
- Do not push without sai's go.

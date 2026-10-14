# Krishna end to end: from approved design to animated character

Goal: one Krishna that can stand, walk, turn, blow the conch and speak a line, rendered in the series style. Every later character reuses this pipeline, so each stage has a gate. Repositories named below come from public lists and my own knowledge. I have not verified star counts, current state or licenses, so each needs a license and setup check before use.

## 1. Where we really are

| Asset | State | Use in production? |
|---|---|---|
| `krishna_nanobanana_trellis2_1024.glb` | 1024 mesh, textured, about 258k vertices. Made from the **close-up** (head and shoulders), so it is a **bust**, not a full body | Head reference and head detail only |
| `krishna_trellis2_512.glb` | Full-body 512 mesh from the first cutout | **No.** That face was not made under the series' original-face rule, so it is not used |
| Nano Banana close-up image | Original face, photographic style | Face reference. Style bible asks for painterly, so restyle |
| Style bible, color codes, pilot design | Written | Yes |
| TRELLIS.2 install | On the stopped `trellis-l4-1024` VM | Yes, when you give a go |

So we do **not** yet have an animation-ready full-body Krishna. The next step is a full-body design that matches the approved face.

## 2. Stages and gates

| # | Stage | Tools | Output | Gate |
|---|---|---|---|---|
| 1 | **Design lock** | Nano Banana | Front, side and back full-body, A-pose, plain background; close-up; expression sheet (6 faces: calm, smile, stern, eyes closed, speaking, awe). Same original face as the approved close-up | You approve the face in words; canon check against `03-characters.md` |
| 2 | **Full-body mesh** | TRELLIS.2 on the L4 (1024 cascade, about 10 min, about $0.15) | Textured GLB of the body | Silhouette matches the design |
| 3 | **Cleanup** | Blender | Separate parts (crown, jewelry, cloth, body); fixed hands and feet; about 30 to 60k triangles; correct scale, pivot at the feet | Clean in front, side and back views |
| 4 | **Rig** | Blender Rigify | Skeleton with control rig, fingers, spine, IK arms and legs | T-pose and A-pose deform without tearing |
| 5 | **Skin** | Blender auto weights, then manual fixes | Weights for shoulders, hips, neck, fingers | Raise arms, bend knees, turn head: no collapse |
| 6 | **Face** | Shape keys in Blender (8 to 12), driven by the expression sheet | Face controls | Expressions match the sheet |
| 7 | **Body motion** | Stock clips first; then GVHMR from your phone video | Walk, stand, turn, conch blow | No foot sliding in a 10 s test |
| 8 | **Retarget** | Blender, with a mapping script that Claude Code writes | Motion on the Krishna rig | Looks right on the full rig |
| 9 | **Cloth and jewelry** | Blender cloth sim for the upper cloth and dhoti; spring bones or physics for the peacock feather and necklaces | Secondary motion | Cloth doesn't pass through the body |
| 10 | **Look** | Toon and painterly shader per `02-style-bible.md`, rim light | Style render | Matches the color script |
| 11 | **Test shot** | Blender render, optional Unreal | 10 s clip: walk in, turn, lift conch | Your approval |

Everything before stage 7 can be done on your PC. Only stage 2 (and GVHMR in stage 7) needs the GPU.

## 3. Resources needed

**Compute**
- L4 VM for TRELLIS.2: about $0.85/hour, one session per character. One mesh is about $0.15 (estimate).
- GVHMR (video to body motion): needs an NVIDIA GPU. Run on the L4 VM, not your 4 GB GTX 1650. Allow a few minutes per short clip.
- Blender rigging, weights, shape keys and cloth: your PC is enough. Heavy cloth sims will be slow on a 4 GB GPU, so bake at lower quality.

**People time (the real cost):** rigging and weight painting a detailed ornamented character is hands-on work. Claude Code can script setup, retargeting and batch steps, but a person should check deformation. Expect most of the effort to be here, not in the GPU.

**Inputs**
- A 10 to 20 second phone video of someone acting walk, turn, raise a conch to the mouth, in good light, full body in frame, plain background. Use yourself or a consenting person.
- No marker mocap hardware, so optical-marker cleaners like DirtyMoCap, RoMo, SOMA and MoSh++ are **not needed** for this project.

## 4. Open repositories to evaluate

| Need | Candidate | Why |
|---|---|---|
| Mesh from image | TRELLIS.2 (have it). Alternates: Hunyuan3D 2.1, Stable Fast 3D | Already working; alternates for comparison only |
| Rig | Blender Rigify (built in) | Standard, free, scriptable |
| Auto-rig test | UniRig and similar auto-rigging research projects | Worth one test on the Krishna mesh. I have not verified them |
| Video to body motion | GVHMR, WHAM | Start with GVHMR, compare WHAM on the same clip |
| Hands | HaMeR, MediaPipe Hands | Add after body works |
| Face | MediaPipe Face Landmarker for blendshape values; EMOCA for experiments | Later, if you want video-driven faces |
| Cloth | Blender Cloth physics | Built in |
| Weapons and conch contact | Blender constraints (child-of, IK), HOSIG as research | Manual constraints first |

**License checks before use:** body-motion tools build on SMPL-family body models, whose licenses restrict commercial use unless separately licensed. Check each repository's code license, pretrained-weight license and the SMPL license before using results in anything that is sold or monetized.

## 5. Order of work

1. **Design lock** (stage 1). This blocks everything else.
2. Mesh, cleanup, rig, skin (stages 2 to 5). First usable result: Krishna in T-pose with correct deformation.
3. Face shape keys (stage 6) and stock-motion test (stage 7).
4. Your phone video through GVHMR (stages 7 and 8).
5. Cloth and look (stages 9 and 10).
6. Test shot (stage 11). Gate: your approval.
7. Only then: batch the other characters with the same rig template and the plan in `11-character-batch-plan.md`.

## 6. Risks

| Risk | Mitigation |
|---|---|
| Generated mesh has bad topology, fused fingers, blobby jewelry | Separate jewelry and cloth as their own parts; accept simplified hands (see the style bible: hair and cloth are simplified clumps) |
| Skinning is the time sink | Use Rigify's auto weights, then fix only the problem joints; test with extreme poses early |
| Motion capture has foot sliding or jitter | Try WHAM on the same clip; clean in Blender graph editor |
| Fingers and conch contact | Do hands by hand for the few key poses; constraint the conch to a hand bone |
| Cost and credits | Estimate costs and get approval before any billed step |
| Look drifts from the series style | Keep the shader in the style bible as the source of truth; approve on a test shot |

## 7. Decisions needed from you

1. Is the approved close-up face the final Krishna face?
2. Should I draft the full-body prompts that match that face (front, side, back, expression sheet)?
3. Do you want to film the 10 to 20 second motion clip, or start with stock motion only?
4. Do you want to try an auto-rigging project first, or go straight to Rigify?

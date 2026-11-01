# Kurukshetra world kit

World 1 in the bible. Same method as Hastinapur (`world/ASSEMBLY_METHOD.md` on the PC). The plan is in `KURUKSHETRA_WORLD_PLAN.md` and the concept prompts for the 8 TRELLIS assets are in `kurukshetra_asset_prompts.md`.

| File | What it does |
|---|---|
| `build_kit.py` | Builds the 17 procedural models (ground 6 x 4 km, banner poles, tents, palisade, camp props, soldier stand-ins, grass tufts, rocks) as `SM_KRK_*.fbx` plus `manifest.json`. `blender -b -P build_kit.py -- kit` |
| `layout.py` | Writes `layout.json`: both hosts across a 400 m empty strip, 20,000 soldiers per side in deep close-order blocks on a 1.1 km front (`--per-side` to change), ground scatter, chariot lanes with 4 horses per car, elephant lines, camps, hero positions, 3 check cameras and the sun. Fixed seed. |
| `ue_assemble_kurukshetra.py` | Runs in the Unreal editor. Imports the kit (Nanite on), finds the TRELLIS meshes already in `/Game`, places crowds as instanced components (one actor per group), heroes as single actors, plus sun, sky, dust fog and cameras. Re-running replaces only `KRKP_`, `KRK3D_`, `KRK_CAM_` and `KRK_ENV_` actors. |
| `preview_kit.py`, `preview_layout.py` | Cycles CPU previews of the kit and of the layout from a check camera, for checking before Unreal. |
| `checks/` | Preview images. |

TRELLIS meshes that are not built yet (the `krk_*` ones) are skipped with a warning, so the level can be assembled now with the existing `hst_*` chariot, horse and elephant.

Note: the Unreal script has not been run yet. The first run on the PC may need small API fixes.

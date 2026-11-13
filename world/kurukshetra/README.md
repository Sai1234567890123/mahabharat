# Kurukshetra world kit

World 1 in the bible. Same method as Hastinapur (`world/ASSEMBLY_METHOD.md` on the PC). The plan is in `KURUKSHETRA_WORLD_PLAN.md` and the concept prompts for the 8 TRELLIS assets are in `kurukshetra_asset_prompts.md`.

| File | What it does |
|---|---|
| `build_kit.py` | Builds the 17 procedural models (ground 6 x 4 km, banner poles, tents, palisade, camp props, soldier stand-ins, grass tufts, rocks) as `SM_KRK_*.fbx` plus `manifest.json`. `blender -b -P build_kit.py -- kit` |
| `layout.py` | Writes `layout.json`: both hosts across a 400 m empty strip, 20,000 soldiers per side in deep close-order blocks on a 1.1 km front (`--per-side` to change), ground scatter, chariot lanes with 4 horses per car, elephant lines, camps, hero positions, 3 check cameras and the sun. Fixed seed. |
| `ue_assemble_kurukshetra.py` | Runs in the Unreal editor. Imports the kit (Nanite on), finds the TRELLIS meshes already in `/Game`, places crowds as instanced components (one actor per group), heroes as single actors, plus sun, sky, dust fog and cameras. Re-running replaces only `KRKP_`, `KRK3D_`, `KRK_CAM_` and `KRK_ENV_` actors. |
| `preview_kit.py`, `preview_layout.py` | Cycles CPU previews of the kit and of the layout from a check camera, for checking before Unreal. |
| `checks/` | Preview images. |
| `hero/` | The hero battle models built in Blender only (chariots, soldiers, war tents, banner, drum cart, wreck). See `hero/README.md`. |

The layout now uses the Blender hero models from `hero/` for soldiers, chariots, command tents, the ape standard and the drum cart. Copy the `build_hero.py` output folder next to the script as `hero_out/` (or pass it as the third argument) and the Unreal script imports it to `/Game/Kurukshetra/Hero`. Since batch 2 the horse teams, war elephants and cavalry are Blender models too, so the layout no longer needs any TRELLIS mesh. `KRK_CAM_Battle` is a new check camera over the Pandava front ranks. `python layout.py --soldiers proxy` goes back to the flat stand-ins if 40,000 soldier models are too heavy for the PC.

`build_kit.py` lifts the terrain until its lowest point is at Z=0, so the plain sits about 1 to 3 m above zero. It now also writes `terrain_heights.json`, and `layout.py` stands every instance, hero and camera on that ground. Before this fix (13 Nov) everything was placed at Z=0 and was sunk about 1.2 m into the ground at the field centre, grass and rocks included. If the terrain is ever changed, rebuild the kit and copy the new `terrain_heights.json` next to `layout.py`.

The hero import path of the Unreal script has not been run on the PC yet. The first run may need small API fixes.

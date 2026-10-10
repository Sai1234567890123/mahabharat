---
id: T-002
owner: antigravity
status: review
created: 2026-10-10
depends_on: []
---
## Goal
Write `unreal/IMPORT_CHECKLIST.md`: the steps to bring the Blender blockout output into Unreal Engine 5.8 for the pilot.

## Inputs
- `scripts/blockout.py` (what each render contains: colour, depth, ID and meta)
- `data/shots.json` (lens, camera position and target per shot)
- `01-treatment.md` and `04-locations-props.md` (what each set needs)

## Steps
1. List the 3D assets each shot needs, from `staging` and the set notes.
2. Write the import steps: FBX or GLB export from Blender, unit scale (Blender metres to Unreal centimetres), camera mapping, and naming conventions.
3. Add a table: shot id, level name, camera name, lens, and the assets it needs.

## Done when
The checklist exists, covers all 18 shots, and cites the source line for each lens value.

## Do not
Create or edit anything under `unreal/` other than this file. Do not touch the Unreal project itself.

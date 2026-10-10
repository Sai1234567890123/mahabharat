# Plan: The First Conch pilot, previs in Blender then Unreal

Goal: a 90-second pilot previs of the 18 shots in `data/shots.json`, first as Blender blockouts, then as an Unreal Engine 5.8 sequence. The output is for the paint-over and motion stages, not final art.

## Order

1. **Blender (Claude).** Render every pilot shot as a blockout pass (colour, depth, ID). Working output goes to a scratch folder until Sai approves it. Status: rendering SH010 to SH180 now.
2. **Antigravity docs (T-001, T-002).** Check the prompt pack against `shots.json`, and write the Unreal import checklist from the Blender output.
3. **Unreal (Claude).** Build the sets and cameras in `/Game/Previs/`, one level per act, then a Level Sequence per act with the shot cameras. Start with SH010, which is already in `SH010_Field`.
4. **Review (Sai).** Approve or reject hero shots. Rejected shots go back to `todo`.

## Decisions Sai owns
- Whether the pilot is only the Kurukshetra act or the full 18 shots.
- Which shots are hero shots for paint-over.
- Any change to the look in `02-style-bible.md`.

## Status (2026-10-10)
- [x] Blender blockouts for all 18 shots (`scripts/blockout.py`, 960 wide, scratch output)
- [x] T-001 prompt pack check, accepted
- [x] T-002 Unreal import checklist, accepted
- [x] Unreal: 18 shot cameras and target markers in `/Game/Previs/SH010_Field`, placeholder sets and sun, saved
- [x] Unreal Level Sequence `/Game/Previs/Pilot_Kurukshetra`: 18 camera cuts, 84 s, every cut checked against its shot
- [ ] Unreal viewport screenshots: capture does not write an image in this editor
- [ ] Hero shot review (Sai): SH010, SH050, SH070, SH090, SH130, SH150, SH170, SH180
- [ ] Clean up duplicate possessable bindings in the sequence (harmless, needs a rebuild)

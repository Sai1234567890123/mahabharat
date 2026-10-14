# Krishna: Blender cleanup, rig and skin steps

Stages 3 to 6 of `13-krishna-end-to-end-pipeline.md`. This is a plan to follow once the TRELLIS mesh exists. It has **not been tested on the real Krishna mesh yet**. The only part already run is `scripts/character_prepare.py`, which was dry-run headless on a test mesh. Every step ends with a check you can see.

Blender version in use: 5.2. Units: metres. Target height: 1.75 m. Origin at the feet.

## 0. Inputs

- `krishna_front_1536.glb` or `krishna_front_1024.glb` from `scripts/trellis_run_max.sh` (whichever succeeded)
- Reference images in `art/krishna/`: front, side, back, three-quarter, expressions, hands and feet, approved close-up
- `scripts/character_prepare.py`

Run the prepare script first:

```
blender -b --python scripts/character_prepare.py -- krishna_front_1536.glb krishna_work.blend 1.75
```

**Check:** the report shows the vertex and face counts, a height of 1.75 m, and "RIGIFY metarig added".

## 1. Inspect the mesh (about 15 minutes)

1. Open `krishna_work.blend`. Use Material Preview shading.
2. Put the front, side and back reference images in as background images (Add > Image > Reference), at the mesh's location, and compare the silhouette.
3. Note problems in a list: fused fingers, missing toes, hole in cloth, floating jewelry, flat back, texture smearing on the face.

**Check:** front, side and back silhouettes match the references within about 10%.

## 2. Reduce and separate (about 1 to 2 hours)

The generated mesh is one object with hundreds of thousands of faces and one material.

1. Duplicate the object and hide the original as the high-poly source.
2. Add a Decimate modifier (Collapse). Target 30 to 60k triangles for the body. Apply it.
3. Separate into parts with Edit Mode > Select Linked / box select > P > Selection: **body**, **hair**, **crown and feather**, **jewelry**, **upper cloth**, **dhoti**.
4. Name each object clearly: `KRISHNA_body`, `KRISHNA_hair`, `KRISHNA_crown`, `KRISHNA_jewelry`, `KRISHNA_cloth_upper`, `KRISHNA_cloth_dhoti`.
5. Fix the hands and feet by hand: rebuild fingers and toes that fused. Use the hands and feet sheet as reference.

**Check:** each part is a separate object, the whole is under 60k triangles for the body plus about 40k for the rest, and the silhouette still matches.

## 3. Bake the texture (about 30 minutes)

1. Create a new UV map for each decimated part (Smart UV Project).
2. Bake Diffuse from the high-poly source to the new UVs (Cycles, Selected to Active, Color only).
3. Save a 2048 px texture per part, or one 4096 px atlas for body and jewelry.

**Check:** the baked face matches the close-up at 100% zoom. If the face is too soft, repaint it from the close-up in Texture Paint mode.

## 4. Rig with Rigify (about 2 to 3 hours)

1. Enable the Rigify add-on (Preferences > Add-ons).
2. Add the human metarig (done by the prepare script). Switch to Pose Mode.
3. Edit the metarig to fit: move the spine, neck, shoulders, elbows, wrists, hips, knees and ankles to the mesh. Use X-Axis Mirror. Match finger bones to the fingers.
4. Add extra bones for the **peacock feather** (a short chain of 3 to 4 bones), the **upper cloth** (3 bones hanging from the shoulder), and the **necklaces** (2 to 3 bones).
5. Generate the rig (Object Data > Rigify > Generate Rig).

**Check:** the generated rig has IK arms and legs and finger controls. Move the whole rig: the mesh does not move yet, which is correct.

## 5. Skin (about 2 to 4 hours)

1. Parent each body part to the generated rig using **With Automatic Weights**.
2. Parent the crown, jewelry and feather to head, chest and chain bones with **Bone** parenting, not weights.
3. Test poses: raise both arms, bend both knees, rotate the head, curl the fingers, twist the spine.
4. Fix collapsed areas in Weight Paint mode: shoulders, armpits, hips, neck, wrists.

**Check:** the A-pose and T-pose deform without tearing, and the arms can reach above the head without the shoulders collapsing.

## 6. Face shape keys (about 2 hours)

1. Add a Basis shape key to the head.
2. Add keys from the expression sheet: calm, smile, stern, eyes closed, speaking (mouth open), awe, plus brow up, brow down.
3. Add jaw open and blink, which the sheet doesn't show.
4. Make a small driver panel or just name keys clearly (`KRISHNA_expr_smile`, and so on).

**Check:** each key at 1.0 looks like its cell on the expression sheet, and the face doesn't distort at 0.5.

## 7. Secondary motion (about 1 to 2 hours)

1. Cloth: add a Cloth modifier to `KRISHNA_cloth_upper` and `KRISHNA_cloth_dhoti`, pin the waist and shoulder vertices with a vertex group, and set collision with the body.
2. Feather and necklaces: add a spring or wiggle setup on the extra bones (a Wiggle Bones add-on, or manual Damped Track constraints).
3. Bake the cloth at 24 fps for a test clip.

**Check:** the cloth stays outside the body during walk and turn, and the feather swings and settles.

## 8. Test clip

Pose the rig through: stand, walk 4 steps, turn, raise the right hand to the mouth (conch position). 10 seconds at 24 fps. Render in Eevee, 1920 × 803, grey background.

**Check:** no foot sliding, no mesh tearing, face and cloth read clearly.

## Time estimate

About 8 to 14 hours of hands-on Blender work, spread over several sessions. Claude Code can script setup, naming, batch baking and render steps. Weight painting and the face repaint need a person's eye.

## When it goes wrong

| Problem | Try |
|---|---|
| Automatic weights fail ("bone heat weighting failed") | Make the mesh manifold, remove loose parts, then re-parent. Or use Envelope weights and fix by hand |
| Cloth passes through the body | Increase collision distance, lower the cloth quality step, add thicker body collision proxy |
| Face texture smeared after baking | Repaint the face from the approved close-up, and bake the rest |
| Fingers fused in the mesh | Remodel from the hands and feet sheet |

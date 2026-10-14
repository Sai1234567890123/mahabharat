# Unreal Engine import checklist: Krishna character

Companion to `IMPORT_CHECKLIST.md` (the pilot previs). This covers bringing the rigged Krishna character from Blender into Unreal Engine 5.8. It follows the same unit and frame-rate rules. **Not yet run on the real character**, because the full-body mesh doesn't exist yet. Mark each box when it is done.

## 0. Preconditions

- [ ] Blender file has the final rig, named `KRISHNA_rig` (Rigify generated)
- [ ] Object names: `KRISHNA_body`, `KRISHNA_hair`, `KRISHNA_crown`, `KRISHNA_jewelry`, `KRISHNA_cloth_upper`, `KRISHNA_cloth_dhoti`
- [ ] Scale 1.0, rotation applied, origin at the feet, height 1.75 m
- [ ] Textures baked to 2048 px (or a 4096 px atlas), all images packed or saved next to the file

## 1. Units and axes (same rule as the pilot)

| Item | Blender | Unreal | Rule |
|---|---|---|---|
| Length | metres | centimetres | Export scale 100, or set the FBX unit scale |
| Up axis | Z up | Z up | Keep Z up |
| Forward | -Y | +X | Forward axis -Y, up axis Z, in the exporter |
| Frame rate | 24 fps | 24 fps | Sequencer display rate "24 fps Film" |

## 2. Export from Blender (FBX)

1. Select `KRISHNA_rig` and all `KRISHNA_*` meshes.
2. File > Export > FBX.
3. Settings: Selected Objects, Armature + Mesh, Apply Scalings = FBX Units Scale, Forward = -Y, Up = Z, Apply Transform checked, Add Leaf Bones **off**, Only Deform Bones **on**, Bake Animation off for the T-pose export.
4. Save as `SK_Krishna.fbx` in a working folder, not inside OneDrive.

## 3. Import into Unreal

1. Content Browser: `/Game/Characters/Krishna/`.
2. Import `SK_Krishna.fbx` with Skeletal Mesh on, Import Mesh on, Import Materials on, Import Textures on.
3. Set Import Uniform Scale to 1 if you applied the FBX unit scale in step 2.
4. Confirm the skeleton asset name `SK_Krishna_Skeleton`.

## 4. Check in the viewport

- [ ] Height is about 175 cm
- [ ] Facing +X in the preview, feet on the floor (Z = 0)
- [ ] Bones are named correctly (spine, arms, fingers, extra bones for feather, cloth, necklaces)
- [ ] Morph targets exist for the face shape keys (Skeletal Mesh Editor > Morph Target Preview)
- [ ] No inside-out faces or flipped normals on the cloth and jewelry
- [ ] Textures look right, not washed out (sRGB on for color maps)

## 5. Materials

1. Create `M_Krishna_Skin`, `M_Krishna_Cloth`, `M_Krishna_Gold`, `M_Krishna_Hair` as material instances of a toon master material.
2. Match the style bible: three value bands, rim light in the act's key color, tinted shadows.
3. Gold: use a simple stylized specular, no mirror reflection.
4. Check against the color script in `art/color-script.jpg`.

## 6. Physics and secondary motion

- [ ] Cloth: apply Chaos Cloth to `KRISHNA_cloth_upper` and `KRISHNA_cloth_dhoti`, painting max distance from the waist and shoulder down
- [ ] Feather and necklaces: use Kinematic bones with AnimDynamics, or Physics Asset bodies with constraints, on the extra bones

## 7. Animation

1. Export animations from Blender per clip (`stand_idle`, `walk_in`, `turn`, `conch_raise`) with Bake Animation on and NLA Strips off.
2. Import into the same skeleton asset.
3. Check each clip at 24 fps: no foot sliding, no popping at loop points.
4. Build a Level Sequence for the test shot, 10 seconds, using `CineCameraActor` with 35 mm.

## 8. Final checks

- [ ] A 10-second test sequence renders from Movie Render Queue at 1920 × 803
- [ ] Face is readable at 85 mm close shot
- [ ] Cloth and feather do not intersect the body in the walk and conch clips
- [ ] File size and triangle count recorded (body about 60k, whole character about 100k)
- [ ] Asset names follow `SK_`, `M_`, `T_`, `A_` prefixes

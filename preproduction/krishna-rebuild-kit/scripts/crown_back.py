"""Add relief to the back of the crown (headless Blender).

Usage:
  HEAD_SCALE_MULT=1.25 blender -b --python scripts/crown_back.py -- IN.blend OUT.blend

The approved crown has repousse ridges and studs at the back, and the TRELLIS back is smooth. This adds a
non-destructive Displace modifier with a ridged procedural texture, masked by a vertex group on the
back of the crown only (above the hairline, behind the centre line). The modifier sits before the armature,
so the relief follows the head in the pose tests. Shape keys are untouched.
"""

import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1 :]
in_blend, out_blend = argv[0], argv[1]
K = float(os.environ.get("HEAD_SCALE_MULT", "1.0"))
STRENGTH = float(os.environ.get("CROWN_RELIEF", "0.004"))

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
head = bpy.data.objects["KRISHNA_head"]
me = head.data
nv = len(me.vertices)
co = np.empty(nv * 3, dtype=np.float32)
(me.shape_keys.key_blocks[0].data if me.shape_keys else me.vertices).foreach_get("co", co)
co = co.reshape(nv, 3).astype(np.float64)
xs, ys, zs = co[:, 0], co[:, 1], co[:, 2]
z_top = zs.max()
cx = float(np.median(xs[zs > z_top - 0.2 * K]))
cy = float((ys.max() + ys.min()) * 0.5)
eye_z = z_top - 0.30 * K - 0.014 * K + 0.0883 * K
crown_back = (zs > eye_z + 0.06 * K) & (ys > cy) & (np.abs(xs - cx) < 0.11 * K)
print("CROWN back verts", int(crown_back.sum()), flush=True)

grp = head.vertex_groups.get("crown_back") or head.vertex_groups.new(name="crown_back")
idx = np.nonzero(crown_back)[0].tolist()
# Smooth falloff near boundary so the relief blends into the crown rim
weights = np.clip(1.0 - ((np.abs(xs[crown_back] - cx) / (0.11 * K)) ** 3), 0.2, 1.0)
for i_v, w in zip(idx, weights):
    grp.add([i_v], float(w), "REPLACE")

# 1. Repousse ridges relief
tex_relief = bpy.data.textures.get("KRISHNA_crown_relief") or bpy.data.textures.new("KRISHNA_crown_relief", type="VORONOI")
tex_relief.noise_scale = 0.015 * K
tex_relief.distance_metric = "DISTANCE"
tex_relief.contrast = 1.4
tex_relief.intensity = 1.1

disp_relief = head.modifiers.get("crown_relief") or head.modifiers.new("crown_relief", "DISPLACE")
disp_relief.texture = tex_relief
disp_relief.texture_coords = "LOCAL"
disp_relief.vertex_group = "crown_back"
disp_relief.strength = STRENGTH * 1.6 * K
disp_relief.mid_level = 0.5

# 2. Jewel studs & gem bead detail
tex_jewels = bpy.data.textures.get("KRISHNA_crown_jewels") or bpy.data.textures.new("KRISHNA_crown_jewels", type="VORONOI")
tex_jewels.noise_scale = 0.0065 * K
tex_jewels.distance_metric = "DISTANCE"
tex_jewels.contrast = 1.8
tex_jewels.intensity = 1.3

disp_jewels = head.modifiers.get("crown_jewels") or head.modifiers.new("crown_jewels", "DISPLACE")
disp_jewels.texture = tex_jewels
disp_jewels.texture_coords = "LOCAL"
disp_jewels.vertex_group = "crown_back"
disp_jewels.strength = 0.0035 * K
disp_jewels.mid_level = 0.45

# keep relief and jewels before the armature so they follow the pose
if "Armature" in head.modifiers:
    for mod_name in ("crown_relief", "crown_jewels"):
        while head.modifiers.find(mod_name) > head.modifiers.find("Armature"):
            bpy.context.view_layer.objects.active = head
            bpy.ops.object.modifier_move_up(modifier=mod_name)
print("MODIFIER order", [m.name for m in head.modifiers], flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("SAVED", out_blend, flush=True)

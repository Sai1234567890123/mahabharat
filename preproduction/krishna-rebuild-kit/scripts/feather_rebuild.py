"""Replace the flat feather card with a curved, two-sided peacock feather (headless Blender).

Usage:
  HEAD_SCALE_MULT=1.25 blender -b --python scripts/feather_rebuild.py -- IN.blend OUT.blend

The old feather is a single flat card. This builds a feather that curves away from the crown, with a
shaft, a shallow V cross-section (so it reads from the side), and a texture with a concentric eye
(blue centre, gold ring, green barbs). The new feather takes the old one's position and rides the head bone.
"""

import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1 :]
in_blend, out_blend = argv[0], argv[1]
K = float(os.environ.get("HEAD_SCALE_MULT", "1.0"))

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
old = bpy.data.objects.get("KRISHNA_feather")
quill = bpy.data.objects.get("KRISHNA_feather_quill")
head = bpy.data.objects["KRISHNA_head"]
rig = bpy.data.objects.get("KRISHNA_rig")
base = old.location.copy() if old else Vector((-0.07, 0.0, 1.66))
for o in (old, quill):
    if o is not None:
        bpy.data.objects.remove(o, do_unlink=True)

LEN, WID = 0.20, 0.050
SEG_U, SEG_V = 30, 12
verts, faces, uvs = [], [], []
for i in range(SEG_U + 1):
    t = i / SEG_U
    # spine curves backwards (toward the back of the head) and then up
    bend = 0.045 * t ** 2
    z = LEN * t
    width = WID * (math.sin(math.pi * min(1.0, 0.16 + 0.84 * t)) ** 0.8) * (min(1.0, t / 0.1))
    for j in range(SEG_V + 1):
        s = j / SEG_V * 2 - 1
        # shallow V: the two sides fold slightly, so the feather shows its face from the side
        fold = 0.012 * abs(s)
        verts.append((-bend + s * width * 0.5, fold, z))
        uvs.append((0.5 + s * 0.5, t))
for i in range(SEG_U):
    for j in range(SEG_V):
        a = i * (SEG_V + 1) + j
        faces.append((a, a + 1, a + SEG_V + 2, a + SEG_V + 1))
fm = bpy.data.meshes.new("KRISHNA_feather_mesh")
fm.from_pydata(verts, [], faces)
fm.update()
uv = fm.uv_layers.new(name="UVMap")
for poly in fm.polygons:
    for li in poly.loop_indices:
        uv.data[li].uv = uvs[fm.loops[li].vertex_index]
for p in fm.polygons:
    p.use_smooth = True

# eye texture, painted in numpy
FW, FH = 256, 512
yy, xx = np.mgrid[0:FH, 0:FW].astype(np.float32)
u, v = xx / (FW - 1), yy / (FH - 1)
ecx, ecy = 0.5, 0.74
d = np.sqrt(((u - ecx) * 1.4) ** 2 + (v - ecy) ** 2)
stops = [(0.00, (0.02, 0.05, 0.22)), (0.06, (0.05, 0.28, 0.80)), (0.12, (0.02, 0.52, 0.46)),
         (0.20, (0.82, 0.64, 0.14)), (0.34, (0.04, 0.42, 0.20)), (1.00, (0.02, 0.26, 0.12))]
rgb = np.zeros((FH, FW, 3), dtype=np.float32)
for k in range(3):
    rgb[..., k] = np.interp(d, [t for t, _ in stops], [c[k] for _, c in stops])
barb = 0.86 + 0.14 * np.sin(u * 150.0 + v * 4.0)
rgb *= barb[..., None]
fimg = bpy.data.images.new("T_Krishna_Feather2", FW, FH, alpha=False)
fimg.pixels.foreach_set(np.dstack([rgb, np.ones((FH, FW, 1), np.float32)]).reshape(-1))
fimg.pack()
fmat = bpy.data.materials.new("M_Krishna_Feather")
fmat.use_nodes = True
nt = fmat.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = fimg
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
fm.materials.append(fmat)

feather = bpy.data.objects.new("KRISHNA_feather", fm)
bpy.context.scene.collection.objects.link(feather)
feather.location = base
feather.rotation_euler = (0.0, math.radians(-14), math.radians(8))
feather.parent = None

# no quill: a curve cannot take head-bone weights, so it trailed off the head in the pose test
quill_obj = None

# feather and quill ride the head bone (weight 1.0), the same as the head in rig_skin.py
if rig is not None:
    for o in (feather,):
        for vg in list(o.vertex_groups):
            o.vertex_groups.remove(vg)
        g = o.vertex_groups.new(name="DEF-spine.006")
        g.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
        o.parent = rig
        m = o.modifiers.new("Armature", "ARMATURE")
        m.object = rig
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("FEATHER (no quill) rebuilt at", tuple(round(c, 3) for c in base), "verts", len(fm.vertices), flush=True)
print("SAVED", out_blend, flush=True)

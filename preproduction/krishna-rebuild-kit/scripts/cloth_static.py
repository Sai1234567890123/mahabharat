"""Posed static cloth: the dhoti and shawl follow the body's bones (headless Blender).

Usage:
  HEAD_SCALE_MULT=1.25 blender -b --python scripts/cloth_static.py -- IN.blend OUT.blend

Run on a rigged file that already has KRISHNA_cloth_dhoti and KRISHNA_cloth_shawl (cloth_build.py output).
Removes the Cloth and collision modifiers (no simulation), copies each cloth vertex's bone weights from the
nearest body vertex, and adds an armature modifier to the rig. The sheets then bend with the body in any pose.
"""

import os
import sys

import bpy
import numpy as np
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index("--") + 1 :]
in_blend, out_blend = argv[0], argv[1]

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
body = bpy.data.objects["KRISHNA_body"]
rig = bpy.data.objects["KRISHNA_rig"]
n = len(body.data.vertices)
co = np.empty(n * 3, dtype=np.float32)
body.data.vertices.foreach_get("co", co)
co = co.reshape(n, 3).astype(np.float64)
kd = KDTree(n)
for i in range(n):
    kd.insert(tuple(co[i]), i)
kd.balance()
names = {g.index: g.name for g in body.vertex_groups}

for cloth_name in ("KRISHNA_cloth_dhoti", "KRISHNA_cloth_shawl"):
    ob = bpy.data.objects[cloth_name]
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    for vg in list(ob.vertex_groups):
        if vg.name != "pin":
            ob.vertex_groups.remove(vg)
    for vg in body.vertex_groups:
        if vg.name.startswith("DEF-") and vg.name not in ob.vertex_groups:
            ob.vertex_groups.new(name=vg.name)
    grp_index = {g.name: g.index for g in ob.vertex_groups}
    for v in ob.data.vertices:
        p = ob.matrix_world @ v.co
        _, i, _ = kd.find((p.x, p.y, p.z))
        for g in body.data.vertices[i].groups:
            name = names[g.group]
            if g.weight > 0.01 and name in grp_index:
                ob.vertex_groups[grp_index[name]].add([v.index], g.weight, "REPLACE")
    ob.parent = rig
    am = ob.modifiers.new("Armature", "ARMATURE")
    am.object = rig
    print("CLOTH static", cloth_name, "weighted verts", len(ob.data.vertices), flush=True)

# drop the collision modifier from the body (no simulation any more)
for m in list(body.modifiers):
    if m.type == "COLLISION":
        body.modifiers.remove(m)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("SAVED", out_blend, flush=True)

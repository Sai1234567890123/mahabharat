"""Bake the dhoti and shawl cloth for 48 frames (headless Blender).

Usage:
  blender -b --python scripts/cloth_bake.py -- IN.blend OUT.blend
"""

import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1 :]
in_blend, out_blend = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
scn = bpy.context.scene
scn.frame_start = 1
scn.frame_end = 48
for name in ("KRISHNA_cloth_dhoti", "KRISHNA_cloth_shawl"):
    ob = bpy.data.objects[name]
    for m in ob.modifiers:
        if m.type == "CLOTH":
            m.point_cache.frame_start = 1
            m.point_cache.frame_end = 48
print("BAKE start", flush=True)
for f in range(1, 49):
    scn.frame_set(f)
    if f % 8 == 0:
        print("FRAME", f, flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("SAVED", out_blend, flush=True)

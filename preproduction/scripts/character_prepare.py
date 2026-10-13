"""Prepare a generated character mesh for rigging (headless Blender).

Usage:
  blender -b --python scripts/character_prepare.py -- IN.glb OUT.blend [HEIGHT_M]

Steps:
  1. Import the GLB into an empty scene.
  2. Report mesh statistics (vertices, faces, materials, bounding box).
  3. Apply transforms, scale to HEIGHT_M metres (default 1.75), put the origin at the feet.
  4. Enable Rigify, add a human metarig and fit it to the mesh bounding box.
  5. Save OUT.blend and print a short report.

The metarig fit is a starting point only. Joints must be moved to match the mesh before
generating the rig.
"""

import sys

import bpy
from mathutils import Vector

argv = sys.argv
argv = argv[argv.index("--") + 1 :] if "--" in argv else []
if len(argv) < 2:
    raise SystemExit("usage: blender -b --python character_prepare.py -- IN.glb OUT.blend [HEIGHT_M]")
src, dst = argv[0], argv[1]
height = float(argv[2]) if len(argv) > 2 else 1.75

bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not meshes:
    raise SystemExit("no mesh found in " + src)

report = ["IMPORTED %d mesh object(s)" % len(meshes)]
for o in meshes:
    me = o.data
    report.append(
        "  %s: %d verts, %d faces, %d materials, %d uv layers"
        % (o.name, len(me.vertices), len(me.polygons), len(me.materials), len(me.uv_layers))
    )

# Join to one body for scale and origin work (keeps materials).
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

lows = []
highs = []
for o in meshes:
    corners = [o.matrix_world @ Vector(c) for c in o.bound_box]
    lows.append(Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners))))
    highs.append(Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners))))
lo = Vector((min(v.x for v in lows), min(v.y for v in lows), min(v.z for v in lows)))
hi = Vector((max(v.x for v in highs), max(v.y for v in highs), max(v.z for v in highs)))
size = hi - lo
report.append("BOUNDING BOX before: %.3f x %.3f x %.3f" % (size.x, size.y, size.z))

# GLB is Y-up on export but Blender imports it Z-up, so height is Z.
scale = height / size.z if size.z > 0 else 1.0
for o in meshes:
    o.scale = o.scale * scale
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# Origin at the feet, centred on X/Y.
cx = (lo.x + hi.x) * 0.5 * scale
cy = (lo.y + hi.y) * 0.5 * scale
fz = lo.z * scale
for o in meshes:
    o.location.x -= cx
    o.location.y -= cy
    o.location.z -= fz
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

for o in meshes:
    corners = [o.matrix_world @ Vector(c) for c in o.bound_box]
report.append("SCALED to %.2f m tall (scale factor %.4f), origin at the feet" % (height, scale))

# Rigify metarig, fitted by bounding box.
try:
    bpy.ops.preferences.addon_enable(module="rigify")
    bpy.ops.object.armature_human_metarig_add()
    meta = bpy.context.active_object
    meta.name = "metarig"
    # Default human metarig is about 1.8 m tall; fit to the mesh height.
    meta.scale = (height / 1.8,) * 3
    meta.location = (0, 0, 0)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    report.append("RIGIFY metarig added: %d bones" % len(meta.data.bones))
except Exception as exc:  # noqa: BLE001
    report.append("RIGIFY NOT ADDED: %r" % (exc,))

bpy.ops.wm.save_as_mainfile(filepath=dst)
report.append("SAVED " + dst)
print("\n".join(["--- character_prepare report ---"] + report))

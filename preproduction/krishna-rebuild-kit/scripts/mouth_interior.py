"""Add teeth and tongue inside the mouth cavity (headless Blender).

Usage:
  HEAD_SCALE_MULT=1.25 blender -b --python scripts/mouth_interior.py -- IN.blend OUT.blend

Adds three objects behind the lip slit, positioned from the existing KRISHNA_mouth_cavity:
  KRISHNA_teeth_upper  fixed, hidden behind the upper lip when closed
  KRISHNA_teeth_lower  drops with KRISHNA_expr_jaw_open (its own 'open' shape key, driven by the head key)
  KRISHNA_tongue       sits on the lower jaw and drops with the jaw (same driver)
The three are returned for the head bone in rig_skin.py.
"""

import os
import sys

import bmesh
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1 :]
in_blend, out_blend = argv[0], argv[1]
K = float(os.environ.get("HEAD_SCALE_MULT", "1.0"))

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
head = bpy.data.objects["KRISHNA_head"]
cav = bpy.data.objects["KRISHNA_mouth_cavity"]
cx, cy, cz = cav.location.x, cav.location.y, cav.location.z


def make(name, kind, loc, scale, color, drop, roll=0.0):
    m = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    if kind == "sphere":
        bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=10, radius=1.0)
    else:
        bmesh.ops.create_cube(bm, size=2.0)
    bm.to_mesh(m)
    bm.free()
    ob = bpy.data.objects.new(name, m)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = Vector(loc)
    ob.scale = Vector(scale)
    ob.rotation_euler = (0, 0, roll)
    mat = bpy.data.materials.new(name + "_mat")
    mat.diffuse_color = (*color, 1)
    ob.data.materials.append(mat)
    ob.shape_key_add(name="Basis", from_mix=False)
    key = ob.shape_key_add(name="open", from_mix=False)
    import numpy as np
    co = np.empty(n * 3, dtype=np.float32)
    m.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    co2 = co.copy()
    if kind != "sphere":
        # Curve the teeth into an anatomical dental arch rather than a flat block
        co2[:, 1] += 0.35 * (co2[:, 0] ** 2)
    co2[:, 2] += drop / max(scale[2], 1e-6)  # drop is in metres; mesh z is in local units
    key.data.foreach_set("co", co2.reshape(-1))
    key.value = 0.0
    fc = key.driver_add("value")
    drv = fc.driver
    drv.type = "SCRIPTED"
    var = drv.variables.new()
    var.name = "jaw"
    var.type = "SINGLE_PROP"
    var.targets[0].id_type = "KEY"
    var.targets[0].id = head.data.shape_keys
    var.targets[0].data_path = 'key_blocks["KRISHNA_expr_jaw_open"].value'
    drv.expression = "jaw"
    return ob


teeth_up = make("KRISHNA_teeth_upper", "cube", (cx, cy - 0.002 * K, cz + 0.002 * K),
                (0.013 * K, 0.0015 * K, 0.0025 * K), (0.92, 0.90, 0.84), drop=0.0)
teeth_lo = make("KRISHNA_teeth_lower", "cube", (cx, cy - 0.002 * K, cz - 0.002 * K),
                (0.012 * K, 0.0015 * K, 0.0025 * K), (0.92, 0.90, 0.84), drop=-0.007 * K)
tongue = make("KRISHNA_tongue", "sphere", (cx, cy + 0.001 * K, cz - 0.004 * K),
              (0.011 * K, 0.006 * K, 0.0022 * K), (0.55, 0.16, 0.16), drop=-0.007 * K)
for ob in (teeth_up, teeth_lo, tongue):
    ob.parent = None
# teeth stay hidden while the mouth is closed: scale them in from the jaw value
for tooth in (teeth_up, teeth_lo):
  fc = tooth.driver_add("scale", 2)
  drv = fc.driver
  drv.type = "SCRIPTED"
  var = drv.variables.new()
  var.name = "jaw"
  var.type = "SINGLE_PROP"
  var.targets[0].id_type = "KEY"
  var.targets[0].id = head.data.shape_keys
  var.targets[0].data_path = 'key_blocks["KRISHNA_expr_jaw_open"].value'
  drv.expression = "max(jaw, 0.0001)"
print("MOUTH teeth + tongue added at z %.4f" % cz, flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("SAVED", out_blend, flush=True)

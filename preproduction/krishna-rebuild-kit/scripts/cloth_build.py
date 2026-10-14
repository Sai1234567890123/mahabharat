"""Build a dhoti and a shawl as separate cloth sheets draped over the Krishna body (headless Blender).

Usage:
  HEAD_SCALE_MULT=1.25 blender -b --python scripts/cloth_build.py -- IN.blend OUT.blend

Each sheet is a grid whose points sit a small offset off the body's own surface (nearest body vertex and
its normal), so it drapes on the body shape. Top edge is pinned (vertex group 'pin'). The body gets a
Collision modifier, and both sheets get a Cloth modifier. The cache is not baked here: bake it in the UI
or with `bpy.ops.ptcache.bake_all` for the test clip.
"""

import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index("--") + 1 :]
in_blend, out_blend = argv[0], argv[1]
K = float(os.environ.get("HEAD_SCALE_MULT", "1.0"))
OFFSET = float(os.environ.get("CLOTH_OFFSET", "0.012"))

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
body = bpy.data.objects["KRISHNA_body"]
me = body.data
n = len(me.vertices)
co = np.empty(n * 3, dtype=np.float32)
me.vertices.foreach_get("co", co)
co = co.reshape(n, 3).astype(np.float64)
nrm = np.empty(n * 3, dtype=np.float32)
me.vertices.foreach_get("normal", nrm)
nrm = nrm.reshape(n, 3).astype(np.float64)
kd = KDTree(n)
for i in range(n):
    kd.insert(tuple(co[i]), i)
kd.balance()
b_top = co[:, 2].max()
print("BODY top %.3f" % b_top, flush=True)


def drape(u_pts, v_pts, surf_fn):
    """Grid of points: u across, v down. surf_fn(x, z) -> (x, y, z, nx, ny, nz) on the body surface."""
    pts = []
    for v in v_pts:
        row = []
        for u in u_pts:
            x, z = u, v
            sx, sy, sz, nx, ny, nz = surf_fn(x, z)
            row.append(Vector((sx + nx * OFFSET, sy + ny * OFFSET, sz + nz * OFFSET)))
        pts.append(row)
    return pts


def surface(x, z):
    """Ray cast from in front of the body (along +Y) onto its surface at (x, z): hit point and normal."""
    ok, loc, nor, idx = body.ray_cast(Vector((x, -2.0, z)), Vector((0.0, 1.0, 0.0)))
    if ok:
        return loc.x, loc.y, loc.z, nor.x, nor.y, nor.z
    _, i, _ = kd.find((x, -0.1, z))
    p, nn = co[i], nrm[i]
    return p[0], p[1], p[2], nn[0], nn[1], nn[2]


def build_sheet(name, pts, color):
    bm = bmesh.new()
    rows = len(pts)
    cols = len(pts[0])
    vs = [[bm.verts.new(p) for p in row] for row in pts]
    for r in range(rows - 1):
        for c in range(cols - 1):
            bm.faces.new((vs[r][c], vs[r][c + 1], vs[r + 1][c + 1], vs[r + 1][c]))
    bm.normal_update()
    m = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(m)
    bm.free()
    ob = bpy.data.objects.new(name, m)
    bpy.context.scene.collection.objects.link(ob)
    pin = ob.vertex_groups.new(name="pin")
    top = [i for i in range(len(m.vertices)) if m.vertices[i].co.z > pts[0][0].z - 1e-6]
    pin.add(top, 1.0, "REPLACE")
    # side edges of the first few rows also pinned (waist and shoulder corners)
    edge = [i for i in range(len(m.vertices)) if m.vertices[i].co.z > pts[0][0].z - 0.06]
    pin.add(edge, 1.0, "REPLACE")
    mat = bpy.data.materials.new(name + "_mat")
    mat.diffuse_color = (*color, 1)
    ob.data.materials.append(mat)
    return ob


# dhoti: front panel from the waist to the ankles with defined cascading pleats
dhoti_u = np.linspace(-0.16, 0.16, 25)
dhoti_v = np.linspace(0.92, 0.10, 36)
pleat_pts = drape(dhoti_u, dhoti_v, surface)
for r, row in enumerate(pleat_pts):
    for c, p in enumerate(row):
        # deeper pleat fold deepening toward the hem as cloth falls free
        v_depth = 0.35 + 0.65 * np.clip((0.92 - p.z) / 0.75, 0.0, 1.0)
        # compound accordion / knife fold
        fold = 0.013 * np.sin(c * 2.2) + 0.005 * np.cos(c * 4.4)
        # center pleat stack forward prominence
        if abs(c - 12) <= 3:
            fold -= 0.007
        p.y += fold * v_depth
dhoti = build_sheet("KRISHNA_cloth_dhoti", pleat_pts, (0.86, 0.66, 0.12))

# shawl: over the left shoulder and down the outside of the arm with graceful diagonal drape folds
shawl_u = np.linspace(-0.30, -0.14, 11)
shawl_v = np.linspace(1.38, 0.72, 28)
shawl_pts = drape(shawl_u, shawl_v, surface)
for r, row in enumerate(shawl_pts):
    for c, p in enumerate(row):
        # diagonal cascading folds over shoulder
        drape_wave = 0.008 * np.sin(r * 0.75 + c * 1.3)
        p.y += drape_wave
        p.x += 0.003 * np.cos(r * 0.6)
shawl = build_sheet("KRISHNA_cloth_shawl", shawl_pts, (0.90, 0.72, 0.16))

# cloth modifiers: pinned top edge, collision with the body
for ob in (dhoti, shawl):
    cm = ob.modifiers.new("Cloth", "CLOTH")
    s = cm.settings
    s.quality = 8
    s.mass = 0.6
    s.tension_stiffness = 60.0
    s.compression_stiffness = 60.0
    s.shear_stiffness = 60.0
    s.bending_stiffness = 8.0
    s.vertex_group_mass = "pin"
    s.pin_stiffness = 1.0
    s.air_damping = 3.0
    cm.collision_settings.use_collision = True
    cm.collision_settings.distance_min = 0.012
    cm.collision_settings.collision_quality = 4
    cm.point_cache.frame_start = 1
    cm.point_cache.frame_end = 48
body.modifiers.new("Collision", "COLLISION")
scn = bpy.context.scene
scn.frame_start = 1
scn.frame_end = 48
print("CLOTH built: dhoti verts %d, shawl verts %d" % (len(dhoti.data.vertices), len(shawl.data.vertices)), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("SAVED", out_blend, flush=True)

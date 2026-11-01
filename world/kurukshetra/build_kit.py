"""Procedural Kurukshetra kit (Blender 5.2, bpy).

Builds every non-TRELLIS asset for the Kurukshetra world, following
world/ASSEMBLY_METHOD.md: metres, Z up, base at Z=0, centred, front -Y,
one asset per FBX named SM_<name>.fbx, only the shared material slots,
and a manifest.json per kit folder.

Run on the PC:   blender -b -P build_kit.py -- <out_dir>
Or headless:     python build_kit.py <out_dir>   (with the bpy wheel)
"""
import json
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Vector, noise

SEED = 1801
SLOTS = {
    "MAT_Marble": (0.94, 0.90, 0.82, 1),
    "MAT_Sandstone": (0.71, 0.54, 0.35, 1),   # battlefield dust #B48A5A
    "MAT_Gold": (0.85, 0.65, 0.20, 1),
    "MAT_Malachite": (0.18, 0.42, 0.25, 1),
    "MAT_Saffron": (0.91, 0.53, 0.12, 1),
    "MAT_Red": (0.48, 0.10, 0.07, 1),          # blood red #7A1A12
    "MAT_Wood": (0.36, 0.24, 0.14, 1),
    "MAT_Bronze": (0.55, 0.36, 0.18, 1),
    "MAT_Water": (0.20, 0.45, 0.50, 1),
}


# ---------------------------------------------------------------- helpers
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for name, col in SLOTS.items():
        m = bpy.data.materials.new(name)
        m.diffuse_color = col
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = col
            if name in ("MAT_Gold", "MAT_Bronze"):
                bsdf.inputs["Metallic"].default_value = 1.0
                bsdf.inputs["Roughness"].default_value = 0.3


def mat(obj, name):
    obj.data.materials.append(bpy.data.materials[name])
    return obj


def cyl(r, depth, loc, m, verts=16, r2=None, rot=(0, 0, 0)):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth, location=loc, rotation=rot)
    return mat(bpy.context.object, m)


def box(size, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return mat(o, m)


def sphere(r, loc, m, seg=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    return mat(bpy.context.object, m)


def flag(w, h, loc, m, wave=0.25, segs=12):
    """Cloth banner hanging from a pole at loc (top-left corner), rippled along X."""
    bm = bmesh.new()
    rows = 4
    verts = []
    for j in range(rows + 1):
        row = []
        for i in range(segs + 1):
            x = w * i / segs
            z = -h * j / rows
            y = wave * math.sin(i / segs * math.pi * 2.2) * (i / segs)
            row.append(bm.verts.new((loc[0] + x, loc[1] + y, loc[2] + z)))
        verts.append(row)
    for j in range(rows):
        for i in range(segs):
            bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
    me = bpy.data.meshes.new("flag")
    bm.to_mesh(me)
    o = bpy.data.objects.new("flag", me)
    bpy.context.collection.objects.link(o)
    sol = o.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = 0.02
    return mat(o, m)


def finish(name, out_dir, category, manifest):
    """Join everything in the scene into one mesh, ground it, export FBX."""
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    o = bpy.context.object
    o.name = f"SM_{name}"
    # base at Z=0, centred in XY
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    minz = min(v.z for v in bb)
    cx = (min(v.x for v in bb) + max(v.x for v in bb)) / 2
    cy = (min(v.y for v in bb) + max(v.y for v in bb)) / 2
    o.location -= Vector((cx, cy, minz))
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    dims = [round(d, 2) for d in o.dimensions]
    path = os.path.join(out_dir, f"SM_{name}.fbx")
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Y", axis_up="Z", mesh_smooth_type="FACE",
    )
    manifest.append({"name": name, "file": os.path.basename(path), "size_m": dims,
                     "category": category, "tris": sum(len(p.vertices) - 2 for p in o.data.polygons)})
    print(f"built {name} {dims}")


# ---------------------------------------------------------------- assets
def terrain(size_x=6000, size_y=4000, res=10):
    """Dusty plain, chariot ruts along the armies' axis, low ridge on the far edges."""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=size_x // res, y_subdivisions=size_y // res,
                                    size=1, location=(0, 0, 0))
    o = bpy.context.object
    o.scale = (size_x, size_y, 1)
    bpy.ops.object.transform_apply(scale=True)
    rng = random.Random(SEED)
    ruts = [rng.uniform(-1200, 1200) for _ in range(14)]
    for v in o.data.vertices:
        x, y = v.co.x, v.co.y
        h = 1.6 * noise.noise(Vector((x / 900, y / 900, 0.3)))
        h += 0.35 * noise.noise(Vector((x / 140, y / 140, 1.7)))
        # ridge: rises over the last 600 m on the far long edges
        edge = max(0.0, (abs(y) - (size_y / 2 - 600)) / 600)
        h += 35 * edge ** 2 * (0.7 + 0.3 * noise.noise(Vector((x / 400, 5.0, 0))))
        # ruts: shallow grooves running X (between the hosts' lines)
        for ry in ruts:
            d = abs(y - ry - 40 * math.sin(x / 700))
            if d < 2.5:
                h -= 0.18 * (1 - d / 2.5)
        v.co.z = h
    mat(o, "MAT_Sandstone")


def banner_pole(height, cloth, flag_w, flag_h, finial="MAT_Gold"):
    cyl(0.09, height, (0, 0, height / 2), "MAT_Wood", verts=10)
    cyl(0.18, 0.5, (0, 0, height + 0.25), finial, verts=10, r2=0.0)
    sphere(0.14, (0, 0, height - 0.05), finial, seg=10)
    cyl(0.03, flag_w + 0.2, (flag_w / 2, 0, height - 0.25), "MAT_Wood", verts=6, rot=(0, math.pi / 2, 0))
    flag(flag_w, flag_h, (0.05, 0, height - 0.25), cloth)
    # gold border strip at the bottom of the flag
    flag(flag_w, 0.18, (0.05, 0, height - 0.25 - flag_h), "MAT_Gold")


def tent(cloth, w=6.0, d=5.0, wall=2.2, roof=2.6):
    # walls: open box of thin slabs, front open
    box((w, 0.06, wall), (0, d / 2, wall / 2), cloth)
    box((0.06, d, wall), (-w / 2, 0, wall / 2), cloth)
    box((0.06, d, wall), (w / 2, 0, wall / 2), cloth)
    # pyramid roof
    bm = bmesh.new()
    ov = 1.08  # eaves overhang
    c = [bm.verts.new((sx * w / 2 * ov, sy * d / 2 * ov, wall - 0.15))
         for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    apex = bm.verts.new((0, 0, wall + roof))
    for i in range(4):
        bm.faces.new((c[i], c[(i + 1) % 4], apex))
    me = bpy.data.meshes.new("roof")
    bm.to_mesh(me)
    o = bpy.data.objects.new("roof", me)
    bpy.context.collection.objects.link(o)
    o.modifiers.new("thick", "SOLIDIFY").thickness = 0.04
    mat(o, cloth)
    # corner posts and finial
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(0.08, wall + 0.2, (sx * w / 2, sy * d / 2, (wall + 0.2) / 2), "MAT_Wood", verts=8)
    cyl(0.03, 1.2, (0, 0, wall + roof + 0.6), "MAT_Wood", verts=6)
    sphere(0.12, (0, 0, wall + roof + 0.15), "MAT_Gold")
    flag(0.8, 0.45, (0.02, 0, wall + roof + 1.15), cloth, wave=0.08, segs=6)
    # rolled-up front curtain
    cyl(0.12, w * 0.6, (0, -d / 2, wall - 0.1), cloth, verts=10, rot=(0, math.pi / 2, 0))


def palisade(length=10.0, h=3.2):
    n = int(length / 0.32)
    rng = random.Random(SEED + 3)
    for i in range(n):
        x = -length / 2 + 0.16 + i * 0.32
        hh = h * rng.uniform(0.9, 1.05)
        cyl(0.15, hh, (x, 0, hh / 2), "MAT_Wood", verts=7)
        cyl(0.15, 0.4, (x, 0, hh + 0.2), "MAT_Wood", verts=7, r2=0.0)
    for z in (0.8, h - 0.6):
        box((length, 0.12, 0.18), (0, -0.2, z), "MAT_Wood")


def weapon_rack():
    for sx in (-1.4, 1.4):
        box((0.12, 0.6, 2.0), (sx, 0, 1.0), "MAT_Wood")
    box((3.0, 0.14, 0.14), (0, 0, 1.9), "MAT_Wood")
    box((3.0, 0.5, 0.1), (0, 0, 0.35), "MAT_Wood")
    for i in range(9):
        x = -1.2 + i * 0.3
        cyl(0.025, 3.2, (x, 0.12, 1.6), "MAT_Wood", verts=6, rot=(0.12, 0, 0))
        cyl(0.05, 0.35, (x, 0.32, 3.15), "MAT_Bronze", verts=6, r2=0.0, rot=(0.12, 0, 0))


def spear_stack():
    """Spears leaned into a cone, the way camps store them."""
    for i in range(14):
        a = i / 14 * math.tau
        tilt = 0.28
        cx, cy = math.cos(a) * 0.45, math.sin(a) * 0.45
        o = cyl(0.025, 3.4, (cx, cy, 1.65), "MAT_Wood", verts=6)
        o.rotation_euler = (-math.sin(a) * tilt * -1, math.cos(a) * tilt * -1, 0)
        o2 = cyl(0.05, 0.35, (cx * 0.05, cy * 0.05, 3.45), "MAT_Bronze", verts=6, r2=0.0)


def shield_stack():
    for i in range(6):
        a = i / 6 * math.tau
        o = cyl(0.42, 0.06, (math.cos(a) * 0.55, math.sin(a) * 0.55, 0.45), "MAT_Bronze", verts=20,
                rot=(math.pi / 2 - 0.25, 0, a + math.pi / 2))
        sphere(0.08, (math.cos(a) * 0.62, math.sin(a) * 0.62, 0.45), "MAT_Gold", seg=8)


def soldier_proxy(cloth, armour, weapon):
    """Low-poly crowd stand-in until TRELLIS K04/K05 exist (about 1.75 m)."""
    cyl(0.17, 0.85, (0, 0, 0.43), cloth, verts=8, r2=0.13)          # legs + dhoti
    cyl(0.2, 0.55, (0, 0, 1.13), armour, verts=8, r2=0.17)          # torso armour
    sphere(0.11, (0, 0, 1.55), "MAT_Sandstone", seg=8)              # head
    cyl(0.12, 0.12, (0, 0, 1.67), armour, verts=8, r2=0.05)         # helmet
    if weapon == "spear":
        cyl(0.02, 2.6, (0.28, 0, 1.3), "MAT_Wood", verts=5)
        cyl(0.04, 0.25, (0.28, 0, 2.7), "MAT_Bronze", verts=5, r2=0.0)
        cyl(0.3, 0.05, (-0.25, -0.05, 1.1), "MAT_Bronze", verts=12, rot=(0, math.pi / 2, 0))
    else:  # bow
        bpy.ops.mesh.primitive_torus_add(major_radius=0.8, minor_radius=0.02, major_segments=16,
                                         minor_segments=4, location=(0.3, 0, 1.2), rotation=(math.pi / 2, 0, 0))
        o = bpy.context.object
        o.scale = (0.25, 1, 1)
        mat(o, "MAT_Wood")
        cyl(0.07, 0.6, (0, 0.18, 1.3), "MAT_Wood", verts=6)       # quiver


def fire_pit():
    for i in range(10):
        a = i / 10 * math.tau
        sphere(0.22, (math.cos(a) * 0.9, math.sin(a) * 0.9, 0.12), "MAT_Sandstone", seg=8)
    for i in range(5):
        a = i / 5 * math.tau
        cyl(0.07, 1.3, (math.cos(a) * 0.25, math.sin(a) * 0.25, 0.3), "MAT_Wood", verts=6,
            rot=(math.sin(a) * 1.2, math.cos(a) * 1.2, 0))


def grass_tuft():
    rng = random.Random(SEED + 7)
    for i in range(9):
        a = rng.uniform(0, math.tau)
        h = rng.uniform(0.25, 0.55)
        o = cyl(0.025, h, (math.cos(a) * 0.06, math.sin(a) * 0.06, h / 2), "MAT_Sandstone", verts=3, r2=0.0)
        o.rotation_euler = (rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 0)


def rock():
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.35, location=(0, 0, 0.12))
    o = bpy.context.object
    o.scale = (1.3, 0.9, 0.5)
    mat(o, "MAT_Sandstone")


ASSETS = [
    ("KRK_Terrain", "terrain", terrain),
    ("KRK_BannerPole_Saffron_Tall", "banner", lambda: banner_pole(9.0, "MAT_Saffron", 2.4, 3.2)),
    ("KRK_BannerPole_Saffron_Short", "banner", lambda: banner_pole(5.5, "MAT_Saffron", 1.4, 1.8)),
    ("KRK_BannerPole_Red_Tall", "banner", lambda: banner_pole(9.0, "MAT_Red", 2.4, 3.2, "MAT_Bronze")),
    ("KRK_BannerPole_Red_Short", "banner", lambda: banner_pole(5.5, "MAT_Red", 1.4, 1.8, "MAT_Bronze")),
    ("KRK_Tent_Saffron", "camp", lambda: tent("MAT_Saffron")),
    ("KRK_Tent_Red", "camp", lambda: tent("MAT_Red")),
    ("KRK_Tent_Marble", "camp", lambda: tent("MAT_Marble", w=4.5, d=4.0)),
    ("KRK_Palisade", "camp", palisade),
    ("KRK_WeaponRack", "camp", weapon_rack),
    ("KRK_SpearStack", "camp", spear_stack),
    ("KRK_ShieldStack", "camp", shield_stack),
    ("KRK_FirePit", "camp", fire_pit),
    ("KRK_SoldierProxy_Pandava", "crowd", lambda: soldier_proxy("MAT_Saffron", "MAT_Gold", "bow")),
    ("KRK_GrassTuft", "ground", grass_tuft),
    ("KRK_Rock", "ground", rock),
    ("KRK_SoldierProxy_Kaurava", "crowd", lambda: soldier_proxy("MAT_Red", "MAT_Bronze", "spear")),
]


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out_dir = os.path.abspath(argv[0] if argv else "kit_out")
    only = set(argv[1:])
    os.makedirs(out_dir, exist_ok=True)
    manifest = []
    for name, cat, fn in ASSETS:
        if only and name not in only:
            continue
        reset()
        random.seed(SEED)
        fn()
        finish(name, out_dir, cat, manifest)
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump({"kit": "Kurukshetra", "seed": SEED, "assets": manifest}, f, indent=2)
    print(f"wrote {len(manifest)} assets to {out_dir}")


if __name__ == "__main__":
    main()

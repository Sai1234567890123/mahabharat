"""Shared modelling helpers for the hero battle assets (Blender 5.2, bpy).

Everything is built as plain meshes with baked coordinates (objects stay at
identity), in metres, Z up, front facing -Y, so parts can be transformed and
joined without operator context. Materials are flat PBR slots (MAT_*), so the
look carries into Unreal through master materials with the same names.
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

PAL = {  # name: (base colour, metallic, roughness)
    "MAT_Gold": ((0.83, 0.61, 0.16), 1.0, 0.28),
    "MAT_GoldDark": ((0.55, 0.38, 0.10), 1.0, 0.40),
    "MAT_Silver": ((0.80, 0.80, 0.82), 1.0, 0.30),
    "MAT_Bronze": ((0.50, 0.30, 0.14), 1.0, 0.38),
    "MAT_Iron": ((0.16, 0.15, 0.15), 1.0, 0.50),
    "MAT_Black": ((0.03, 0.03, 0.035), 0.0, 0.35),
    "MAT_White": ((0.92, 0.90, 0.85), 0.0, 0.55),
    "MAT_Cream": ((0.86, 0.78, 0.62), 0.0, 0.75),
    "MAT_Red": ((0.50, 0.06, 0.05), 0.0, 0.60),
    "MAT_Crimson": ((0.33, 0.03, 0.04), 0.0, 0.45),
    "MAT_Saffron": ((0.90, 0.47, 0.08), 0.0, 0.70),
    "MAT_Green": ((0.05, 0.33, 0.14), 0.0, 0.65),
    "MAT_Wood": ((0.30, 0.19, 0.10), 0.0, 0.75),
    "MAT_Skin": ((0.50, 0.31, 0.19), 0.0, 0.60),
    "MAT_Hide": ((0.62, 0.50, 0.36), 0.0, 0.80),
    "MAT_Soot": ((0.06, 0.05, 0.045), 0.0, 0.95),
}


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for name, (srgb, metal, rough) in PAL.items():
        col = tuple(srgb_to_linear(c) for c in srgb)      # PAL is written in sRGB, shaders want linear
        m = bpy.data.materials.new(name)
        m.diffuse_color = (*col, 1)
        m.metallic = metal
        m.roughness = rough
        m.use_nodes = True
        b = m.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value = (*col, 1)
        b.inputs["Metallic"].default_value = metal
        b.inputs["Roughness"].default_value = rough


def M(name):
    return bpy.data.materials[name]


def obj_from_bm(bm, mat, name="part"):
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    me.materials.append(M(mat))
    return o


def xform(objs, mat):
    """Bake a matrix into mesh data (flips faces when mirrored)."""
    if not isinstance(objs, (list, tuple)):
        objs = [objs]
    flip = mat.determinant() < 0
    for o in objs:
        o.data.transform(mat)
        if flip:
            o.data.flip_normals()
    return objs


def T(x=0, y=0, z=0):
    return Matrix.Translation((x, y, z))


def R(angle, axis):
    return Matrix.Rotation(angle, 4, axis)


def S(x=1, y=None, z=None):
    y = x if y is None else y
    z = x if z is None else z
    return Matrix.Diagonal((x, y, z, 1))


def copy(objs, mat=None):
    out = []
    for o in (objs if isinstance(objs, (list, tuple)) else [objs]):
        c = o.copy()
        c.data = o.data.copy()
        bpy.context.collection.objects.link(c)
        out.append(c)
    if mat is not None:
        xform(out, mat)
    return out


def mirror_x(objs):
    return copy(objs, S(-1, 1, 1))


# ------------------------------------------------------------ primitives
def box(size, loc=(0, 0, 0), mat="MAT_Gold", bevel=0.0, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=2, affect="EDGES")
    o = obj_from_bm(bm, mat)
    m = T(*loc)
    if rot is not None:
        m = m @ rot
    xform(o, m)
    return o


def sphere(r, loc=(0, 0, 0), mat="MAT_Gold", scale=(1, 1, 1), seg=16, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r)
    o = obj_from_bm(bm, mat)
    m = T(*loc)
    if rot is not None:
        m = m @ rot
    xform(o, m @ S(*scale))
    return o


def lathe(profile, mat="MAT_Gold", segs=32, mat4=None):
    """Revolve (r, z) profile points around Z."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-6:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z))
                          for a in (i / segs * math.tau for i in range(segs))])
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        for i in range(segs):
            j = (i + 1) % segs
            if len(a) == 1:
                bm.faces.new((a[0], b[j], b[i]))
            elif len(b) == 1:
                bm.faces.new((a[i], a[j], b[0]))
            else:
                bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = obj_from_bm(bm, mat)
    if mat4 is not None:
        xform(o, mat4)
    return o


def catmull(pts, per=8, closed=False):
    pts = [Vector(p) for p in pts]
    n = len(pts)
    out = []
    rng = range(n if closed else n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[0] * 2 - pts[1]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[-1] * 2 - pts[-2]
        for k in range(per):
            t = k / per
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    if not closed:
        out.append(pts[-1])
    return out


def tube(points, radius=0.03, mat="MAT_Gold", segs=10, per=8, closed=False, smooth=True, flat=1.0):
    """Sweep a circle along a (smoothed) path. radius may be a list per control point.
    flat < 1 squashes the section along the path's side axis (for blades and ribbons)."""
    pts = [Vector(p) for p in points]
    radii = radius if isinstance(radius, (list, tuple)) else [radius] * len(pts)
    if smooth and len(pts) > 2:
        path = catmull(pts, per, closed)
        rr = [r for r in catmull([(r, 0, 0) for r in radii], per, closed)]
        rads = [max(1e-4, v.x) for v in rr]
    else:
        path, rads = pts, list(radii)
    n = len(path)
    bm = bmesh.new()
    rings = []
    tan0 = (path[1] - path[0]).normalized()
    ref = Vector((0, 0, 1)) if abs(tan0.z) < 0.9 else Vector((1, 0, 0))
    nrm = tan0.cross(ref).normalized()
    for i, p in enumerate(path):
        if closed:
            tan = (path[(i + 1) % n] - path[i - 1]).normalized()
        else:
            tan = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
        nrm = (nrm - tan * nrm.dot(tan))
        nrm = nrm.normalized() if nrm.length > 1e-6 else tan.orthogonal().normalized()
        bi = tan.cross(nrm)
        rings.append([bm.verts.new(p + (nrm * math.cos(a) * flat + bi * math.sin(a)) * rads[i])
                      for a in (k / segs * math.tau for k in range(segs))])
    for i in range(n if closed else n - 1):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(segs):
            j = (k + 1) % segs
            bm.faces.new((a[k], a[j], b[j], b[k]))
    if not closed:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return obj_from_bm(bm, mat)


def extrude_poly(outline, depth, mat="MAT_Gold", axis="X", bevel=0.0):
    """Extrude a 2D outline. axis X: outline is (y, z), slab centred on x=0."""
    bm = bmesh.new()
    vs = [bm.verts.new((-depth / 2, a, b)) for a, b in outline]
    f = bm.faces.new(vs)
    res = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(depth, 0, 0), verts=[v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=2, affect="EDGES")
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    o = obj_from_bm(bm, mat)
    if axis == "Y":
        xform(o, R(math.pi / 2, "Z"))
    elif axis == "Z":
        xform(o, R(math.pi / 2, "Y"))
    return o


def offset_outline(outline, d):
    """Shrink a roughly convex outline toward its centroid by about d."""
    cx = sum(p[0] for p in outline) / len(outline)
    cy = sum(p[1] for p in outline) / len(outline)
    out = []
    for x, y in outline:
        v = Vector((x - cx, y - cy))
        L = v.length
        out.append((cx + v.x * (L - d) / L, cy + v.y * (L - d) / L) if L > d else (cx, cy))
    return out


def scroll(center, r0=0.12, turns=1.6, thick=0.022, mat="MAT_Gold", plane="YZ", flip=1, start=0.0):
    """Spiral volute ornament."""
    pts = []
    n = int(turns * 14)
    for i in range(n + 1):
        t = i / n
        a = start + flip * t * turns * math.tau
        r = r0 * (1 - 0.85 * t)
        u, v = r * math.cos(a), r * math.sin(a)
        pts.append({"YZ": (0, u, v), "XZ": (u, 0, v), "XY": (u, v, 0)}[plane])
    rad = [thick * (1 - 0.5 * i / n) for i in range(n + 1)]
    o = tube(pts, rad, mat, segs=8, per=2)
    xform(o, T(*center))
    return o


def join(objs, name="part"):
    objs = [o for o in objs if o is not None]
    bm = bmesh.new()
    mats = []
    for o in objs:
        for m in o.data.materials:
            if m not in mats:
                mats.append(m)
    for o in objs:
        tmp = bmesh.new()
        tmp.from_mesh(o.data)
        remap = [mats.index(m) for m in o.data.materials]
        for f in tmp.faces:
            f.material_index = remap[f.material_index] if remap else 0
        me = bpy.data.meshes.new("tmp")
        tmp.to_mesh(me)
        tmp.free()
        bm.from_mesh(me)
        # from_mesh appends; material indices are kept as set above
        bpy.data.meshes.remove(me)
    out_me = bpy.data.meshes.new(name)
    bm.to_mesh(out_me)
    bm.free()
    for m in mats:
        out_me.materials.append(m)
    for o in objs:
        me = o.data
        bpy.data.objects.remove(o)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    out = bpy.data.objects.new(name, out_me)
    bpy.context.collection.objects.link(out)
    return out


def apply_modifiers(o):
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    old = o.data
    o.modifiers.clear()
    o.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return o


def blob(parts, voxel=0.02, smooth=6, mat="MAT_Gold", decimate=None):
    """Fuse overlapping ellipsoids / capsules into one sculpted form (voxel remesh + smooth).
    parts: ("s", centre, radii) | ("c", p0, p1, r0, r1) | ("t", points, radii)"""
    objs = []
    for p in parts:
        if p[0] == "s":
            rad = p[2] if isinstance(p[2], (tuple, list)) else (p[2],) * 3
            rot = p[3] if len(p) > 3 else None
            objs.append(sphere(1.0, p[1], mat, scale=rad, seg=20, rot=rot))
        elif p[0] == "c":
            objs.append(tube([p[1], p[2]], [p[3], p[4]], mat, segs=14, smooth=False))
            objs.append(sphere(p[3], p[1], mat, seg=14))
            objs.append(sphere(p[4], p[2], mat, seg=14))
        elif p[0] == "t":
            objs.append(tube(p[1], p[2], mat, segs=12, per=6))
            objs.append(sphere(p[2][0], p[1][0], mat, seg=12))
            objs.append(sphere(p[2][-1], p[1][-1], mat, seg=12))
    o = join(objs, "blob")
    rm = o.modifiers.new("remesh", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = voxel
    rm.use_smooth_shade = True
    if smooth:
        sm = o.modifiers.new("smooth", "SMOOTH")
        sm.iterations = smooth
        sm.factor = 0.6
    if decimate:
        dc = o.modifiers.new("dec", "DECIMATE")
        dc.ratio = decimate
    apply_modifiers(o)
    o.data.materials.clear()
    o.data.materials.append(M(mat))
    return o


def decimated(o, ratio):
    dc = o.modifiers.new("dec", "DECIMATE")
    dc.ratio = ratio
    return apply_modifiers(o)


def tri_count(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def ground_and_centre(o, centre_xy=True):
    xs = [v.co for v in o.data.vertices]
    minz = min(v.z for v in xs)
    cx = (min(v.x for v in xs) + max(v.x for v in xs)) / 2 if centre_xy else 0
    cy = (min(v.y for v in xs) + max(v.y for v in xs)) / 2 if centre_xy else 0
    xform(o, T(-cx, -cy, -minz))
    return o


def export(o, name, out_dir, category, manifest, smooth_angle=40):
    o.name = f"SM_{name}"
    o.data.name = f"SM_{name}"
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth_angle))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"SM_{name}.fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"},
                             apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                             axis_forward="-Y", axis_up="Z", mesh_smooth_type="FACE")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, f"SM_{name}.blend"))
    dims = [round(d, 2) for d in o.dimensions]
    manifest.append({"name": name, "file": f"SM_{name}.fbx", "size_m": dims, "category": category,
                     "tris": tri_count(o), "materials": [m.name for m in o.data.materials]})
    print(f"BUILT {name} size={dims} tris={tri_count(o)}")

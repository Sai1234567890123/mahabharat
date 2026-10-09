"""Blender blockout builder for the pilot.

Builds the Kurukshetra layout from data/shots.json for one shot and renders
three passes with Cycles:

  <out>/<SHOT>_color.png   toon-shaded color, transparent sky (RGBA)
  <out>/<SHOT>_depth.png   16-bit log depth, 0 = near, 1 = far
  <out>/<SHOT>_id.png      flat object-ID colors (for line art and masks)
  <out>/<SHOT>_meta.json   camera, horizon line, sun and named anchors in pixels

Run with the bpy module (pip install bpy) or inside Blender:
  python blockout.py --shots ../data/shots.json --shot SH050 --out ../art/render --width 1920
  blender -b -P blockout.py -- --shot SH050 ...
  python blockout.py --lineup --out ../art/render       (character lineup)
  python blockout.py --shot SH050 --save-blend x.blend  (keep the scene)

Everything is procedural proxy geometry (metaballs and simple meshes). The
shading is a 3-value toon ramp with a rim light, built from emission so the
render is fast on a CPU. These renders are the layout and the control passes
for the AI paint-over stage, not final art.
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Vector, Quaternion, Matrix
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- utilities


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def s2l(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin(h):
    r, g, b = hex2rgb(h) if isinstance(h, str) else h
    return (s2l(r), s2l(g), s2l(b), 1.0)


def mix(a, b, t):
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(3))


def scale(a, k):
    return tuple(min(1.0, x * k) for x in a)


def norm(v):
    return Vector(v).normalized()


def reset():
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.metaballs,
                 bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for d in list(coll):
            coll.remove(d)


SCN = None
ACT = None
MAT_CACHE = {}
ID_COUNTER = [0]


def new_id_color():
    """Distinct flat colors for the ID pass (golden-ratio hue walk)."""
    ID_COUNTER[0] += 1
    h = (ID_COUNTER[0] * 0.61803398875) % 1.0
    s, v = 0.6 + 0.4 * ((ID_COUNTER[0] * 7) % 3) / 2, 0.55 + 0.45 * ((ID_COUNTER[0] * 5) % 4) / 3
    i = int(h * 6)
    f = h * 6 - i
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    r, g, b = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i % 6]
    return (r, g, b, 1.0)


def link(obj, parent=None, idcol=None):
    SCN.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    obj.color = idcol or (parent.color if parent is not None else new_id_color())
    return obj


# ---------------------------------------------------------------- materials


def toon(name, base_hex, rim_hex=None, special=None):
    """3-value toon ramp + rim, as emission. Colors shift with the act."""
    key = (name, base_hex, rim_hex, special)
    if key in MAT_CACHE:
        return MAT_CACHE[key]
    A = ACT
    base = hex2rgb(base_hex)
    keyc, shad = hex2rgb(A["key"]), hex2rgb(A["shadow"])
    light = scale(mix(base, keyc, 0.25), 1.12)
    shadow = mix(scale(base, 0.5), shad, 0.45)
    if special == "divine":
        light, base, shadow = (1, 0.98, 0.9), (1, 0.9, 0.62), (0.95, 0.66, 0.35)
    rim = hex2rgb(rim_hex or A["rim"])

    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    geo = N.new("ShaderNodeNewGeometry")
    tc = N.new("ShaderNodeTexCoord")
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 4.0
    L.new(tc.outputs["Object"], noise.inputs["Vector"])

    dot = N.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = norm(A["key_dir"])
    L.new(geo.outputs["Normal"], dot.inputs[0])
    sub = N.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = 0.5
    L.new(noise.outputs["Fac"], sub.inputs[0])
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 0.45  # painted breakup of the terminator
    L.new(sub.outputs[0], mul.inputs[0])
    add = N.new("ShaderNodeMath")
    add.operation = "ADD"
    L.new(dot.outputs["Value"], add.inputs[0])
    L.new(mul.outputs[0], add.inputs[1])
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["From Max"].default_value = 1.0
    L.new(add.outputs[0], mr.inputs["Value"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, lin(shadow)
    els[1].position, els[1].color = 0.47, lin(base)
    e = els.new(0.70)
    e.color = lin(light)
    L.new(mr.outputs[0], ramp.inputs[0])
    em = N.new("ShaderNodeEmission")
    L.new(ramp.outputs["Color"], em.inputs["Color"])

    # rim: facing edge AND turned toward the rim light
    lw = N.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    gt = N.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.62
    L.new(lw.outputs["Facing"], gt.inputs[0])
    rdot = N.new("ShaderNodeVectorMath")
    rdot.operation = "DOT_PRODUCT"
    rdot.inputs[1].default_value = norm(A["rim_dir"])
    L.new(geo.outputs["Normal"], rdot.inputs[0])
    gt2 = N.new("ShaderNodeMath")
    gt2.operation = "GREATER_THAN"
    gt2.inputs[1].default_value = 0.1
    L.new(rdot.outputs["Value"], gt2.inputs[0])
    both = N.new("ShaderNodeMath")
    both.operation = "MULTIPLY"
    L.new(gt.outputs[0], both.inputs[0])
    L.new(gt2.outputs[0], both.inputs[1])
    emr = N.new("ShaderNodeEmission")
    emr.inputs["Color"].default_value = lin(rim)
    L.new(both.outputs[0], emr.inputs["Strength"])
    addsh = N.new("ShaderNodeAddShader")
    L.new(em.outputs[0], addsh.inputs[0])
    L.new(emr.outputs[0], addsh.inputs[1])
    L.new(addsh.outputs[0], out.inputs["Surface"])
    MAT_CACHE[key] = m
    return m


def flat(name, hex_):
    key = ("flat", name, hex_)
    if key in MAT_CACHE:
        return MAT_CACHE[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N = m.node_tree.nodes
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = lin(hex_)
    m.node_tree.links.new(em.outputs[0], out.inputs["Surface"])
    MAT_CACHE[key] = m
    return m


def ground_mat():
    A = ACT
    g = hex2rgb(A["ground"])
    m = bpy.data.materials.new("ground")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    tc = N.new("ShaderNodeTexCoord")
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.05
    noise.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], noise.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, lin(mix(scale(g, 0.86), hex2rgb(A["shadow"]), 0.12))
    els[1].position, els[1].color = 0.45, lin(g)
    e = els.new(0.64)
    e.color = lin(scale(mix(g, hex2rgb(A["key"]), 0.2), 1.05))
    L.new(noise.outputs["Fac"], ramp.inputs[0])
    em = N.new("ShaderNodeEmission")
    L.new(ramp.outputs["Color"], em.inputs["Color"])
    L.new(em.outputs[0], out.inputs["Surface"])
    return m


# ---------------------------------------------------------------- geometry


def empty(name, loc=(0, 0, 0), rot_z=0.0, parent=None):
    o = bpy.data.objects.new(name, None)
    o.location = loc
    o.rotation_euler = (0, 0, rot_z)
    return link(o, parent)


def anchor(name, loc, parent):
    o = bpy.data.objects.new("A:" + name, None)
    o.location = loc
    SCN.collection.objects.link(o)
    o.parent = parent
    return o


def mesh_from_bm(name, bm, mat, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scl=(1, 1, 1), idcol=None, smooth=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    o.location, o.rotation_euler, o.scale = loc, rot, scl
    me.materials.append(mat)
    return link(o, parent, idcol)


def cube(name, mat, loc, size, parent=None, rot=(0, 0, 0), idcol=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    return mesh_from_bm(name, bm, mat, parent, loc, rot, size, idcol)


def sphere(name, mat, loc, r, parent=None, scl=(1, 1, 1), seg=16, idcol=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r)
    return mesh_from_bm(name, bm, mat, parent, loc, (0, 0, 0), scl, idcol, smooth=True)


def cone(name, mat, loc, r1, r2, depth, parent=None, rot=(0, 0, 0), seg=16, idcol=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=depth)
    return mesh_from_bm(name, bm, mat, parent, loc, rot, (1, 1, 1), idcol, smooth=True)


def rod(name, mat, p0, p1, r, parent=None, seg=8, idcol=None):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=d.length)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return mesh_from_bm(name, bm, mat, parent, (p0 + p1) / 2, q.to_euler(), (1, 1, 1), idcol, smooth=True)


def torus(name, mat, loc, R, r, parent=None, rot=(0, 0, 0), seg=32, sseg=8, idcol=None):
    bm = bmesh.new()
    ring = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        row = []
        for j in range(sseg):
            b = 2 * math.pi * j / sseg
            x = (R + r * math.cos(b)) * math.cos(a)
            y = (R + r * math.cos(b)) * math.sin(a)
            z = r * math.sin(b)
            row.append(bm.verts.new((x, y, z)))
        ring.append(row)
    for i in range(seg):
        for j in range(sseg):
            bm.faces.new((ring[i][j], ring[(i + 1) % seg][j], ring[(i + 1) % seg][(j + 1) % sseg], ring[i][(j + 1) % sseg]))
    return mesh_from_bm(name, bm, mat, parent, loc, rot, (1, 1, 1), idcol, smooth=True)


def flag(name, mat, w, h, parent, loc, wave=0.25, phase=0.0, idcol=None):
    """A banner as a rippled grid, attached along its left edge at loc."""
    bm = bmesh.new()
    nx, nz = 14, 6
    vs = []
    for i in range(nx + 1):
        col = []
        for k in range(nz + 1):
            x = w * i / nx
            z = -h * k / nz
            y = wave * (i / nx) * math.sin(i / nx * 2.6 * math.pi + phase + k * 0.3)
            col.append(bm.verts.new((x, y, z)))
        vs.append(col)
    for i in range(nx):
        for k in range(nz):
            bm.faces.new((vs[i][k], vs[i + 1][k], vs[i + 1][k + 1], vs[i][k + 1]))
    return mesh_from_bm(name, bm, mat, parent, loc, (0, 0, 0), (1, 1, 1), idcol)


def bow_curve(name, mat, height, parent, loc, rot=(0, 0, 0), bend=0.16, idcol=None):
    """Recurve bow in the local XZ plane, centred at loc, with a string."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.022
    cu.bevel_resolution = 2
    sp = cu.splines.new("POLY")
    n = 24
    sp.points.add(n - 1)
    for i in range(n):
        t = i / (n - 1) * 2 - 1
        z = t * height / 2
        x = -bend * (1 - t * t) + 0.05 * (abs(t) ** 6)  # recurve tips
        sp.points[i].co = (x, 0, z, 1)
    st = cu.splines.new("POLY")
    st.points.add(1)
    st.points[0].co = (0.05, 0, -height / 2, 1)
    st.points[1].co = (0.05, 0, height / 2, 1)
    cu.materials.append(mat)
    o = bpy.data.objects.new(name, cu)
    o.location, o.rotation_euler = loc, rot
    return link(o, parent, idcol)


# ---------------------------------------------------------------- metaballs

THRESH = 0.6
VIS = 0.474  # visible radius / element radius for an isolated ball at THRESH


def metaball(name, mat, parent, res=0.035, idcol=None):
    mb = bpy.data.metaballs.new(name)
    mb.resolution = res * 2
    mb.render_resolution = res
    mb.threshold = THRESH
    mb.materials.append(mat)
    o = bpy.data.objects.new(name, mb)
    return link(o, parent, idcol)


def ball(mbo, p, r, s=(1, 1, 1)):
    e = mbo.data.elements.new()
    e.co = p
    e.radius = r / VIS
    if s != (1, 1, 1):
        e.type = "ELLIPSOID"
        e.size_x, e.size_y, e.size_z = s
    return e


def capsule(mbo, p0, p1, r):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    e = mbo.data.elements.new()
    e.type = "CAPSULE"
    e.co = (p0 + p1) / 2
    e.radius = r / VIS
    e.size_x = d.length / 2
    e.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized())
    return e


# ---------------------------------------------------------------- characters

POSES = {}


def pose(name):
    def deco(f):
        POSES[name] = f
        return f
    return deco


def base_skeleton(H, w):
    """Joint positions (local, figure faces +Y, origin at feet)."""
    sx = 0.13 * H * w
    j = dict(
        head=(0, 0, 0.915 * H), neck=(0, 0, 0.84 * H), chest=(0, 0, 0.72 * H), belly=(0, 0, 0.6 * H),
        pelvis=(0, 0, 0.51 * H),
        sh_l=(-sx, 0, 0.8 * H), sh_r=(sx, 0, 0.8 * H),
        el_l=(-sx * 1.12, 0, 0.635 * H), el_r=(sx * 1.12, 0, 0.635 * H),
        ha_l=(-sx * 1.18, 0.02 * H, 0.48 * H), ha_r=(sx * 1.18, 0.02 * H, 0.48 * H),
        hip_l=(-0.06 * H * w, 0, 0.5 * H), hip_r=(0.06 * H * w, 0, 0.5 * H),
        kn_l=(-0.065 * H * w, 0.012 * H, 0.27 * H), kn_r=(0.065 * H * w, 0.012 * H, 0.27 * H),
        ft_l=(-0.075 * H * w, 0.0, 0.03 * H), ft_r=(0.075 * H * w, 0.0, 0.03 * H),
        extra_arms=[],
    )
    return j


@pose("stand")
def _p_stand(j, H, w):
    return j


@pose("reins")
def _p_reins(j, H, w):
    j["el_l"], j["el_r"] = (-0.14 * H, 0.07 * H, 0.63 * H), (0.14 * H, 0.07 * H, 0.63 * H)
    j["ha_l"], j["ha_r"] = (-0.08 * H, 0.22 * H, 0.6 * H), (0.08 * H, 0.22 * H, 0.6 * H)
    return j


@pose("turn")
def _p_turn(j, H, w):
    _p_reins(j, H, w)
    j["head"] = (0.01 * H, 0.0, 0.915 * H)
    return j


@pose("conch")
def _p_conch(j, H, w):
    j["head"] = (0, -0.008 * H, 0.92 * H)
    j["el_l"], j["el_r"] = (-0.17 * H, 0.07 * H, 0.79 * H), (0.17 * H, 0.07 * H, 0.79 * H)
    j["ha_l"], j["ha_r"] = (-0.035 * H, 0.1 * H, 0.9 * H), (0.035 * H, 0.1 * H, 0.9 * H)
    j["conch"] = ((0, 0.075 * H, 0.905 * H), (0, 0.24 * H, 0.97 * H))
    return j


@pose("conch_lift")
def _p_conch_lift(j, H, w):
    j["el_r"] = (0.2 * H, 0.03 * H, 0.75 * H)
    j["ha_r"] = (0.14 * H, 0.08 * H, 0.86 * H)
    j["conch"] = ((0.11 * H, 0.08 * H, 0.84 * H), (0.17 * H, 0.1 * H, 0.98 * H))
    return j


@pose("roar")
def _p_roar(j, H, w):
    j["head"] = (0, -0.03 * H, 0.91 * H)
    j["el_r"] = (0.2 * H, 0.0, 0.92 * H)
    j["ha_r"] = (0.16 * H, 0.03 * H, 1.06 * H)
    j["el_l"] = (-0.26 * H, 0.03 * H, 0.72 * H)
    j["ha_l"] = (-0.38 * H, 0.06 * H, 0.66 * H)
    j["conch"] = ((0.14 * H, 0.03 * H, 1.04 * H), (0.16 * H, 0.07 * H, 1.2 * H))
    return j


@pose("mace")
def _p_mace(j, H, w):
    j["el_r"] = (0.22 * H, 0.02 * H, 0.7 * H)
    j["ha_r"] = (0.17 * H, 0.04 * H, 0.84 * H)
    j["mace"] = ((0.17 * H, 0.04 * H, 0.84 * H), (0.1 * H, -0.12 * H, 1.08 * H))
    return j


@pose("bow_rest")
def _p_bow_rest(j, H, w):
    j["el_l"] = (-0.2 * H, 0.04 * H, 0.64 * H)
    j["ha_l"] = (-0.24 * H, 0.08 * H, 0.52 * H)
    j["bow"] = dict(center=(-0.24 * H, 0.08 * H, 0.55 * H), rot=(0, 0, 0.35), height=1.15 * H)
    return j


@pose("bow_raise")
def _p_bow_raise(j, H, w):
    j["el_l"] = (-0.2 * H, 0.04 * H, 0.95 * H)
    j["ha_l"] = (-0.18 * H, 0.08 * H, 1.12 * H)
    j["el_r"] = (0.2 * H, 0.04 * H, 0.66 * H)
    j["ha_r"] = (0.23 * H, 0.08 * H, 0.55 * H)
    j["bow"] = dict(center=(-0.18 * H, 0.08 * H, 1.12 * H), rot=(0, 0.35, math.pi / 2), height=1.15 * H)
    return j


@pose("slump")
def _p_slump(j, H, w):
    dz = -0.32 * H
    for k in ("head", "neck", "chest", "belly", "pelvis", "sh_l", "sh_r", "hip_l", "hip_r"):
        x, y, z = j[k]
        j[k] = (x, y, z + dz)
    j["head"] = (0, 0.12 * H, 0.55 * H)
    j["neck"] = (0, 0.08 * H, 0.5 * H)
    j["chest"] = (0, 0.05 * H, 0.42 * H)
    j["sh_l"], j["sh_r"] = (-0.13 * H, 0.06 * H, 0.47 * H), (0.13 * H, 0.06 * H, 0.47 * H)
    j["el_l"], j["el_r"] = (-0.17 * H, 0.14 * H, 0.32 * H), (0.17 * H, 0.14 * H, 0.32 * H)
    j["ha_l"], j["ha_r"] = (-0.2 * H, 0.22 * H, 0.2 * H), (0.12 * H, 0.22 * H, 0.18 * H)
    j["kn_l"], j["kn_r"] = (-0.16 * H, 0.18 * H, 0.1 * H), (0.16 * H, 0.18 * H, 0.1 * H)
    j["ft_l"], j["ft_r"] = (0.04 * H, 0.2 * H, 0.03 * H), (-0.04 * H, 0.24 * H, 0.03 * H)
    return j


@pose("universal")
def _p_universal(j, H, w):
    _p_stand(j, H, w)
    j["el_l"], j["el_r"] = (-0.2 * H, 0.03 * H, 0.75 * H), (0.2 * H, 0.03 * H, 0.75 * H)
    j["ha_l"], j["ha_r"] = (-0.28 * H, 0.06 * H, 0.88 * H), (0.28 * H, 0.06 * H, 0.88 * H)
    arms = []
    for side in (-1, 1):
        for k in range(5):
            a = math.radians(-35 + k * 32)
            sh = (side * 0.12 * H, -0.03 * H, 0.79 * H)
            hand = (side * (0.12 * H + 0.36 * H * math.cos(a)), -0.04 * H - 0.01 * k * H, 0.79 * H + 0.36 * H * math.sin(a))
            el = ((sh[0] + hand[0]) / 2 + side * 0.03 * H, (sh[1] + hand[1]) / 2, (sh[2] + hand[2]) / 2 - 0.03 * H)
            arms.append((sh, el, hand))
    j["extra_arms"] = arms
    j["mace"] = ((-0.28 * H, 0.06 * H, 0.88 * H), (-0.3 * H, 0.08 * H, 1.15 * H))
    j["discus"] = (0.3 * H, 0.06 * H, 0.98 * H)
    return j


def humanoid(key, C, parent, loc, rot_z=0.0, H=1.9, w=1.0, pose_name="stand", res=0.03,
             costume="dhoti", hair="#14100E", beard=False, crown=None, feather=False, parasol=False,
             special=None, hair_long=False):
    """A stylized proxy figure: skin, costume and hair as separate metaball families."""
    root = empty(f"{key}_root", loc, rot_z, parent)
    root.color = new_id_color()
    j = POSES[pose_name](base_skeleton(H, w), H, w)
    rim = C.get("energy")
    skin_m = toon(f"{key}_skin", C["skin"], rim, special)
    cos_m = toon(f"{key}_costume", C["costume"], rim, special)
    acc_m = toon(f"{key}_accent", C["accent"], rim, special)
    gold = toon("gold", "#D9A441", rim, special)
    hair_m = toon(f"{key}_hair", hair, rim, special)

    body = metaball(f"{key}Skin", skin_m, root, res)
    r_head = 0.056 * H
    hx, hy, hz = j["head"]
    ball(body, j["head"], r_head, (0.9, 1.0, 1.15))
    ball(body, (hx, hy + 0.045 * H, hz - 0.005 * H), 0.012 * H, (0.7, 1.0, 1.2))  # nose
    capsule(body, j["neck"], (hx, hy, hz - 0.03 * H), 0.024 * H)
    ball(body, j["chest"], 0.082 * H * w, (1.32, 0.74, 1.0))
    ball(body, j["belly"], 0.066 * H * w, (1.0, 0.75, 1.0))
    ball(body, j["pelvis"], 0.07 * H * w, (1.1, 0.8, 0.9))
    for s_ in ("l", "r"):
        ball(body, j[f"sh_{s_}"], 0.034 * H * w)
        capsule(body, j[f"sh_{s_}"], j[f"el_{s_}"], 0.025 * H * w)
        capsule(body, j[f"el_{s_}"], j[f"ha_{s_}"], 0.021 * H * w)
        ball(body, j[f"ha_{s_}"], 0.023 * H)
        capsule(body, j[f"hip_{s_}"], j[f"kn_{s_}"], 0.034 * H * w)
        capsule(body, j[f"kn_{s_}"], j[f"ft_{s_}"], 0.026 * H * w)
        fx_, fy_, fz_ = j[f"ft_{s_}"]
        ball(body, (fx_, fy_ + 0.02 * H, fz_), 0.024 * H, (0.9, 1.7, 0.6))
    for sh, el, ha in j["extra_arms"]:
        capsule(body, sh, el, 0.025 * H)
        capsule(body, el, ha, 0.021 * H)
        ball(body, ha, 0.024 * H)

    cos = metaball(f"{key}Costume", cos_m, root, res)
    ball(cos, j["pelvis"], 0.08 * H * w, (1.18, 0.92, 0.95))
    for s_ in ("l", "r"):
        flare = 0.044 if costume == "dhoti" else 0.04
        capsule(cos, j[f"hip_{s_}"], j[f"kn_{s_}"], flare * H * w)
    if costume == "dhoti":
        px, py, pz = j["pelvis"]
        kx, ky, kz = j["kn_l"]
        capsule(cos, (px, py + 0.04 * H, pz - 0.02 * H), (px, ky + 0.05 * H, kz + 0.02 * H), 0.026 * H)
    if costume in ("armor", "armor_heavy"):
        ball(cos, j["chest"], 0.088 * H * w, (1.32, 0.8, 1.02))
        ball(cos, j["belly"], 0.07 * H * w, (1.05, 0.82, 0.9))
        for s_ in ("l", "r"):
            ball(cos, j[f"sh_{s_}"], (0.05 if costume == "armor_heavy" else 0.04) * H * w, (1.2, 1.0, 0.8))
    if costume == "upper_cloth":
        capsule(cos, j["sh_l"], (j["pelvis"][0] + 0.07 * H, j["pelvis"][1] + 0.03 * H, j["pelvis"][2] + 0.06 * H), 0.03 * H)
    # waist sash in the accent color
    sash = metaball(f"{key}Sash", acc_m, root, res)
    bx, by, bz = j["pelvis"]
    ball(sash, (bx, by, bz + 0.04 * H), 0.075 * H * w, (1.22, 0.95, 0.35))

    hb = metaball(f"{key}Hair", hair_m, root, res)
    ball(hb, (hx, hy - 0.022 * H, hz + 0.018 * H), r_head * 1.0, (1.0, 0.92, 1.0))
    ball(hb, (hx, hy - 0.05 * H, hz - 0.045 * H), r_head * 0.82, (1.15, 0.8, 1.4))
    if hair_long:
        for k in range(3):
            ball(hb, (hx + (k - 1) * 0.04 * H, hy - 0.055 * H, hz - 0.1 * H - 0.02 * H * (k % 2)), r_head * 0.5, (0.9, 0.7, 1.6))
    # eyes and tilak: just enough to read the face direction in the blockout
    eye = toon("eye", "#120E0C", None, None)
    for ex in (-0.02, 0.02):
        sphere(f"{key}_eye{ex}", eye, (hx + ex * H, hy + r_head * 1.0, hz + 0.004 * H), 0.008 * H, root, (1.5, 0.45, 0.75), 8)
    sphere(f"{key}_tilak", gold, (hx, hy + r_head * 1.04, hz + 0.03 * H), 0.005 * H, root, (0.6, 0.4, 2.0), 8)
    if beard:
        ball(hb, (hx, hy + 0.04 * H, hz - 0.06 * H), r_head * 0.7, (0.95, 0.6, 1.5))
        ball(hb, (hx, hy + 0.05 * H, hz - 0.12 * H), r_head * 0.5, (0.8, 0.55, 1.5))

    if crown:
        cone(f"{key}_crown", gold, (hx, hy - 0.008 * H, hz + 0.055 * H + crown * H / 2), r_head * 0.92, r_head * 0.3,
             crown * H, root, (-0.12, 0, 0), 12)
        torus(f"{key}_crownband", gold, (hx, hy - 0.004 * H, hz + 0.05 * H), r_head * 0.95, 0.008 * H, root,
              (-0.12, 0, 0), 24, 6)
    if feather:
        sphere(f"{key}_feather", toon(f"{key}_feather", "#1E8C8C", rim), (hx + 0.02 * H, hy - 0.03 * H, hz + 0.12 * H),
               0.05 * H, root, (0.35, 0.18, 1.0), 12)
        sphere(f"{key}_feathereye", toon("feather_eye", "#1B2A6B", rim), (hx + 0.02 * H, hy - 0.018 * H, hz + 0.145 * H),
               0.013 * H, root, (1, 0.3, 1.2), 8)
    # ornaments: necklace and armlets as gold beads
    for k in range(9):
        a = math.radians(200 + k * 17.5)
        cx, cy, cz = j["chest"]
        sphere(f"{key}_bead{k}", gold, (cx + 0.07 * H * math.cos(a) * -1, cy + 0.065 * H, cz + 0.06 * H + 0.04 * H * math.sin(a)),
               0.008 * H, root, seg=8)

    anchor(f"{key}.head", j["head"], root)
    anchor(f"{key}.chest", j["chest"], root)
    anchor(f"{key}.hand_l", j["ha_l"], root)
    anchor(f"{key}.hand_r", j["ha_r"], root)
    if "conch" in j:
        p0, p1 = j["conch"]
        cone(f"{key}_conch", toon("conch", "#F4EFE4", rim), tuple((Vector(p0) + Vector(p1)) / 2), 0.035 * H, 0.008 * H,
             (Vector(p1) - Vector(p0)).length, root,
             Vector((0, 0, 1)).rotation_difference((Vector(p1) - Vector(p0)).normalized()).to_euler(), 12)
        anchor(f"{key}.conch", tuple(Vector(p1) + (Vector(p1) - Vector(p0)).normalized() * 0.05 * H), root)
    if "mace" in j:
        p0, p1 = j["mace"]
        rod(f"{key}_mace_h", gold, p0, p1, 0.012 * H, root)
        sphere(f"{key}_mace", toon("iron", "#5A5F66", rim, special), p1, 0.07 * H, root, seg=12)
    if "discus" in j:
        torus(f"{key}_discus", gold, j["discus"], 0.09 * H, 0.012 * H, root, (math.pi / 2, 0, 0))
        anchor(f"{key}.discus", j["discus"], root)
    if parasol:
        rod(f"{key}_parasol_pole", gold, (0.1 * H, -0.12 * H, 0.0), (0.1 * H, -0.12 * H, 1.35 * H), 0.008 * H, root)
        cone(f"{key}_parasol", toon("parasol", "#F4F1E8", rim), (0.1 * H, -0.12 * H, 1.35 * H), 0.42 * H, 0.02 * H,
             0.12 * H, root, (0, 0, 0), 24)
    return root, j


def add_bow(key, j, root, H, state="held"):
    b = j.get("bow")
    rim = ACT["rim"]
    m = toon("gandiva", "#2B211C", "#6FC3FF")
    if state == "falling":
        c = (-0.32 * H, 0.32 * H, 0.42 * H)
        o = bow_curve(f"{key}_bow", m, 1.15 * H, root, c, (0.0, -0.95, 0.4))
        anchor(f"{key}.bow_top", (c[0] - 0.45 * H, c[1], c[2] + 0.4 * H), root)
        anchor(f"{key}.bow_bottom", (c[0] + 0.45 * H, c[1], c[2] - 0.4 * H), root)
        return o
    if not b:
        return None
    o = bow_curve(f"{key}_bow", m, b["height"], root, b["center"], b["rot"])
    cx, cy, cz = b["center"]
    tilt = b["rot"][1]
    hh = b["height"] / 2
    anchor(f"{key}.bow_top", (cx + math.sin(tilt) * hh, cy, cz + math.cos(tilt) * hh), root)
    anchor(f"{key}.bow_bottom", (cx - math.sin(tilt) * hh, cy, cz - math.cos(tilt) * hh), root)
    return o


# ---------------------------------------------------------------- horses, chariots, armies

HORSE_MESH = {}


def horse_mesh(color_hex, rim=None):
    """One metaball horse, frozen to a mesh and reused for every instance."""
    key = (color_hex, rim)
    if key in HORSE_MESH:
        return HORSE_MESH[key]
    tmp = empty("horse_tmp")
    mb = metaball("HorseTmp" + str(len(HORSE_MESH)), toon("horse", color_hex, rim), tmp, 0.05)
    ball(mb, (0, 0, 1.36), 0.3, (0.9, 2.3, 0.95))
    ball(mb, (0, 0.6, 1.4), 0.31)
    ball(mb, (0, -0.62, 1.42), 0.32)
    capsule(mb, (0, 0.7, 1.45), (0, 1.0, 1.95), 0.21)
    capsule(mb, (0, 1.0, 1.98), (0, 1.36, 1.6), 0.12)
    ball(mb, (0, 1.42, 1.5), 0.1, (0.85, 1.1, 0.95))
    ball(mb, (-0.06, 0.96, 2.18), 0.035, (0.6, 0.6, 1.8))
    ball(mb, (0.06, 0.96, 2.18), 0.035, (0.6, 0.6, 1.8))
    for k in range(5):
        ball(mb, (0, 0.62 + k * 0.085, 1.68 + k * 0.1), 0.065, (0.5, 1.0, 1.0))
    for sx in (-0.17, 0.17):
        capsule(mb, (sx, 0.62, 1.22), (sx, 0.66, 0.66), 0.085)
        capsule(mb, (sx, 0.66, 0.66), (sx, 0.64, 0.08), 0.05)
        capsule(mb, (sx, -0.6, 1.28), (sx, -0.76, 0.68), 0.105)
        capsule(mb, (sx, -0.76, 0.68), (sx, -0.66, 0.08), 0.05)
        ball(mb, (sx, 0.66, 0.06), 0.06, (1.0, 1.2, 0.7))
        ball(mb, (sx, -0.64, 0.06), 0.06, (1.0, 1.2, 0.7))
    capsule(mb, (0, -0.9, 1.55), (0, -1.12, 0.85), 0.075)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(mb.evaluated_get(dg))
    me.materials.clear()
    me.materials.append(toon("horse", color_hex, rim))
    bpy.data.objects.remove(mb)
    bpy.data.objects.remove(tmp)
    HORSE_MESH[key] = me
    return me


def place_mesh(name, me, parent, loc, rot_z=0.0, idcol=None):
    o = bpy.data.objects.new(name, me)
    o.location = loc
    o.rotation_euler = (0, 0, rot_z)
    return link(o, parent, idcol)


def chariot(key, parent_loc, rot_z, body_hex="#D9A441", trim_hex="#F2D27A", horse_hex="#F4F1EA",
            banner=None, horses=True, bells=True, rim=None, hero=False):
    root = empty(f"{key}_car", parent_loc, rot_z)
    gold = toon(f"{key}_body", body_hex, rim)
    trim = toon(f"{key}_trim", trim_hex, rim)
    wood = toon("wood", "#5B3A22", rim)
    cube(f"{key}_floor", gold, (0, 0.05, 0.95), (1.7, 1.4, 0.12), root)
    cube(f"{key}_front", gold, (0, 0.72, 1.36), (1.6, 0.1, 0.8), root)
    cube(f"{key}_fronttrim", trim, (0, 0.74, 1.78), (1.7, 0.14, 0.08), root)
    for sx in (-0.8, 0.8):
        sphere(f"{key}_finial{sx}", trim, (sx, 0.74, 1.9), 0.09, root, seg=10)
    for sx in (-0.82, 0.82):
        cube(f"{key}_rail{sx}", trim, (sx, 0.05, 1.32), (0.06, 1.3, 0.06), root)
        cube(f"{key}_side{sx}", gold, (sx, 0.05, 1.12), (0.05, 1.3, 0.36), root)
        if bells:
            for k in range(9):
                sphere(f"{key}_bell{sx}{k}", trim, (sx * 1.03, -0.55 + k * 0.14, 1.24), 0.035, root, seg=8)
    for sx in (-0.98, 0.98):
        torus(f"{key}_wheel{sx}", trim, (sx, 0.0, 0.9), 0.86, 0.06, root, (0, math.pi / 2, 0), 40, 8)
        cone(f"{key}_hub{sx}", gold, (sx, 0, 0.9), 0.12, 0.12, 0.2, root, (0, math.pi / 2, 0))
        for k in range(12):
            a = 2 * math.pi * k / 12
            rod(f"{key}_spoke{sx}{k}", wood, (sx, 0, 0.9), (sx, 0.84 * math.cos(a), 0.9 + 0.84 * math.sin(a)), 0.025, root, 6)
    rod(f"{key}_axle", wood, (-1.05, 0, 0.9), (1.05, 0, 0.9), 0.05, root)
    anchor(f"{key}.chariot", (0, 0.3, 1.8), root)
    if horses:
        rod(f"{key}_pole", wood, (0, 0.7, 1.0), (0, 4.3, 1.45), 0.06, root)
        rod(f"{key}_yoke", trim, (-1.3, 3.9, 1.5), (1.3, 3.9, 1.5), 0.05, root)
        me = horse_mesh(horse_hex, rim)
        for k, sx in enumerate((-1.5, -0.5, 0.5, 1.5)):
            place_mesh(f"{key}_horse{k}", me, root, (sx, 3.3 + (0.15 if k in (1, 2) else 0), 0), 0.0)
    if banner:
        pole_h = banner.get("height", 9.0)
        rod(f"{key}_bpole", trim, (0, -0.55, 1.0), (0, -0.55, pole_h), 0.05, root)
        fm = toon(f"{key}_flag", banner["color"], rim)
        flag(f"{key}_flag", fm, banner.get("w", 2.2), banner.get("h", 1.3), root, (0, -0.55, pole_h - 0.4),
             0.35, banner.get("phase", 0))
        anchor(f"{key}.banner", (0.0, -0.55, pole_h + 0.6), root)
        if banner.get("ape"):
            ape = metaball(f"{key}Ape", toon("ape", "#D9A441", rim), root, 0.03)
            z = pole_h + 0.05
            ball(ape, (0, -0.55, z + 0.45), 0.32, (1.0, 0.85, 1.1))
            ball(ape, (0, -0.42, z + 0.95), 0.2)
            ball(ape, (0, -0.28, z + 0.9), 0.1, (1.0, 1.2, 0.8))
            capsule(ape, (-0.25, -0.5, z + 0.7), (-0.42, -0.3, z + 0.25), 0.07)
            capsule(ape, (0.25, -0.5, z + 0.7), (0.5, -0.25, z + 1.05), 0.07)
            capsule(ape, (-0.2, -0.55, z + 0.25), (-0.3, -0.35, z + 0.0), 0.08)
            capsule(ape, (0.2, -0.55, z + 0.25), (0.3, -0.35, z + 0.0), 0.08)
            capsule(ape, (0, -0.8, z + 0.3), (0.1, -1.2, z + 0.9), 0.04)
        if banner.get("palmyra"):
            z = pole_h + 0.1
            rod(f"{key}_palm", toon("palm_gold", "#D9A441", rim), (0, -0.55, z), (0, -0.55, z + 1.1), 0.05, root)
            for k in range(7):
                a = 2 * math.pi * k / 7
                rod(f"{key}_frond{k}", toon("palm_gold", "#D9A441", rim), (0, -0.55, z + 1.1),
                    (0.55 * math.cos(a), -0.55 + 0.55 * math.sin(a), z + 0.85), 0.03, root, 6)
            for k in range(5):
                a = 2 * math.pi * k / 5
                sphere(f"{key}_star{k}", toon("star", "#FFF2C4", rim), (0.75 * math.cos(a), -0.55, z + 1.0 + 0.6 * math.sin(a)), 0.07, root, seg=8)
    return root


def soldier_mesh(name, body_hex, spear=True, shield_hex=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.24, radius2=0.18, depth=1.35,
                          matrix=Matrix.Translation((0, 0, 0.68)))
    bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=0.13, matrix=Matrix.Translation((0, 0, 1.5)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.15, radius2=0.02, depth=0.22,
                          matrix=Matrix.Translation((0, 0, 1.7)))
    if spear:
        bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.02, radius2=0.02, depth=2.6,
                              matrix=Matrix.Translation((0.25, 0.1, 1.3)))
        bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.05, radius2=0.0, depth=0.3,
                              matrix=Matrix.Translation((0.25, 0.1, 2.75)))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(toon(name, body_hex))
    return me


def standard_mesh(name, flag_hex, h=6.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.04, radius2=0.04, depth=h,
                          matrix=Matrix.Translation((0, 0, h / 2)))
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0.55, 0, h - 0.6)) @ Matrix.Diagonal((1.1, 0.03, 0.9, 1)))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(toon(name, flag_hex))
    return me


def vert_cloud(name, pts):
    me = bpy.data.meshes.new(name)
    me.from_pydata(pts, [], [])
    o = bpy.data.objects.new(name, me)
    o.instance_type = "VERTS"
    return link(o)


# Reserved ID-pass colors so the compositor can find the massed armies.
ARMY_ID = {-1: (0.0, 0.0, 0.5, 1.0), 1: (0.5, 0.0, 0.0, 1.0)}
DIVINE_ID = (0.0, 0.5, 0.0, 1.0)


def army(side, seed, x_half=650, depth=230, spacing=2.3, front=110.0, far=False):
    """Instanced soldiers and standards. side=-1 Pandava (y<0), +1 Kaurava."""
    rnd = random.Random(seed)
    if side < 0:
        body, body2, flags = "#7A6248", "#8C7A5E", ["#E8862A", "#F4F1E8", "#2C4A8C", "#E8B92F"]
    else:
        body, body2, flags = "#4A3A36", "#5E4440", ["#9E1B2F", "#3A2A2A", "#C9A23A", "#6E1424"]
    variants = [soldier_mesh(f"sold{side}a", body, True), soldier_mesh(f"sold{side}b", body2, False)]
    pts = [[], []]
    y0 = side * front
    n_rows = int(depth / spacing)
    n_cols = int(2 * x_half / spacing)
    for r in range(n_rows):
        for c in range(n_cols):
            x = -x_half + c * spacing + rnd.uniform(-0.9, 0.9)
            y = y0 + side * (r * spacing + rnd.uniform(-0.9, 0.9))
            if -48 < x < 25 and abs(y) < abs(front) + 10:  # gap for the hero chariots
                continue
            pts[rnd.random() < 0.3].append((x, y, 0))
    for k, me in enumerate(variants):
        cloud = vert_cloud(f"army{side}_{k}", pts[k])
        cloud.color = ARMY_ID[side]
        o = bpy.data.objects.new(f"soldier{side}_{k}", me)
        o.rotation_euler = (0, 0, 0 if side < 0 else math.pi)
        link(o, cloud, cloud.color)
    # standards
    for k, fh in enumerate(flags):
        sp = []
        for r in range(0, n_rows, 6):
            for c in range(0, n_cols, 7):
                if rnd.random() < 0.16:
                    x = -x_half + c * spacing + rnd.uniform(-3, 3)
                    y = y0 + side * (r * spacing + rnd.uniform(4, 10))
                    if -48 < x < 25 and abs(y) < abs(front) + 10:
                        continue
                    sp.append((x, y, 0))
        cloud = vert_cloud(f"stand{side}_{k}", sp)
        cloud.color = ARMY_ID[side]
        me = standard_mesh(f"std{side}{k}", fh, 5.5 + k * 0.8)
        o = bpy.data.objects.new(f"standard{side}_{k}", me)
        o.rotation_euler = (0, 0, rnd.uniform(-0.4, 0.4) + (0 if side < 0 else math.pi))
        link(o, cloud, cloud.color)
    # the deep host: a few big rows of flat painted masses
    deep = toon(f"deep{side}", body)
    for k in range(6):
        y = side * (front + depth + 40 + k * 70)
        cube(f"mass{side}{k}", deep, (0, y, 1.0), (3000, 40, 2.0 + k * 0.4), None, idcol=ARMY_ID[side])


# ---------------------------------------------------------------- scene


def build(data, shot, lineup=False):
    global SCN, ACT
    reset()
    MAT_CACHE.clear()
    HORSE_MESH.clear()
    ID_COUNTER[0] = 0
    SCN = bpy.context.scene
    ACT = data["acts"][shot["act"]] if shot else data["acts"]["A"]
    C = data["characters"]
    st = shot["staging"] if shot else {}
    if st.get("key_dir"):
        ACT = dict(ACT, key_dir=st["key_dir"])
    poses = st.get("poses", {})
    hide = set(st.get("hide", []))

    if lineup:
        ACT = dict(ACT, key_dir=[0.4, 1.0, 0.6], rim_dir=[-0.6, -0.4, 0.4], shadow="#3A3550", key="#FFF0DA", rim="#FFFFFF")
        lineup_figs = [
            ("krishna", dict(pose_name="reins", crown=0.07, feather=True, costume="dhoti")),
            ("arjuna", dict(pose_name="bow_rest", crown=0.035, costume="armor", w=0.95, hair_long=True)),
            ("bhishma", dict(pose_name="stand", H=2.05, costume="armor", hair="#ECEBE6", beard=True, crown=0.02,
                             hair_long=True)),
            ("duryodhana", dict(pose_name="mace", costume="armor_heavy", w=1.18, crown=0.05)),
            ("bhima", dict(pose_name="mace", costume="dhoti", w=1.38, H=1.95)),
            ("yudhishthira", dict(pose_name="stand", costume="upper_cloth", crown=0.04, parasol=True)),
        ]
        for i, (k, kw) in enumerate(lineup_figs):
            root, j = humanoid(k, C[k], None, ((i - 2.5) * 1.25, 0, 0), 0.0, **kw)
            if k == "arjuna":
                add_bow(k, j, root, kw.get("H", 1.9))
        return

    # ground
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6000)
    mesh_from_bm("ground", bm, ground_mat())

    # Arjuna's car
    pos = (0, -100, 0) if st.get("chariot", "front") == "front" else (0, -6, 0)
    car = chariot("arjuna", pos, 0.0, banner=None if "banner" in hide else dict(color="#E8862A", ape=True, height=8.6),
                  horses="horses" not in hide, hero=True)
    root_k, jk = humanoid("krishna", C["krishna"], car, (0.3, 0.42, 1.0), 0.0, pose_name=poses.get("krishna", "reins"),
                          crown=0.07, feather=True, costume="dhoti")
    root_a, ja = humanoid("arjuna", C["arjuna"], car, (-0.35, -0.2, 1.0), 0.0, pose_name=poses.get("arjuna", "bow_rest"),
                          crown=0.035, costume="armor", w=0.95, hair_long=True)
    add_bow("arjuna", ja, root_a, 1.9, "falling" if st.get("arjuna_bow") == "falling" else "held")

    if not st.get("vishvarupa"):
        # Pandava heroes
        bc = chariot("bhima", (-28, -104, 0), 0.0, body_hex="#7E6A55", trim_hex="#B8892F",
                     banner=dict(color="#E07A1F", height=7.0, phase=1.0))
        humanoid("bhima", C["bhima"], bc, (0.0, 0.1, 1.0), 0.0, pose_name=poses.get("bhima", "mace"), w=1.38, H=1.95)
        yc = chariot("yudhishthira", (-38, -110, 0), 0.0, body_hex="#E8DDC4", trim_hex="#D9A441",
                     banner=dict(color="#2C4A8C", height=7.5, phase=2.0))
        humanoid("yudhishthira", C["yudhishthira"], yc, (0.0, 0.1, 1.0), 0.0, pose_name=poses.get("yudhishthira", "stand"),
                 costume="upper_cloth", crown=0.04, parasol=True)
        # Kaurava heroes
        kc = chariot("bhishma", (-12, 96, 0), math.pi, body_hex="#E9ECEF", trim_hex="#C9CED6", horse_hex="#F4F1EA",
                     banner=dict(color="#F4F1E8", height=9.5, palmyra=True))
        humanoid("bhishma", C["bhishma"], kc, (0.0, 0.1, 1.0), 0.0, pose_name=poses.get("bhishma", "stand"), H=2.05,
                 costume="armor", hair="#ECEBE6", beard=True, crown=0.02, hair_long=True)
        dc = chariot("duryodhana", (-30, 103, 0), math.pi, body_hex="#5A1A22", trim_hex="#C9A23A", horse_hex="#2B2422",
                     banner=dict(color="#9E1B2F", height=8.0, phase=0.5))
        humanoid("duryodhana", C["duryodhana"], dc, (0.0, 0.1, 1.0), 0.0, pose_name=poses.get("duryodhana", "mace"),
                 costume="armor_heavy", w=1.18, crown=0.05)
        drc = chariot("drona", (14, 99, 0), math.pi, body_hex="#8C8A84", trim_hex="#C9A23A",
                      banner=dict(color="#C9A23A", height=8.0, phase=1.4))
        humanoid("drona", dict(skin="#A88462", costume="#B8B4AC", accent="#E07A1F", energy="#FFFFFF"), drc, (0, 0.1, 1.0),
                 0.0, pose_name="stand", costume="dhoti", hair="#CFCBC2", beard=True)
        # generic cars along both front lines
        for i, x in enumerate([30, 55, 82, -62, -88, 110, -115]):
            pc = chariot(f"pcar{i}", (x, -106 - (i % 3) * 3, 0), 0.0, body_hex="#9A7A50", trim_hex="#C9A23A",
                         banner=dict(color=["#E8862A", "#F4F1E8", "#2C4A8C"][i % 3], height=6.5, phase=i), bells=False)
            humanoid(f"pw{i}", dict(skin="#7E5A40", costume=["#E8862A", "#EDE3CC", "#2C4A8C"][i % 3], accent="#C9A23A",
                     energy="#FFD9A0"), pc, (0, 0.1, 1.0), 0.0, pose_name=["stand", "mace", "bow_rest"][i % 3],
                     costume="armor", res=0.07, crown=0.03)
            kc2 = chariot(f"kcar{i}", (-x * 0.9, 100 + (i % 3) * 3, 0), math.pi, body_hex="#4A2A2A", trim_hex="#9A7A3A",
                          horse_hex="#3A302C", banner=dict(color=["#9E1B2F", "#3A2A2A", "#C9A23A"][i % 3], height=6.5,
                          phase=i), bells=False)
            humanoid(f"kw{i}", dict(skin="#7A5A3A", costume=["#9E1B2F", "#3A2A2A", "#6E1424"][i % 3], accent="#C9A23A",
                     energy="#D0213F"), kc2, (0, 0.1, 1.0), 0.0, pose_name=["mace", "stand", "bow_rest"][i % 3],
                     costume="armor_heavy", res=0.07, crown=0.03)
        army(-1, 1, front=116)
        army(+1, 2, front=108, spacing=2.1)
    else:
        # The universal form towers beyond the field.
        army(-1, 1, front=116)
        army(+1, 2, front=108, spacing=2.8)
        vr, vj = humanoid("vishvarupa", dict(skin="#FFE9A8", costume="#FFD27A", accent="#FFF2C4", energy="#7FF5EA"), None,
                          (0, 1000, -100), math.pi, H=1600, pose_name="universal", crown=0.16, res=10.0, special="divine")
        for o in bpy.data.objects:
            if o.name.startswith("vishvarupa"):
                o.color = DIVINE_ID


def setup_camera(cam_spec, width, height):
    cd = bpy.data.cameras.new("cam")
    cd.lens = cam_spec["lens"]
    cd.sensor_width = 36
    cd.clip_start = 0.1
    cd.clip_end = 20000
    cam = bpy.data.objects.new("cam", cd)
    SCN.collection.objects.link(cam)
    cam.location = cam_spec["loc"]
    d = Vector(cam_spec["target"]) - Vector(cam_spec["loc"])
    q = d.to_track_quat("-Z", "Y")
    roll = math.radians(cam_spec.get("roll", 0))
    q = q @ Quaternion((0, 0, 1), roll)
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = q
    SCN.camera = cam
    SCN.render.resolution_x = width
    SCN.render.resolution_y = height
    SCN.render.resolution_percentage = 100
    return cam


def render_passes(out, tag, samples):
    r = SCN.render
    r.engine = "CYCLES"
    SCN.cycles.device = "CPU"
    SCN.cycles.use_denoising = False
    SCN.cycles.max_bounces = 0
    SCN.cycles.use_adaptive_sampling = False
    r.film_transparent = True
    r.image_settings.file_format = "PNG"
    vl = SCN.view_layers[0]
    world = bpy.data.worlds.new("w") if not SCN.world else SCN.world
    SCN.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Strength"].default_value = 0.0

    # color
    SCN.view_settings.view_transform = "Standard"
    SCN.view_settings.look = "None"
    r.image_settings.color_mode = "RGBA"
    r.image_settings.color_depth = "8"
    SCN.cycles.samples = samples
    vl.material_override = None
    r.filepath = os.path.join(out, f"{tag}_color.png")
    bpy.ops.render.render(write_still=True)

    # depth (log, raw)
    SCN.view_settings.view_transform = "Raw"
    r.image_settings.color_mode = "BW"
    r.image_settings.color_depth = "16"
    SCN.cycles.samples = 4
    vl.material_override = depth_mat()
    r.filepath = os.path.join(out, f"{tag}_depth.png")
    bpy.ops.render.render(write_still=True)

    # object id
    r.image_settings.color_mode = "RGB"
    r.image_settings.color_depth = "8"
    SCN.cycles.samples = 1
    r.film_transparent = True
    vl.material_override = id_mat()
    r.filepath = os.path.join(out, f"{tag}_id.png")
    bpy.ops.render.render(write_still=True)
    vl.material_override = None
    SCN.view_settings.view_transform = "Standard"


NEAR, FAR = 0.3, 8000.0


def depth_mat():
    m = bpy.data.materials.new("depth")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    cd = N.new("ShaderNodeCameraData")
    lg = N.new("ShaderNodeMath")
    lg.operation = "LOGARITHM"
    lg.inputs[1].default_value = math.e
    sock = cd.outputs.get("View Z Depth") or cd.outputs[1]
    L.new(sock, lg.inputs[0])
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = math.log(NEAR)
    mr.inputs["From Max"].default_value = math.log(FAR)
    L.new(lg.outputs[0], mr.inputs["Value"])
    em = N.new("ShaderNodeEmission")
    L.new(mr.outputs[0], em.inputs["Color"])
    L.new(em.outputs[0], out.inputs["Surface"])
    return m


def id_mat():
    m = bpy.data.materials.new("idpass")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    oi = N.new("ShaderNodeObjectInfo")
    em = N.new("ShaderNodeEmission")
    L.new(oi.outputs["Color"], em.inputs["Color"])
    L.new(em.outputs[0], out.inputs["Surface"])
    return m


def to_px(cam, co, W, H):
    v = world_to_camera_view(SCN, cam, Vector(co))
    return [v.x * W, (1 - v.y) * H, v.z]


def write_meta(out, tag, cam, shot, W, H):
    bpy.context.view_layer.update()
    meta = dict(shot=tag, width=W, height=H, act=shot["act"] if shot else "A", anchors={})
    for o in bpy.data.objects:
        if o.name.startswith("A:"):
            meta["anchors"][o.name[2:]] = to_px(cam, o.matrix_world.translation, W, H)
    fwd = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    fh = Vector((fwd.x, fwd.y, 0))
    if fh.length < 1e-3:
        fh = Vector((0, 1, 0))
    fh.normalize()
    side = Vector((-fh.y, fh.x, 0))
    c = cam.matrix_world.translation
    p1 = c + (fh + side * 0.3) * 1e5
    p2 = c + (fh - side * 0.3) * 1e5
    p1.z = p2.z = c.z  # the horizon is at eye level
    meta["horizon"] = [to_px(cam, p1, W, H), to_px(cam, p2, W, H)]
    sun = norm((shot or {}).get("staging", {}).get("sun_dir", ACT["sun_dir"]))
    meta["sun"] = to_px(cam, c + sun * 1e5, W, H)
    meta["cam"] = dict(loc=list(c), fwd=list(fwd), lens=cam.data.lens)
    meta["near"], meta["far"] = NEAR, FAR
    with open(os.path.join(out, f"{tag}_meta.json"), "w") as f:
        json.dump(meta, f, indent=1)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", default=os.path.join(HERE, "..", "data", "shots.json"))
    ap.add_argument("--shot")
    ap.add_argument("--lineup", action="store_true")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "art", "render"))
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--samples", type=int, default=12)
    ap.add_argument("--save-blend")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    data = json.load(open(a.shots))
    if a.lineup:
        build(data, None, lineup=True)
        W, Hh = a.width, int(a.width * 0.45)
        cd = bpy.data.cameras.new("cam")
        cd.type = "ORTHO"
        cd.ortho_scale = 8.4
        cam = bpy.data.objects.new("cam", cd)
        SCN.collection.objects.link(cam)
        cam.location = (0, 30, 1.25)
        cam.rotation_euler = (math.pi / 2, 0, math.pi)
        SCN.camera = cam
        SCN.render.resolution_x, SCN.render.resolution_y = W, Hh
        render_passes(a.out, "lineup", a.samples)
        write_meta(a.out, "lineup", cam, None, W, Hh)
        return
    shot = next(s for s in data["shots"] if s["id"] == a.shot)
    build(data, shot)
    W = a.width
    Hh = int(round(W / data.get("aspect", 2.39)))
    cam = setup_camera(shot["camera"], W, Hh)
    if a.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save_blend))
    render_passes(a.out, shot["id"], a.samples)
    write_meta(a.out, shot["id"], cam, shot, W, Hh)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(argv)

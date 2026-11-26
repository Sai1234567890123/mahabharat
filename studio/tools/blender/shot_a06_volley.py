#!/usr/bin/env python3
"""Gate 4 proof shot A06, Karna's volley: 5 s, 24 fps, hand-keyed on twos, rendered in Cycles on the CPU. FREE.

  python studio/tools/blender/shot_a06_volley.py FULLDRAW.blend OUT_DIR [--frames 0-119] [--size 1280x720]
                                                 [--samples 24] [--only 0,28,40]

FULLDRAW.blend is made by karna_rig.py (Karna posed at full draw, bow rig, aim toward +X).
Writes OUT_DIR/a06_scene.blend (the animated shot), OUT_DIR/frames/####.png and OUT_DIR/fx.json (screen position of the
bow for the 2D FX pass, studio/tools/fx_a06_post.py).

Shot card A06: Karna at full draw facing screen left, seven arrows nocked as a fan, sun-fire along each shaft, the sun
behind him. 0-1 s hold at full draw (anticipation); 1-2 s release, the camera rides beside one orange arrow toward screen
left; 2-5 s the fan spreads across the sky, a whip-pan left.

Timing (frames): 0-27 hold, a small tremble from 14; 28 release (string snaps past brace, limbs unbend, the draw hand
flies back, the bow tips toward the target); 28-48 arrow-cam; 48-58 whip-pan; 58-119 the fan opens across the sky.
Karna and the bow are keyed on twos (constant interpolation), the camera and the arrows move on ones.
"""
import argparse, json, math, pathlib, random, sys

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Quaternion, Vector

ap = argparse.ArgumentParser()
ap.add_argument("blend"); ap.add_argument("out")
ap.add_argument("--frames", default="0-119"); ap.add_argument("--size", default="1280x720")
ap.add_argument("--samples", type=int, default=24); ap.add_argument("--only", default="")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
out = pathlib.Path(a.out).resolve()
(out / "frames").mkdir(parents=True, exist_ok=True)

bpy.ops.preferences.addon_enable(module="rigify")
bpy.ops.wm.open_mainfile(filepath=str(pathlib.Path(a.blend).resolve()))
sc = bpy.context.scene
rig = bpy.data.objects["KARNA_rig"]
bow_arm = bpy.data.objects["KARNA_bow_rig"]
pb = rig.pose.bones
bpb = bow_arm.pose.bones
for n in ("KARNA_arrow", "KARNA_arrowhead"):
    bpy.data.objects.remove(bpy.data.objects[n])

F_RELEASE, F_END = 28, 119
NOCK = Vector((-0.015, -0.105, 1.60))
GRIP = Vector((0.733, -0.055, 1.55))
AIM = (GRIP - NOCK).normalized()
sc.frame_start, sc.frame_end = 0, F_END
sc.render.fps = 24
rnd = random.Random(7)


def upd():
    bpy.context.view_layer.update()


# ---- Karna on twos -----------------------------------------------------------------------------------------------------
FINGERS = [f"{f}.{k}.{s}" for f in ("f_index", "f_middle", "f_ring", "f_pinky", "thumb") for k in ("01", "02", "03") for s in ("L", "R")]
CTRL = ["torso", "chest", "head", "hand_ik.L", "hand_ik.R", "upper_arm_ik_target.L", "upper_arm_ik_target.R"] + [f for f in FINGERS if f in pb]
for n in CTRL:
    pb[n].rotation_mode = "QUATERNION"
upd()
DRAW = {n: pb[n].matrix_basis.copy() for n in CTRL}

# the bow rides the left hand from now on, so it follows through with the wrist
mw = bow_arm.matrix_world.copy()
bow_arm.parent, bow_arm.parent_type, bow_arm.parent_bone = rig, "BONE", "DEF-hand.L"
upd()
bow_arm.matrix_world = mw
upd()
BOW_DRAW = {b.name: b.matrix_basis.copy() for b in bpb}


def reset():
    for n in CTRL:
        pb[n].matrix_basis = DRAW[n]
    upd()


def nudge(name, offset=None, axis=None, deg=0.0, pivot=None):
    b = pb[name]
    m = b.matrix.copy()
    if axis is not None:
        piv = m.translation.copy() if pivot is None else pivot
        m = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-piv) @ m
    if offset is not None:
        m.translation += offset
    b.matrix = m
    upd()


def open_fingers(side, k):
    """open a hand by k (0 = as posed, 1 = straight)"""
    for n in CTRL:
        if n.endswith(f".{side}") and n.split(".")[0] in ("f_index", "f_middle", "f_ring", "f_pinky"):
            q = DRAW[n].to_quaternion().slerp(Quaternion(), k)
            m = q.to_matrix().to_4x4()
            m.translation = DRAW[n].translation
            pb[n].matrix_basis = m
    upd()


def key_char(frame):
    for n in CTRL:
        pb[n].keyframe_insert("location", frame=frame)
        pb[n].keyframe_insert("rotation_quaternion", frame=frame)


def key_bow(frame, limb_k, nock_offset):
    """limb_k: 1 = bent at full draw, 0 = braced, negative = overshoot; nock_offset: None = at the anchor"""
    for b in bpb:
        if b.name.startswith("limb_"):
            q = BOW_DRAW[b.name].to_quaternion()
            axis, ang = q.to_axis_angle()
            b.rotation_mode = "QUATERNION"
            b.rotation_quaternion = Quaternion(axis, ang * limb_k)
            b.keyframe_insert("rotation_quaternion", frame=frame)
    nk = bpb["nock"]
    nk.rotation_mode = "QUATERNION"
    if nock_offset is None:
        nk.matrix_basis = BOW_DRAW["nock"]
    else:
        nk.matrix_basis = Matrix.Translation(Vector((0, nock_offset, 0)))     # the nock bone's Y runs from the bow toward him
    nk.keyframe_insert("location", frame=frame)
    nk.keyframe_insert("rotation_quaternion", frame=frame)


# hold: still, then a small tremble as the draw is held past comfort
for f in range(0, F_RELEASE, 2):
    reset()
    if f >= 14:
        s = (f - 12) / 16
        nudge("hand_ik.R", offset=Vector([rnd.uniform(-1, 1) * 0.003 * s for _ in range(3)]) - AIM * 0.006 * s)
        nudge("chest", axis="Z", deg=rnd.uniform(-1, 1) * 0.4 * s)
    key_char(f)
    key_bow(f, 1.0, None)
# release and follow-through
FOLLOW = [  # frame, draw-hand travel back, bow tip toward target (deg), fingers open, chest recoil (deg), limbs, nock
    (28, 0.09, 4, 0.65, 1.5, 0.0, -0.035),
    (30, 0.15, 10, 0.85, 2.5, -0.18, 0.012),
    (32, 0.17, 14, 0.90, 2.0, 0.06, 0.0),
    (34, 0.175, 15, 0.90, 1.6, 0.0, 0.0),
    (40, 0.175, 15, 0.90, 1.2, 0.0, 0.0),
]

def all_fcurves(idb):
    """F-curves of an ID's action; Blender 5 keeps them in layers > strips > channelbags."""
    ad = getattr(idb, "animation_data", None)
    act = ad.action if ad else None
    if act is None:
        return []
    if hasattr(act, "fcurves"):
        return list(act.fcurves)
    out = []
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                out.extend(bag.fcurves)
    return out

for f, back, tip, op, recoil, limb, nock in FOLLOW:
    reset()
    nudge("hand_ik.R", offset=-AIM * back + Vector((0, 0.025, 0.02)) * (back / 0.175))
    nudge("upper_arm_ik_target.R", offset=-AIM * back * 0.8)
    nudge("hand_ik.L", axis=Vector((0, 1, 0)), deg=tip, offset=Vector((0, 0, -0.015 * tip / 15)))
    nudge("chest", axis="Z", deg=recoil)
    open_fingers("R", op)
    key_char(f)
    key_bow(f, limb, nock)
for obj in (rig, bow_arm):
    for fc in all_fcurves(obj):
        for k in fc.keyframe_points:
            k.interpolation = "CONSTANT"                              # on twos: poses hold, then snap

# ---- seven arrows ---------------------------------------------------------------------------------------------------------
def mat(name, base, emit=None, strength=0.0, metal=0.0, rough=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*base, 1)
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough
    if emit:
        p.inputs["Emission Color"].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = strength
    return m


def fire_mat(name, color, strength, along="Z", fade_to_tail=True):
    """soft fire tube: a hot yellow core and deep orange edges, fading along the object's own length
    (Generated coordinates) and toward its silhouette, flickering with noise"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        N.remove(n)

    def math_node(op, a=None, b=None):
        n = N.new("ShaderNodeMath")
        n.operation = op
        for idx, v in ((0, a), (1, b)):
            if isinstance(v, (int, float)):
                n.inputs[idx].default_value = v
            elif v is not None:
                L.new(v, n.inputs[idx])
        return n.outputs[0]

    outn = N.new("ShaderNodeOutputMaterial")
    mix = N.new("ShaderNodeMixShader")
    tr = N.new("ShaderNodeBsdfTransparent")
    em = N.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = strength
    lw = N.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    core = math_node("POWER", math_node("SUBTRACT", 1.0, lw.outputs["Facing"]), 1.6)   # 1 on the axis, 0 at the rim
    heat = N.new("ShaderNodeMix")
    heat.data_type = "RGBA"
    heat.inputs["A"].default_value = (*color, 1)                        # rim: the given deep orange
    heat.inputs["B"].default_value = (1.0, 0.78, 0.38, 1)               # core: yellow-white
    L.new(math_node("POWER", core, 2.5), heat.inputs["Factor"])
    L.new(heat.outputs["Result"], em.inputs["Color"])
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Generated"], sep.inputs[0])
    ramp = N.new("ShaderNodeValToRGB")
    if fade_to_tail:
        ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
        ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    L.new(sep.outputs[along], ramp.inputs["Fac"])
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 6.0
    noise.inputs["Detail"].default_value = 4.0
    nr = N.new("ShaderNodeMapRange")
    nr.inputs["From Min"].default_value, nr.inputs["From Max"].default_value = 0.35, 0.65
    nr.inputs["To Min"].default_value, nr.inputs["To Max"].default_value = 0.45, 1.0
    L.new(noise.outputs["Fac"], nr.inputs["Value"])
    fac = math_node("MULTIPLY", math_node("MULTIPLY", ramp.outputs["Color"], nr.outputs["Result"]), core)
    L.new(fac, mix.inputs["Fac"])
    L.new(tr.outputs[0], mix.inputs[1])
    L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], outn.inputs["Surface"])
    return m, em, noise


shaft_m = mat("a06_shaft", (0.09, 0.06, 0.04), rough=0.55)
head_m = mat("a06_head", (1.0, 0.70, 0.25), emit=(1.0, 0.55, 0.12), strength=0.0, metal=1.0, rough=0.25)
fletch_m = mat("a06_fletch", (0.75, 0.12, 0.05), rough=0.7)
sleeve_m, sleeve_em, sleeve_noise = fire_mat("a06_sunfire", (1.0, 0.25, 0.02), 0.0)
trail_m, trail_em, trail_noise = fire_mat("a06_trail", (1.0, 0.16, 0.01), 7.0)
spark_m = bpy.data.materials.new("a06_spark")
spark_m.use_nodes = True
_sN, _sL = spark_m.node_tree.nodes, spark_m.node_tree.links
for _n in list(_sN):
    _sN.remove(_n)
_so, _smx, _str, _sem, _slw = (_sN.new(t) for t in ("ShaderNodeOutputMaterial", "ShaderNodeMixShader", "ShaderNodeBsdfTransparent",
                                                    "ShaderNodeEmission", "ShaderNodeLayerWeight"))
_sem.inputs["Color"].default_value = (1.0, 0.62, 0.22, 1)
_sem.inputs["Strength"].default_value = 0.0
_sinv = _sN.new("ShaderNodeMath")
_sinv.operation = "SUBTRACT"
_sinv.inputs[0].default_value = 1.0
_sL.new(_slw.outputs["Facing"], _sinv.inputs[1])
_spow = _sN.new("ShaderNodeMath")
_spow.operation = "POWER"
_spow.inputs[1].default_value = 3.0
_sL.new(_sinv.outputs[0], _spow.inputs[0])
_sL.new(_spow.outputs[0], _smx.inputs["Fac"])
_sL.new(_str.outputs[0], _smx.inputs[1])
_sL.new(_sem.outputs[0], _smx.inputs[2])
_sL.new(_smx.outputs[0], _so.inputs["Surface"])
for f, s_ in ((F_RELEASE - 1, 0.0), (F_RELEASE, 14.0), (F_END, 9.0)):
    _sem.inputs["Strength"].default_value = s_
    _sem.inputs["Strength"].keyframe_insert("default_value", frame=f)
# sun-fire grows through the hold, flares at release
for f, s in ((0, 0.0), (8, 0.6), (18, 3.0), (26, 9.0), (28, 22.0), (34, 10.0), (F_END, 10.0)):
    sleeve_em.inputs["Strength"].default_value = s
    sleeve_em.inputs["Strength"].keyframe_insert("default_value", frame=f)
    head_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = s * 0.6
    head_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
for nz in (sleeve_noise, trail_noise):                                # the fire crawls
    nz.noise_dimensions = "4D"
    for f, w in ((0, 0.0), (F_END, 30.0)):
        nz.inputs["W"].default_value = w
        nz.inputs["W"].keyframe_insert("default_value", frame=f)
    for fc in all_fcurves(nz.id_data):
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"


def part(name, kind, parent, mtl, **kw):
    if kind == "cyl":
        bpy.ops.mesh.primitive_cylinder_add(vertices=kw.get("v", 10), radius=kw["r"], depth=kw["d"], location=(0, 0, kw["z"]))
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=kw.get("v", 10), radius1=kw["r1"], radius2=kw.get("r2", 0.0), depth=kw["d"],
                                        location=(0, 0, kw["z"]), end_fill_type=kw.get("fill", "NGON"))
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mtl)
    o.parent = parent
    return o


LEN = 0.86
arrows, trails, sparks, trail_len = [], [], [], [[0.001] * (F_END + 1) for _ in range(7)]
for i in range(7):
    e = bpy.data.objects.new(f"A06_arrow_{i}", None)
    sc.collection.objects.link(e)
    part(f"A06_shaft_{i}", "cyl", e, shaft_m, r=0.0055, d=LEN - 0.08, z=(LEN - 0.08) / 2)
    part(f"A06_head_{i}", "cone", e, head_m, r1=0.016, d=0.08, z=LEN - 0.04)
    part(f"A06_sleeve_{i}", "cyl", e, sleeve_m, r=0.016, d=LEN - 0.12, z=(LEN - 0.12) / 2 + 0.06, v=12)
    for k in range(2):                                                # two crossed vanes at the tail
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.08))
        vane = bpy.context.object
        vane.name = f"A06_vane_{i}_{k}"
        vane.scale = (0.03, 0.001, 0.09)
        vane.rotation_euler = (0, 0, math.radians(90 * k))
        vane.data.materials.append(fletch_m)
        vane.parent = e
    tr = part(f"A06_trail_{i}", "cone", e, trail_m, r1=0.0, r2=0.022, d=1.0, z=-0.5, v=12, fill="NOTHING")   # cone base at the arrow, tip trailing
    tr.scale = (1, 1, 0.001)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.02, location=(0, 0, LEN - 0.02))
    spark = bpy.context.object                                        # the burning point at the head, readable from far off
    spark.name = f"A06_spark_{i}"
    spark.data.materials.append(spark_m)
    spark.parent = e
    sparks.append(spark)
    arrows.append(e)
    trails.append(tr)


def rot_to(d):
    return d.normalized().to_track_quat("Z", "Y")


def tilt(d, up_deg, side_deg):
    side = d.cross(Vector((0, 0, 1))).normalized()
    up = side.cross(d).normalized()
    v = d + up * math.tan(math.radians(up_deg)) + side * math.tan(math.radians(side_deg))
    return v.normalized()


NOCKED = [tilt(AIM, -7.5 + 2.5 * i, 0.0) for i in range(7)]          # the fan on the string, heads spread through the bow
FLIGHT = [tilt(Vector((1, 0, 0)), 4.0 + 1.2 * i, (i - 3) * 2.2) for i in range(7)]
V = 1.3                                                              # metres per frame at full speed (31 m/s)
paths = [[] for _ in range(7)]
for i in range(7):
    p = NOCK - NOCKED[i] * 0.02
    for f in range(F_END + 1):
        if f < F_RELEASE:
            d, step = NOCKED[i], 0.0
        else:
            t = f - F_RELEASE
            w = min(1.0, t / 4)
            d = NOCKED[i].lerp(FLIGHT[i], w).normalized()
            step = V * (1 - math.exp(-(t + 1) / 1.6)) * (1 + 0.04 * math.sin(i * 1.7))
        p = p + d * step
        paths[i].append((p.copy(), d.copy()))
        arrows[i].location = p
        arrows[i].rotation_mode = "QUATERNION"
        arrows[i].rotation_quaternion = rot_to(d)
        arrows[i].keyframe_insert("location", frame=f)
        arrows[i].keyframe_insert("rotation_quaternion", frame=f)
        if f >= F_RELEASE - 1:
            trav = (p - (NOCK - NOCKED[i] * 0.02)).length
            trail_len[i][f] = max(0.001, min(trav * 0.85, 9.0 + trav * 0.12))
for o in arrows:
    if o.animation_data:
        for fc in all_fcurves(o):
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"

# ---- world: low sun behind him, dusty red ground ------------------------------------------------------------------------
P0, T0 = Vector((2.5, 2.3, 1.30)), Vector((0.25, 0.0, 1.58))          # low three-quarter: his face, the bow, arrows aimed screen left
_h = Vector(((T0 - P0).x, (T0 - P0).y, 0)).normalized()
SUN_DIR = (Matrix.Rotation(math.radians(-9), 3, "Z") @ _h).normalized()  # just past his head as the camera sees it
SUN_ELEV = math.radians(6.5)
w = bpy.data.worlds.new("A06_sky")
sc.world = w
w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links
sky = wn.new("ShaderNodeTexSky")
sky.sky_type = "MULTIPLE_SCATTERING"
sky.sun_disc = True
sky.sun_elevation = SUN_ELEV
sky.sun_rotation = math.atan2(SUN_DIR.x, SUN_DIR.y) % (2 * math.pi)  # checked against the sun lamp in the test frames
sky.sun_size = math.radians(2.2)
sky.sun_intensity = 0.6
sky.air_density, sky.aerosol_density = 1.6, 4.5             # thick dusty air: a burnt orange horizon
wl.new(sky.outputs["Color"], wn["Background"].inputs["Color"])
wn["Background"].inputs["Strength"].default_value = 0.35
sun = bpy.data.objects.new("A06_sun", bpy.data.lights.new("A06_sun", "SUN"))
sc.collection.objects.link(sun)
sun.data.energy, sun.data.color, sun.data.angle = 4.5, (1.0, 0.72, 0.45), math.radians(1.5)
to_sun = Vector((SUN_DIR.x * math.cos(SUN_ELEV), SUN_DIR.y * math.cos(SUN_ELEV), math.sin(SUN_ELEV)))
sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()
fill = bpy.data.objects.new("A06_fill", bpy.data.lights.new("A06_fill", "SUN"))
sc.collection.objects.link(fill)
fill.data.energy, fill.data.color = 0.9, (0.62, 0.72, 1.0)
fill.rotation_euler = Vector((-0.5, -0.6, -0.6)).to_track_quat("-Z", "Y").to_euler()
bpy.ops.mesh.primitive_plane_add(size=1200, location=(300, 0, 0))
ground = bpy.context.object
ground.name = "A06_ground"
gm = bpy.data.materials.new("A06_dust")
gm.use_nodes = True
gN, gL = gm.node_tree.nodes, gm.node_tree.links
gp = gN["Principled BSDF"]
gp.inputs["Roughness"].default_value = 0.95
gnz = gN.new("ShaderNodeTexNoise")
gnz.inputs["Scale"].default_value = 0.35
gnz.inputs["Detail"].default_value = 10.0
gcr = gN.new("ShaderNodeValToRGB")
gcr.color_ramp.elements[0].color = (0.16, 0.07, 0.035, 1)
gcr.color_ramp.elements[1].color = (0.42, 0.22, 0.11, 1)
gtc = gN.new("ShaderNodeTexCoord")
gL.new(gtc.outputs["Object"], gnz.inputs["Vector"])
gL.new(gnz.outputs["Fac"], gcr.inputs["Fac"])
gL.new(gcr.outputs["Color"], gp.inputs["Base Color"])
gbump = gN.new("ShaderNodeBump")
gbump.inputs["Strength"].default_value = 0.4
gfine = gN.new("ShaderNodeTexNoise")
gfine.inputs["Scale"].default_value = 40.0
gL.new(gtc.outputs["Object"], gfine.inputs["Vector"])
gL.new(gfine.outputs["Fac"], gbump.inputs["Height"])
gL.new(gbump.outputs["Normal"], gp.inputs["Normal"])
ground.data.materials.append(gm)

# painted cloud deck: torn bands lit gold toward the sun, dusky violet away from it (concept-art sky, not a sim)
bpy.ops.mesh.primitive_plane_add(size=40000, location=(0, 0, 420))
clouds = bpy.context.object
clouds.name = "A06_clouds"
cm = bpy.data.materials.new("A06_clouds")
cm.use_nodes = True
cN, cL = cm.node_tree.nodes, cm.node_tree.links
for n in list(cN):
    cN.remove(n)
c_out = cN.new("ShaderNodeOutputMaterial")
c_mix = cN.new("ShaderNodeMixShader")
c_tr = cN.new("ShaderNodeBsdfTransparent")
c_em = cN.new("ShaderNodeEmission")
c_em.inputs["Strength"].default_value = 1.6
c_tc = cN.new("ShaderNodeTexCoord")
c_map = cN.new("ShaderNodeMapping")
c_map.inputs["Scale"].default_value = (1.0, 3.2, 1.0)                 # bands stretched across the sun line
c_map.inputs["Rotation"].default_value = (0, 0, math.atan2(SUN_DIR.y, SUN_DIR.x))
cL.new(c_tc.outputs["Object"], c_map.inputs["Vector"])
c_nz = cN.new("ShaderNodeTexNoise")
c_nz.inputs["Scale"].default_value = 0.0016
c_nz.inputs["Detail"].default_value = 12.0
c_nz.inputs["Roughness"].default_value = 0.62
cL.new(c_map.outputs["Vector"], c_nz.inputs["Vector"])
c_cov = cN.new("ShaderNodeMapRange")
c_cov.inputs["From Min"].default_value, c_cov.inputs["From Max"].default_value = 0.47, 0.62
cL.new(c_nz.outputs["Fac"], c_cov.inputs["Value"])
c_len = cN.new("ShaderNodeVectorMath")
c_len.operation = "LENGTH"
cL.new(c_tc.outputs["Object"], c_len.inputs[0])
c_far = cN.new("ShaderNodeMapRange")                                  # thins out toward the horizon, so no hard deck edge
c_far.inputs["From Min"].default_value, c_far.inputs["From Max"].default_value = 2500.0, 14000.0
c_far.inputs["To Min"].default_value, c_far.inputs["To Max"].default_value = 1.0, 0.0
cL.new(c_len.outputs["Value"], c_far.inputs["Value"])
c_fac = cN.new("ShaderNodeMath")
c_fac.operation = "MULTIPLY"
cL.new(c_cov.outputs["Result"], c_fac.inputs[0])
cL.new(c_far.outputs["Result"], c_fac.inputs[1])
cL.new(c_fac.outputs[0], c_mix.inputs["Fac"])
c_sun = cN.new("ShaderNodeVectorMath")                                # how far toward the sun this bit of cloud lies
c_sun.operation = "DOT_PRODUCT"
c_sun.inputs[1].default_value = (SUN_DIR.x, SUN_DIR.y, 0)
cL.new(c_tc.outputs["Object"], c_sun.inputs[0])
c_glow = cN.new("ShaderNodeMapRange")
c_glow.inputs["From Min"].default_value, c_glow.inputs["From Max"].default_value = -600.0, 1800.0
cL.new(c_sun.outputs["Value"], c_glow.inputs["Value"])
c_col = cN.new("ShaderNodeValToRGB")
c_col.color_ramp.elements[0].color = (0.42, 0.26, 0.30, 1)            # dusty rose, away from the sun
c_col.color_ramp.elements.new(0.55).color = (0.55, 0.20, 0.07, 1)     # ember
c_col.color_ramp.elements[1].color = (1.0, 0.62, 0.25, 1)             # gold rims near the sun
cL.new(c_glow.outputs["Result"], c_col.inputs["Fac"])
cL.new(c_col.outputs["Color"], c_em.inputs["Color"])
cL.new(c_tr.outputs[0], c_mix.inputs[1])
cL.new(c_em.outputs[0], c_mix.inputs[2])
cL.new(c_mix.outputs[0], c_out.inputs["Surface"])
clouds.data.materials.append(cm)
clouds.visible_shadow = False

# ---- camera on ones ------------------------------------------------------------------------------------------------------
cam = bpy.data.objects.new("A06_cam", bpy.data.cameras.new("A06_cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 35
cam.data.clip_end = 30000


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


P0b = P0 + (T0 - P0) * 0.14
WHIP = 46
RIDE = Vector((-0.55, 0.95, 0.16))                                    # beside and a little behind arrow 3, on his back side
cam_pos, cam_tgt = [], []
for f in range(F_END + 1):
    if f < F_RELEASE:
        p = P0.lerp(P0b, smooth(f / (F_RELEASE - 1)))
        t = T0.copy()
    else:
        h3, d3 = paths[3][f]
        head3 = h3 + d3 * LEN
        w_ = smooth((f - F_RELEASE) / 8)
        p_static, t_static = P0b, T0
        p_ride, t_ride = head3 + RIDE, head3 - d3 * 0.3     # the whole arrow sits mid-frame, head leading left
        p, t = p_static.lerp(p_ride, w_), t_static.lerp(t_ride, w_)
        if f >= WHIP:                                                 # the camera eases off the arrow and whips left after the fan
            k = f - WHIP
            fan_v = sum((paths[i][f][0] - paths[i][f - 1][0] for i in range(7)), Vector()) / 7
            keep = 1.0 - 0.55 * smooth(k / 18)                        # falls behind so the fan opens up across the frame
            p = cam_pos[-1] + fan_v * keep + Vector((0, 0.03, 0.025)) * smooth(k / 10)
            look_ride = (t_ride - p_ride).normalized()
            fan_mid = sum((paths[i][f][0] for i in range(7)), Vector()) / 7
            look_fan = (fan_mid + Vector((0, 0, 0.6)) - p).normalized()
            look = look_ride.lerp(look_fan, smooth(k / 7)).normalized()
            t = p + look * 10
    if F_RELEASE <= f < F_RELEASE + 12:                               # recoil shake on the camera
        amp = 0.03 * (1 - (f - F_RELEASE) / 12) ** 2
        t = t + Vector([rnd.uniform(-amp, amp) for _ in range(3)]) * 4
    cam_pos.append(p.copy())
    cam_tgt.append(t.copy())
    cam.location = p
    cam.rotation_euler = (t - p).to_track_quat("-Z", "Y").to_euler()
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
for fc in all_fcurves(cam):
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"

# streaks and sparks fatten with distance from the lens, so the far fan still reads as seven fire lines
for i in range(7):
    for f in range(F_RELEASE - 1, F_END + 1):
        h, d = paths[i][f]
        dist = (h + d * LEN - cam_pos[f]).length
        wide = min(max(dist / 5.0, 1.0), 40.0)
        trails[i].scale = (wide, wide, trail_len[i][f])
        trails[i].location = (0, 0, -trail_len[i][f] / 2)
        trails[i].keyframe_insert("scale", frame=f)
        trails[i].keyframe_insert("location", frame=f)
        g = min(max(dist / 3.0, 1.0), 60.0)
        sparks[i].scale = (g, g, g)
        sparks[i].keyframe_insert("scale", frame=f)
    for o in (trails[i], sparks[i]):
        for fc in all_fcurves(o):
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"

# ---- render settings ---------------------------------------------------------------------------------------------------------
W_, H_ = (int(v) for v in a.size.split("x"))
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = a.samples
try:
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
except Exception as ex:                                               # some pip builds have no denoiser
    print("no denoiser:", ex)
sc.render.resolution_x, sc.render.resolution_y = W_, H_
sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 0.5
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Punchy" if "AgX - Punchy" in [i.identifier for i in sc.view_settings.bl_rna.properties["look"].enum_items] else "None"
for o in bpy.data.objects:
    if o.name.startswith("WGT-") or o.name == "metarig":
        o.hide_render = True
rig.hide_render = bow_arm.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=str(out / "a06_scene.blend"), relative_remap=True)

# screen positions of the bow grip for the 2D FX pass
fx = {"release": F_RELEASE, "size": [W_, H_], "grip": {}}
for f in range(F_END + 1):
    sc.frame_set(f)
    g = bow_arm.matrix_world @ bpb["grip"].head
    c = world_to_camera_view(sc, cam, g)
    fx["grip"][f] = [c.x * W_, (1 - c.y) * H_, c.z]
(out / "fx.json").write_text(json.dumps(fx))

f0, f1 = (int(v) for v in a.frames.split("-"))
todo = [int(v) for v in a.only.split(",")] if a.only else list(range(f0, f1 + 1))
for f in todo:
    p = out / "frames" / f"{f:04d}.png"
    if p.exists():
        continue                                                      # resumable: finished frames are kept
    sc.frame_set(f)
    sc.render.filepath = str(p)
    bpy.ops.render.render(write_still=True)
    print("frame", f, flush=True)
print("done", len(todo), "frames", flush=True)

#!/usr/bin/env python3
"""Rig Karna for hand animation and pose him at full draw with the bow Vijaya. FREE, runs in the cloud (pip install bpy).

  python studio/tools/blender/karna_rig.py WORK.blend BOW.glb OUT_DIR [TAG]

  WORK.blend  made by karna_prepare.py (KARNA_body, 1.9 m, feet at z 0, front -Y, his left +X)
  BOW.glb     the TRELLIS.2 bow (string on +X, grip at -X, 1 unit tall)

Writes, never overwriting (TAG, for example _v2, is added to every name):
  OUT_DIR/karna_rigged.blend     Rigify control rig KARNA_rig, body skinned; the bow KARNA_bow on its own rig
                                 KARNA_bow_rig (grip, three bones per limb, a nock bone the string follows)
  OUT_DIR/karna_fulldraw.blend   the same file posed at full draw, limbs bent, for the Gate 4 previs
  OUT_DIR/fulldraw_<view>.png, fulldraw_sheet.jpg and fulldraw_hands.jpg   check renders

Weights: Blender's bone-heat solver fails on fused TRELLIS meshes (the Krishna rebuild hit this too), so every vertex
takes inverse-distance weights from its nearest deform bones, then the weights are smoothed along mesh edges. Two masks
follow: arm bones may not pull the cuirass (inside the shoulder joint the arm weight goes to the chest and shoulder bones,
so the gold edge stays put when the arm lifts), and finger bones may not pull the palm (behind the knuckles the finger
weight goes to the hand bone, so the palm stays solid when the fingers curl).
Joint positions were measured from slices of KARNA_body; they are constants below.
"""
import math, os, pathlib, sys

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
if len(argv) not in (3, 4):
    raise SystemExit(__doc__)
work, bow_glb, out_dir = (pathlib.Path(p).resolve() for p in argv[:3])
TAG = argv[3] if len(argv) == 4 else ""
out_dir.mkdir(parents=True, exist_ok=True)
for name in ("karna_rigged", "karna_fulldraw"):
    if (out_dir / f"{name}{TAG}.blend").exists():
        raise SystemExit(f"exists, not overwriting (folder law 1): {out_dir / name}{TAG}.blend")

# ---- joints of this body (metres; x = his left, -y = his front, z up) ----------------------------------------------
SPINE = ["spine", "spine.001", "spine.002", "spine.003", "spine.004", "spine.005", "spine.006"]
SPINE_Z = [1.00, 1.11, 1.23, 1.35, 1.50, 1.58, 1.66, 1.90]        # hips .. chest, neck, head base, crown
SPINE_Y = [0.00, 0.00, 0.00, 0.00, 0.00, -0.005, -0.01, -0.01]
SHOULDER = Vector((0.20, 0.0, 1.41))
ELBOW = Vector((0.332, -0.02, 1.172))                             # a little behind the shoulder-wrist line: a clean IK bend
WRIST = Vector((0.436, -0.06, 0.993))
HAND_TIP = Vector((0.473, -0.110, 0.803))                         # 0.20 m hand toward the TRELLIS fingertips (z 0.72)
HAND_K = (HAND_TIP - WRIST).length / 0.165                       # hand size against the first rig (radii were tuned there)
HIP = Vector((0.095, 0.0, 0.98))
KNEE = Vector((0.125, -0.01, 0.52))                               # a little in front of the hip-ankle line
ANKLE = Vector((0.15, 0.045, 0.09))
TOE_BASE = Vector((0.16, -0.09, 0.03))
TOE_TIP = Vector((0.17, -0.18, 0.02))

bpy.ops.preferences.addon_enable(module="rigify")
bpy.ops.wm.open_mainfile(filepath=str(work))
scene = bpy.context.scene
body = bpy.data.objects["KARNA_body"]


def select_only(*objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[-1]


# ---- 1. human metarig, fitted -------------------------------------------------------------------------------------------
bpy.ops.object.armature_human_metarig_add()
meta = bpy.context.object
meta.name = "metarig"
bpy.ops.object.mode_set(mode="EDIT")
eb = meta.data.edit_bones


def descendants(b):
    out = []
    for c in b.children:
        out += [c] + descendants(c)
    return out


doomed = set()
for root in ("face", "breast.L", "breast.R"):                      # his face moves by shape keys later, not bones
    if root in eb:
        doomed |= {root} | {b.name for b in descendants(eb[root])}
for n in doomed:
    eb.remove(eb[n])
connected = {b.name: b.use_connect for b in eb}
for b in eb:
    b.use_connect = False


def put(name, h, t):
    if name in eb:
        eb[name].head, eb[name].tail = h, t


for i, n in enumerate(SPINE):
    put(n, Vector((0, SPINE_Y[i], SPINE_Z[i])), Vector((0, SPINE_Y[i + 1], SPINE_Z[i + 1])))
hand = eb["hand.L"]
h0 = hand.head.copy()
tips = [b for b in descendants(hand) if b.name.startswith(("f_middle.03", "f_index.03", "f_ring.03", "f_pinky.03"))]
old = sum((b.tail for b in tips), Vector()) / len(tips) - h0
new = HAND_TIP - WRIST
rot = old.normalized().rotation_difference(new.normalized()).to_matrix()
sc = new.length / old.length
fingers = [(b.name, b.head.copy(), b.tail.copy()) for b in descendants(hand)]
for n, (h, t) in {
    "shoulder.L": (Vector((0.03, 0.0, 1.45)), SHOULDER),
    "upper_arm.L": (SHOULDER, ELBOW), "forearm.L": (ELBOW, WRIST),
    "hand.L": (WRIST, WRIST + new * 0.35),
    "pelvis.L": (Vector((0.0, 0.0, 1.0)), Vector((0.10, 0.0, 1.07))),
    "thigh.L": (HIP, KNEE), "shin.L": (KNEE, ANKLE), "foot.L": (ANKLE, TOE_BASE), "toe.L": (TOE_BASE, TOE_TIP),
    "heel.02.L": (Vector((0.20, 0.10, 0.0)), Vector((0.10, 0.10, 0.0))),
}.items():
    put(n, h, t)
for n, h, t in fingers:
    put(n, WRIST + (rot @ (h - h0)) * sc, WRIST + (rot @ (t - h0)) * sc)
for b in list(eb):                                                   # mirror his left to his right
    if b.name.endswith(".L") and b.name[:-2] + ".R" in eb:
        r = eb[b.name[:-2] + ".R"]
        r.head, r.tail, r.roll = Vector((-b.head.x, b.head.y, b.head.z)), Vector((-b.tail.x, b.tail.y, b.tail.z)), -b.roll
for b in eb:
    if connected.get(b.name):
        b.use_connect = True
bpy.ops.object.mode_set(mode="OBJECT")

# ---- 2. generate the control rig ---------------------------------------------------------------------------------------
select_only(meta)
bpy.ops.pose.rigify_generate()
rig = next(o for o in bpy.data.objects if o.type == "ARMATURE" and o is not meta)
rig.name = "KARNA_rig"
meta.hide_viewport = meta.hide_render = True
print("rig bones", len(rig.data.bones), flush=True)

# ---- 2b. new hands -----------------------------------------------------------------------------------------------------------
# TRELLIS made each hand one lump, so finger bones had nothing separate to bend. The lumps are cut off just past the wrist
# (under the bracer edge) and each hand is rebuilt along the rig's own palm, finger and thumb bones: a skin-modifier tube
# per bone chain, subdivided, then weighted segment by segment, so the fingers curl cleanly.
bones = rig.data.bones
bme = body.data
# TRELLIS splits the mesh at every UV seam (about 7900 loose pieces), so a raised arm tore open along the seams.
# Welding coincident vertices makes one connected skin; the UVs live on the face corners and are kept.
bm = bmesh.new()
bm.from_mesh(bme)
n0 = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
bm.to_mesh(bme)
print("welded seams:", n0, "->", len(bm.verts), "verts", flush=True)
bm.free()
tex_img = next(n.image for n in body.active_material.node_tree.nodes if n.type == "TEX_IMAGE" and "basecolor" in n.image.filepath)
TW, TH = tex_img.size
tpx = np.empty(TW * TH * 4, np.float32)
tex_img.pixels.foreach_get(tpx)
tpx = tpx.reshape(TH, TW, 4)
bco = np.empty(len(bme.vertices) * 3, np.float32)
bme.vertices.foreach_get("co", bco)
bco = bco.reshape(-1, 3)
cut = np.zeros(len(bco), bool)
for side, sx in (("L", 1), ("R", -1)):
    hb = bones[f"DEF-hand.{side}"]
    yhat = np.array(hb.matrix_local.col[1][:3])
    rel = bco - np.array(hb.head_local)
    t = rel @ yhat
    radial = np.linalg.norm(rel - t[:, None] * yhat[None], axis=1)
    cut |= (t > 0.012) & (radial < 0.16) & (bco[:, 0] * sx > 0.36)
lv = np.empty(len(bme.loops), np.int32)
bme.loops.foreach_get("vertex_index", lv)
luv = np.empty(len(bme.loops) * 2, np.float32)
bme.uv_layers.active.data.foreach_get("uv", luv)
luv = luv.reshape(-1, 2)
on = cut[lv]
samp = tpx[np.clip((luv[on, 1] * TH).astype(int), 0, TH - 1), np.clip((luv[on, 0] * TW).astype(int), 0, TW - 1), :3]
skin_srgb = np.median(samp, axis=0)
skin_lin = np.where(skin_srgb <= 0.04045, skin_srgb / 12.92, ((skin_srgb + 0.055) / 1.055) ** 2.4)
bm = bmesh.new()
bm.from_mesh(bme)
bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[int(i)] for i in np.nonzero(cut)[0]], context="VERTS")
bm.to_mesh(bme)
bm.free()
print("cut the lump hands:", int(cut.sum()), "verts; skin colour", np.round(skin_srgb, 3), flush=True)

skin_m = bpy.data.materials.new("KARNA_hand_skin")
skin_m.use_nodes = True
snt = skin_m.node_tree
bsdf = snt.nodes["Principled BSDF"]
bsdf.inputs["Roughness"].default_value = 0.62
noise = snt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 60.0
ramp = snt.nodes.new("ShaderNodeValToRGB")                           # painted variation, a little darker in the creases
ramp.color_ramp.elements[0].color = (*(skin_lin * 0.88), 1)
ramp.color_ramp.elements[1].color = (*(skin_lin * 1.18), 1)
snt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
snt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

FINGER_R = {"f_index": 1.0, "f_middle": 1.04, "f_ring": 0.96, "f_pinky": 0.84}


def tube(name, pts, rads):
    """one tapered finger: a skin-modifier tube along the points, subdivided"""
    me_ = bpy.data.meshes.new(name)
    me_.from_pydata([tuple(p_) for p_ in pts], [(i, i + 1) for i in range(len(pts) - 1)], [])
    ob = bpy.data.objects.new(name, me_)
    scene.collection.objects.link(ob)
    ob.modifiers.new("skin", "SKIN")
    for i, r in enumerate(rads):
        sv = me_.skin_vertices[0].data[i]
        sv.radius = (r, r)
        sv.use_root = i == 0
    ob.modifiers.new("sub", "SUBSURF").levels = 2
    select_only(ob)
    bpy.ops.object.modifier_apply(modifier="skin")
    bpy.ops.object.modifier_apply(modifier="sub")
    return ob


def weigh(ob, bone_names, power=6):
    """each vertex to its nearest one or two of the given bones, sharply, so each segment moves as a unit"""
    bl = [bones[n] for n in bone_names]
    hh = np.array([list(b.head_local) for b in bl], np.float32)
    ht = np.array([list(b.tail_local) for b in bl], np.float32)
    hs = ht - hh
    n_ = len(ob.data.vertices)
    c_ = np.empty(n_ * 3, np.float32)
    ob.data.vertices.foreach_get("co", c_)
    c_ = c_.reshape(-1, 3) @ np.array(ob.matrix_world.to_3x3()).T + np.array(ob.matrix_world.translation)
    rel = c_[:, None] - hh[None]
    tt = np.clip((rel * hs[None]).sum(2) / np.maximum((hs ** 2).sum(1), 1e-8)[None], 0, 1)
    dd = np.linalg.norm(rel - tt[..., None] * hs[None], axis=2)
    k = min(2, len(bl))
    idx = np.argsort(dd, axis=1)[:, :k]
    ww = 1 / (np.take_along_axis(dd, idx, 1) + 0.002) ** power
    ww /= ww.sum(1, keepdims=True)
    groups = {n: ob.vertex_groups.new(name=n) for n in bone_names}
    for vi in range(n_):
        for j in range(k):
            if ww[vi, j] > 0.01:
                groups[bone_names[idx[vi, j]]].add([vi], float(ww[vi, j]), "REPLACE")


hands = []
for side in ("L", "R"):
    def h(n):
        return Vector(bones[f"ORG-{n}.{side}"].head_local)

    def tl(n):
        return Vector(bones[f"ORG-{n}.{side}"].tail_local)

    hb = bones[f"DEF-hand.{side}"]
    wrist = Vector(hb.head_local)
    knuck = [h(f"{f}.01") for f in FINGER_R]
    kc = sum(knuck, Vector()) / 4
    hy = (kc - wrist).normalized()                                   # along the palm
    hx = knuck[3] - knuck[0]
    hx = (hx - hy * hx.dot(hy)).normalized()                          # index to pinky
    hz = hx.cross(hy)                                                 # through the palm
    if hz.dot(h("thumb.02") - wrist) < 0:                             # palm side = thumb side
        hz = -hz
    plen = (kc - wrist).length
    pw = (knuck[3] - knuck[0]).length + 0.026 * HAND_K                # palm a little wider than the knuckle row
    parts = []
    # palm: a rounded block from inside the bracer to the knuckles, thicker at the heel of the hand
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    palm = bpy.context.object
    palm.name = f"palm_{side}"
    M = Matrix((hx, hy, hz)).transposed().to_4x4()
    M.translation = wrist + hy * (plen * 0.45) + hz * (0.004 * HAND_K)
    palm.matrix_world = M @ Matrix.Diagonal((pw, plen * 1.2, 0.029 * HAND_K, 1))
    bv = palm.modifiers.new("bev", "BEVEL")
    bv.width, bv.segments = 0.45, 3
    bv.offset_type = "PERCENT"
    bv.width_pct = 28
    palm.modifiers.new("sub", "SUBSURF").levels = 2
    select_only(palm)
    bpy.ops.object.modifier_apply(modifier="bev")
    bpy.ops.object.modifier_apply(modifier="sub")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    weigh(palm, [f"DEF-hand.{side}"] + [f"DEF-palm.0{k}.{side}" for k in range(1, 5)], power=3)
    parts.append(palm)
    # wrist collar: fills the cut opening under the bracer
    w_ = tube(f"wrist_{side}", [wrist - hy * 0.03, wrist + hy * 0.012], [0.031, 0.029])
    weigh(w_, [f"DEF-hand.{side}", f"DEF-forearm.01.{side}" if f"DEF-forearm.01.{side}" in bones else f"DEF-forearm.{side}"], power=3)
    parts.append(w_)
    for k, (f, sc_) in enumerate(FINGER_R.items()):
        pts = [h(f"{f}.01") - hy * 0.012, h(f"{f}.02"), h(f"{f}.03"), tl(f"{f}.03")]
        o = tube(f"{f}_{side}", pts, [r * sc_ * HAND_K * 1.15 for r in (0.0098, 0.0090, 0.0081, 0.0066)])
        weigh(o, [f"DEF-{f}.01.{side}", f"DEF-{f}.02.{side}", f"DEF-{f}.03.{side}"])
        parts.append(o)
    o = tube(f"thumb_{side}", [h("thumb.01"), h("thumb.02"), h("thumb.03"), tl("thumb.03")],
             [r * HAND_K * 1.1 for r in (0.0140, 0.0110, 0.0095, 0.0078)])
    weigh(o, [f"DEF-thumb.01.{side}", f"DEF-thumb.02.{side}", f"DEF-thumb.03.{side}"])
    parts.append(o)
    select_only(*parts)
    bpy.ops.object.join()
    ho = bpy.context.object
    ho.name = f"KARNA_hand.{side}"
    bpy.ops.object.shade_smooth()
    ho.data.materials.clear()
    ho.data.materials.append(skin_m)
    ho.parent = rig
    ho.modifiers.new("Armature", "ARMATURE").object = rig
    hands.append(ho)
    print("new hand", side, len(ho.data.polygons), "faces", flush=True)

# ---- 3. skin weights ---------------------------------------------------------------------------------------------------------
defs = [b for b in rig.data.bones if b.name.startswith("DEF-")]
heads = np.array([list(b.head_local) for b in defs], np.float32)
tails = np.array([list(b.tail_local) for b in defs], np.float32)
seg = tails - heads
seg2 = np.maximum((seg ** 2).sum(1), 1e-8)
nv = len(body.data.vertices)
co = np.empty(nv * 3, np.float32)
body.data.vertices.foreach_get("co", co)
co = co.reshape(nv, 3)
W = np.zeros((nv, len(defs)), np.float32)
for s0 in range(0, nv, 20000):
    p = co[s0:s0 + 20000]
    rel = p[:, None] - heads[None]
    t = np.clip((rel * seg[None]).sum(2) / seg2[None], 0, 1)
    d = np.linalg.norm(rel - t[..., None] * seg[None], axis=2)
    idx = np.argpartition(d, 4, axis=1)[:, :4]
    wn = 1 / (np.take_along_axis(d, idx, 1) + 0.015) ** 2.5
    W[s0:s0 + 20000][np.arange(len(p))[:, None], idx] = wn / wn.sum(1, keepdims=True)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


names = [b.name for b in defs]
col = {n: i for i, n in enumerate(names)}
ARM = np.array([any(k in n for k in ("upper_arm", "forearm", "hand", "f_", "thumb", "palm")) for n in names])
FINGER = np.array([n.startswith(("DEF-f_", "DEF-palm")) for n in names])
# shoulder mask: inside |x| 0.18 the arm bones let go; what they held goes to the chest and shoulder bones
m = smoothstep(0.18, 0.25, np.abs(co[:, 0]))
for side, sx in (("L", 1), ("R", -1)):
    near = (co[:, 0] * sx > 0)
    lost = (W[:, ARM] * (1 - m)[:, None]).sum(1) * near
    W[np.ix_(near, ARM)] *= m[near, None]
    W[:, col["DEF-spine.003"]] += lost * 0.6
    W[:, col[f"DEF-shoulder.{side}"]] += lost * 0.4
# palm mask: behind the knuckle line the finger bones let go; the hand bone takes it
for side in ("L", "R"):
    hb = rig.data.bones[f"DEF-hand.{side}"]
    yhat = np.array(hb.matrix_local.col[1][:3])
    knuckle = float(np.dot(np.array(rig.data.bones[f"DEF-f_middle.01.{side}"].head_local) - np.array(hb.head_local), yhat))
    t = (co - np.array(hb.head_local)) @ yhat
    fm = smoothstep(knuckle - 0.02, knuckle + 0.005, t)
    hand_zone = (co[:, 0] * (1 if side == "L" else -1) > 0.36)
    lost = (W[:, FINGER] * (1 - fm)[:, None]).sum(1) * hand_zone
    W[np.ix_(hand_zone, FINGER)] *= fm[hand_zone, None]
    W[:, col[f"DEF-hand.{side}"]] += lost
ev = np.empty(len(body.data.edges) * 2, np.int32)
body.data.edges.foreach_get("vertices", ev)
ev = ev.reshape(-1, 2)
deg = np.maximum(np.bincount(ev.ravel(), minlength=nv), 1).astype(np.float32)
for _ in range(6):
    acc = np.zeros_like(W)
    np.add.at(acc, ev[:, 0], W[ev[:, 1]])
    np.add.at(acc, ev[:, 1], W[ev[:, 0]])
    W = 0.5 * W + 0.5 * acc / deg[:, None]
top = np.argpartition(-W, 4, axis=1)[:, :4]
K = np.zeros_like(W)
rows = np.arange(nv)[:, None]
K[rows, top] = W[rows, top]
K /= np.maximum(K.sum(1, keepdims=True), 1e-8)
for vg in list(body.vertex_groups):
    body.vertex_groups.remove(vg)
for b in defs:
    body.vertex_groups.new(name=b.name)
bm = bmesh.new()
bm.from_mesh(body.data)
dl = bm.verts.layers.deform.verify()
bm.verts.ensure_lookup_table()
for v, g in zip(*np.nonzero(K > 0.01)):
    bm.verts[int(v)][dl][int(g)] = float(K[v, g])
bm.to_mesh(body.data)
bm.free()
body.modifiers.new("Armature", "ARMATURE").object = rig
body.parent = rig
print("skinned", nv, "verts to", len(defs), "deform bones", flush=True)

# ---- 4. the bow Vijaya: decimated, its straight string cut out, held by its grip in his left hand -------------------------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(bow_glb))
bow = next(o for o in set(bpy.data.objects) - before if o.type == "MESH")
for o in set(bpy.data.objects) - before - {bow}:
    bpy.data.objects.remove(o)
bow.name = "KARNA_bow"
bm = bmesh.new()
bm.from_mesh(bow.data)
cut = [v for v in bm.verts if v.co.x > 0.100 and abs(v.co.z) < 0.38]    # the string: a thin rod at x 0.1035
bmesh.ops.delete(bm, geom=cut, context="VERTS")
bm.to_mesh(bow.data)
bm.free()
select_only(bow)
dec = bow.modifiers.new("dec", "DECIMATE")
dec.ratio = 0.2
bpy.ops.object.modifier_apply(modifier="dec")
BOW_H = 1.70                                                         # a great bow, a little shorter than he is
bow.scale = (BOW_H,) * 3
select_only(bow)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)   # bow space is now metres
BOW_GRIP = Vector((-0.044, 0.0, 0.0)) * BOW_H                        # middle of the handle (z -0.04..0.04)
STRING_X = 0.1035 * BOW_H
print("bow faces", len(bow.data.polygons), flush=True)

# bow rig: a grip bone, three bones down the middle of each limb, and a nock bone at the middle of the string
bn = len(bow.data.vertices)
bco = np.empty(bn * 3, np.float32)
bow.data.vertices.foreach_get("co", bco)
bco = bco.reshape(bn, 3)


def limb_x(z):
    """middle of the limb at height z (bow space, metres), from the mesh itself"""
    sl = bco[(np.abs(bco[:, 2] - z) < 0.012) & (bco[:, 0] < STRING_X - 0.01)]
    return float(np.median(sl[:, 0])) if len(sl) else float(BOW_GRIP.x)


LIMB_Z = [0.045, 0.20, 0.34, 0.47]                                   # joints up a limb, as a share of the bow height
bow_arm = bpy.data.objects.new("KARNA_bow_rig", bpy.data.armatures.new("KARNA_bow_rig"))
scene.collection.objects.link(bow_arm)
select_only(bow_arm)
bpy.ops.object.mode_set(mode="EDIT")
be = bow_arm.data.edit_bones
grip = be.new("grip")
grip.head, grip.tail = BOW_GRIP, BOW_GRIP + Vector((-0.08, 0, 0))   # points at the target
for tag, sz in (("up", 1), ("lo", -1)):
    parent = grip
    for i in range(3):
        z0, z1 = sz * LIMB_Z[i] * BOW_H, sz * LIMB_Z[i + 1] * BOW_H
        e = be.new(f"limb_{tag}.{i + 1:02d}")
        e.head, e.tail = Vector((limb_x(z0), 0, z0)), Vector((limb_x(z1), 0, z1))
        e.parent, e.use_connect = parent, i > 0
        parent = e
nock = be.new("nock")
nock.head, nock.tail, nock.parent = Vector((STRING_X, 0, 0)), Vector((STRING_X + 0.06, 0, 0)), grip
bpy.ops.object.mode_set(mode="OBJECT")
bdefs = [b for b in bow_arm.data.bones if b.name != "nock"]
bh = np.array([list(b.head_local) for b in bdefs], np.float32)
bt = np.array([list(b.tail_local) for b in bdefs], np.float32)
bs = bt - bh
rel = bco[:, None] - bh[None]
tt = np.clip((rel * bs[None]).sum(2) / np.maximum((bs ** 2).sum(1), 1e-8)[None], 0, 1)
bd = np.linalg.norm(rel - tt[..., None] * bs[None], axis=2)
bw = 1 / (bd + 0.01) ** 4
bw[:, 0] = np.where(np.abs(bco[:, 2]) < 0.035 * BOW_H, 1e6, 0.0)       # the handle is rigid on the grip bone
bw /= bw.sum(1, keepdims=True)
for i, b in enumerate(bdefs):
    g = bow.vertex_groups.new(name=b.name)
    for v in np.nonzero(bw[:, i] > 0.01)[0]:
        g.add([int(v)], float(bw[v, i]), "REPLACE")
bow.parent = bow_arm
bow.modifiers.new("Armature", "ARMATURE").object = bow_arm


def material(name, rgb, metal, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1)
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough
    return m


string_m = material("bowstring", (0.78, 0.70, 0.52), 0.0, 0.6)
for tag, sz in (("top", 1), ("bottom", -1)):                          # the string: tip end rides the limb, other end the nock
    a_, b_ = Vector((STRING_X, 0, sz * 0.385 * BOW_H)), Vector((STRING_X, 0, 0))
    d = b_ - a_
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.0028, depth=d.length, location=(a_ + b_) / 2)
    st = bpy.context.object
    st.name = f"KARNA_bowstring_{tag}"
    st.data.materials.append(string_m)
    select_only(st)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    gt, gn = st.vertex_groups.new(name=f"limb_{'up' if sz > 0 else 'lo'}.03"), st.vertex_groups.new(name="nock")
    for v in st.data.vertices:
        (gt if abs(v.co.z) > 0.1 else gn).add([v.index], 1.0, "REPLACE")
    st.parent = bow_arm
    st.modifiers.new("Armature", "ARMATURE").object = bow_arm
print("bow rig: grip, 2 x 3 limb bones, nock", flush=True)

rig.hide_render = True
select_only(rig)
bpy.ops.wm.save_as_mainfile(filepath=str(out_dir / f"karna_rigged{TAG}.blend"), relative_remap=True)
print("saved", out_dir / f"karna_rigged{TAG}.blend", flush=True)

# ---- 5. full-draw pose -----------------------------------------------------------------------------------------------------------
# The arrow flies toward his left (+X). Bow arm straight out at shoulder height, draw hand anchored under the right jaw,
# head turned to the target, chest opened a little toward the camera, feet stay planted.
pb = rig.pose.bones
for n in ("upper_arm_parent.L", "upper_arm_parent.R"):
    pb[n]["IK_FK"] = 0.0                                             # arms on IK
    pb[n]["pole_vector"] = True                                        # the elbow follows its pole control
bpy.context.view_layer.update()


def world_rotate(name, axis, deg, pivot=None):
    b = pb[name]
    piv = b.head if pivot is None else pivot
    b.matrix = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-piv) @ b.matrix
    bpy.context.view_layer.update()


def move_to(name, loc):
    m = pb[name].matrix.copy()
    m.translation = loc
    pb[name].matrix = m
    bpy.context.view_layer.update()


world_rotate("torso", "Z", -10)                                      # chest stays square to camera, a touch toward the draw side
world_rotate("chest", "Y", -4)                                       # leans a touch away from the bow side
world_rotate("head", "Z", 72)                                        # looks along the arrow to his left (about 62 deg net)
ARROW = Vector((1.0, 0.0, -0.12)).normalized()                       # flight line, a little downhill from the anchor
NOCK = Vector((-0.015, -0.105, 1.60))                                # string anchor at the corner of his jaw; his face stays clear toward the target
BOW_WRIST = Vector((0.64, -0.06, 1.49))                              # bow arm almost straight at shoulder height
DRAW_WRIST = NOCK - ARROW * 0.085 * HAND_K                                    # the hooked fingers sit on the string, wrist behind it


def orient_hand(ctrl, side, fwd, up):
    """turn an IK hand so its length points along fwd and its index-to-pinky line stands along up (knuckles vertical)"""
    rest = rig.data.bones[f"DEF-hand.{side}"].matrix_local.to_3x3()
    bones = rig.data.bones
    y0 = rest.col[1].normalized()
    v0 = bones[f"ORG-f_index.01.{side}"].head_local - bones[f"ORG-f_pinky.01.{side}"].head_local
    v0 = (v0 - y0 * v0.dot(y0)).normalized()
    A = Matrix((y0, v0, y0.cross(v0))).transposed()
    y1 = fwd.normalized()
    v1 = (up - y1 * up.dot(y1)).normalized()
    B = Matrix((y1, v1, y1.cross(v1))).transposed()
    m = ((B @ A.transposed()) @ rest).to_4x4()
    m.translation = pb[ctrl].matrix.translation
    pb[ctrl].matrix = m
    bpy.context.view_layer.update()


move_to("hand_ik.L", BOW_WRIST)
move_to("upper_arm_ik_target.L", Vector((0.42, 0.35, 1.30)))         # bow elbow rolled down and out, clear of the string
move_to("hand_ik.R", DRAW_WRIST)
move_to("upper_arm_ik_target.R", Vector((-0.60, -0.05, 1.80)))       # draw elbow high and back, in line with the arrow
orient_hand("hand_ik.L", "L", ARROW, Vector((0, 0, 1)))
orient_hand("hand_ik.R", "R", ARROW, Vector((0, 0, 1)))
# curl: the palm is on the hand's +Z side in this rig, so fingers close by turning about the hand's X axis
# (positive on the left hand, negative on the mirrored right hand)
for side, sign, angs in (("L", 1, (75, 85, 60)), ("R", -1, (40, 80, 60))):   # fist on the grip; a hook on the string
    for f in ("f_index", "f_middle", "f_ring", "f_pinky"):
        for k, ang in zip(("01", "02", "03"), angs):
            n = f"{f}.{k}.{side}"
            if n in pb:
                axis = pb[f"DEF-hand.{side}"].matrix.col[0].xyz.normalized()
                world_rotate(n, axis, sign * ang)

# bow into the left fist, limbs vertical, string side toward him (bow space -X turned to world +X)
hm = pb["DEF-hand.L"].matrix
grip_world = rig.matrix_world @ (hm.translation + hm.col[1].xyz * 0.075 * HAND_K + hm.col[2].xyz * 0.022 * HAND_K)
R = Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Rotation(math.radians(-6), 4, "X")   # a slight cant, as archers hold it
bow_arm.matrix_world = Matrix.Translation(grip_world) @ R @ Matrix.Translation(-BOW_GRIP)
bpy.context.view_layer.update()
# full draw: limbs bend toward him (bow space +X), more toward the tips; the nock comes back to the anchor
bpb = bow_arm.pose.bones
BEND = (4.0, 6.0, 7.0)
for tag, sz in (("up", 1), ("lo", -1)):
    for i, deg in enumerate(BEND):
        b = bpb[f"limb_{tag}.{i + 1:02d}"]
        piv = b.head.copy()
        b.matrix = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(sz * deg), 4, "Y") @ Matrix.Translation(-piv) @ b.matrix
        bpy.context.view_layer.update()
nm = bpb["nock"].matrix.copy()
nm.translation = bow_arm.matrix_world.inverted() @ NOCK
bpb["nock"].matrix = nm
bpy.context.view_layer.update()
nock = NOCK
tip_up = bow_arm.matrix_world @ bpb["limb_up.03"].tail
print("bow tip moved toward him by %.3f m" % ((bow_arm.matrix_world @ bow_arm.data.bones["limb_up.03"].tail_local) - tip_up).length, flush=True)


def rod(name, a, b, r, mat):
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=r, depth=d.length, location=(a + b) / 2)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(mat)
    return o


shaft_m = material("arrow_shaft", (0.10, 0.07, 0.05), 0.0, 0.5)
gold_m = material("arrow_gold", (0.95, 0.66, 0.24), 1.0, 0.3)
rest_pt = grip_world + Vector((0, 0, 0.045))                        # the arrow rests on top of the fist
aim = (rest_pt - nock).normalized()
head_at = rest_pt + aim * 0.16
rod("KARNA_arrow", nock - aim * 0.02, head_at, 0.0055, shaft_m)
bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.016, depth=0.07, location=head_at + aim * 0.035)
ah = bpy.context.object
ah.name = "KARNA_arrowhead"
ah.rotation_euler = aim.to_track_quat("Z", "Y").to_euler()
ah.data.materials.append(gold_m)
print("bow hand", tuple(round(v, 3) for v in grip_world), "nock", tuple(round(v, 3) for v in nock),
      "draw length %.2f m" % (grip_world - nock).length, flush=True)

bpy.ops.wm.save_as_mainfile(filepath=str(out_dir / f"karna_fulldraw{TAG}.blend"), relative_remap=True)
print("saved", out_dir / f"karna_fulldraw{TAG}.blend", flush=True)

# ---- 6. check renders (same light as turntable.py) ------------------------------------------------------------------------
sc = scene
sc.render.engine = "CYCLES"
sc.cycles.samples = 32
sc.cycles.device = "CPU"
sc.render.resolution_x, sc.render.resolution_y = 900, 900
sc.view_settings.view_transform = "AgX"
w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.52, 0.48, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
bpy.ops.mesh.primitive_plane_add(size=80)
floor = bpy.context.object
floor.data.materials.append(material("floor", (0.42, 0.38, 0.33), 0.0, 0.8))
for name, energy, color, rot in (("key", 3.2, (1.0, 0.86, 0.68), (50, 0, -35)), ("rim", 2.4, (0.62, 0.74, 1.0), (60, 0, 160))):
    d = bpy.data.lights.new(name, "SUN")
    d.energy, d.color = energy, color
    o = bpy.data.objects.new(name, d)
    sc.collection.objects.link(o)
    o.rotation_euler = [math.radians(r) for r in rot]
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 50
tgt = Vector((0.22, 0, 1.15))
paths = []
for label, ang in (("front", 0), ("target_side", 70), ("back34", 200), ("left_rear", 300)):
    a = math.radians(ang)
    cam.location = tgt + Vector((math.sin(a) * 4.6, -math.cos(a) * 4.6, 0.25))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = str(out_dir / f"fulldraw{TAG}_{label}.png")
    bpy.ops.render.render(write_still=True)
    paths.append(sc.render.filepath)

from PIL import Image
ims = [Image.open(p).convert("RGB") for p in paths]
sheet = Image.new("RGB", (sum(i.width for i in ims), ims[0].height))
for k, im in enumerate(ims):
    sheet.paste(im, (k * im.width, 0))
sheet.save(out_dir / f"fulldraw{TAG}_sheet.jpg", quality=88)
print("wrote", out_dir / f"fulldraw{TAG}_sheet.jpg", flush=True)

# close-ups: the bow hand, the draw hand at his jaw, the draw shoulder from behind
sc.render.resolution_x, sc.render.resolution_y = 700, 700
cam.data.lens = 85
close = []
for label, look, frm in (("bowhand", grip_world, Vector((0.25, -1.3, 0.10))),
                         ("anchor", NOCK + Vector((-0.08, 0, 0.02)), Vector((-0.15, -1.3, 0.05))),
                         ("shoulder", Vector((-0.22, 0.0, 1.50)), Vector((-0.75, 1.0, 0.25)))):
    cam.location = look + frm
    cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = str(out_dir / f"fulldraw{TAG}_{label}.png")
    bpy.ops.render.render(write_still=True)
    close.append(Image.open(sc.render.filepath).convert("RGB"))
row = Image.new("RGB", (sum(i.width for i in close), close[0].height))
for k, im in enumerate(close):
    row.paste(im, (k * im.width, 0))
row.save(out_dir / f"fulldraw{TAG}_hands.jpg", quality=88)
print("wrote", out_dir / f"fulldraw{TAG}_hands.jpg", flush=True)

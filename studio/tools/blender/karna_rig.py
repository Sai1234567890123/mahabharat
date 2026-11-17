#!/usr/bin/env python3
"""Rig Karna for hand animation and pose him at full draw with the bow Vijaya. FREE, runs in the cloud (pip install bpy).

  python studio/tools/blender/karna_rig.py WORK.blend BOW.glb OUT_DIR

  WORK.blend  made by karna_prepare.py (KARNA_body, 1.9 m, feet at z 0, front -Y, his left +X)
  BOW.glb     the TRELLIS.2 bow (string on +X, grip at -X, 1 unit tall)

Writes, never overwriting:
  OUT_DIR/karna_rigged.blend     Rigify control rig KARNA_rig, body skinned, the bow as KARNA_bow (rest pose)
  OUT_DIR/karna_fulldraw.blend   the same file posed at full draw, for the Gate 4 previs
  OUT_DIR/fulldraw_<view>.png and fulldraw_sheet.jpg   check renders

Weights: Blender's bone-heat solver fails on fused TRELLIS meshes (the Krishna rebuild hit this too), so every vertex
takes inverse-distance weights from its nearest deform bones, then the weights are smoothed along mesh edges.
Joint positions were measured from slices of KARNA_body; they are constants below.
"""
import math, os, pathlib, sys

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
if len(argv) != 3:
    raise SystemExit(__doc__)
work, bow_glb, out_dir = (pathlib.Path(p).resolve() for p in argv)
out_dir.mkdir(parents=True, exist_ok=True)
for name in ("karna_rigged.blend", "karna_fulldraw.blend", "fulldraw_sheet.jpg"):
    if (out_dir / name).exists():
        raise SystemExit(f"exists, not overwriting (folder law 1): {out_dir / name}")

# ---- joints of this body (metres; x = his left, -y = his front, z up) ----------------------------------------------
SPINE = ["spine", "spine.001", "spine.002", "spine.003", "spine.004", "spine.005", "spine.006"]
SPINE_Z = [1.00, 1.11, 1.23, 1.35, 1.50, 1.58, 1.66, 1.90]        # hips .. chest, neck, head base, crown
SPINE_Y = [0.00, 0.00, 0.00, 0.00, 0.00, -0.005, -0.01, -0.01]
SHOULDER = Vector((0.20, 0.0, 1.41))
ELBOW = Vector((0.332, -0.02, 1.172))                             # a little behind the shoulder-wrist line: a clean IK bend
WRIST = Vector((0.436, -0.06, 0.993))
HAND_TIP = Vector((0.515, -0.111, 0.857))
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
BOW_GRIP = Vector((-0.044, 0.0, 0.0)) * BOW_H                        # middle of the handle (z -0.04..0.04), bow space, scaled
BOW_TIPS = [Vector((0.1035, 0.0, z)) * BOW_H for z in (0.40, -0.40)]  # where the string met the limbs
bow.scale = (BOW_H,) * 3
bow.rotation_euler = (0, 0, 0)
bow.location = (0, 0, 0)
print("bow faces", len(bow.data.polygons), flush=True)

rig.hide_render = True
select_only(rig)
bpy.ops.wm.save_as_mainfile(filepath=str(out_dir / "karna_rigged.blend"), relative_remap=True)
print("saved", out_dir / "karna_rigged.blend", flush=True)

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
NOCK = Vector((0.03, -0.115, 1.62))                                  # string anchor at the side of his jaw, below the eye
BOW_WRIST = Vector((0.64, -0.06, 1.49))                              # bow arm almost straight at shoulder height
DRAW_WRIST = NOCK - ARROW * 0.085                                    # the hooked fingers sit on the string, wrist behind it


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

# bow into the left fist, limbs vertical, string side toward him (bow local -X turned to world +X)
hand_def = pb["DEF-hand.L"] if "DEF-hand.L" in pb else pb["hand_ik.L"]
hm = hand_def.matrix
grip_world = rig.matrix_world @ (hm.translation + hm.col[1].xyz * 0.075 + hm.col[2].xyz * 0.022)
R = Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Rotation(math.radians(-6), 4, "X")   # a slight cant, as archers hold it
bow.matrix_world = Matrix.Translation(grip_world) @ R @ Matrix.Translation(-BOW_GRIP) @ Matrix.Diagonal((BOW_H, BOW_H, BOW_H, 1))
bpy.context.view_layer.update()
bow_m = Matrix.Translation(grip_world) @ R @ Matrix.Translation(-BOW_GRIP)
tips = [bow_m @ t for t in BOW_TIPS]
draw_def = pb["DEF-hand.R"] if "DEF-hand.R" in pb else pb["hand_ik.R"]
nock = NOCK


def rod(name, a, b, r, mat):
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=r, depth=d.length, location=(a + b) / 2)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(mat)
    return o


def material(name, rgb, metal, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1)
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough
    return m


string_m = material("bowstring", (0.78, 0.70, 0.52), 0.0, 0.6)
shaft_m = material("arrow_shaft", (0.10, 0.07, 0.05), 0.0, 0.5)
gold_m = material("arrow_gold", (0.95, 0.66, 0.24), 1.0, 0.3)
rod("KARNA_bowstring_top", tips[0], nock, 0.0028, string_m)
rod("KARNA_bowstring_bottom", nock, tips[1], 0.0028, string_m)
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

bpy.ops.wm.save_as_mainfile(filepath=str(out_dir / "karna_fulldraw.blend"), relative_remap=True)
print("saved", out_dir / "karna_fulldraw.blend", flush=True)

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
    sc.render.filepath = str(out_dir / f"fulldraw_{label}.png")
    bpy.ops.render.render(write_still=True)
    paths.append(sc.render.filepath)

from PIL import Image
ims = [Image.open(p).convert("RGB") for p in paths]
sheet = Image.new("RGB", (sum(i.width for i in ims), ims[0].height))
for k, im in enumerate(ims):
    sheet.paste(im, (k * im.width, 0))
sheet.save(out_dir / "fulldraw_sheet.jpg", quality=88)
print("wrote", out_dir / "fulldraw_sheet.jpg", flush=True)

"""Fit the Rigify metarig to the Krishna body, generate the rig, skin the meshes (headless Blender).

Usage:
  blender -b --python scripts/rig_skin.py -- IN.blend OUT.blend [PREVIEW_DIR]

What it does:
  1. Enables Rigify and opens IN.blend (made by head_join / head_fix / head_polish / face_project /
     chest_project; it holds KRISHNA_body, KRISHNA_head, KRISHNA_feather, KRISHNA_feather_quill and
     a default `metarig`).
  2. Deletes the face and breast bones from the metarig (the face is driven by shape keys),
     moves the spine, arm and leg chains to this body's joints, and fits the finger chains to the hand
     with one rotation and scale.  Mirrors left to right.
  3. Generates the control rig with Rigify (named KRISHNA_rig).
  4. Skins the body: weights are computed with automatic weights on a decimated copy and
     transferred to the full-resolution mesh; head, feather and quill are weighted 1.0 to the head bone.
  5. Saves OUT.blend and, with PREVIEW_DIR, renders a rest pose and a test pose
     (raised arm, bent knee, head turn).

Joint positions are for this character (1.75 m, A-pose, +X is the character's left). They are
constants near the top so another character only needs new numbers.
"""

import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
if len(argv) < 2:
    raise SystemExit("usage: blender -b --python rig_skin.py -- IN.blend OUT.blend [PREVIEW_DIR]")
in_blend, out_blend = argv[0], argv[1]
preview_dir = argv[2] if len(argv) > 2 else None

# ---- joint positions for this character (x right of the character's left, y forward is -Y, z up) ----
SPINE_NAMES = ["spine", "spine.001", "spine.002", "spine.003", "spine.004", "spine.005", "spine.006"]
SPINE_Z = [0.98, 1.07, 1.17, 1.27, 1.36, 1.405, 1.45, 1.80]  # joint heights along the spine, up to the head tip
SPINE_Y = [0.020, 0.012, 0.005, 0.000, 0.000, 0.002, 0.006, 0.012]
SHOULDER = Vector((0.17, 0.0, 1.34))
ELBOW = Vector((0.27, -0.010, 1.065))
WRIST = Vector((0.394, -0.050, 0.830))
HAND_TIP = Vector((0.450, -0.080, 0.700))
HIP = Vector((0.085, 0.0, 0.97))
KNEE = Vector((0.080, -0.010, 0.52))
ANKLE = Vector((0.085, 0.015, 0.085))
TOE_BASE = Vector((0.090, -0.090, 0.030))
TOE_TIP = Vector((0.090, -0.150, 0.020))

bpy.ops.preferences.addon_enable(module="rigify")
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
scene = bpy.context.scene
meta = bpy.data.objects["metarig"]
body = bpy.data.objects["KRISHNA_body"]
head = bpy.data.objects["KRISHNA_head"]
feather = bpy.data.objects["KRISHNA_feather"]
quill = bpy.data.objects.get("KRISHNA_feather_quill")

# ---- 1. clean the metarig -----------------------------------------------------------------------------
bpy.ops.object.select_all(action="DESELECT")
meta.select_set(True)
bpy.context.view_layer.objects.active = meta
bpy.ops.object.mode_set(mode="EDIT")
eb = meta.data.edit_bones


def descendants(bone):
    out = []
    for c in bone.children:
        out.append(c)
        out.extend(descendants(c))
    return out


doomed = set()
for root in ("face", "breast.L", "breast.R"):
    if root in eb:
        doomed.add(root)
        doomed.update(b.name for b in descendants(eb[root]))
for name in doomed:
    eb.remove(eb[name])
print("RIG removed bones:", len(doomed), "left:", len(eb), flush=True)

# remember connectivity, then free every bone so positions can be set independently
connected = {b.name: b.use_connect for b in eb}
for b in eb:
    b.use_connect = False


def set_bone(name, head, tail):
    if name in eb:
        eb[name].head = head
        eb[name].tail = tail


# spine chain: each tail is exactly the next head, so Rigify sees a continuous chain
for i, name in enumerate(SPINE_NAMES):
    set_bone(name, Vector((0.0, SPINE_Y[i], SPINE_Z[i])), Vector((0.0, SPINE_Y[i + 1], SPINE_Z[i + 1])))
# hands: remember the default hand frame before moving the arm
hand_def = eb["hand.L"]
hand_head0 = hand_def.head.copy()
tips = [b for b in descendants(hand_def) if b.name.startswith(("f_middle.03", "f_index.03", "f_ring.03", "f_pinky.03"))]
tip0 = sum((b.tail for b in tips), Vector()) / max(len(tips), 1)
old_vec = tip0 - hand_head0
hand_desc = [(b.name, b.head.copy(), b.tail.copy(), b.roll) for b in descendants(hand_def)]
new_vec = HAND_TIP - WRIST
rot = old_vec.normalized().rotation_difference(new_vec.normalized()).to_matrix()
sc = new_vec.length / max(old_vec.length, 1e-6)
print("HAND scale %.3f" % sc, flush=True)

side_bones = {
    "shoulder.L": (Vector((0.030, 0.0, 1.355)), SHOULDER),
    "upper_arm.L": (SHOULDER, ELBOW),
    "forearm.L": (ELBOW, WRIST),
    "hand.L": (WRIST, WRIST + (HAND_TIP - WRIST) * 0.35),
    "pelvis.L": (Vector((0.0, 0.020, 0.98)), Vector((0.09, 0.0, 1.04))),
    "thigh.L": (HIP, KNEE),
    "shin.L": (KNEE, ANKLE),
    "foot.L": (ANKLE, TOE_BASE),
    "toe.L": (TOE_BASE, TOE_TIP),
    "heel.02.L": (Vector((0.115, 0.045, 0.0)), Vector((0.065, 0.045, 0.0))),
}
for name, (h, t) in side_bones.items():
    set_bone(name, h, t)
for name, h0, t0, roll in hand_desc:
    if name in eb:
        eb[name].head = WRIST + (rot @ (h0 - hand_head0)) * sc
        eb[name].tail = WRIST + (rot @ (t0 - hand_head0)) * sc

# mirror .L to .R (x -> -x)
for b in list(eb):
    if b.name.endswith(".L"):
        r = b.name[:-2] + ".R"
        if r in eb:
            eb[r].head = Vector((-b.head.x, b.head.y, b.head.z))
            eb[r].tail = Vector((-b.tail.x, b.tail.y, b.tail.z))
            eb[r].roll = -b.roll
# restore connectivity (this snaps child heads onto parent tails; they already coincide)
for b in eb:
    if connected.get(b.name):
        b.use_connect = True
bpy.ops.object.mode_set(mode="OBJECT")

# ---- 2. generate the Rigify rig ------------------------------------------------------------------------------
bpy.ops.object.select_all(action="DESELECT")
meta.select_set(True)
bpy.context.view_layer.objects.active = meta
bpy.ops.pose.rigify_generate()
rig = bpy.context.view_layer.objects.active
if rig is meta or rig.type != "ARMATURE":
    rig = next(o for o in bpy.data.objects if o.type == "ARMATURE" and o is not meta)
rig.name = "KRISHNA_rig"
meta.hide_viewport = True
meta.hide_render = True
print("RIG generated:", rig.name, "bones", len(rig.data.bones), flush=True)

# ---- 3. skinning --------------------------------------------------------------------------------------------------
def select_only(*objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[-1]


# Weights: Blender's bone-heat solver fails on this mesh even after remeshing (fused cloth, Rigify's
# overlapping DEF bones), so weights are built here: each vertex takes inverse-distance weights from
# its nearest deform bone segments, then the weights are smoothed along mesh edges so joints blend.
import bmesh

def_bones = [b for b in rig.data.bones if b.name.startswith("DEF-")]
G = len(def_bones)
heads = np.array([list(b.head_local) for b in def_bones], dtype=np.float32)
tails = np.array([list(b.tail_local) for b in def_bones], dtype=np.float32)
nv = len(body.data.vertices)
co = np.empty(nv * 3, dtype=np.float32)
body.data.vertices.foreach_get("co", co)
co = co.reshape(nv, 3)
seg = tails - heads
seg_len2 = np.maximum((seg ** 2).sum(1), 1e-8)
NEAR = int(os.environ.get("SKIN_NEAREST", "4"))
POW = float(os.environ.get("SKIN_POWER", "2.5"))
EPS = float(os.environ.get("SKIN_EPS", "0.015"))
W = np.zeros((nv, G), dtype=np.float32)
CH = 20000
for s0 in range(0, nv, CH):
    p = co[s0 : s0 + CH]
    rel = p[:, None, :] - heads[None, :, :]
    t = np.clip((rel * seg[None]).sum(2) / seg_len2[None], 0.0, 1.0)
    d = np.linalg.norm(rel - t[..., None] * seg[None], axis=2)  # (n, G)
    idx = np.argpartition(d, NEAR, axis=1)[:, :NEAR]
    dn = np.take_along_axis(d, idx, axis=1)
    wn = 1.0 / (dn + EPS) ** POW
    wn /= wn.sum(1, keepdims=True)
    rows = np.arange(len(p))[:, None]
    W[s0 : s0 + CH][rows, idx] = wn
print("SKIN initial weights built, bones", G, flush=True)

# smooth along mesh edges
ne = len(body.data.edges)
ev = np.empty(ne * 2, dtype=np.int32)
body.data.edges.foreach_get("vertices", ev)
ev = ev.reshape(-1, 2)
deg = np.zeros(nv, dtype=np.float32)
np.add.at(deg, ev[:, 0], 1)
np.add.at(deg, ev[:, 1], 1)
for it in range(int(os.environ.get("SKIN_SMOOTH", "6"))):
    acc = np.zeros_like(W)
    np.add.at(acc, ev[:, 0], W[ev[:, 1]])
    np.add.at(acc, ev[:, 1], W[ev[:, 0]])
    W = 0.5 * W + 0.5 * acc / np.maximum(deg, 1)[:, None]
# keep the four strongest per vertex and normalise
top = np.argpartition(-W, 4, axis=1)[:, :4]
keep = np.zeros_like(W)
rows = np.arange(nv)[:, None]
keep[rows, top] = W[rows, top]
keep /= np.maximum(keep.sum(1, keepdims=True), 1e-8)
print("SKIN smoothed", flush=True)

for vg in list(body.vertex_groups):
    body.vertex_groups.remove(vg)
for b in def_bones:
    body.vertex_groups.new(name=b.name)
bm = bmesh.new()
bm.from_mesh(body.data)
dl = bm.verts.layers.deform.verify()
bm.verts.ensure_lookup_table()
nz = np.nonzero(keep > 0.01)
order = np.argsort(nz[0], kind="stable")
vi, gi = nz[0][order], nz[1][order]
for v_i, g_i in zip(vi, gi):
    bm.verts[int(v_i)][dl][int(g_i)] = float(keep[v_i, g_i])
bm.to_mesh(body.data)
bm.free()
body.data.update()
print("WEIGHTS written", flush=True)

arm_mod = body.modifiers.new("Armature", "ARMATURE")
arm_mod.object = rig
body.parent = rig

# head, feather and quill ride the head bone rigidly
HEAD_BONE = "DEF-spine.006"
if quill is not None:
    select_only(quill)
    bpy.ops.object.convert(target="MESH")
    quill.parent = None
    select_only(quill, feather)
    bpy.ops.object.join()
    feather = bpy.context.view_layer.objects.active
mouth_parts = [bpy.data.objects.get(n) for n in ("KRISHNA_mouth_cavity", "KRISHNA_teeth_upper", "KRISHNA_teeth_lower", "KRISHNA_tongue")]
for o in [x for x in (head, feather, *mouth_parts) if x is not None]:
    for vg in list(o.vertex_groups):
        o.vertex_groups.remove(vg)
    g = o.vertex_groups.new(name=HEAD_BONE)
    g.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
    o.parent = rig
    m = o.modifiers.new("Armature", "ARMATURE")
    m.object = rig
rig.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("SAVED", out_blend, flush=True)

# ---- 4. test pose and previews ---------------------------------------------------------------------------------------
if preview_dir:
    os.makedirs(preview_dir, exist_ok=True)
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light = "FLAT"
    sh.color_type = "TEXTURE"
    scene.render.resolution_x = 700
    scene.render.resolution_y = 1200
    scene.world = scene.world or bpy.data.worlds.new("w")
    scene.world.color = (0.6, 0.6, 0.6)
    cd = bpy.data.cameras.new("c")
    cd.type = "ORTHO"
    cd.ortho_scale = 2.3
    cam = bpy.data.objects.new("c", cd)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.location = (0, -6, 0.95)
    cam.rotation_euler = (math.radians(90), 0, 0)

    def render(name):
        scene.render.filepath = os.path.join(preview_dir, name + ".png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", name, flush=True)

    render("rig_rest")
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")
    pb = rig.pose.bones
    names = [b.name for b in pb]
    print("CONTROLS", [n for n in names if "fk" in n or n in ("head", "torso", "chest", "neck")][:30], flush=True)

    def rot(name, axis, deg):
        if name in pb:
            pb[name].rotation_mode = "XYZ"
            e = list(pb[name].rotation_euler)
            e["XYZ".index(axis)] = math.radians(deg)
            pb[name].rotation_euler = e
            return True
        print("MISSING control", name, flush=True)
        return False

    rot("upper_arm_fk.L", "Y", -80)  # raise left arm sideways
    rot("upper_arm_fk.R", "X", -70)  # swing right arm forward
    rot("forearm_fk.R", "X", -60)
    rot("head", "Z", 35)  # turn head
    rot("torso", "Z", 10)
    scene.frame_set(scene.frame_current)
    render("rig_pose")

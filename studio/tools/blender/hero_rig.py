"""Join a face-rigged series-look head to its TRELLIS body and rig the hero (cloud Blender, free).

sai, 2026-11-22 ("yes"): after the face rigs (face_rig.py), each hero becomes one rigged character:
  1. the body GLB is welded (TRELLIS splits it at every UV seam), thinned to about 150k faces, scaled to HEIGHT metres,
     feet on the ground, front facing -Y;
  2. the joints are placed from Karna's hand-fitted joints (karna_rig.py) as fractions of height, the arm joints along the
     line from the shoulder to the farthest fingertip of this body's A-pose, and a Rigify human rig is generated
     (no face bones: the face moves by shape keys);
  3. skin weights by distance to the bones, smoothed along the mesh (as karna_rig.py, step 3);
  4. the face-rigged head is lined up on the body by its nose tip and crown top, the body's own head is cut away above the
     neck, the new head is cut below its chin, and it rides the head and neck bones with its shape keys intact;
  5. a check pose (one arm raised, head turned, jaw open with a smile) is rendered next to the rest pose.
The TRELLIS hands stay one piece each (no finger bend yet; karna_rig.py rebuilds hands, which is the next step).

  python hero_rig.py <hero> <body.glb> <face_rig.blend> <out.blend> [height_m]
"""
import json, math, pathlib, sys
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
HERO, BODY_GLB, FACE_BLEND, OUT = args[:4]
H = float(args[4]) if len(args) > 4 else 1.85
TAG = HERO.upper()
if pathlib.Path(OUT).exists():
    sys.exit(f"exists, not overwriting (folder law 1): {OUT}")
K = H / 1.9                                                        # Karna's joints were fitted on a 1.9 m body


def select_only(*objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[-1]


def verts(o):
    n = len(o.data.vertices); a = np.empty(n * 3, np.float32); o.data.vertices.foreach_get("co", a)
    return a.reshape(n, 3)

# ---- 1. body ---------------------------------------------------------------------------------------------------------------
bpy.ops.preferences.addon_enable(module="rigify")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="rigify")
bpy.ops.import_scene.gltf(filepath=str(pathlib.Path(BODY_GLB).resolve()))
body = max((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
body.name = body.data.name = f"{TAG}_body"
for o in list(bpy.data.objects):
    if o is not body and o.type != "MESH":
        bpy.data.objects.remove(o)
body.parent = None
select_only(body)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bm = bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bm.to_mesh(body.data); bm.free()
if len(body.data.polygons) > 150000:
    d = body.modifiers.new("decimate", "DECIMATE"); d.ratio = 150000 / len(body.data.polygons)
    bpy.ops.object.modifier_apply(modifier=d.name)
co = verts(body)
lo, hi = co.min(0), co.max(0)
s = H / (hi[2] - lo[2])
body.scale = (s, s, s); body.location = (-(lo[0] + hi[0]) / 2 * s, -(lo[1] + hi[1]) / 2 * s, -lo[2] * s)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = verts(body)
print("body faces", len(body.data.polygons), "height", round(co[:, 2].max(), 3), flush=True)

# ---- 2. joints and rig --------------------------------------------------------------------------------------------------
V = lambda x, y, z: Vector((x * K, y * K, z * K))
# the neck is where the front of the body steps back most between chest and chin (these heroes have shorter necks and
# taller crowns than Karna's old body, so Karna's spine heights are re-spaced to this neck)
zs = np.arange(0.70 * H, 0.86 * H, 0.01)
front_y = []
for z in zs:
    sl = co[(np.abs(co[:, 2] - z) < 0.005) & (np.abs(co[:, 0]) < 0.06 * K)]
    front_y.append(sl[:, 1].min() if len(sl) else -1)
NECK = float(zs[int(np.argmax(front_y))])
SPINE = ["spine", "spine.001", "spine.002", "spine.003", "spine.004", "spine.005", "spine.006"]
lower = np.linspace(1.00 * K, NECK - 0.03 * K, 6)                  # hips, spine 1-4 ends, neck base
SPINE_Zm = list(lower) + [NECK + 0.05 * K, H]
SPINE_Z = [z / K for z in SPINE_Zm]
SPINE_Y = [0.00, 0.00, 0.00, 0.00, 0.00, -0.005, -0.01, -0.01]
SHOULDER = Vector((0.20 * K, 0.0, NECK - 0.14 * K))
print("neck z", round(NECK, 3), flush=True)
side = co[:, 0] > 0.25 * K                                         # his left arm and hand, out to the side in the A-pose
arm = co[side & (co[:, 2] > 0.55 * K) & (co[:, 2] < 1.45 * K)]
far = arm[np.argsort(-np.linalg.norm(arm[:, [0, 2]] - np.array([SHOULDER.x, SHOULDER.z]), axis=1))[:40]]
HAND_TIP = Vector(far.mean(0))
line = HAND_TIP - SHOULDER
ELBOW = SHOULDER + line * 0.41 + Vector((0, 0.02 * K, 0))
WRIST = SHOULDER + line * 0.72
HIP, KNEE, ANKLE = V(0.095, 0.0, 0.98), V(0.125, -0.01, 0.52), V(0.15, 0.045, 0.09)
TOE_BASE, TOE_TIP = V(0.16, -0.09, 0.03), V(0.17, -0.18, 0.02)
print("hand tip", tuple(round(c, 3) for c in HAND_TIP), flush=True)

bpy.ops.object.armature_human_metarig_add()
meta = bpy.context.object; meta.name = "metarig"
bpy.ops.object.mode_set(mode="EDIT")
eb = meta.data.edit_bones


def descendants(b):
    out = []
    for c in b.children:
        out += [c] + descendants(c)
    return out


doomed = set()
for root in ("face", "breast.L", "breast.R"):
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
    put(n, V(0, SPINE_Y[i], SPINE_Z[i]), V(0, SPINE_Y[i + 1], SPINE_Z[i + 1]))
hand = eb["hand.L"]; h0 = hand.head.copy()
tips = [b for b in descendants(hand) if b.name.startswith(("f_middle.03", "f_index.03", "f_ring.03", "f_pinky.03"))]
old = sum((b.tail for b in tips), Vector()) / len(tips) - h0
new = HAND_TIP - WRIST
rot = old.normalized().rotation_difference(new.normalized()).to_matrix(); sc = new.length / old.length
fingers = [(b.name, b.head.copy(), b.tail.copy()) for b in descendants(hand)]
for n, (h, t) in {
    "shoulder.L": (Vector((0.03 * K, 0.0, SHOULDER.z + 0.04 * K)), SHOULDER), "upper_arm.L": (SHOULDER, ELBOW), "forearm.L": (ELBOW, WRIST),
    "hand.L": (WRIST, WRIST + new * 0.35), "pelvis.L": (V(0.0, 0.0, 1.0), V(0.10, 0.0, 1.07)),
    "thigh.L": (HIP, KNEE), "shin.L": (KNEE, ANKLE), "foot.L": (ANKLE, TOE_BASE), "toe.L": (TOE_BASE, TOE_TIP),
    "heel.02.L": (V(0.20, 0.10, 0.0), V(0.10, 0.10, 0.0)),
}.items():
    put(n, h, t)
for n, h, t in fingers:
    put(n, WRIST + (rot @ (h - h0)) * sc, WRIST + (rot @ (t - h0)) * sc)
for b in list(eb):
    if b.name.endswith(".L") and b.name[:-2] + ".R" in eb:
        r = eb[b.name[:-2] + ".R"]
        r.head, r.tail, r.roll = Vector((-b.head.x, b.head.y, b.head.z)), Vector((-b.tail.x, b.tail.y, b.tail.z)), -b.roll
for b in eb:
    if connected.get(b.name):
        b.use_connect = True
bpy.ops.object.mode_set(mode="OBJECT")
select_only(meta)
bpy.ops.pose.rigify_generate()
rig = next(o for o in bpy.data.objects if o.type == "ARMATURE" and o is not meta)
rig.name = f"{TAG}_rig"
meta.hide_viewport = meta.hide_render = True

# ---- 4 (before weights). the face-rigged head, lined up by nose tip and crown top -----------------------------------------
with bpy.data.libraries.load(str(pathlib.Path(FACE_BLEND).resolve())) as (src, dst):
    dst.objects = list(src.objects)
heads = [o for o in dst.objects if o is not None]
for o in heads:
    bpy.context.scene.collection.objects.link(o)
head = next(o for o in heads if "face_rig" in o.keys())
info = json.loads(head["face_rig"])
extras = [o for o in heads if o is not head and o.type == "MESH"]
for o in heads:
    if o.type not in ("MESH",):
        bpy.data.objects.remove(o)
hc = verts(head)
mz = info["mouth"][2]
def nose_tip(c, zlo, zhi):
    sel = (np.abs(c[:, 0]) < 0.02 * K) & (c[:, 2] > zlo) & (c[:, 2] < zhi)
    i = np.argmin(c[sel, 1]); return c[sel][i]
hn = nose_tip(hc, mz, info["eyes_z"])
htop = hc[:, 2].max()
bhead = co[(co[:, 2] > NECK) & (np.abs(co[:, 0]) < 0.15 * K)]
bn = nose_tip(bhead, NECK + 0.04 * K, NECK + 0.20 * K)
btop = bhead[:, 2].max()
k = (btop - bn[2]) / (htop - hn[2])
off = Vector(bn) - Vector(hn) * k
for o in [head] + extras:
    o.parent = None
    o.matrix_world = Matrix.Translation(off) @ Matrix.Scale(k, 4) @ o.matrix_world
select_only(head)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)   # shape keys are applied with the mesh
for o in extras:
    select_only(o); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
hc = verts(head)
chin = (mz - 0.045) * k + off.z
cut = chin - 0.035 * K
print("head scale", round(k, 3), "nose body", np.round(bn, 3), "chin", round(chin, 3), "neck cut", round(cut, 3), flush=True)
# cut the new head below the neck, and the body's own head above the neck (inside the new head's outline only)
def delete_where(o, mask):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.nonzero(mask)[0]], context="VERTS")
    bm.to_mesh(o.data); bm.free()
delete_where(head, hc[:, 2] < cut)
hc = verts(head)
hlo, hhi = hc.min(0), hc.max(0)
co = verts(body)
inside = (co[:, 2] > cut + 0.012 * K) & (co[:, 0] > hlo[0] - 0.01) & (co[:, 0] < hhi[0] + 0.01) & (co[:, 1] > hlo[1] - 0.01) & (co[:, 1] < hhi[1] + 0.01)
delete_where(body, inside)
co = verts(body)
print("body verts cut for the head", int(inside.sum()), flush=True)

# ---- 3. skin weights (body) ------------------------------------------------------------------------------------------------
defs = [b for b in rig.data.bones if b.name.startswith("DEF-")]
names = [b.name for b in defs]; col = {n: i for i, n in enumerate(names)}
hb_ = np.array([list(b.head_local) for b in defs], np.float32); tb_ = np.array([list(b.tail_local) for b in defs], np.float32)
seg = tb_ - hb_; seg2 = np.maximum((seg ** 2).sum(1), 1e-8)


def weights(o, c):
    nv = len(c); W = np.zeros((nv, len(defs)), np.float32)
    for s0 in range(0, nv, 20000):
        p = c[s0:s0 + 20000]; rel = p[:, None] - hb_[None]
        t = np.clip((rel * seg[None]).sum(2) / seg2[None], 0, 1)
        dd = np.linalg.norm(rel - t[..., None] * seg[None], axis=2)
        idx = np.argpartition(dd, 4, axis=1)[:, :4]
        wn = 1 / (np.take_along_axis(dd, idx, 1) + 0.015) ** 2.5
        W[s0:s0 + 20000][np.arange(len(p))[:, None], idx] = wn / wn.sum(1, keepdims=True)
    return W


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def write(o, W, rounds=6):
    nv = len(W)
    ev = np.empty(len(o.data.edges) * 2, np.int32); o.data.edges.foreach_get("vertices", ev); ev = ev.reshape(-1, 2)
    deg = np.maximum(np.bincount(ev.ravel(), minlength=nv), 1).astype(np.float32)
    for _ in range(rounds):
        acc = np.zeros_like(W); np.add.at(acc, ev[:, 0], W[ev[:, 1]]); np.add.at(acc, ev[:, 1], W[ev[:, 0]])
        W = 0.5 * W + 0.5 * acc / deg[:, None]
    top = np.argpartition(-W, 4, axis=1)[:, :4]; Kk = np.zeros_like(W); rows = np.arange(nv)[:, None]
    Kk[rows, top] = W[rows, top]; Kk /= np.maximum(Kk.sum(1, keepdims=True), 1e-8)
    for vg in list(o.vertex_groups):
        o.vertex_groups.remove(vg)
    for b in defs:
        o.vertex_groups.new(name=b.name)
    for g in range(len(defs)):
        vs = np.nonzero(Kk[:, g] > 0.01)[0]
        for v in vs:
            o.vertex_groups[g].add([int(v)], float(Kk[v, g]), "REPLACE")
    o.modifiers.new("Armature", "ARMATURE").object = rig
    o.parent = rig


W = weights(body, co)
ARM = np.array([any(t in n for t in ("upper_arm", "forearm", "hand", "f_", "thumb", "palm")) for n in names])
m = smoothstep(0.18 * K, 0.25 * K, np.abs(co[:, 0]))
for sd, sx in (("L", 1), ("R", -1)):
    near = co[:, 0] * sx > 0
    lost = (W[:, ARM] * (1 - m)[:, None]).sum(1) * near
    W[np.ix_(near, ARM)] *= m[near, None]
    W[:, col["DEF-spine.003"]] += lost * 0.6; W[:, col[f"DEF-shoulder.{sd}"]] += lost * 0.4
FINGER = np.array([n.startswith(("DEF-f_", "DEF-palm", "DEF-thumb")) for n in names])
lost = W[:, FINGER].sum(1)                                         # one-piece TRELLIS hands: the hand bone takes the fingers
W[:, FINGER] = 0
for sd, sx in (("L", 1), ("R", -1)):
    W[:, col[f"DEF-hand.{sd}"]] += lost * (co[:, 0] * sx > 0)
write(body, W)
# head: rigid on the head bone, blending into the neck bone over its lower few centimetres
hc = verts(head)
Wh = np.zeros((len(hc), len(defs)), np.float32)
t = smoothstep(cut, cut + 0.05 * K, hc[:, 2])
Wh[:, col["DEF-spine.006"]] = t; Wh[:, col["DEF-spine.005"]] = 1 - t
write(head, Wh, rounds=0)
for o in extras:
    mw = o.matrix_world.copy(); o.parent = rig; o.parent_type = "BONE"; o.parent_bone = "DEF-spine.006"; o.matrix_world = mw
print("rigged", TAG, flush=True)

# ---- 5. check: rest pose and a test pose ------------------------------------------------------------------------------------
scene = bpy.context.scene
cam = bpy.data.cameras.new("chk"); co_ = bpy.data.objects.new("chk", cam); scene.collection.objects.link(co_); scene.camera = co_
cam.type = "ORTHO"; cam.ortho_scale = H * 1.1
co_.location = (0, -6, H / 2); co_.rotation_euler = (math.radians(90), 0, 0)
for e, rz in ((3, -25), (1.2, 40)):
    l = bpy.data.lights.new("k", "SUN"); l.energy = e; lo_ = bpy.data.objects.new("k", l); scene.collection.objects.link(lo_)
    lo_.rotation_euler = (math.radians(60), 0, math.radians(rz))
wd = bpy.data.worlds.new("w"); scene.world = wd; wd.color = (0.32, 0.32, 0.35)
scene.render.engine = "CYCLES"; scene.cycles.samples = 16; scene.render.resolution_x = 540; scene.render.resolution_y = 720
out = pathlib.Path(OUT)
scene.render.filepath = str(out.with_name(out.stem + "_rest.png")); bpy.ops.render.render(write_still=True)
pb = rig.pose.bones
def turn(name, axis, deg):
    if name in pb:
        b = pb[name]; b.rotation_mode = "XYZ"; r = list(b.rotation_euler); r["XYZ".index(axis)] += math.radians(deg); b.rotation_euler = r
turn("upper_arm_fk.L", "X", -70); turn("upper_arm_fk.L", "Z", 25); turn("forearm_fk.L", "X", -40)
if "upper_arm_parent.L" in pb:
    pb["upper_arm_parent.L"]["IK_FK"] = 1.0
turn("head", "Z", 20); turn("neck", "X", -8)
for kname, v in (("jaw_open", 0.6), ("smile_L", 0.8), ("smile_R", 0.8), ("brow_up", 0.4)):
    if kname in head.data.shape_keys.key_blocks:
        head.data.shape_keys.key_blocks[kname].value = v
bpy.context.view_layer.update()
scene.render.filepath = str(out.with_name(out.stem + "_pose.png")); bpy.ops.render.render(write_still=True)
for b in pb:
    b.rotation_euler = (0, 0, 0); b.location = (0, 0, 0)
for kb in head.data.shape_keys.key_blocks:
    kb.value = 0
bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()), compress=True)
print("saved", OUT, flush=True)

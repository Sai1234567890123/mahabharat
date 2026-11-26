"""Bending fingers for a rigged series-look hero, a fixed mouth interior, and (Arjuna) his thin moustache (cloud Blender, free).

sai, 2026-11-23 ("go ahead"), on top of hero_rig.py's v1 heroes:

1. Fingers. hero_rig.py gave the whole TRELLIS hand to the hand bone, so the fingers could not bend. A first try rebuilt
   the hands from tubes along the bones (as karna_rig.py did for the old Karna): they bent, but looked like puppet gloves
   next to the painted body, so this keeps each hero's own painted TRELLIS hands and fits the finger bones inside them:
     - the hand is found by a flood fill from the fingertips (the hip and skirt beside it are never touched);
     - in a frame along the hand, every slice across the fingers is split between the four fingers and the thumb by the
       nearest bone chain, and each finger's chain is moved to the middle of its own slices, from the knuckle to the real
       fingertip (joint spacing as in Rigify's human metarig); the thumb is fitted along its own points;
     - the finger bones get a roll with Z toward the palm (Rigify's convention), so a positive X rotation curls them;
     - the rig is regenerated from its metarig into the same rig object, and the hand vertices are re-weighted: each
       finger's skin rides its own three bones, blending into the hand bone across the knuckles, then smoothed so the
       skin between touching fingers stretches softly.
2. Mouth interior. In the v1 rigs the dark mouth cavity and the teeth landed about 7 cm above the mouth (inside the
   head), so an open mouth showed nothing behind the lips. They are moved back behind the lips, found from the head's own
   jaw_open shape key, with the offsets face_rig.py used.
3. --moustache paints a thin dark moustache on the upper lip into a copy of the head's colour texture (Arjuna's locked
   look has one; his series head came out clean-shaven). It is painted in UV space through the rest shape, so it rides
   the lip shape keys.

  python hero_hands.py <hero> <in.blend> <out.blend> [--moustache]

Check renders next to <out>: _<pose>_<side>.png for rest, fist, point and spread, and _mouth.png (open mouth, and the
moustache if painted).
"""
import json, math, pathlib, sys
import bpy
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
MOUSTACHE = "--moustache" in args
args = [a for a in args if not a.startswith("--")]
HERO, IN, OUT = args[:3]
TAG = HERO.upper()
if pathlib.Path(OUT).exists():
    sys.exit(f"exists, not overwriting (folder law 1): {OUT}")
out = pathlib.Path(OUT).resolve()

bpy.ops.wm.open_mainfile(filepath=str(pathlib.Path(IN).resolve()))
bpy.ops.preferences.addon_enable(module="rigify")
scene = bpy.context.scene
rig = bpy.data.objects[f"{TAG}_rig"]
meta = bpy.data.objects["metarig"]
body = bpy.data.objects[f"{TAG}_body"]
head = bpy.data.objects[f"{TAG}_head"]
for o in list(scene.objects):                                      # old check camera and lights from hero_rig.py
    if o.type in ("CAMERA", "LIGHT"):
        bpy.data.objects.remove(o)
FINGERS = ["f_index", "f_middle", "f_ring", "f_pinky"]
CHAINS = FINGERS + ["thumb"]


def verts(o):
    n = len(o.data.vertices); a = np.empty(n * 3, np.float32); o.data.vertices.foreach_get("co", a)
    a = a.reshape(n, 3); M = np.array(o.matrix_world)
    return a @ M[:3, :3].T + M[:3, 3]


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def seg_dist(p, a, b):
    """distance from points p to segment a-b, and the position along it (0..1)"""
    ab = b - a; t = np.clip(((p - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1), t


def poly_dist(p, pts):
    return np.min([seg_dist(p, pts[i], pts[i + 1])[0] for i in range(len(pts) - 1)], axis=0)


def along(line, fracs):
    """points at the given fractions of a polyline's length"""
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(line, axis=0), axis=1))]
    out_ = []
    for fr in fracs:
        d = fr * seg[-1]; i = min(int(np.searchsorted(seg, d, side="right")) - 1, len(line) - 2)
        u = (d - seg[i]) / max(seg[i + 1] - seg[i], 1e-9)
        out_.append(line[i] + u * (line[i + 1] - line[i]))
    return np.array(out_)


def select_only(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.hide_set(False); o.hide_viewport = False; o.select_set(True)
    bpy.context.view_layer.objects.active = o


# ---- 1. fit the finger bones inside the TRELLIS fingers --------------------------------------------------------------------
co = verts(body)
me = body.data
ev = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", ev); ev = ev.reshape(-1, 2)
B = rig.data.bones
fit, hand_sets = {}, {}
for side, sx in (("L", 1), ("R", -1)):
    org = lambda n, end=0: np.array((B[f"ORG-{n}.{side}"].head_local, B[f"ORG-{n}.{side}"].tail_local)[end])
    w = np.array(B[f"DEF-hand.{side}"].head_local)
    fa = B[f"DEF-forearm.{side}"]
    ax = np.array(fa.tail_local) - np.array(fa.head_local); ax /= np.linalg.norm(ax)
    rel = co - w; t = rel @ ax
    radial = np.linalg.norm(rel - t[:, None] * ax, axis=1)
    region = (t > -0.01) & (radial < 0.13) & (co[:, 0] * sx > 0.2)
    keep = region & (np.linalg.norm(co - org("f_middle.03", 1), axis=1) < 0.06)
    a, b = ev[:, 0], ev[:, 1]; inner = region[a] & region[b]
    for _ in range(500):                                           # grow from the fingertips along edges, inside the region
        grow = np.zeros_like(keep); grow[a[inner & keep[b]]] = True; grow[b[inner & keep[a]]] = True
        if not (grow & ~keep).any():
            break
        keep |= grow
    idx = np.nonzero(keep)[0]
    P = co[idx]
    far = P[np.argsort(-((P - w) @ ax))[:30]].mean(0)
    hy = far - w; L = float(np.linalg.norm(hy)); hy /= L
    kx = org("f_pinky.01") - org("f_index.01"); hx = kx - hy * (kx @ hy); hx /= np.linalg.norm(hx)
    hz = np.cross(hx, hy)
    palm = np.array([-sx, 0.0, 0.0]); palm -= hy * (palm @ hy); palm /= np.linalg.norm(palm)   # A-pose: palms face the thighs
    s = (P - w) @ hy
    # template chains (joints: head .01, head .02, head .03, tail .03)
    chains = {f: np.array([org(f"{f}.01"), org(f"{f}.02"), org(f"{f}.03"), org(f"{f}.03", 1)]) for f in CHAINS}
    frac = {f: np.cumsum([0] + [np.linalg.norm(c[i + 1] - c[i]) for i in range(3)]) for f, c in chains.items()}
    frac = {f: v / v[-1] for f, v in frac.items()}
    tmpl_tip = max((chains[f][-1] - w) @ hy for f in FINGERS)
    for it in range(5):
        D = np.stack([poly_dist(P, chains[f]) for f in CHAINS], 1)
        lab = np.argmin(D, 1)
        lab[s < 0.22 * L] = -1                                     # wrist and heel of the hand: hand bone only
        new = {}
        for i, f in enumerate(FINGERS):
            q = P[lab == i]; qs = s[lab == i]
            if len(q) < 30:
                new[f] = chains[f]; continue
            sk = float((chains[f][0] - w) @ hy) * (L / tmpl_tip) if it == 0 else float((chains[f][0] - w) @ hy)
            tip_s = float(np.percentile(qs, 99.5)) - 0.003
            cs, cp = [], []
            for s0 in np.arange(sk, tip_s + 1e-4, 0.006):
                m = np.abs(qs - s0) < 0.0045
                if m.sum() >= 4:
                    cs.append(s0); cp.append(q[m].mean(0))
            if len(cp) < 4:
                new[f] = chains[f]; continue
            cp = np.array(cp)
            cp[1:-1] = (cp[:-2] + cp[1:-1] + cp[2:]) / 3            # smooth the centre line
            tipq = q[qs > tip_s - 0.006]
            tip = tipq.mean(0) + hy * (tip_s - float((tipq.mean(0) - w) @ hy))
            line = np.vstack([cp, tip])
            new[f] = along(line, frac[f])
        q = P[lab == 4]
        base = chains["thumb"][0]
        if len(q) > 30:
            d = q - base
            dirn = np.linalg.svd(d - d.mean(0), full_matrices=False)[2][0]
            if dirn @ (chains["thumb"][-1] - base) < 0:
                dirn = -dirn
            reach = float(np.percentile(d @ dirn, 99)) - 0.004
            cen = q.mean(0); cen -= dirn * ((cen - base) @ dirn)       # the thumb's own centre line, through its points
            off = (cen - base) * 0.6
            new["thumb"] = np.array([base + off * fr + dirn * reach * fr for fr in frac["thumb"]])
        else:
            new["thumb"] = chains["thumb"]
        chains = new
    hand_sets[side] = dict(idx=idx, lab=lab, s=s, L=L, hy=hy, palm=palm, w=w)
    fit[side] = dict(chains=chains, palm=palm, hx=hx, hy=hy, L=L)
    print("hand", side, "verts", len(idx), "length", round(L, 3), "per chain",
          [int((lab == i).sum()) for i in range(5)], flush=True)
    for f in CHAINS:
        print("   ", f, "tip moved", round(float(np.linalg.norm(chains[f][-1] - np.array(B[f"ORG-{f}.03.{side}"].tail_local))), 4),
              "length", round(float(sum(np.linalg.norm(np.diff(chains[f], axis=0), axis=1))), 3), flush=True)

# ---- 2. move the metarig's finger bones and regenerate the rig into the same object ---------------------------------------
select_only(meta)
bpy.ops.object.mode_set(mode="EDIT")
eb = meta.data.edit_bones
for side, F in fit.items():
    for f in CHAINS:
        c = F["chains"][f]
        for k in range(3):
            bn = eb[f"{f}.0{k + 1}.{side}"]
            bn.head, bn.tail = Vector(c[k]), Vector(c[k + 1])
            yv = c[k + 1] - c[k]; yv /= np.linalg.norm(yv)
            if f == "thumb":
                zt = F["hx"]                                        # thumb: Z toward the fingers (Rigify's metarig)
            else:
                zt = F["palm"]                                      # fingers: Z toward the palm, so +X curls
            zt = zt - yv * (zt @ yv)
            bn.align_roll(Vector(zt / np.linalg.norm(zt)))
    for k, f in enumerate(FINGERS):                                 # palm bones end at the new knuckles
        pb_ = eb[f"palm.0{k + 1}.{side}"]
        pb_.tail = Vector(F["chains"][f][0])
bpy.ops.object.mode_set(mode="OBJECT")
meta.data.rigify_target_rig = rig
bpy.ops.pose.rigify_generate()
meta.hide_set(True); meta.hide_render = True
rig = bpy.data.objects[f"{TAG}_rig"]
B = rig.data.bones
print("rig regenerated:", len(B), "bones", flush=True)

# ---- 3. re-weight the hand vertices --------------------------------------------------------------------------------------
vg = {g.name: g for g in body.vertex_groups}
for side, H in hand_sets.items():
    idx, lab, s = H["idx"], H["lab"], H["s"]
    P = co[idx]
    names = [f"DEF-hand.{side}"] + [f"DEF-{f}.0{k}.{side}" for f in CHAINS for k in (1, 2, 3)]
    col = {n: i for i, n in enumerate(names)}
    W = np.zeros((len(idx), len(names)), np.float32)
    # current weights of these vertices (hand bone, forearm, whatever hero_rig gave): kept for the palm and wrist
    old = {}
    for i, v in enumerate(idx):
        for ge in me.vertices[int(v)].groups:
            nm = body.vertex_groups[ge.group].name
            old.setdefault(nm, np.zeros(len(idx), np.float32))[i] = ge.weight
    D = np.stack([poly_dist(P, fit[side]["chains"][f]) for f in CHAINS], 1)
    lab = np.argmin(D, 1)
    fw = np.zeros(len(idx), np.float32)                             # how much the fingers own each vertex
    for i, f in enumerate(CHAINS):
        m = lab == i
        if not m.any():
            continue
        c = fit[side]["chains"][f]
        dd = np.stack([seg_dist(P[m], c[k], c[k + 1])[0] for k in range(3)], 1)
        tt = seg_dist(P[m], c[0], c[1])[1]
        o2 = np.argsort(dd, 1)[:, :2]
        ww = 1 / (np.take_along_axis(dd, o2, 1) + 0.002) ** 6; ww /= ww.sum(1, keepdims=True)
        sub = np.zeros((m.sum(), 3), np.float32)
        sub[np.arange(m.sum())[:, None], o2] = ww
        if f == "thumb":
            own = smoothstep(0.0, 0.35, tt)                         # the thumb's root blends into the hand
        else:
            own = smoothstep(-0.012, 0.006, (P[m] - c[0]) @ fit[side]["hy"])   # behind the knuckle: the hand bone
        own = np.where(dd.min(1) < 0.035, own, 0)
        rows = np.nonzero(m)[0]
        for k in range(3):
            W[rows, col[f"DEF-{f}.0{k + 1}.{side}"]] = sub[:, k] * own
        fw[rows] = own
    # smooth over the hand's own edges, so the skin between touching fingers stretches softly
    loc = -np.ones(len(co), np.int64); loc[idx] = np.arange(len(idx))
    e = ev[(loc[ev[:, 0]] >= 0) & (loc[ev[:, 1]] >= 0)]; e = loc[e]
    deg = np.maximum(np.bincount(e.ravel(), minlength=len(idx)), 1).astype(np.float32)[:, None]
    X = np.c_[W, fw]
    for _ in range(3):
        acc = np.zeros_like(X); np.add.at(acc, e[:, 0], X[e[:, 1]]); np.add.at(acc, e[:, 1], X[e[:, 0]])
        X = 0.5 * X + 0.5 * acc / deg
    W, fw = X[:, :-1], np.clip(X[:, -1], 0, 1)
    Wsum = W.sum(1, keepdims=True); W = np.where(Wsum > 1e-6, W / np.maximum(Wsum, 1e-6), 0) * fw[:, None]
    # the rest (1 - fw) keeps the old weights, with the old finger share handed to the hand bone
    for nm, arr in old.items():
        tgt = f"DEF-hand.{side}" if nm.startswith(("DEF-f_", "DEF-thumb", "DEF-palm")) else nm
        vals = arr * (1 - fw)
        if tgt in col:
            W[:, col[tgt]] += vals
        else:
            g = vg.get(tgt) or body.vertex_groups.new(name=tgt)
            for i, v in enumerate(idx):
                g.add([int(v)], float(vals[i]), "REPLACE") if vals[i] > 0.002 else g.remove([int(v)])
    for n in names:
        g = vg.get(n) or body.vertex_groups.new(name=n)
        vals = W[:, col[n]]
        on = vals > 0.002
        g.remove([int(v) for v in idx[~on]])
        for v, x in zip(idx[on], vals[on]):
            g.add([int(v)], float(x), "REPLACE")
    print("re-weighted", side, "hand:", len(idx), "verts; finger-owned", int((fw > 0.5).sum()), flush=True)

# ---- 4. mouth interior back behind the lips --------------------------------------------------------------------------------
kb = head.data.shape_keys.key_blocks
def key_co(k):
    a = np.empty(len(k.data) * 3, np.float32); k.data.foreach_get("co", a); return a.reshape(-1, 3)
hb_ = key_co(kb["Basis"])
dj = np.linalg.norm(key_co(kb["jaw_open"]) - hb_, axis=1)
dp = np.linalg.norm(key_co(kb["mouth_press"]) - hb_, axis=1)
lower = hb_[dj > 0.3 * dj.max()]
press = hb_[dp > 0.3 * dp.max()]
mx = float((press[:, 0].min() + press[:, 0].max()) / 2)
mz = float(lower[:, 2].max())                                       # the mouth line: top of what the jaw moves
lipm = (np.abs(hb_[:, 0] - mx) < 0.004) & (np.abs(hb_[:, 2] - mz) < 0.004)
lip_y = float(hb_[lipm, 1].min())
cav, teeth = bpy.data.objects["FACE_mouth_cavity"], bpy.data.objects["FACE_teeth_upper"]
k = teeth.dimensions.y / 0.008                                       # face_rig.py made the teeth 0.008 deep
hw_k = cav.dimensions.x / (2 * 0.95)                                 # half the mouth width, in this hero's size
tb = 0.012
for o, target in ((teeth, Vector((mx, lip_y + tb * k, mz + 0.001 * k))), (cav, Vector((mx, lip_y + (tb + 0.016) * k, mz - 0.004 * k)))):
    c = sum((o.matrix_world @ Vector(v) for v in o.bound_box), Vector()) / 8
    mw = o.matrix_world.copy(); mw.translation += target - c; o.matrix_world = mw
    print("moved", o.name, "by", tuple(round(x, 3) for x in (target - c)), flush=True)
head["face_rig_hero"] = json.dumps(dict(mouth=[mx, lip_y, mz], half_width=hw_k, scale=k))

# ---- 5. moustache (Arjuna): painted in UV space through the head's rest shape -----------------------------------------------
if MOUSTACHE:
    tn = next(n for n in head.active_material.node_tree.nodes
              if n.type == "TEX_IMAGE" and any(l.to_socket.name == "Base Color" for l in n.outputs[0].links))
    img = tn.image.copy(); img.name = f"{TAG}_head_colour_moustache"
    IW, IH = img.size
    px = np.empty(IW * IH * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(IH, IW, 4)
    a_ = hw_k

    def mask(p):
        u = np.abs(p[:, 0] - mx) / a_; v = p[:, 2] - mz
        centre = a_ * (0.88 - 0.72 * u ** 2)                        # above the upper lip's red, drooping to the corners
        half = a_ * (0.10 - 0.05 * u) * smoothstep(0.04, 0.13, u)   # thin, with a small gap under the nose
        edge = a_ * 0.03
        m_ = 1 - smoothstep(half - edge, half + edge, np.abs(v - centre))
        m_ *= 1 - smoothstep(0.95, 1.12, u)
        m_ *= p[:, 1] < lip_y + a_ * 0.9                            # front of the face only
        return m_

    hm = head.data
    hm.calc_loop_triangles()
    tl_ = np.empty(len(hm.loop_triangles) * 3, np.int32); hm.loop_triangles.foreach_get("loops", tl_); tl_ = tl_.reshape(-1, 3)
    hlv = np.empty(len(hm.loops), np.int32); hm.loops.foreach_get("vertex_index", hlv)
    huv = np.empty(len(hm.loops) * 2, np.float32); hm.uv_layers.active.data.foreach_get("uv", huv); huv = huv.reshape(-1, 2)
    Pt = hb_[hlv[tl_]]
    box = (np.abs(Pt[..., 0] - mx).min(1) < a_ * 1.25) & (np.abs(Pt[..., 2] - mz).min(1) < a_ * 0.9) & (Pt[..., 1].min(1) < lip_y + a_)
    dark = np.array([0.045, 0.034, 0.030])
    painted = 0
    for ti_ in np.nonzero(box)[0]:
        uv = huv[tl_[ti_]] * np.array([IW, IH]); p3 = Pt[ti_]
        x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        q = np.c_[gx.ravel() + 0.5, gy.ravel() + 0.5]
        Tm = np.array([uv[1] - uv[0], uv[2] - uv[0]]).T
        if abs(np.linalg.det(Tm)) < 1e-9:
            continue
        bc = np.linalg.solve(Tm, (q - uv[0]).T).T
        wgt = np.c_[1 - bc.sum(1), bc]
        ins = (wgt > -0.03).all(1)
        if not ins.any():
            continue
        m_ = mask(wgt[ins] @ p3)
        if m_.max() <= 0:
            continue
        xi = np.clip(gx.ravel()[ins], 0, IW - 1); yi = np.clip(gy.ravel()[ins], 0, IH - 1)
        f_ = (0.96 * m_)[:, None]
        px[yi, xi, :3] = np.minimum(px[yi, xi, :3], px[yi, xi, :3] * (1 - f_) + dark * f_)
        painted += int((m_ > 0.5).sum())
    img.pixels.foreach_set(px.ravel())
    img.pack()
    tn.image = img
    print("moustache painted:", painted, "texels", flush=True)

# ---- 6. checks ---------------------------------------------------------------------------------------------------------------
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = 24
cam = bpy.data.cameras.new("chk"); camo = bpy.data.objects.new("chk", cam); scene.collection.objects.link(camo); scene.camera = camo
cam.type = "ORTHO"
for e, rz in ((3, -25), (1.2, 40)):
    l = bpy.data.lights.new("k", "SUN"); l.energy = e; lo_ = bpy.data.objects.new("k", l); scene.collection.objects.link(lo_)
    lo_.rotation_euler = (math.radians(60), 0, math.radians(rz))
scene.world.color = (0.32, 0.32, 0.35)
scene.render.resolution_x = scene.render.resolution_y = 480
pb = rig.pose.bones


def pose_fingers(curl, spread=0.0, point=False):
    for side in ("L", "R"):
        for f in CHAINS:
            c = 0 if (point and f == "f_index") else curl * (0.5 if f == "thumb" else 1.0)
            for kk in ("01", "02", "03"):
                n = f"{f}.{kk}.{side}"
                if n in pb:
                    pb[n].rotation_mode = "XYZ"; pb[n].rotation_euler = (math.radians(c), 0, 0)
            m = f"{f}.01_master.{side}"
            if m in pb:
                i = (FINGERS.index(f) - 1.5) if f in FINGERS else 0
                pb[m].rotation_mode = "XYZ"; pb[m].rotation_euler = (0, 0, math.radians(spread * i))
    bpy.context.view_layer.update()


shots = []


def snap(name, target, scale, side_view):
    cam.ortho_scale = scale
    if side_view:
        sg = 1 if target.x > 0 else -1
        camo.location = (target.x + 3 * sg, target.y - 1.2, target.z); camo.rotation_euler = (math.radians(90), 0, math.radians(68 * sg))
    else:
        camo.location = (target.x, target.y - 3, target.z); camo.rotation_euler = (math.radians(90), 0, 0)
    p = out.with_name(out.stem + f"_{name}.png"); scene.render.filepath = str(p)
    bpy.ops.render.render(write_still=True); shots.append(p)


for side in ("L", "R"):
    F = fit[side]
    tgt = Vector(F["chains"]["f_middle"][0]) - Vector(F["hy"]) * 0.02
    for name, curl, spread, point in (("rest", 0, 0, False), ("fist", 60, 0, False), ("point", 60, 0, True), ("spread", -8, 9, False)):
        pose_fingers(curl, spread, point)
        snap(f"{name}_{side}", tgt, 0.30, True)
pose_fingers(0)
for b in pb:
    b.rotation_euler = (0, 0, 0); b.location = (0, 0, 0)
kb["jaw_open"].value = 0.7
bpy.context.view_layer.update()
cam.ortho_scale = 0.16
camo.location = (mx + 1.2, lip_y - 2.7, mz + 0.012); camo.rotation_euler = (math.radians(90), 0, math.radians(24))
p = out.with_name(out.stem + "_mouth_open.png"); scene.render.filepath = str(p); bpy.ops.render.render(write_still=True); shots.append(p)
kb["jaw_open"].value = 0
bpy.context.view_layer.update()
camo.location = (mx, lip_y - 3, mz + 0.012); camo.rotation_euler = (math.radians(90), 0, 0)
p = out.with_name(out.stem + "_mouth.png"); scene.render.filepath = str(p); bpy.ops.render.render(write_still=True); shots.append(p)
bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
print("saved", OUT, flush=True)

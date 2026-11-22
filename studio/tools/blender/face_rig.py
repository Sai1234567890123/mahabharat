"""Face rig for a TRELLIS hero head: a mouth that can open, and shape keys for speech and expressions. Free, CPU only.

sai, 2026-11-22 ("Both"): the heroes must speak and emote. A TRELLIS head is one closed sculpt with painted eyes and no
mouth inside, so this script:
  1. subdivides the face (about 2 mm edges instead of 7 mm) so it can bend smoothly; UVs and bone weights are interpolated;
  2. cuts the lips open along the mouth line and puts a dark mouth cavity and an upper row of teeth behind them,
     parented to the head bone;
  3. adds shape keys built from smooth falloff fields around face landmarks:
       speech: jaw_open, mouth_wide, mouth_round, mouth_press
       expression: smile_L, smile_R, frown, blink_L, blink_R, brow_up, brow_angry, brow_sad
  4. writes visemes.json next to the output: the Rhubarb Lip Sync mouth shapes A to H and X as mixes of these keys.

Landmarks are per character (world metres, the character faces -Y). Karna's were measured on karna_rigged_v7.blend from a
depth profile along the face centre line and a front render. Never edits the input file (folder law 1).

  python face_rig.py <in.blend> <out.blend> [landmarks.json]
  python face_rig.py <head.glb> <out.blend> landmarks.json      # a bare TRELLIS head (no rig): set "subdivide": 0 if dense
"""
import json, math, pathlib, sys
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

KARNA = dict(
    body="KARNA_body", rig="KARNA_rig", head_bone="DEF-spine.006",
    face_box=dict(xmax=0.08, zmin=1.52, zmax=1.72, ymax=-0.045),   # region that is subdivided and may move
    mouth=dict(z=1.577, half_width=0.024, y=-0.106),                   # mouth line, half width, lip surface depth
    jaw_pivot=(0.0, 0.0, 1.628), jaw_deg=16.0,
    eyes=dict(x=0.031, z=1.662, half_width=0.016, y=-0.112),
    brows=dict(z=1.678, inner=0.008, outer=0.052),
    cheek=dict(x=0.036, z=1.603),
)

def smooth(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)

def blob(p, c, r):
    """Smooth bump of radius r (x, y, z radii) around c: 1 at the centre, 0 at the edge."""
    d = np.sqrt((((p - np.asarray(c)) / np.asarray(r)) ** 2).sum(1))
    return smooth(1 - d)

def build(src, dst, L):
    bpy.ops.wm.open_mainfile(filepath=src)
    if src.lower().endswith((".glb", ".gltf")):           # a bare TRELLIS head: import it, no armature yet
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=src)
        mesh = max((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
        mesh.name = L["body"]
    body, rig = bpy.data.objects[L["body"]], bpy.data.objects.get(L.get("rig") or "")
    mw, mwi = body.matrix_world.copy(), body.matrix_world.inverted()
    fb, m = L["face_box"], L["mouth"]

    # ---- 1 and 2: subdivide the face, cut the mouth open
    bm = bmesh.new(); bm.from_mesh(body.data)
    bm.verts.layers.deform.verify()
    def world(v): return mw @ v.co
    def in_face(f):
        c = mw @ f.calc_center_median()
        return abs(c.x) < fb["xmax"] and fb["zmin"] < c.z < fb["zmax"] and c.y < fb["ymax"]
    faces = [f for f in bm.faces if in_face(f)]
    edges = list({e for f in faces for e in f.edges})
    if L.get("subdivide", 2):
        bmesh.ops.subdivide_edges(bm, edges=edges, cuts=L.get("subdivide", 2), use_grid_fill=True, smooth=0.0)
    bm.faces.ensure_lookup_table()
    # cut along the mouth line: bisect the lip faces with the plane z = mouth z, then split the new edges inside the mouth
    lip_faces = [f for f in bm.faces if (lambda c: abs(c.x) < m["half_width"] + 0.01 and abs(c.z - m["z"]) < 0.008 and c.y < fb["ymax"])(mw @ f.calc_center_median())]
    geom = list({g for f in lip_faces for g in (list(f.verts) + list(f.edges))}) + lip_faces
    zl_local = (mwi @ Vector((0, 0, m["z"]))).z    # the body has no rotation, so a horizontal world plane is horizontal here
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, zl_local), plane_no=(0, 0, 1), dist=1e-6)
    cut = [e for e in bm.edges if all(abs(world(v).z - m["z"]) < 2e-5 and abs(world(v).x) < m["half_width"] and world(v).y < fb["ymax"] for v in e.verts)]
    bmesh.ops.split_edges(bm, edges=cut)
    bm.to_mesh(body.data); bm.free()
    print("face subdivided; mouth cut edges:", len(cut))

    # which vertices belong to the lower lip side of the cut (seam twins are told apart by the faces they touch)
    me = body.data
    co = np.array([mw @ v.co for v in me.vertices])
    below = co[:, 2] < m["z"] - 1e-5
    on = np.abs(co[:, 2] - m["z"]) < 2e-5
    fz = {}
    for p in me.polygons:
        cz = (mw @ Vector(p.center)).z
        for vi in p.vertices:
            fz.setdefault(vi, []).append(cz)
    for vi in np.where(on)[0]:
        below[vi] = np.mean(fz.get(vi, [m["z"] + 1])) < m["z"]
    front = smooth((fb["ymax"] + 0.01 - co[:, 1]) / 0.04)          # only the front of the face moves
    side = smooth((fb["xmax"] - np.abs(co[:, 0])) / 0.03)

    # ---- 3: shape keys (deltas in world space, stored in local space)
    if not me.shape_keys:
        body.shape_key_add(name="Basis", from_mix=False)
    R = np.array(mwi.to_3x3())
    def key(name, delta):
        k = body.shape_key_add(name=name, from_mix=False)
        loc = np.array([v.co for v in me.vertices]) + delta @ R.T
        k.data.foreach_set("co", loc.ravel())
        print(f"key {name:12s} moved {int((np.linalg.norm(delta, axis=1) > 1e-4).sum())} verts, max {np.linalg.norm(delta, axis=1).max() * 1000:.1f} mm")

    # jaw_open: the lower lip, chin and jaw turn down and back about the jaw pivot
    wj = below * smooth((m["z"] + 0.002 - co[:, 2]) / 0.006) * smooth((co[:, 2] - (fb["zmin"] - 0.005)) / 0.03) * front * side
    wj = wj * smooth((0.075 - np.abs(co[:, 0])) / 0.035)
    piv = np.array(L["jaw_pivot"]); a = math.radians(L["jaw_deg"])
    rel = co - piv
    rot = np.c_[rel[:, 0], rel[:, 1] * math.cos(a) - rel[:, 2] * math.sin(a), rel[:, 1] * math.sin(a) + rel[:, 2] * math.cos(a)]
    d = (rot - rel) * wj[:, None]
    up = (~below) * blob(co, (0, m["y"], m["z"] + 0.004), (m["half_width"] * 1.2, 0.03, 0.008))
    d[:, 2] += 0.0025 * up                                       # the upper lip lifts a little
    key("jaw_open", d)

    mc = np.array([0, m["y"], m["z"]])
    cl, cr = mc + [m["half_width"], 0.004, 0], mc + [-m["half_width"], 0.004, 0]
    wl = blob(co, cl, (0.018, 0.03, 0.014)) * front
    wr = blob(co, cr, (0.018, 0.03, 0.014)) * front
    lips = blob(co, mc, (m["half_width"] * 1.5, 0.03, 0.014)) * front

    d = np.zeros_like(co); d[:, 0] += 0.006 * (wl - wr); d[:, 1] += 0.002 * (wl + wr)
    key("mouth_wide", d)
    d = np.zeros_like(co); d[:, 0] -= 0.35 * co[:, 0] * lips; d[:, 1] -= 0.005 * lips
    key("mouth_round", d)
    d = np.zeros_like(co); d[:, 2] += 0.0015 * lips * below - 0.0008 * lips * (~below); d[:, 1] += 0.0015 * lips
    key("mouth_press", d)

    ch = L["cheek"]
    for name, w, cheek_x in (("smile_L", wl, ch["x"]), ("smile_R", wr, -ch["x"])):
        wc = blob(co, (cheek_x, m["y"] - 0.005, ch["z"]), (0.022, 0.04, 0.016)) * front
        d = np.zeros_like(co)
        d[:, 2] += 0.008 * w + 0.004 * wc
        d[:, 0] += 0.005 * w * np.sign(cheek_x)
        d[:, 1] += 0.002 * w - 0.001 * wc
        key(name, d)
    d = np.zeros_like(co); d[:, 2] -= 0.006 * (wl + wr); d[:, 1] += 0.001 * (wl + wr)
    key("frown", d)

    e = L["eyes"]
    for name, sx in (("blink_L", 1), ("blink_R", -1)):
        ex = sx * e["x"]
        ring = blob(co, (ex, e["y"], e["z"]), (e["half_width"] * 1.35, 0.03, 0.016)) * front
        upper = ring * smooth((co[:, 2] - (e["z"] - 0.002)) / 0.004)
        lower = ring * smooth(((e["z"] - 0.002) - co[:, 2]) / 0.004)
        target = e["z"] - 0.005
        d = np.zeros_like(co)
        d[:, 2] += (target - co[:, 2]) * upper * (co[:, 2] < e["z"] + 0.012)
        d[:, 2] += 0.002 * lower
        key(name, d)

    b = L["brows"]
    ax = np.abs(co[:, 0])
    span = smooth((ax - b["inner"] + 0.006) / 0.008) * smooth((b["outer"] + 0.008 - ax) / 0.012)
    band = smooth(1 - np.abs(co[:, 2] - b["z"]) / 0.014) * front * span
    inner = band * smooth((0.03 - ax) / 0.015)
    outer = band * smooth((ax - 0.025) / 0.015)
    d = np.zeros_like(co); d[:, 2] += 0.007 * band
    key("brow_up", d)
    d = np.zeros_like(co); d[:, 2] -= 0.0045 * band + 0.0025 * inner; d[:, 0] -= 0.003 * inner * np.sign(co[:, 0]); d[:, 1] -= 0.0015 * inner
    key("brow_angry", d)
    d = np.zeros_like(co); d[:, 2] += 0.0065 * inner - 0.002 * outer
    key("brow_sad", d)

    # ---- mouth cavity and teeth behind the lips, on the head bone
    def ellipsoid(name, centre, radii, colour, rough=0.6):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0, location=centre)
        o = bpy.context.active_object; o.name = name; o.scale = radii
        mat = bpy.data.materials.new(name + "_mat"); mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = colour; bsdf.inputs["Roughness"].default_value = rough
        o.data.materials.append(mat)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        mwo = o.matrix_world.copy()
        if rig:
            o.parent, o.parent_type, o.parent_bone = rig, "BONE", L["head_bone"]
        else:
            o.parent = body
        o.matrix_world = mwo
        return o
    hw = m["half_width"]
    ellipsoid("FACE_mouth_cavity", (0, m["y"] + 0.022, m["z"] - 0.004), (hw * 0.95, 0.02, 0.013), (0.09, 0.025, 0.02, 1))
    ellipsoid("FACE_teeth_upper", (0, m["y"] + 0.0065, m["z"] + 0.0005), (hw * 0.62, 0.004, 0.0028), (0.82, 0.77, 0.66, 1), 0.35)

    # ---- 4: Rhubarb Lip Sync mouth shapes as mixes of the keys
    visemes = {
        "X": {},                                                    # rest
        "A": {"mouth_press": 1.0},                                  # M, B, P
        "B": {"jaw_open": 0.2, "mouth_wide": 0.35},                 # most consonants, teeth slightly apart
        "C": {"jaw_open": 0.45, "mouth_wide": 0.3},                 # EH, AE
        "D": {"jaw_open": 0.9, "mouth_wide": 0.1},                  # AA
        "E": {"jaw_open": 0.5, "mouth_round": 0.5},                 # AO, ER
        "F": {"jaw_open": 0.15, "mouth_round": 1.0},                # UW, OW, W
        "G": {"jaw_open": 0.1, "mouth_press": 0.5},                 # F, V
        "H": {"jaw_open": 0.4},                                     # L
    }
    pathlib.Path(dst).with_suffix(".visemes.json").write_text(json.dumps(visemes, indent=1))
    bpy.ops.wm.save_as_mainfile(filepath=dst, compress=True)
    print("saved", dst)

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    L = dict(KARNA)
    if len(args) > 2:
        L.update(json.loads(pathlib.Path(args[2]).read_text()))
    if pathlib.Path(args[1]).exists():
        sys.exit(f"exists, not overwriting (folder law 1): {args[1]}")
    build(args[0], args[1], L)

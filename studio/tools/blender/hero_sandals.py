"""Gold strap sandals painted onto a barefoot hero (Arjuna: the old sheet's gold sandals, an open point in the bible since the
hero set was locked barefoot). Cloud Blender, free.

Painted in UV space into a copy of the body's colour texture, through the body's rest positions, only on skin texels (the
dhoti hem and anything not skin-coloured is left alone):
  sole rim   a dark leather edge with a thin gold line along the ground
  toe strap  across the base of the toes
  cross      two straps crossing over the instep
  ankle      a band round the ankle, joined to the cross by a short strap at the front
Feet are found as the skin below ANKLE_Z; the toe is the foot's -Y end (hero front).

  python hero_sandals.py <hero> <in.blend> <out.blend>
Check render next to <out>: _sandals.jpg (front three-quarter and side of both feet).
"""
import colorsys, math, pathlib, sys
import bpy
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
HERO, IN, OUT = args[:3]
TAG = HERO.upper()
if pathlib.Path(OUT).exists():
    sys.exit(f"exists, not overwriting (folder law 1): {OUT}")
out = pathlib.Path(OUT).resolve()
bpy.ops.wm.open_mainfile(filepath=str(pathlib.Path(IN).resolve()))
bpy.ops.preferences.addon_enable(module="rigify")
scene = bpy.context.scene
for o in list(scene.objects):
    if o.type in ("CAMERA", "LIGHT"):
        bpy.data.objects.remove(o)
body = bpy.data.objects[f"{TAG}_body"]
me = body.data
ANKLE_Z = 0.13
GOLD, GOLD_DK, LEATHER = np.array([0.50, 0.35, 0.11]), np.array([0.30, 0.17, 0.04]), np.array([0.09, 0.05, 0.025])


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


tn = next(n for n in body.active_material.node_tree.nodes
          if n.type == "TEX_IMAGE" and any(l.to_socket.name == "Base Color" for l in n.outputs[0].links))
img = tn.image.copy(); img.name = f"{TAG}_body_colour_sandals"
IW, IH = img.size
px = np.empty(IW * IH * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(IH, IW, 4)

co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
M = np.array(body.matrix_world); co = co @ M[:3, :3].T + M[:3, 3]
me.calc_loop_triangles()
tl = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("loops", tl); tl = tl.reshape(-1, 3)
lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", lv)
luv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get("uv", luv); luv = luv.reshape(-1, 2)


def is_skin(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = np.where(mx > 1e-4, (mx - mn) / np.maximum(mx, 1e-4), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (r >= g) & (g >= b * 0.9) & (sat > 0.25) & (mx > 0.02) & (mx < 0.85)


# the feet: skin-coloured loops below the ankle, per side
tex_at = lambda uv: px[np.clip((uv[:, 1] * IH).astype(int), 0, IH - 1), np.clip((uv[:, 0] * IW).astype(int), 0, IW - 1), :3]
low = co[lv][:, 2] < ANKLE_Z
skin_loop = low & is_skin(tex_at(luv))
feet = {}
for side in (-1, 1):
    P = co[lv[skin_loop & (co[lv][:, 0] * side > 0)]]
    if len(P) < 50:
        continue
    feet[side] = dict(z0=float(P[:, 2].min()), toe=float(np.percentile(P[:, 1], 1)), heel=float(np.percentile(P[:, 1], 99)),
                      xc=float(np.median(P[:, 0])), w=float(np.percentile(P[:, 0], 97) - np.percentile(P[:, 0], 3)))
    print("foot", side, {k: round(v, 3) for k, v in feet[side].items()}, flush=True)


def pattern(p):
    """(gold strength, leather strength) for world points p"""
    side = np.where(p[:, 0] > 0, 1, -1)
    g = np.zeros(len(p)); l_ = np.zeros(len(p))
    for sd, F in feet.items():
        m = side == sd
        if not m.any():
            continue
        q = p[m]
        s = (q[:, 1] - F["toe"]) / (F["heel"] - F["toe"])            # 0 at the toe tip, 1 at the heel
        h = q[:, 2] - F["z0"]
        u = (q[:, 0] - F["xc"]) / max(F["w"], 1e-3) * sd               # across the foot, + toward its outside
        band = lambda x, c, hw: 1 - smoothstep(hw * 0.7, hw, np.abs(x - c))
        sole = (1 - smoothstep(0.010, 0.014, h)) * smoothstep(0.10, 0.16, s)
        rim = band(h, 0.017, 0.004) * smoothstep(0.10, 0.16, s)         # not over the toe tips
        toe = band(s, 0.30, 0.03) * (h < 0.07)
        cross = np.maximum(band(s - 0.95 * u, 0.50, 0.035), band(s + 0.95 * u, 0.50, 0.035)) * (s > 0.33) * (s < 0.72) * (h > 0.02)
        ankle = band(h, 0.092, 0.011) * (s > 0.45)
        front = band(u, 0.0, 0.06) * (s > 0.5) * (s < 0.72) * (h > 0.05) * (h < 0.095)
        g[m] = np.clip(np.maximum.reduce([rim, toe, cross, ankle, front]), 0, 1)
        l_[m] = sole
    return g, l_


painted = 0
Pt = co[lv[tl]]
box = (Pt[..., 2].min(1) < ANKLE_Z + 0.01)
for ti in np.nonzero(box)[0]:
    uv = luv[tl[ti]] * np.array([IW, IH]); p3 = Pt[ti]
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
    xi = np.clip(gx.ravel()[ins], 0, IW - 1); yi = np.clip(gy.ravel()[ins], 0, IH - 1)
    rgb = px[yi, xi, :3]
    sk = is_skin(rgb)
    if not sk.any():
        continue
    g, l_ = pattern(wgt[ins] @ p3)
    g *= sk; l_ *= sk
    shade = rgb.max(-1, keepdims=True) / 0.45                         # keep the painted light and shadow of the skin
    gold = np.clip(GOLD * np.clip(shade, 0.45, 1.4), 0, 1)
    edge = (g > 0.05) & (g < 0.6)
    col = np.where(edge[:, None], GOLD_DK, gold)
    new = rgb * (1 - g[:, None]) + col * g[:, None]
    new = new * (1 - l_[:, None]) + LEATHER * l_[:, None]
    px[yi, xi, :3] = new
    painted += int(((g > 0.5) | (l_ > 0.5)).sum())
img.pixels.foreach_set(px.ravel()); img.pack(); tn.image = img
print("sandal texels painted:", painted, flush=True)

# ---- check renders ---------------------------------------------------------------------------------------------------------------
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = 24
cam = bpy.data.cameras.new("chk"); camo = bpy.data.objects.new("chk", cam); scene.collection.objects.link(camo); scene.camera = camo
cam.type = "ORTHO"; cam.ortho_scale = 0.75
for e, rz in ((3, -25), (1.2, 140)):
    l = bpy.data.lights.new("k", "SUN"); l.energy = e; lo = bpy.data.objects.new("k", l); scene.collection.objects.link(lo)
    lo.rotation_euler = (math.radians(55), 0, math.radians(rz))
scene.world.color = (0.32, 0.32, 0.35)
scene.render.resolution_x, scene.render.resolution_y = 700, 400
shots = []
for az, el in ((25, 18), (90, 8)):
    a, e = math.radians(az), math.radians(el)
    dv = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    camo.location = Vector((0, -0.05, 0.12)) + dv * 3; camo.rotation_euler = dv.to_track_quat("Z", "Y").to_euler()
    p = out.with_name(out.stem + f"_sandals_{az:03d}.png"); scene.render.filepath = str(p); bpy.ops.render.render(write_still=True)
    shots.append(p)
bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
print("saved", OUT, flush=True)
print("shots", " ".join(map(str, shots)), flush=True)

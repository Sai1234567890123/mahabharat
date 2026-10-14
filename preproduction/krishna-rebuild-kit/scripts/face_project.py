"""Project the approved close-up face onto the Krishna head texture (headless Blender).

Usage:
  HEAD_SCALE_MULT=1.25 blender -b --python scripts/face_project.py -- IN.blend REFERENCE.png OUT.blend [PREVIEW_DIR]

The TRELLIS face has the right structure but a different expression and softer detail than the
approved close-up. This script fits a 2D similarity transform (scale, rotation, shift) from the
head's front plane to the reference photo using four landmarks (both eyes, mouth, chin), then
paints the reference colours onto the face-skin texels. Texels near the edge of the face region
fade back to the existing texture, so the join with forehead, ears and neck is soft.

Landmarks are in pixel coordinates of two images and must be updated for a new character:
  MODEL_LM : pixels in the front preview rendered by head_fix.py / head_polish.py (900 px, ortho
             0.5*K m wide, camera centred on x = head centre line, z = z_top - 0.15*K)
  REF_LM   : pixels in the reference image scaled to 1024 x 1024
"""

import math
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
if len(argv) < 3:
    raise SystemExit("usage: blender -b --python face_project.py -- IN.blend REFERENCE.png OUT.blend [PREVIEW_DIR]")
in_blend, ref_png, out_blend = argv[:3]
preview_dir = argv[3] if len(argv) > 3 else None
K = float(os.environ.get("HEAD_SCALE_MULT", "1.0"))

# landmark order: left eye, right eye, mouth centre, chin bottom
MODEL_LM = np.array([(398, 521), (498, 521), (452, 600), (450, 680)], dtype=np.float64)
REF_LM = np.array([(440, 440), (592, 440), (515, 598), (515, 690)], dtype=np.float64)

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
head = bpy.data.objects["KRISHNA_head"]
me = head.data
nv = len(me.vertices)
co = np.empty(nv * 3, dtype=np.float32)
me.vertices.foreach_get("co", co)
# use the Basis (rest) positions, not the smile-deformed mix
if me.shape_keys:
    me.shape_keys.key_blocks[0].data.foreach_get("co", co)
co = co.reshape(nv, 3).astype(np.float64)
xs, ys, zs = co[:, 0], co[:, 1], co[:, 2]
z_top = float(zs.max())
cx = float(np.median(xs[zs > z_top - 0.2 * K]))
# landmarks were measured on a render framed at the ORIGINAL crown top; FOREHEAD_RAISE moved it
zc = z_top - 0.15 * K - float(os.environ.get("FOREHEAD_RAISE", "0")) * K
s_px = 0.5 * K / 900.0
mx = cx + (MODEL_LM[:, 0] - 450) * s_px
mz = zc - (MODEL_LM[:, 1] - 450) * s_px
print("MODEL landmarks (x,z):", np.round(np.stack([mx, mz], 1), 4).tolist(), flush=True)

# affine transform model(x,z) -> ref(u,v) by least squares over the four landmarks
# (scale, shear and shift; lets the face stretch a little differently up and down than across)
Am = np.stack([mx, mz, np.ones_like(mx)], 1)
coef, *_ = np.linalg.lstsq(Am, REF_LM, rcond=None)  # (3, 2)
scale = float(np.sqrt(abs(np.linalg.det(coef[:2, :]))))


def to_ref(x, z):
    return np.stack([x, z, np.ones_like(x)], 1) @ coef


fit = to_ref(mx, mz)
print("FIT residual px:", np.round(np.abs(fit - REF_LM).max(), 2), "scale px/m %.0f" % scale, flush=True)

# reference pixels (bottom-up rows) -> top-down array
ref = bpy.data.images.load(os.path.abspath(ref_png))
rw, rh = ref.size
buf = np.empty(rw * rh * 4, dtype=np.float32)
ref.pixels.foreach_get(buf)
refpx = buf.reshape(rh, rw, 4)[::-1, :, :3]
ku, kv = rw / 1024.0, rh / 1024.0


def sample(u, v):
    uu = np.clip(u * ku, 0, rw - 1.001)
    vv = np.clip(v * kv, 0, rh - 1.001)
    u0, v0 = uu.astype(int), vv.astype(int)
    fu, fv = (uu - u0)[:, None], (vv - v0)[:, None]
    c00, c10 = refpx[v0, u0], refpx[v0, u0 + 1]
    c01, c11 = refpx[v0 + 1, u0], refpx[v0 + 1, u0 + 1]
    return (c00 * (1 - fu) + c10 * fu) * (1 - fv) + (c01 * (1 - fu) + c11 * fu) * fv


# face region on the head
y_front = float(np.percentile(ys[zs > z_top - 0.3 * K], 40))
front = ys < y_front
eye_z = float(mz[:2].mean())
chin_z = float(mz[3])
z_lo, z_hi = chin_z - 0.004, eye_z + float(os.environ.get("FACE_TOP", "0.075")) * K  # up into the raised forehead
half = 0.048 * K
fade = 0.016 * K
wz = np.clip((zs - z_lo) / fade, 0, 1) * np.clip((z_hi - zs) / (1.5 * fade), 0, 1)
wx = np.clip((half - np.abs(xs - cx)) / fade, 0, 1)
w = (wz * wx * front).astype(np.float64)
print("FACE verts weighted", int((w > 0.05).sum()), flush=True)

uv_all = to_ref(xs, zs)
col = sample(uv_all[:, 0], uv_all[:, 1])
# Far from the centre line the reference shows hair and shadow, not skin: drop dark samples there
lum = col @ np.array([0.30, 0.59, 0.11])
w = np.where((np.abs(xs - cx) > 0.032 * K) & (lum < 0.22), 0.0, w)
# Soften the reference's side shadow: lift dark outer samples toward a minimum brightness so the
# cheeks do not show a dark streak when the head turns.
outer = np.abs(xs - cx) > 0.018 * K
floor = 0.34
ramp = np.clip((np.abs(xs - cx) - 0.018 * K) / (0.022 * K), 0, 1)  # smooth, no seam down the middle
lift = 1.0 + (np.where(lum < floor, floor / np.maximum(lum, 0.05), 1.0) - 1.0) * ramp
col = np.clip(col * np.minimum(lift, 2.2)[:, None], 0, 1)

# texture
img = next(n.image for n in me.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and "Image_0" in n.image.name)
W, H = img.size
tb = np.empty(W * H * 4, dtype=np.float32)
img.pixels.foreach_get(tb)
tex = tb.reshape(H, W, 4)
nl = len(me.loops)
lv = np.empty(nl, dtype=np.int32)
me.loops.foreach_get("vertex_index", lv)
uvl = np.empty(nl * 2, dtype=np.float32)
me.uv_layers[0].data.foreach_get("uv", uvl)
uvl = uvl.reshape(nl, 2)
px = np.clip((uvl[:, 0] * W).astype(np.int32), 0, W - 1)
py = np.clip((uvl[:, 1] * H).astype(np.int32), 0, H - 1)
lw = w[lv]
sel = lw > 0.02
acc = np.zeros((H, W, 3), dtype=np.float64)
cnt = np.zeros((H, W), dtype=np.float64)
wgt = np.zeros((H, W), dtype=np.float64)
np.add.at(acc, (py[sel], px[sel]), col[lv[sel]] * lw[sel, None])
np.add.at(cnt, (py[sel], px[sel]), lw[sel])
np.maximum.at(wgt, (py[sel], px[sel]), lw[sel])
have = cnt > 0
mean = np.zeros_like(acc)
mean[have] = acc[have] / cnt[have, None]
# fill gaps between vertices: 6 rounds of 4-neighbour dilation (colour and weight)
for _ in range(6):
    m2, w2, h2 = mean.copy(), wgt.copy(), have.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        sm = np.roll(mean, (dy, dx), axis=(0, 1))
        sw = np.roll(wgt, (dy, dx), axis=(0, 1))
        sh = np.roll(have, (dy, dx), axis=(0, 1))
        take = sh & ~h2
        m2[take], w2[take], h2[take] = sm[take], sw[take], True
    mean, wgt, have = m2, w2, h2
a = np.clip(wgt, 0, 1)[..., None] * 0.92
tex[..., :3] = np.clip(tex[..., :3] * (1 - a) + mean * a, 0, 1)
img.pixels.foreach_set(tex.reshape(-1))
img.update()
img.pack()
print("PROJECTED texels", int(have.sum()), flush=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("SAVED", out_blend, flush=True)

if preview_dir:
    os.makedirs(preview_dir, exist_ok=True)
    scene = bpy.context.scene
    for o in scene.objects:
        if o.type == "ARMATURE":
            o.hide_render = True
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light = "FLAT"
    sh.color_type = "TEXTURE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.world = scene.world or bpy.data.worlds.new("w")
    scene.world.color = (0.6, 0.6, 0.6)
    cd = bpy.data.cameras.new("c")
    cd.type = "ORTHO"
    cd.ortho_scale = 0.5 * K
    cam = bpy.data.objects.new("c", cd)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cy = float((ys.max() + ys.min()) * 0.5)
    views = {
        "proj_front": ((cx, cy - 5, zc), (math.radians(90), 0, 0)),
        "proj_three_quarter": ((cx + 3.5, cy - 3.5, zc), (math.radians(90), 0, math.radians(45))),
    }
    for name, (loc, rot) in views.items():
        cam.location, cam.rotation_euler = loc, rot
        scene.render.filepath = os.path.join(preview_dir, name + ".png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", scene.render.filepath, flush=True)

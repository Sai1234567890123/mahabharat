"""Project the approved close-up's necklace and garlands onto the body's chest texture (headless Blender).

Usage:
  blender -b --python scripts/chest_project.py -- IN.blend REFERENCE.png OUT.blend [PREVIEW_PNG]

Same idea as face_project.py: a least-squares affine fit from the body's front plane (x, z) to the
reference photo using three landmarks (base of the neck, pendant gem, right shoulder top), then the
reference colours are painted onto the chest-skin texels with soft edges. The neck stays the
model's own so it matches the head, and the watermark corner of the reference is skipped.

MODEL_LM are pixel positions in the chest preview made by chest_view (1000 px, ortho 0.7 m wide,
camera centred on x = 0, z = 1.30). REF_LM are pixels in the reference scaled to 1024 x 1024.
"""

import math
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1 :]
in_blend, ref_png, out_blend = argv[:3]
preview = argv[3] if len(argv) > 3 else None

MODEL_LM = np.array([(490, 385), (498, 508), (790, 470)], dtype=np.float64)  # neck base, gem, right shoulder
REF_LM = np.array([(515, 745), (520, 930), (900, 790)], dtype=np.float64)
ZC, ORTHO = 1.30, 0.7

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
body = bpy.data.objects["KRISHNA_body"]
me = body.data
nv = len(me.vertices)
co = np.empty(nv * 3, dtype=np.float32)
me.vertices.foreach_get("co", co)
co = co.reshape(nv, 3).astype(np.float64)
xs, ys, zs = co[:, 0], co[:, 1], co[:, 2]

s_px = ORTHO / 1000.0
mx = (MODEL_LM[:, 0] - 500) * s_px
mz = ZC - (MODEL_LM[:, 1] - 500) * s_px
coef, *_ = np.linalg.lstsq(np.stack([mx, mz, np.ones(3)], 1), REF_LM, rcond=None)


def to_ref(x, z):
    return np.stack([x, z, np.ones_like(x)], 1) @ coef


print("FIT residual", np.abs(to_ref(mx, mz) - REF_LM).max(), flush=True)

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
    return (refpx[v0, u0] * (1 - fu) + refpx[v0, u0 + 1] * fu) * (1 - fv) + (refpx[v0 + 1, u0] * (1 - fu) + refpx[v0 + 1, u0 + 1] * fu) * fv


uv_all = to_ref(xs, zs)
col = sample(uv_all[:, 0], uv_all[:, 1])
front = ys < float(np.percentile(ys[(zs > 1.0) & (zs < 1.45)], 45))
z_neck, z_bot = float(mz[0]) - 0.010, 1.25
w = (
    np.clip((z_neck - zs) / 0.012, 0, 1)
    * np.clip((zs - z_bot) / 0.025, 0, 1)
    * np.clip((0.23 - np.abs(xs)) / 0.02, 0, 1)
    * front
)
# skip the watermark corner of the reference and anything outside the picture
inside = (uv_all[:, 0] > 70) & (uv_all[:, 0] < 960) & (uv_all[:, 1] < 1015)
wm = (uv_all[:, 0] > 850) & (uv_all[:, 1] > 930)
w = w * inside * (~wm)
print("CHEST verts weighted", int((w > 0.05).sum()), flush=True)

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
# Rasterise each triangle in UV space and interpolate colour and weight across it, so the paint
# is continuous (no blocky patches) and stays inside the chest triangles.
me.calc_loop_triangles()
ntri = len(me.loop_triangles)
tl = np.empty(ntri * 3, dtype=np.int32)
me.loop_triangles.foreach_get("loops", tl)
tl = tl.reshape(-1, 3)
tvv = lv[tl]
keep = (w[tvv].min(axis=1) > 0.0) | (w[tvv].max(axis=1) > 0.3)
tl, tvv = tl[keep], tvv[keep]
print("TRIANGLES", len(tl), flush=True)
mean = np.zeros((H, W, 3))
wgt = np.zeros((H, W))
for loops, verts in zip(tl, tvv):
    q = uvl[loops] * np.array([W, H])
    x0, x1 = int(np.floor(q[:, 0].min())), int(np.ceil(q[:, 0].max()))
    y0, y1 = int(np.floor(q[:, 1].min())), int(np.ceil(q[:, 1].max()))
    if x1 < 0 or y1 < 0 or x0 >= W or y0 >= H or (x1 - x0) > 40 or (y1 - y0) > 40:
        continue
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, W - 1), min(y1, H - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    d = (q[1, 1] - q[2, 1]) * (q[0, 0] - q[2, 0]) + (q[2, 0] - q[1, 0]) * (q[0, 1] - q[2, 1])
    if abs(d) < 1e-9:
        continue
    l0 = ((q[1, 1] - q[2, 1]) * (gx - q[2, 0]) + (q[2, 0] - q[1, 0]) * (gy - q[2, 1])) / d
    l1 = ((q[2, 1] - q[0, 1]) * (gx - q[2, 0]) + (q[0, 0] - q[2, 0]) * (gy - q[2, 1])) / d
    l2 = 1 - l0 - l1
    inside_t = (l0 >= -0.02) & (l1 >= -0.02) & (l2 >= -0.02)
    if not inside_t.any():
        continue
    c = l0[..., None] * col[verts[0]] + l1[..., None] * col[verts[1]] + l2[..., None] * col[verts[2]]
    ww = l0 * w[verts[0]] + l1 * w[verts[1]] + l2 * w[verts[2]]
    sl = (slice(y0, y1 + 1), slice(x0, x1 + 1))
    better = inside_t & (ww > wgt[sl])
    mean[sl][better] = c[better]
    wgt[sl][better] = ww[better]
have = wgt > 0
a = np.clip(wgt, 0, 1)[..., None] * 0.95
tex[..., :3] = np.clip(tex[..., :3] * (1 - a) + mean * a, 0, 1)
img.pixels.foreach_set(tex.reshape(-1))
img.update()
img.pack()
print("PROJECTED texels", int(have.sum()), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("SAVED", out_blend, flush=True)

if preview:
    sc = bpy.context.scene
    for o in sc.objects:
        if o.type == "ARMATURE":
            o.hide_render = True
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "FLAT"
    sh.color_type = "TEXTURE"
    sc.render.resolution_x = sc.render.resolution_y = 1000
    sc.world = sc.world or bpy.data.worlds.new("w")
    sc.world.color = (0.6, 0.6, 0.6)
    cd = bpy.data.cameras.new("c")
    cd.type = "ORTHO"
    cd.ortho_scale = ORTHO
    cam = bpy.data.objects.new("c", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = (0, -6, ZC)
    cam.rotation_euler = (math.radians(90), 0, 0)
    sc.render.filepath = os.path.abspath(preview)
    bpy.ops.render.render(write_still=True)

#!/usr/bin/env python3
"""Repaint Karna's face, chest sun-face, crown, back of the head and back plate from his approved model sheets. FREE.

  python studio/tools/blender/karna_texture_project.py WORK.blend FRONT.png BACK.png OUT.blend OUT_TEXTURE.png

TRELLIS.2 built the body from FRONT.png, so the sheet lines up with the model seen straight on: the figure's bounding box
in the sheet (height = 1.9 m, centred) maps model x, z to sheet pixels, and BACK.png lines up the same way, mirrored.
Every texel of the body texture is found in 3D by rasterising the UV triangles. A texel takes the sheet colour where its
surface faces the camera, is the nearest surface along that view (depth test), and lies inside the head and torso area.
The weight fades out toward the sides and the area edges, so the join with the old texture is soft. Arms and dhoti keep
their TRELLIS paint (the sheets are wider there than the model). Never overwrites.
"""
import pathlib, sys

import bpy
import numpy as np
from PIL import Image

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
if len(argv) != 5:
    raise SystemExit(__doc__)
work, front_png, back_png, out_blend, out_tex = (pathlib.Path(p).resolve() for p in argv)
for p in (out_blend, out_tex):
    if p.exists():
        raise SystemExit(f"exists, not overwriting (folder law 1): {p}")

HEIGHT = 1.9


def sheet_map(path):
    """sheet pixels and the scale and offsets that map model (x, z) to sheet (u, v)"""
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32) / 255
    fig = np.abs(a - a[2, 2]).sum(2) > 40 / 255
    ys, xs = np.nonzero(fig)
    s = (ys.max() - ys.min()) / HEIGHT
    return a, fig, s, (xs.min() + xs.max()) / 2, ys.max()


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


bpy.ops.wm.open_mainfile(filepath=str(work))
body = bpy.data.objects["KARNA_body"]
me = body.data
nt = body.active_material.node_tree
tex_node = next(n for n in nt.nodes if n.type == "TEX_IMAGE" and "basecolor" in n.image.filepath)
img = tex_node.image
TW, TH = img.size
buf = np.empty(TW * TH * 4, np.float32)
img.pixels.foreach_get(buf)
tex = buf.reshape(TH, TW, 4)                                   # row 0 = bottom (v = 0)

# ---- texel positions: rasterise the UV triangles ---------------------------------------------------------------------
me.calc_loop_triangles()
nt_ = len(me.loop_triangles)
tl = np.empty(nt_ * 3, np.int32); me.loop_triangles.foreach_get("loops", tl); tl = tl.reshape(-1, 3)
tv = np.empty(nt_ * 3, np.int32); me.loop_triangles.foreach_get("vertices", tv); tv = tv.reshape(-1, 3)
uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
vn = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("normal", vn); vn = vn.reshape(-1, 3)

# only triangles in the head and torso box
c3 = co[tv]                                                    # (T, 3, 3)
torso_tri = (np.abs(c3[..., 0]).min(1) < 0.30) & (c3[..., 2].max(1) > 0.95)
arm_tri = (np.abs(c3[..., 0]).max(1) > 0.17) & (np.abs(c3[..., 0]).min(1) < 0.60) & (c3[..., 2].min(1) > 0.80) & (c3[..., 2].max(1) < 1.60)
keep = torso_tri | arm_tri
tl, tv = tl[keep], tv[keep]
P = uv[tl] * [TW, TH] - 0.5                                    # texel-centre space
lo = np.floor(P.min(1)).astype(int); hi = np.ceil(P.max(1)).astype(int)
size = (hi - lo).max(1)
pix_t, pix_xy, pix_b = [], [], []


def raster(ids, K):
    g = np.stack(np.meshgrid(np.arange(K + 1), np.arange(K + 1)), -1).reshape(-1, 2)
    for s0 in range(0, len(ids), 4000):
        t = ids[s0:s0 + 4000]
        q = lo[t][:, None, :] + g[None]                        # (n, G, 2)
        a, b, c = P[t, 0][:, None], P[t, 1][:, None], P[t, 2][:, None]
        v0, v1, v2 = b - a, c - a, q - a
        d00 = (v0 * v0).sum(-1); d01 = (v0 * v1).sum(-1); d11 = (v1 * v1).sum(-1)
        d20 = (v2 * v0).sum(-1); d21 = (v2 * v1).sum(-1)
        den = d00 * d11 - d01 * d01
        den = np.where(np.abs(den) < 1e-12, 1e-12, den)
        w1 = (d11 * d20 - d01 * d21) / den; w2 = (d00 * d21 - d01 * d20) / den; w0 = 1 - w1 - w2
        inside = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4) & (q[..., 0] >= 0) & (q[..., 0] < TW) & (q[..., 1] >= 0) & (q[..., 1] < TH)
        ti, gi = np.nonzero(inside)
        pix_t.append(t[ti]); pix_xy.append(q[ti, gi]); pix_b.append(np.stack([w0[ti, gi], w1[ti, gi], w2[ti, gi]], 1))


small = np.nonzero(size <= 12)[0]
raster(small, 12)
big = np.nonzero(size > 12)[0]
for t in big:
    raster(np.array([t]), int(size[t]))
T = np.concatenate(pix_t); XY = np.concatenate(pix_xy); B = np.concatenate(pix_b)
pos = (co[tv[T]] * B[..., None]).sum(1)
nor = (vn[tv[T]] * B[..., None]).sum(1)
nor /= np.maximum(np.linalg.norm(nor, axis=1, keepdims=True), 1e-8)
print("texels in the head and torso box", len(T), "from", len(tl), "triangles", flush=True)
x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]

# head: crown to chin, torso: shoulders to the belt, never the arms
torso = smooth(0.0, 1.0, (0.215 - np.abs(x)) / 0.03) * smooth(0.0, 1.0, (z - 1.00) / 0.04)
head = smooth(0.0, 1.0, (0.13 - np.abs(x)) / 0.03) * (z > 1.55)
region = np.maximum(torso, head)
# arms: upper arm and forearm skin only (the sheet's bracers and gold are left to the TRELLIS paint, which matches them)
arm = smooth(0.17, 0.21, np.abs(x)) * smooth(0.58, 0.53, np.abs(x)) * smooth(0.80, 0.88, z) * smooth(1.58, 1.48, z)

acc = np.zeros((TH, TW, 3), np.float32); wsum = np.zeros((TH, TW), np.float32)
for path, sign in ((front_png, 1), (back_png, -1)):
    a, fig, s, cx, bot = sheet_map(path)
    u = cx + sign * x * s                                     # seen from behind, his left is on the sheet's left
    v = bot - z * s
    facing = smooth(0.30, 0.65, -sign * nor[:, 1])
    facing_arm = smooth(-0.35, 0.10, -sign * nor[:, 1])           # the outside of the arm turns away from both sheets
    # depth test: nearest surface to this camera per sheet pixel
    ui, vi = np.clip(u.astype(int), 0, a.shape[1] - 1), np.clip(v.astype(int), 0, a.shape[0] - 1)
    depth = -sign * y                                         # larger = nearer the camera
    near = np.full(a.shape[:2], -9.0, np.float32)
    np.maximum.at(near, (vi, ui), depth)
    visible = depth >= near[vi, ui] - 0.012
    # bilinear sample of the sheet; inside the figure only
    u0 = np.clip(np.floor(u).astype(int), 0, a.shape[1] - 2); v0 = np.clip(np.floor(v).astype(int), 0, a.shape[0] - 2)
    fu = np.clip(u - u0, 0, 1)[:, None]; fv = np.clip(v - v0, 0, 1)[:, None]
    col = (a[v0, u0] * (1 - fu) + a[v0, u0 + 1] * fu) * (1 - fv) + (a[v0 + 1, u0] * (1 - fu) + a[v0 + 1, u0 + 1] * fu) * fv
    r_, g_, b_ = col[:, 0], col[:, 1], col[:, 2]
    skin = smooth(0.12, 0.20, r_) * smooth(0.30, 0.38, b_ / np.maximum(r_, 1e-4)) * smooth(0.82, 0.74, g_ / np.maximum(r_, 1e-4))
    w_arm = arm * facing_arm * skin
    w = np.maximum(region * facing, w_arm) * visible * fig[vi, ui]
    sel = w > 0.01
    px, py = XY[sel, 0].astype(int), XY[sel, 1].astype(int)
    np.add.at(acc, (py, px), col[sel] * w[sel, None])
    np.add.at(wsum, (py, px), w[sel])
    print(path.name, "scale %.1f px/m" % s, "texels painted", int(sel.sum()), "arm skin", int((w_arm * visible * fig[vi, ui] > 0.01).sum()), flush=True)

have = wsum > 0
mean = np.zeros_like(acc); mean[have] = acc[have] / wsum[have, None]
alpha = np.clip(wsum, 0, 1)
for _ in range(2):                                            # carry the new paint 2 texels past the island edges
    m2, a2, h2 = mean.copy(), alpha.copy(), have.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        sm, sa, sh = (np.roll(arr, (dy, dx), axis=(0, 1)) for arr in (mean, alpha, have))
        take = sh & ~h2
        m2[take], a2[take], h2[take] = sm[take], sa[take], True
    mean, alpha, have = m2, a2, h2
# sheets are sRGB; Blender holds this texture in linear floats only if it is not sRGB, so convert to match
if img.colorspace_settings.name.lower().startswith("srgb") and img.is_float:
    mean = np.where(mean <= 0.04045, mean / 12.92, ((mean + 0.055) / 1.055) ** 2.4)
sheet_rows = mean
a3 = (alpha * 0.95)[..., None]
tex[..., :3] = np.clip(tex[..., :3] * (1 - a3) + sheet_rows * a3, 0, 1)
print("texels changed", int((alpha > 0.01).sum()), "of", TW * TH, flush=True)

# crack fill on the arms: the underside of the arm faces neither sheet, so its TRELLIS paint keeps thin dark cracks.
# Any arm texel much darker than the median of its neighbourhood takes that median instead.
from PIL import ImageFilter
arm_mask = np.zeros((TH, TW), bool)
am = arm > 0.3
arm_mask[XY[am, 1].astype(int), XY[am, 0].astype(int)] = True
rgb8 = Image.fromarray((np.clip(tex[..., :3], 0, 1) * 255).astype(np.uint8))
med = np.asarray(rgb8.filter(ImageFilter.MedianFilter(9))).astype(np.float32) / 255
lum = tex[..., :3] @ np.array([0.30, 0.59, 0.11], np.float32)
mlum = med @ np.array([0.30, 0.59, 0.11], np.float32)
crack = arm_mask & (lum < 0.80 * mlum)
crack = np.asarray(Image.fromarray(crack.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(3))) > 0
crack &= arm_mask
tex[crack, :3] = med[crack]
print("arm crack texels filled", int(crack.sum()), "of", int(arm_mask.sum()), "arm texels", flush=True)

out = bpy.data.images.new(out_tex.stem, TW, TH, alpha=True)
out.pixels.foreach_set(tex.reshape(-1))
out.filepath_raw = str(out_tex)
out.file_format = "PNG"
out.save()
new = bpy.data.images.load(str(out_tex))
new.filepath = bpy.path.relpath(str(out_tex), start=str(out_blend.parent))   # the PC opens it from its own folder
new.colorspace_settings.name = img.colorspace_settings.name
tex_node.image = new
bpy.ops.wm.save_as_mainfile(filepath=str(out_blend), relative_remap=True)
print("wrote", out_tex, "and", out_blend, flush=True)

"""Enlarge the left iris to match the right, from marks on the 600 px front render (headless Blender).

Usage:
  HEAD_SCALE_MULT=1.25 blender -b --python scripts/iris_mark.py -- IN.blend OUT.blend

Marks (confirmed by sai) are pixel positions on the 600 px neutral front render: right iris (360, 265),
left iris (244, 267), radius about 3.5 px (right) and about 3.0 px (left). Each render pixel is mapped to
the nearest front vertex (ortho camera: 0.34 m across 600 px, centred on the head), and that vertex's UV
gives the texel centre. The left iris texels are then resampled so the left iris grows by the ratio of the
two radii, with a soft edge.
"""

import os
import sys

import bpy
import numpy as np
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index("--") + 1 :]
in_blend, out_blend = argv[0], argv[1]
K = float(os.environ.get("HEAD_SCALE_MULT", "1.0"))
RIGHT_PX, LEFT_PX = (360, 265), (244, 267)
R_RIGHT, R_LEFT = 3.5, 3.0
ORTHO, RES = 0.34, 600.0

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
head = bpy.data.objects["KRISHNA_head"]
me = head.data
nv = len(me.vertices)
co = np.empty(nv * 3, dtype=np.float32)
(me.shape_keys.key_blocks[0].data if me.shape_keys else me.vertices).foreach_get("co", co)
co = co.reshape(nv, 3).astype(np.float64)
xs, ys, zs = co[:, 0], co[:, 1], co[:, 2]
z_top = zs.max()
cx = float(np.median(xs[zs > z_top - 0.2 * K]))
y_front = float(np.percentile(ys[zs > z_top - 0.3 * K], 40))
front_idx = np.nonzero(ys < y_front)[0]
cam_z = z_top - 0.215 * K
mpp = ORTHO / RES

img = next(n.image for n in me.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and "Image_0" in n.image.name)
W, H = img.size
nl = len(me.loops)
lv = np.empty(nl, dtype=np.int32)
me.loops.foreach_get("vertex_index", lv)
uvl = np.empty(nl * 2, dtype=np.float32)
me.uv_layers[0].data.foreach_get("uv", uvl)
uvl = uvl.reshape(nl, 2)
vuv = np.zeros((nv, 2))
vuv[lv[::-1]] = uvl[::-1]
kd = KDTree(len(front_idx))
for k, i in enumerate(front_idx):
    kd.insert((xs[i], zs[i], 0.0), k)
kd.balance()


def px_to_texel(px, py):
    x = cx + (px - RES / 2) * mpp
    z = cam_z - (py - RES / 2) * mpp
    _, k, _ = kd.find((x, z, 0.0))
    v = front_idx[k]
    return vuv[v, 0] * W, vuv[v, 1] * H


rc = px_to_texel(*RIGHT_PX)
lc = px_to_texel(*LEFT_PX)
print("TEXEL right iris %.1f,%.1f  left iris %.1f,%.1f" % (rc[0], rc[1], lc[0], lc[1]), flush=True)

pb = np.empty(W * H * 4, dtype=np.float32)
img.pixels.foreach_get(pb)
tex = pb.reshape(H, W, 4).copy()
# texel radius per render pixel: iris radius in texels scales with the local texel density
tpx = np.sqrt(((vuv[front_idx[:1], 0]) ** 2).sum())  # placeholder for clarity
texels_per_m = 1852.0  # measured on this head (texel.py, 2048 px texture)
iris_r_tex = R_LEFT * mpp * texels_per_m
ratio = R_LEFT / R_RIGHT  # output(p) = input(c + (p - c) * ratio): iris grows from R_LEFT to R_RIGHT
cxl, cyl = lc
reach = int(R_RIGHT * mpp * texels_per_m * 3.0) + 4
x0, x1 = max(int(cxl) - reach, 0), min(int(cxl) + reach, W)
y0, y1 = max(int(cyl) - reach, 0), min(int(cyl) + reach, H)
gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
sx = np.clip(cxl + (gx - cxl) * ratio, 0, W - 1.001)
sy = np.clip(cyl + (gy - cyl) * ratio, 0, H - 1.001)
ix, iy = sx.astype(int), sy.astype(int)
fx, fy = (sx - ix)[..., None], (sy - iy)[..., None]
samp = (tex[iy, ix, :3] * (1 - fx) + tex[iy, ix + 1, :3] * fx) * (1 - fy) + (tex[iy + 1, ix, :3] * (1 - fx) + tex[iy + 1, ix + 1, :3] * fx) * fy
rr = np.sqrt((gx - cxl) ** 2 + (gy - cyl) ** 2) / reach
wgt = np.clip((1.0 - rr) / 0.25, 0.0, 1.0)[..., None]
tex[y0:y1, x0:x1, :3] = samp * wgt + tex[y0:y1, x0:x1, :3] * (1 - wgt)
img.pixels.foreach_set(tex.reshape(-1))
img.update()
img.pack()
print("IRIS left grown by %.2fx (reach %d texels)" % (1 / ratio, reach), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("SAVED", out_blend, flush=True)

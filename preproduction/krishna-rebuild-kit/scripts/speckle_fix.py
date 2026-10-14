"""Inpaint bright speckles on the cheek below the left eye (headless Blender).

Usage:
  HEAD_SCALE_MULT=1.25 blender -b --python scripts/speckle_fix.py -- IN.blend OUT.blend

eye_match.py can leave a few light texels on the cheek under the left eye. This finds texels there
that are much brighter than their 5x5 neighbourhood median and replaces them with that median.
Only texels owned by vertices in the cheek patch are touched.
"""

import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1 :]
in_blend, out_blend = argv[0], argv[1]
K = float(os.environ.get("HEAD_SCALE_MULT", "1.0"))

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
z_chin = z_top - 0.30 * K - 0.014 * K
eye_z = z_chin + 0.0883 * K
y_front = float(np.percentile(ys[zs > z_top - 0.3 * K], 40))
dx = xs - cx
cheek = (ys < y_front) & (zs < eye_z - 0.006 * K) & (zs > eye_z - 0.030 * K) & (dx < -0.010 * K) & (dx > -0.045 * K)

img = next(n.image for n in me.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and "Image_0" in n.image.name)
W, H = img.size
pb = np.empty(W * H * 4, dtype=np.float32)
img.pixels.foreach_get(pb)
tex = pb.reshape(H, W, 4)
nl = len(me.loops)
lv = np.empty(nl, dtype=np.int32)
me.loops.foreach_get("vertex_index", lv)
uvl = np.empty(nl * 2, dtype=np.float32)
me.uv_layers[0].data.foreach_get("uv", uvl)
uvl = uvl.reshape(nl, 2)
sel = cheek[lv]
px = np.clip((uvl[sel, 0] * W).astype(int), 2, W - 3)
py = np.clip((uvl[sel, 1] * H).astype(int), 2, H - 3)
mask = np.zeros((H, W), dtype=bool)
mask[py, px] = True
mask = mask | np.roll(mask, 1, 0) | np.roll(mask, -1, 0) | np.roll(mask, 1, 1) | np.roll(mask, -1, 1)
mask[:2] = mask[-2:] = False
mask[:, :2] = mask[:, -2:] = False

lum = tex[..., :3] @ np.array([0.30, 0.59, 0.11], dtype=np.float32)
# local 5x5 median luminance (computed only where the mask is set)
ys_, xs_ = np.nonzero(mask)
print('CANDIDATES', len(ys_), flush=True)
fixed = 0
for y, x in zip(ys_, xs_):
    patch = lum[y - 2 : y + 3, x - 2 : x + 3]
    med = np.median(patch)
    if lum[y, x] > med + float(os.environ.get("SPECK_THR", "0.05")):
        win = tex[y - 2 : y + 3, x - 2 : x + 3, :3].reshape(-1, 3)
        lw = patch.reshape(-1)
        order = np.argsort(lw)
        tex[y, x, :3] = win[order[len(order) // 2]]
        fixed += 1
print("SPECKLES fixed", fixed, flush=True)
img.pixels.foreach_set(tex.reshape(-1))
img.update()
img.pack()
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("SAVED", out_blend, flush=True)

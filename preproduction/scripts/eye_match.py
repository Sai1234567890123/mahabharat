"""Make the two eyes of the Krishna head match (headless Blender).

Usage:
  HEAD_SCALE_MULT=1.25 blender -b --python scripts/eye_match.py -- IN.blend OUT.blend

The projected face has one eye (image left) heavier than the other. This copies the texture of the
clean eye onto the heavier eye, but only for texels in a tight eye-only band, and only where each
mirrored vertex is close to its twin (so the cheek and brow are never touched).
"""

import os
import sys

import bpy
import numpy as np
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index("--") + 1 :]
in_blend, out_blend = argv[0], argv[1]
K = float(os.environ.get("HEAD_SCALE_MULT", "1.0"))
CLEAN = os.environ.get("CLEAN_EYE", "right")  # which eye is the clean one (image right = character's left)

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
front = ys < y_front
# eye centre height: measured from the approved front render (eyes at ~0.0883 m above the chin, K-scaled)
z_chin = z_top - 0.30 * K - 0.014 * K
eye_z = z_chin + 0.0883 * K
dx = xs - cx

band = front & (np.abs(zs - eye_z) < 0.0042 * K)
left = band & (dx < -0.017 * K) & (dx > -0.036 * K)
right = band & (dx > 0.017 * K) & (dx < 0.036 * K)
src_side, dst_side = (right, left) if CLEAN == "right" else (left, right)

kd = KDTree(len(xs))
for i in np.nonzero(src_side)[0]:
    kd.insert((xs[i], ys[i], zs[i]), int(i))
kd.balance()

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
vuv = np.zeros((nv, 2))
vuv[lv[::-1]] = uvl[::-1]
px = np.clip((vuv[:, 0] * W).astype(int), 0, W - 1)
py = np.clip((vuv[:, 1] * H).astype(int), 0, H - 1)
col = tex[py, px, :3].copy()

changed = 0
for i in np.nonzero(dst_side)[0]:
    mx, my, mz = 2 * cx - xs[i], ys[i], zs[i]
    _, j, dist = kd.find((mx, my, mz))
    # skip bright sclera texels: copying them lands white specks on the cheek
    lum_src = col[j] @ np.array([0.30, 0.59, 0.11])
    lum_dst = col[i] @ np.array([0.30, 0.59, 0.11])
    if dist < 0.0012 * K and lum_src - lum_dst < 0.18:
        col[i] = col[j]
        changed += 1
print("EYE twins copied", changed, "of", int(dst_side.sum()), flush=True)

# write back at the destination vertices' texels (only the texels those vertices own)
sel_loops = dst_side[lv]
tex[py[lv[sel_loops]], px[lv[sel_loops]], :3] = col[lv[sel_loops]]
img.pixels.foreach_set(tex.reshape(-1))
img.update()
img.pack()
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("SAVED", out_blend, flush=True)

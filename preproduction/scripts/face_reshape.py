"""Reshape the joined Krishna head toward the approved face proportions (headless Blender).

Usage:
  HEAD_SCALE_MULT=1.25 blender -b --python scripts/face_reshape.py -- IN.blend OUT.blend

Run after head_fix.py and before head_polish.py. Comparing an aligned render with the approved
close-up showed four structural differences, which this script corrects with smooth displacement
fields (no seams, no new vertices):
  1. Forehead: the crown sat too low and hid the forehead, so everything above the brow is raised.
  2. Crown: slightly wide at the sides, so it is narrowed a little above the brow.
  3. Earrings and ears: too far out, so they are pulled toward the face.
  4. Jaw and neck: the jaw is eased toward a more pointed chin and the neck (head and body parts)
     is slimmed.
All amounts scale with HEAD_SCALE_MULT.
"""

import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1 :]
in_blend, out_blend = argv[0], argv[1]
K = float(os.environ.get("HEAD_SCALE_MULT", "1.0"))
RAISE = float(os.environ.get("FOREHEAD_RAISE", "0.014"))
CROWN_NARROW = float(os.environ.get("CROWN_NARROW", "0.06"))
EAR_IN = float(os.environ.get("EAR_IN", "0.14"))
JAW_IN = float(os.environ.get("JAW_IN", "0.07"))
NECK_IN = float(os.environ.get("NECK_IN", "0.18"))
DEPTH = float(os.environ.get("HEAD_DEPTH", "1.30"))  # front-to-back stretch; TRELLIS heads come out too shallow

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
head = bpy.data.objects["KRISHNA_head"]
body = bpy.data.objects["KRISHNA_body"]
feather = bpy.data.objects.get("KRISHNA_feather")


def smooth(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def get(obj):
    n = len(obj.data.vertices)
    a = np.empty(n * 3, dtype=np.float32)
    obj.data.vertices.foreach_get("co", a)
    return a.reshape(n, 3).astype(np.float64)


def put(obj, a):
    obj.data.vertices.foreach_set("co", a.astype(np.float32).reshape(-1))
    obj.data.update()


h = get(head)
z_top = h[:, 2].max()
cx = float(np.median(h[h[:, 2] > z_top - 0.2 * K, 0]))
z_chin = z_top - 0.30 * K
brow = z_chin + 0.125 * K
x, z = h[:, 0] - cx, h[:, 2]

# 3. ears/earrings in (outer verts around chin..cheek height)
wz = smooth((z - (z_chin - 0.02 * K)) / (0.02 * K)) * (1 - smooth((z - (z_chin + 0.09 * K)) / (0.03 * K)))
wx = smooth((np.abs(x) - 0.058 * K) / (0.012 * K))
x = x * (1 - EAR_IN * wz * wx)
# 4. jaw toward a more pointed chin
wj = smooth((z - z_chin + 0.004 * K) / (0.008 * K)) * (1 - smooth((z - (z_chin + 0.045 * K)) / (0.02 * K)))
wjx = 1 - smooth((np.abs(x) - 0.052 * K) / (0.012 * K))
x = x * (1 - JAW_IN * wj * wjx)
# 4b. neck of the head mesh
wn = smooth((z_chin - z) / (0.02 * K))
x = x * (1 - NECK_IN * wn)
# 2. crown narrower above the brow
wc = smooth((z - (brow + 0.03 * K)) / (0.04 * K))
x = x * (1 - CROWN_NARROW * wc)
# 1. forehead raised: everything above the brow moves up
dz = RAISE * K * smooth((z - brow) / (0.04 * K))
h[:, 0] = cx + x
h[:, 2] = z + dz
# depth: stretch front-to-back about the ear plane (middle of the head at cheek height) so the
# skull, crown and nose gain volume; seen from the side the head was about 25% too shallow
band = (z > z_chin) & (z < z_chin + 0.10 * K)
y_pivot = float((h[band, 1].max() + h[band, 1].min()) * 0.5)
h[:, 1] = y_pivot + (h[:, 1] - y_pivot) * DEPTH
put(head, h)
if feather is not None:
    feather.location.z += RAISE * K
    feather.location.y = y_pivot + (feather.location.y - y_pivot) * DEPTH
    for ob in (feather,):
        pass

# body neck slimmed: only the narrow column above the trapezius
b = get(body)
bz_top = b[:, 2].max()
bx = b[:, 0] - cx
w_xx = 1 - smooth((np.abs(bx) - 0.085) / (0.03))
w_zz = smooth((b[:, 2] - (bz_top - 0.10)) / (0.06))
b[:, 0] = cx + bx * (1 - NECK_IN * w_xx * w_zz)
b[:, 1] = y_pivot + (b[:, 1] - y_pivot) * (1 + (DEPTH - 1) * w_xx * w_zz)  # deeper neck to meet the deeper head
put(body, b)
print("RESHAPE done: raise %.4f m, crown -%.0f%%, ear -%.0f%%, jaw -%.0f%%, neck -%.0f%%" % (RAISE * K, CROWN_NARROW * 100, EAR_IN * 100, JAW_IN * 100, NECK_IN * 100), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("SAVED", out_blend, flush=True)

"""Move the nose tip and chin of the Krishna head to the approved side profile (headless Blender).

Usage:
  HEAD_SCALE_MULT=1.25 blender -b --python scripts/profile_fix.py -- IN.blend OUT.blend

Marks taken from the approved side image (grid, confirmed by sai): eye (512, 213), nose tip (539, 233),
chin (523, 278) in source pixels. Scale comes from the eye-to-chin distance on the model, so the
offsets are in metres. Nose and chin are pushed or pulled along the depth axis (Y) with a Gaussian
falloff, so the rest of the face does not move.
"""

import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1 :]
in_blend, out_blend = argv[0], argv[1]
K = float(os.environ.get("HEAD_SCALE_MULT", "1.0"))

APPROVED = {"eye": (512, 213), "nose": (539, 233), "chin": (523, 278)}

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
front = ys < y_front
dxc = np.abs(xs - cx)

# face surface depth at the eye, nose and chin levels (frontmost points near the centre line)
def front_y(z_lo, z_hi, half):
    m = front & (zs > z_lo) & (zs < z_hi) & (dxc < half)
    return float(ys[m].min()) if m.any() else None, m

eye_y, _ = front_y(eye_z - 0.006 * K, eye_z + 0.006 * K, 0.02 * K)
nose_y, nose_m = front_y(eye_z - 0.040 * K, eye_z - 0.012 * K, 0.012 * K)
chin_y, chin_m = front_y(z_chin - 0.004 * K, z_chin + 0.012 * K, 0.030 * K)
print("EYE y %.4f  NOSE y %.4f  CHIN y %.4f" % (eye_y, nose_y, chin_y), flush=True)

# metres per source pixel from the eye-to-chin distance on the model vs the approved image
model_drop = eye_z - z_chin
approved_drop = APPROVED["chin"][1] - APPROVED["eye"][1]
s = model_drop / approved_drop
target_nose_y = eye_y - (APPROVED["nose"][0] - APPROVED["eye"][0]) * s
target_chin_y = eye_y - (APPROVED["chin"][0] - APPROVED["eye"][0]) * s
print("SCALE %.5f m/px  nose target y %.4f (was %.4f)  chin target y %.4f (was %.4f)" % (s, target_nose_y, nose_y, target_chin_y, chin_y), flush=True)

def gauss(cz, cy_, sz, sy):
    return np.exp(-(((zs - cz) / sz) ** 2 + ((xs - cx) / (0.035 * K)) ** 2) / 2.0) * front

NOSE_FRACTION = float(os.environ.get("NOSE_FRACTION", "0.6"))  # full target gave a beak; 60% reads as the approved nose
w_nose = np.exp(-(((zs - (eye_z - 0.026 * K)) / (0.020 * K)) ** 2 + ((xs - cx) / (0.024 * K)) ** 2) / 2.0) * front
w_chin = np.exp(-(((zs - (z_chin + 0.004 * K)) / (0.014 * K)) ** 2 + ((xs - cx) / (0.022 * K)) ** 2) / 2.0) * front
# the chin reading is unreliable (the frontmost point in its band is behind the neck), so only the
# nose moves; the move is capped at MAX_SHIFT so a bad reading cannot wreck the face
MAX_SHIFT = float(os.environ.get("MAX_SHIFT", "0.020"))
disp_y = np.clip((target_nose_y - nose_y) * NOSE_FRACTION * w_nose, -MAX_SHIFT, MAX_SHIFT)
print("CHIN skipped: frontmost chin point reads %.4f, out of range" % chin_y, flush=True)
new = co.copy()
new[:, 1] = ys + disp_y
# shape keys stored relative to the Basis: move every key by the same offset so expressions still work
me.vertices.foreach_set("co", new.astype(np.float32).reshape(-1))
me.update()
if me.shape_keys:
    for kb in me.shape_keys.key_blocks:
        if kb.name == "Basis":
            continue
        kc = np.empty(nv * 3, dtype=np.float32)
        kb.data.foreach_get("co", kc)
        kc = kc.reshape(nv, 3).astype(np.float64)
        kc[:, 1] += disp_y
        kb.data.foreach_set("co", kc.astype(np.float32).reshape(-1))
    me.shape_keys.key_blocks[0].data.foreach_set("co", new.astype(np.float32).reshape(-1))
print("PROFILE moved nose verts %d, chin verts %d, max shift mm %.2f" % (int((w_nose > 0.3).sum()), int((w_chin > 0.3).sum()), np.abs(disp_y).max() * 1000), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("SAVED", out_blend, flush=True)

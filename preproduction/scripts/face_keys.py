"""Add expression shape keys to the Krishna head (headless Blender).

Usage:
  HEAD_SCALE_MULT=1.25 FOREHEAD_RAISE=0.014 blender -b --python scripts/face_keys.py -- IN.blend OUT.blend

Run after head_polish.py (which creates Basis and KRISHNA_expr_smile). Adds, as relative shape keys
driven by Gaussian displacement fields around landmarks measured from the face:
  KRISHNA_expr_jaw_open, KRISHNA_expr_brow_up, KRISHNA_expr_brow_down, KRISHNA_expr_blink_L,
  KRISHNA_expr_blink_R, KRISHNA_expr_pucker, KRISHNA_expr_frown
Amounts are in metres at HEAD_SCALE_MULT = 1 and scale with it. Texture is painted on the mesh,
so lid keys squash and drag the painted eye (a convincing squint or blink at small values).
"""

import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1 :]
in_blend, out_blend = argv[0], argv[1]
K = float(os.environ.get("HEAD_SCALE_MULT", "1.0"))
RAISE = float(os.environ.get("FOREHEAD_RAISE", "0"))

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
head = bpy.data.objects["KRISHNA_head"]
me = head.data
nv = len(me.vertices)
co = np.empty(nv * 3, dtype=np.float32)
if me.shape_keys:
    me.shape_keys.key_blocks[0].data.foreach_get("co", co)
else:
    me.vertices.foreach_get("co", co)
    head.shape_key_add(name="Basis", from_mix=False)
co = co.reshape(nv, 3).astype(np.float64)
xs, ys, zs = co[:, 0], co[:, 1], co[:, 2]
z_top = zs.max()
cx = float(np.median(xs[zs > z_top - 0.2 * K]))
z_chin = z_top - 0.30 * K - RAISE * K
y_front = float(np.percentile(ys[zs > z_top - 0.3 * K], 40))
front = ys < y_front
eye_z = z_chin + 0.0883 * K
mouth_z = z_chin + 0.0444 * K
eye_dx = 0.0278 * K
dx = xs - cx


def g(cx_, cz_, sx, sz):
    return np.exp(-(((xs - cx_) / sx) ** 2 + ((zs - cz_) / sz) ** 2) / 2.0) * front


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


keys = {}
# jaw open: everything below the mouth line in a face-width column drops and swings back a little
# taper to zero well above the cut, so the open jaw never tears away from the neck
# the drop fades out gradually down into the neck (no step under the lip), so the chin moves
# and the neck stretches instead of tearing
wj = smooth((mouth_z + 0.004 * K - zs) / (0.012 * K)) * smooth((zs - (z_chin - 0.07 * K)) / (0.05 * K)) * (np.abs(dx) < 0.07 * K) * front
d = np.zeros_like(co); d[:, 2] = -0.010 * K * wj; d[:, 1] = 0.003 * K * wj
keys["KRISHNA_expr_jaw_open"] = d
# brows
wb = np.zeros(nv)
for s in (-1, 1):
    wb = np.maximum(wb, g(cx + s * eye_dx, eye_z + 0.016 * K, 0.017 * K, 0.007 * K))
d = np.zeros_like(co); d[:, 2] = 0.006 * K * wb
keys["KRISHNA_expr_brow_up"] = d
d = np.zeros_like(co); d[:, 2] = -0.005 * K * wb
keys["KRISHNA_expr_brow_down"] = d
# blinks
for name, s in (("KRISHNA_expr_blink_L", 1), ("KRISHNA_expr_blink_R", -1)):
    # deeper, tighter lid drop: the eye is painted, so the lid must cover it to read as a blink
    w = g(cx + s * eye_dx, eye_z + 0.003 * K, 0.010 * K, 0.009 * K)
    d = np.zeros_like(co); d[:, 2] = -0.012 * K * w
    keys[name] = d
# mouth corners: pucker pulls them in and forward, frown pulls them down
dpk = np.zeros_like(co); dfr = np.zeros_like(co)
for s in (-1, 1):
    w = g(cx + s * 0.019 * K, mouth_z, 0.011 * K, 0.010 * K)
    dpk[:, 0] += -s * 0.008 * K * w
    dpk[:, 1] += -0.004 * K * w
    dfr[:, 2] += -0.0055 * K * w
# (A lower-lip drop was tried and reverted: it stretched the chin texture into a block.)
keys["KRISHNA_expr_pucker"] = dpk
keys["KRISHNA_expr_frown"] = dfr

# ---- texture: a thin dark seam at the lip line, so the jaw-open drop reveals a mouth ---------
# (A mirror copy of the right eye onto the left was tried and reverted: it speckled the cheek.)
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
px_v = np.clip((vuv[:, 0] * W).astype(int), 0, W - 1)
py_v = np.clip((vuv[:, 1] * H).astype(int), 0, H - 1)
rows_tex = tex[py_v, px_v, :3].copy()

mouth_band = front & (np.abs(zs - mouth_z) < 0.0045 * K) & (np.abs(dx) < 0.018 * K)
seam_rows = rows_tex[mouth_band]
dark = np.array([0.10, 0.03, 0.03])
for i in np.nonzero(mouth_band)[0]:
    rows_tex[i] = dark * 0.85 + 0.15 * rows_tex[i]
print("MOUTH seam verts", int(mouth_band.sum()), flush=True)

# write the painted colours back to the texture at the vertex texels
nlc = nl
pxl = np.clip((uvl[:, 0] * W).astype(int), 0, W - 1)
pyl = np.clip((uvl[:, 1] * H).astype(int), 0, H - 1)
lsel = mouth_band[lv]
tex[pyl[lsel], pxl[lsel], :3] = rows_tex[lv[lsel]]
img.pixels.foreach_set(tex.reshape(-1))
img.update()
img.pack()

for name, disp in keys.items():
    if me.shape_keys and name in me.shape_keys.key_blocks:
        head.shape_key_remove(me.shape_keys.key_blocks[name])
    sk = head.shape_key_add(name=name, from_mix=False)
    sk.data.foreach_set("co", (co + disp).astype(np.float32).reshape(-1))
    sk.value = 0.0
    print("KEY", name, "max shift mm %.2f" % (np.abs(disp).max() * 1000), flush=True)
# ---- mouth cavity ----------------------------------------------------------------------------
# Cut a slit through the face where the lips meet. In neutral the slit is thin and reads as a closed
# mouth; the lower lip drops with jaw_open, and a dark cavity object behind the slit grows with it
# (driven by the jaw_open key value), so the mouth actually opens.
import bmesh

# the lip line measured in the render sits about 2.3 cm above mouth_z (the lip landmark was taken on a
# differently framed render), so the slit, lower lip and cavity use this corrected height
lip_z = mouth_z + 0.0227
bm = bmesh.new()
bm.from_mesh(me)
bm.faces.ensure_lookup_table()
hole_faces = []
for f in bm.faces:
    cz = sum(v.co.z for v in f.verts) / len(f.verts)
    cxf = sum(v.co.x for v in f.verts) / len(f.verts)
    cyf = sum(v.co.y for v in f.verts) / len(f.verts)
    if abs(cz - lip_z) < 0.0025 * K and abs(cxf - cx) < 0.010 * K and cyf < y_front:
        hole_faces.append(f)
print("MOUTH hole faces", len(hole_faces), flush=True)
bmesh.ops.delete(bm, geom=hole_faces, context="FACES_ONLY")
bm.to_mesh(me)
bm.free()
me.update()
nv_after = len(me.vertices)
print("MOUTH verts kept", nv_after, "of", nv, flush=True)

# lower lip follows the jaw in jaw_open (only a thin band, so the chin texture does not stretch)
jk = me.shape_keys.key_blocks["KRISHNA_expr_jaw_open"]
lip_w = front * smooth((lip_z - 0.002 * K - zs) / (0.006 * K)) * smooth((zs - (lip_z - 0.010 * K)) / (0.004 * K)) * (np.abs(dx) < 0.016 * K)
jco = np.empty(nv_after * 3, dtype=np.float32)
jk.data.foreach_get("co", jco)
jco = jco.reshape(nv_after, 3).astype(np.float64)
jco[:, 2] -= 0.010 * K * lip_w[:nv_after] if lip_w.shape[0] == nv_after else 0
jk.data.foreach_set("co", jco.astype(np.float32).reshape(-1))

# cavity: a dark ellipsoid just behind the slit, flattened in neutral, opened by the driver
import bmesh as _bm
cav_m = bpy.data.meshes.new("KRISHNA_mouth_cavity_mesh")
cb = _bm.new()
_bm.ops.create_uvsphere(cb, u_segments=16, v_segments=8, radius=1.0)
cb.to_mesh(cav_m)
cb.free()
cav = bpy.data.objects.new("KRISHNA_mouth_cavity", cav_m)
bpy.context.scene.collection.objects.link(cav)
cav.location = (cx, y_front + 0.012 * K, lip_z)
cav.scale = (0.014 * K, 0.006 * K, 0.0015 * K)
cav.parent = None
mat = bpy.data.materials.new("M_Krishna_MouthInterior")
mat.diffuse_color = (0.12, 0.03, 0.03, 1)
cav.data.materials.append(mat)
cav.shape_key_add(name="Basis", from_mix=False)
open_key = cav.shape_key_add(name="open", from_mix=False)
ncv = len(cav_m.vertices)
cvc = np.empty(ncv * 3, dtype=np.float32)
cav_m.vertices.foreach_get("co", cvc)
cvc = cvc.reshape(ncv, 3)
cvc2 = cvc.copy()
cvc2[:, 2] *= 6.0
open_key.data.foreach_set("co", cvc2.reshape(-1))
open_key.value = 0.0
drv_fc = open_key.driver_add("value")
drv = drv_fc.driver
drv.type = "SCRIPTED"
var = drv.variables.new()
var.name = "jaw"
var.type = "SINGLE_PROP"
var.targets[0].id_type = "KEY"
var.targets[0].id = me.shape_keys
var.targets[0].data_path = 'key_blocks["KRISHNA_expr_jaw_open"].value'
drv.expression = "jaw"
print("CAVITY added, driven by jaw_open", flush=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("SAVED", out_blend, flush=True)

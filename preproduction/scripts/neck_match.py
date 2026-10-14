"""Match neck skin colour (head and body textures) to the projected face (headless Blender).

Usage:
  HEAD_SCALE_MULT=1.25 blender -b --python scripts/neck_match.py -- IN.blend OUT.blend

Takes the mean Lab colour of the cheeks (after face_project.py) and shifts the neck skin texels of
the head texture and of the body texture by that difference, so face, neck and chest read as one skin.
Only skin-hued texels move, so pearls, gold and cloth are left alone.
"""

import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index("--") + 1 :]
in_blend, out_blend = argv[0], argv[1]
K = float(os.environ.get("HEAD_SCALE_MULT", "1.0"))
STRENGTH = float(os.environ.get("NECK_MATCH", "0.9"))


def srgb_to_lab(rgb):
    c = np.clip(rgb, 0, 1)
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = lin @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


def lab_to_srgb(lab):
    fy = (lab[..., 0] + 16) / 116
    f = np.stack([fy + lab[..., 1] / 500, fy, fy - lab[..., 2] / 200], axis=-1)
    xyz = np.where(f ** 3 > 0.008856, f ** 3, (f - 16 / 116) / 7.787) * np.array([0.95047, 1.0, 1.08883])
    m = np.linalg.inv(np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]))
    lin = np.clip(xyz @ m.T, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


def skin_mask(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-6
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60.0
    s = (mx - mn) / (mx + 1e-6)
    return (h >= 0) & (h < 34) & (s > 0.10) & (s < 0.75) & (mx > 0.25)


bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
head = bpy.data.objects["KRISHNA_head"]
body = bpy.data.objects["KRISHNA_body"]


def base_image(obj):
    return next(n.image for n in obj.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and "Image_0" in n.image.name)


def verts_and_uv(obj):
    me = obj.data
    n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(n, 3).astype(np.float64)
    nl = len(me.loops)
    lv = np.empty(nl, dtype=np.int32)
    me.loops.foreach_get("vertex_index", lv)
    uv = np.empty(nl * 2, dtype=np.float32)
    me.uv_layers[0].data.foreach_get("uv", uv)
    return co, lv, uv.reshape(nl, 2)


def texel_mask(obj, vmask, W, H, grow=3):
    co, lv, uv = verts_and_uv(obj)
    sel = vmask[lv]
    px = np.clip((uv[sel, 0] * W).astype(int), 0, W - 1)
    py = np.clip((uv[sel, 1] * H).astype(int), 0, H - 1)
    m = np.zeros((H, W), dtype=bool)
    m[py, px] = True
    for _ in range(grow):
        m2 = m.copy()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            m2 |= np.roll(m, (dy, dx), axis=(0, 1))
        m = m2
    return m


def pixels(img):
    W, H = img.size
    b = np.empty(W * H * 4, dtype=np.float32)
    img.pixels.foreach_get(b)
    return b.reshape(H, W, 4), W, H


hco, _, _ = verts_and_uv(head)
z_top = hco[:, 2].max()
cx = float(np.median(hco[hco[:, 2] > z_top - 0.2 * K, 0]))
z_chin = z_top - 0.30 * K - float(os.environ.get("FOREHEAD_RAISE", "0")) * K * 0  # chin level is unchanged by the raise
y_front = float(np.percentile(hco[hco[:, 2] > z_top - 0.3 * K, 1], 40))
dx = np.abs(hco[:, 0] - cx)

himg = base_image(head)
hp, W, H = pixels(himg)
cheeks_v = (hco[:, 1] < y_front) & (hco[:, 2] > z_chin + 0.07 * K) & (hco[:, 2] < z_chin + 0.10 * K) & (dx > 0.015 * K) & (dx < 0.05 * K)
cheek_m = texel_mask(head, cheeks_v, W, H, grow=1) & skin_mask(hp[..., :3])
ref_lab = srgb_to_lab(hp[cheek_m][:, :3]).mean(0)
print("CHEEK texels", int(cheek_m.sum()), "Lab", np.round(ref_lab, 1), flush=True)

# head neck: below the chin line
neck_v = (hco[:, 2] < z_chin + 0.002 * K) & (hco[:, 2] > z_chin - 0.10 * K) & (dx < 0.075 * K)
neck_m = texel_mask(head, neck_v, W, H, grow=1) & skin_mask(hp[..., :3]) & ~cheek_m
if neck_m.sum() > 200:
    lab = srgb_to_lab(hp[neck_m][:, :3])
    shift = (ref_lab - lab.mean(0)) * STRENGTH
    hp[neck_m, :3] = np.clip(lab_to_srgb(lab + shift), 0, 1)
    himg.pixels.foreach_set(hp.reshape(-1))
    himg.update()
    himg.pack()
    print("HEAD neck texels", int(neck_m.sum()), "shift", np.round(shift, 1), flush=True)

bco, _, _ = verts_and_uv(body)
bimg = base_image(body)
bp, BW, BH = pixels(bimg)
by_front = float(np.percentile(bco[(bco[:, 2] > 1.0) & (bco[:, 2] < 1.45), 1], 45))
bneck_v = (bco[:, 2] > bco[:, 2].max() - 0.12) & (np.abs(bco[:, 0] - cx) < 0.075)
bneck_m = texel_mask(body, bneck_v, BW, BH, grow=1) & skin_mask(bp[..., :3])
if bneck_m.sum() > 200:
    lab = srgb_to_lab(bp[bneck_m][:, :3])
    shift = (ref_lab - lab.mean(0)) * STRENGTH
    bp[bneck_m, :3] = np.clip(lab_to_srgb(lab + shift), 0, 1)
    bimg.pixels.foreach_set(bp.reshape(-1))
    bimg.update()
    bimg.pack()
    print("BODY neck texels", int(bneck_m.sum()), "shift", np.round(shift, 1), flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("SAVED", out_blend, flush=True)

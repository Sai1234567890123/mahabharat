"""Colour-grade, jewel and smile pass for the joined Krishna (run after head_fix.py), headless Blender.

Usage:
  HEAD_SCALE_MULT=1.25 blender -b --python scripts/head_polish.py -- IN.blend REFERENCE.png OUT.blend [PREVIEW_DIR]

What it does:
  1. Colour grade: moves the gold (crown, earrings) and skin texels of the head texture, and the
     skin texels of the body texture, toward the colour statistics of the approved close-up
     (mean and spread in Lab). Texel shading detail is kept; only the colour distribution moves.
  2. Sharpen: a light unsharp mask on gold and skin texels of the head.
  3. Jewels: paints rows of pearls and rubies onto the crown texture along arches parallel to the
     crown edge, like the approved close-up.
  4. Smile: adds a Basis and a KRISHNA_expr_smile shape key to the head (mouth corners and cheeks
     lift) and sets it to a gentle default.
"""

import math
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
if len(argv) < 3:
    raise SystemExit("usage: blender -b --python head_polish.py -- IN.blend REFERENCE.png OUT.blend [PREVIEW_DIR]")
in_blend, ref_png, out_blend = argv[:3]
preview_dir = argv[3] if len(argv) > 3 else None
K = float(os.environ.get("HEAD_SCALE_MULT", "1.0"))
SMILE = float(os.environ.get("SMILE_DEFAULT", "0.6"))


# ---- colour helpers --------------------------------------------------------------------
def srgb_to_lab(rgb):
    c = np.clip(rgb, 0, 1)
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = lin @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


def lab_to_srgb(lab):
    fy = (lab[..., 0] + 16) / 116
    fx = fy + lab[..., 1] / 500
    fz = fy - lab[..., 2] / 200
    f = np.stack([fx, fy, fz], axis=-1)
    xyz = np.where(f ** 3 > 0.008856, f ** 3, (f - 16 / 116) / 7.787) * np.array([0.95047, 1.0, 1.08883])
    m = np.linalg.inv(np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]))
    lin = np.clip(xyz @ m.T, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


def hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-6
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60.0
    s = np.where(mx > 1e-6, (mx - mn) / (mx + 1e-6), 0)
    return h, s, mx


def class_masks(rgb):
    h, s, v = hsv(rgb)
    gold = (h >= 32) & (h <= 62) & (s > 0.28) & (v > 0.30)
    skin = (h >= 4) & (h < 32) & (s > 0.12) & (s < 0.75) & (v > 0.18) & (v < 0.78)  # v cap keeps pale earrings out
    return gold, skin


def transfer(rgb, mask, target_lab, strength=0.9, spread=(0.7, 1.5)):
    """Move masked texels' Lab mean/std toward target_lab (an (N,3) sample)."""
    if mask.sum() < 500 or len(target_lab) < 500:
        return rgb
    lab = srgb_to_lab(rgb[mask])
    mu_s, sd_s = lab.mean(0), lab.std(0) + 1e-3
    mu_t, sd_t = target_lab.mean(0), target_lab.std(0) + 1e-3
    ratio = np.clip(sd_t / sd_s, *spread)
    new = (lab - mu_s) * ratio + mu_t
    out = rgb.copy()
    out[mask] = np.clip(lab_to_srgb(lab * (1 - strength) + new * strength), 0, 1)
    return out


def blur3(a, n=2):
    for _ in range(n):
        s = a.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy or dx:
                    s = s + np.roll(a, (dy, dx), axis=(0, 1))
        a = s / 9.0
    return a


def get_pixels(img):
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    return buf.reshape(h, w, 4)


def put_pixels(img, px):
    img.pixels.foreach_set(px.reshape(-1))
    img.update()
    img.pack()


# ---- reference stats from the approved close-up -----------------------------------------------
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
ref = bpy.data.images.load(os.path.abspath(ref_png))
rw, rh = ref.size
rpx = get_pixels(ref)[..., :3]  # rows are bottom-up


def crop(x0, y0, x1, y1):  # coordinates as seen in the picture (y down)
    return rpx[rh - y1 : rh - y0, x0:x1].reshape(-1, 3)


sx, sy = rw / 1024.0, rh / 1024.0
face_px = crop(int(400 * sx), int(440 * sy), int(640 * sx), int(640 * sy))
crown_px = crop(int(330 * sx), int(130 * sy), int(700 * sx), int(290 * sy))
g_f, s_f = class_masks(face_px)
g_c, s_c = class_masks(crown_px)
face_lab = srgb_to_lab(face_px[s_f])
crown_lab = srgb_to_lab(crown_px[g_c])
print("REF face texels", int(s_f.sum()), "mean rgb", face_px[s_f].mean(0), flush=True)
print("REF crown texels", int(g_c.sum()), "mean rgb", crown_px[g_c].mean(0), flush=True)

head = bpy.data.objects["KRISHNA_head"]
body = bpy.data.objects["KRISHNA_body"]


def base_image(obj):
    """The colour texture of the object's material (the glTF 'Image_0')."""
    imgs = [n.image for n in obj.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE"]
    return next(i for i in imgs if "Image_0" in i.name)


himg, bimg = base_image(head), base_image(body)

# ---- 1 + 2. grade and sharpen the head texture -------------------------------------------------
hp = get_pixels(himg)
rgb = hp[..., :3].copy()
gold, skin = class_masks(rgb)
print("HEAD texels gold", int(gold.sum()), "skin", int(skin.sum()), flush=True)
rgb = transfer(rgb, gold, crown_lab, strength=0.95, spread=(1.0, 2.2))
# richer gold: boost chroma and pull the lightness down a little, like the approved metal
glab = srgb_to_lab(rgb[gold])
glab[:, 1:] *= 1.35
glab[:, 0] = np.clip(glab[:, 0] * 0.96, 0, 100)
rgb[gold] = np.clip(lab_to_srgb(glab), 0, 1)
rgb = transfer(rgb, skin, face_lab, strength=0.85, spread=(0.7, 1.4))
sharp = (gold | skin)[..., None]
bl = blur3(rgb, 1)
rgb = np.where(sharp, np.clip(rgb + 0.55 * (rgb - bl), 0, 1), rgb)
hp[..., :3] = rgb
put_pixels(himg, hp)

# ---- body skin matches the new face colour -------------------------------------------------------
bp = get_pixels(bimg)
brgb = bp[..., :3].copy()
_, bskin = class_masks(brgb)
print("BODY skin texels", int(bskin.sum()), flush=True)
brgb = transfer(brgb, bskin, face_lab, strength=0.6, spread=(0.8, 1.2))
bp[..., :3] = brgb
put_pixels(bimg, bp)

# ---- 3. jewels and pearls on the crown -------------------------------------------------------------
me = head.data
nv = len(me.vertices)
co = np.empty(nv * 3, dtype=np.float32)
me.vertices.foreach_get("co", co)
co = co.reshape(nv, 3)
mw = np.array(head.matrix_world, dtype=np.float32)
co = co @ mw[:3, :3].T + mw[:3, 3]
nl = len(me.loops)
lv = np.empty(nl, dtype=np.int32)
me.loops.foreach_get("vertex_index", lv)
uv = np.empty(nl * 2, dtype=np.float32)
me.uv_layers[0].data.foreach_get("uv", uv)
uv = uv.reshape(nl, 2)
# one UV per vertex (first loop wins)
vuv = np.zeros((nv, 2), dtype=np.float32)
vuv[lv[::-1]] = uv[::-1]

zs, xs, ys = co[:, 2], co[:, 0], co[:, 1]
z_top = float(zs.max())
cx = float(np.median(xs[zs > z_top - 0.2 * K]))
y_front = float(np.percentile(ys[zs > z_top - 0.3 * K], 40))
z_chin = z_top - 0.30 * K - float(os.environ.get("FOREHEAD_RAISE", "0")) * K  # the raise lifted the crown top
H_, W_ = himg.size[1], himg.size[0]
cur = get_pixels(himg)
cg, _ = class_masks(cur[..., :3])
# crown vertices: front facing, gold coloured texel, above the brow line
px_v = np.clip((vuv[:, 0] * W_).astype(int), 0, W_ - 1)
py_v = np.clip((vuv[:, 1] * H_).astype(int), 0, H_ - 1)
is_crown = (ys < y_front) & cg[py_v, px_v] & (zs > z_chin + 0.165 * K)
cz = zs[is_crown]
cxs = xs[is_crown]
print("CROWN front verts", int(is_crown.sum()), flush=True)
if is_crown.sum() > 500:
    half_w = float(np.percentile(np.abs(cxs - cx), 92))
    z_base = float(np.percentile(cz, 4))
    z_peak = float(np.percentile(cz, 99.5))
    idx_crown = np.nonzero(is_crown)[0]
    pts = np.stack([xs[idx_crown], zs[idx_crown]], axis=1)

    def paint_blob(u, v, r, base, hi):
        cxp, cyp = u * W_, v * H_
        y0, y1 = int(max(cyp - r - 2, 0)), int(min(cyp + r + 3, H_))
        x0, x1 = int(max(cxp - r - 2, 0)), int(min(cxp + r + 3, W_))
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.sqrt((xx - cxp) ** 2 + (yy - cyp) ** 2) / r
        inside = d <= 1.0
        shade = np.clip(1.0 - d, 0, 1)
        # highlight toward the upper left
        hd = np.sqrt((xx - (cxp - 0.35 * r)) ** 2 + (yy - (cyp + 0.35 * r)) ** 2) / (0.45 * r)
        spec = np.clip(1.0 - hd, 0, 1) ** 1.5
        col = np.array(base)[None, None, :] * (0.55 + 0.45 * shade[..., None]) + np.array(hi)[None, None, :] * spec[..., None]
        rim = (d > 0.78) & inside
        col = np.where(rim[..., None], np.array([0.45, 0.33, 0.12])[None, None, :], col)
        sub = cur[y0:y1, x0:x1, :3]
        cur[y0:y1, x0:x1, :3] = np.where(inside[..., None], np.clip(col, 0, 1), sub)

    n_pearl = n_ruby = 0
    arches = [
        (0.52, 15, "pearl"),
        (0.72, 11, "pearl"),
        (0.88, 9, "ruby"),
    ]
    for frac, count, kind in arches:
        for i in range(count):
            t = -0.82 + 1.64 * i / (count - 1)
            tx = cx + t * half_w
            tz = z_base + (z_peak - z_base) * (frac * math.sqrt(max(1 - (t * 0.85) ** 2, 0.05)) + 0.05)
            j = int(np.argmin(((pts[:, 0] - tx) ** 2 + (pts[:, 1] - tz) ** 2)))
            if ((pts[j, 0] - tx) ** 2 + (pts[j, 1] - tz) ** 2) > (0.012 * K) ** 2:
                continue
            vi = idx_crown[j]
            u, v = float(vuv[vi, 0]), float(vuv[vi, 1])
            if kind == "pearl":
                paint_blob(u, v, 11.0, (0.93, 0.90, 0.84), (1.0, 1.0, 0.98))
                n_pearl += 1
            else:
                paint_blob(u, v, 13.0, (0.72, 0.04, 0.10), (1.0, 0.55, 0.5))
                n_ruby += 1
    print("JEWELS pearls", n_pearl, "rubies", n_ruby, flush=True)
    hp2 = get_pixels(himg)
    hp2[..., :3] = cur[..., :3]
    put_pixels(himg, hp2)

# ---- 4. smile shape key -------------------------------------------------------------------------------
if me.shape_keys is None:
    head.shape_key_add(name="Basis", from_mix=False)
sk = head.shape_key_add(name="KRISHNA_expr_smile", from_mix=False)
zm = z_chin + 0.059 * K
front = ys < y_front
disp = np.zeros_like(co)
for side in (-1, 1):
    mxc = cx + side * 0.019 * K
    d2 = (xs - mxc) ** 2 + (zs - zm) ** 2
    w = np.exp(-d2 / (2 * (0.011 * K) ** 2)) * front
    disp[:, 2] += 0.0085 * K * w
    disp[:, 0] += side * 0.0030 * K * w
    cxc, czc = cx + side * 0.030 * K, zm + 0.020 * K
    d2c = (xs - cxc) ** 2 + (zs - czc) ** 2
    wc = np.exp(-d2c / (2 * (0.020 * K) ** 2)) * front
    disp[:, 2] += 0.0030 * K * wc
# the shape key stores object-space coordinates; the object has an identity transform after apply
basis = np.empty(nv * 3, dtype=np.float32)
me.vertices.foreach_get("co", basis)
basis = basis.reshape(nv, 3)
sk.data.foreach_set("co", (basis + disp).astype(np.float32).reshape(-1))
sk.value = SMILE
print("SMILE key added, default", SMILE, "max shift mm %.2f" % (np.abs(disp).max() * 1000), flush=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
print("SAVED", out_blend, flush=True)

# ---- previews ----------------------------------------------------------------------------------------------
if preview_dir:
    import mathutils

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
    zc = z_top - 0.15 * K
    cy = float((ys.max() + ys.min()) * 0.5)
    views = {
        "polish_front": ((cx, cy - 5, zc), (math.radians(90), 0, 0)),
        "polish_three_quarter": ((cx + 3.5, cy - 3.5, zc), (math.radians(90), 0, math.radians(45))),
    }
    for name, (loc, rot) in views.items():
        cam.location, cam.rotation_euler = loc, rot
        scene.render.filepath = os.path.join(preview_dir, name + ".png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", scene.render.filepath, flush=True)

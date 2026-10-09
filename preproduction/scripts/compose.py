"""2D compositor for the pilot concept frames.

Takes the Blender passes from blockout.py and paints the parts of the look
that belong to 2D: the matte-painted sky, stepped atmospheric haze, colored
line art, the hand-drawn FX listed in shots.json (sound rings, god rays,
halos, yantra, chakra, lightning, dust), the lens (flare, bloom, chromatic
fringe, grain, vignette) and the 3-color impact frames.

  python3 compose.py --shot SH070            # one shot
  python3 compose.py --all                   # every shot that has passes
  python3 compose.py --shot SH070 --control  # also write AI control passes

Needs numpy and Pillow only.
"""
import argparse
import json
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))

# ---------------------------------------------------------------- helpers


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], dtype=np.float32)


def rgb255(h, a=255):
    c = (rgb(h) * 255).astype(int)
    return (int(c[0]), int(c[1]), int(c[2]), int(a))


def to_img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


def from_img(im):
    return np.asarray(im).astype(np.float32) / 255.0


def blur(a, r):
    """Gaussian blur of a float array (H,W) or (H,W,C) in [0,1]."""
    if r <= 0:
        return a
    if a.ndim == 2:
        return from_img(to_img(a).filter(ImageFilter.GaussianBlur(r)))
    return np.dstack([blur(a[..., i], r) for i in range(a.shape[2])])


def smooth_noise(h, w, cell_y, cell_x, seed):
    """Low-frequency value noise in [0,1], stretched by the cell size."""
    rs = np.random.RandomState(seed)
    small = rs.rand(max(2, h // cell_y + 2), max(2, w // cell_x + 2)).astype(np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im).astype(np.float32) / 255.0


def lerp(a, b, t):
    return a * (1 - t) + b * t


def gradient(stops, t):
    """stops: list of rgb arrays from t=0 (horizon) to t=1 (zenith)."""
    t = np.clip(t, 0, 1) * (len(stops) - 1)
    i = np.clip(np.floor(t).astype(int), 0, len(stops) - 2)
    f = (t - i)[..., None]
    S = np.stack(stops)
    return S[i] * (1 - f) + S[i + 1] * f


class Layer:
    """Supersampled RGBA drawing layer for crisp 2D FX."""

    def __init__(self, W, H, ss=2):
        self.W, self.H, self.ss = W, H, ss
        self.im = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def p(self, x, y):
        return (x * self.ss, y * self.ss)

    def s(self, v):
        return v * self.ss

    def done(self):
        return from_img(self.im.resize((self.W, self.H), Image.LANCZOS))


def over(base, layer, mask=None):
    """Alpha-over an RGBA float layer onto an RGB base."""
    a = layer[..., 3:4]
    if mask is not None:
        a = a * mask[..., None]
    return base * (1 - a) + layer[..., :3] * a


def add(base, layer, k=1.0, mask=None):
    a = layer[..., 3:4] * k
    if mask is not None:
        a = a * mask[..., None]
    return base + layer[..., :3] * a


# ---------------------------------------------------------------- passes


def load(render_dir, sid):
    col = from_img(Image.open(os.path.join(render_dir, f"{sid}_color.png")).convert("RGBA"))
    dep = np.asarray(Image.open(os.path.join(render_dir, f"{sid}_depth.png"))).astype(np.float32)
    dep = dep / (65535.0 if dep.max() > 255 else 255.0)
    if dep.ndim == 3:
        dep = dep[..., 0]
    idp = np.asarray(Image.open(os.path.join(render_dir, f"{sid}_id.png")).convert("RGB")).astype(np.int16)
    meta = json.load(open(os.path.join(render_dir, f"{sid}_meta.json")))
    return col, dep, idp, meta


def depth_m(dep, meta):
    ln, lf = math.log(meta["near"]), math.log(meta["far"])
    return np.exp(ln + dep * (lf - ln))


def horizon_field(meta, W, H):
    """Signed pixel distance above the horizon line (positive = sky side)."""
    (x1, y1, _), (x2, y2, _) = meta["horizon"]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = (xx - x1) * nx + (yy - y1) * ny
    # sky is the side that contains the top-centre of the frame
    top = (W / 2 - x1) * nx + (0 - y1) * ny
    if top < 0:
        d = -d
    return d


def anchor(meta, name):
    if name == "sun":
        p = meta["sun"]
    else:
        p = meta["anchors"].get(name)
    if p is None or p[2] <= 0:
        return None
    return p


# ---------------------------------------------------------------- sky


def paint_sky(meta, act, W, H, seed, shot):
    d = horizon_field(meta, W, H)
    stops = [rgb(c) for c in act["sky"]]
    t = d / (0.9 * H * shot["camera"].get("sky_scale", 1.0))
    sky = gradient(stops, t)
    # painted cloud banks: stretched noise, posterized into flat value blocks
    n = 0.65 * smooth_noise(H, W, max(8, H // 7), max(16, W // 5), seed) + \
        0.35 * smooth_noise(H, W, max(4, H // 18), max(8, W // 12), seed + 1)
    band = np.clip(1 - np.abs(t - 0.32) / 0.3, 0, 1)
    cl = np.floor(np.clip((n - 0.42) * 3.2, 0, 1) * 3) / 3 * band
    lighter = gradient(stops, np.clip(t - 0.25, 0, 1)) * 1.06
    darker = gradient(stops, np.clip(t + 0.22, 0, 1))
    sky = lerp(sky, np.where((n > 0.62)[..., None], darker, lighter), cl[..., None] * 0.55)
    if shot["act"] == "C":
        rs = np.random.RandomState(seed + 7)
        stars = np.zeros((H, W), np.float32)
        k = int(W * H / 900)
        ys, xs = rs.randint(0, H, k), rs.randint(0, W, k)
        stars[ys, xs] = rs.rand(k) ** 3
        stars = np.maximum(stars, blur(stars, 1.0) * 2)
        neb = smooth_noise(H, W, H // 4, W // 6, seed + 9)
        neb2 = smooth_noise(H, W, H // 5, W // 8, seed + 10)
        sky = sky + rgb("#C2338F") * (np.clip(neb - 0.55, 0, 1) * 0.9)[..., None]
        sky = sky + rgb("#2FD3C6") * (np.clip(neb2 - 0.6, 0, 1) * 0.6)[..., None]
        sky = sky + stars[..., None]
    return sky, d


def draw_sun(meta, act, W, H, fx):
    p = anchor(meta, "sun")
    lay = Layer(W, H)
    if not p:
        return None
    x, y = p[0], p[1]
    r = 0.032 * H * fx.get("scale", 1.0)
    sun = rgb255(act["sky"][0])
    core = (255, 250, 235, 255)
    for k, (rr, a) in enumerate([(4.5, 26), (3.0, 40), (2.0, 70), (1.4, 120)]):
        lay.d.ellipse([*lay.p(x - r * rr, y - r * rr), *lay.p(x + r * rr, y + r * rr)], fill=sun[:3] + (a,))
    lay.d.ellipse([*lay.p(x - r, y - r), *lay.p(x + r, y + r)], fill=core)
    return lay.done()


# ---------------------------------------------------------------- FX


def fx_rings(lay, p, f, W, H, rnd):
    x, y = p[0], p[1]
    n = f.get("count", 6)
    r0, r1 = f.get("r0", 0.03) * W, f.get("r1", 0.6) * W
    wid = max(1.0, f.get("width", 0.006) * W)
    sq = f.get("squash", 0.8)
    col = rgb255(f["color"])
    ph = f.get("phase", 0.0)
    for i in range(n):
        t = (i + ph + 0.5) / n
        r = r0 + (r1 - r0) * t ** 1.35
        a = int(255 * (1 - t) ** 0.8)
        w = max(1.0, wid * (1.2 - 0.8 * t))
        # broken arcs: a hand-drawn ring is never a perfect closed circle
        start = rnd.uniform(0, 360)
        segs = rnd.randint(3, 6)
        span = 360 / segs
        for k in range(segs):
            a0 = start + k * span
            a1 = a0 + span * rnd.uniform(0.55, 0.9)
            box = [*lay.p(x - r, y - r * sq), *lay.p(x + r, y + r * sq)]
            lay.d.arc(box, a0, a1, fill=col[:3] + (a,), width=int(lay.s(w)))
        if i == 0:
            box = [*lay.p(x - r, y - r * sq), *lay.p(x + r, y + r * sq)]
            lay.d.ellipse(box, fill=col[:3] + (90,))


def fx_speedlines(lay, p, f, W, H, rnd):
    x, y = p[0], p[1]
    col = rgb255(f["color"], int(255 * f.get("alpha", 0.3)))
    R = math.hypot(W, H)
    for _ in range(f.get("count", 40)):
        a = rnd.uniform(0, 2 * math.pi)
        r_in = rnd.uniform(0.18, 0.45) * W
        half = rnd.uniform(0.002, 0.008)
        pts = [(x + math.cos(a) * r_in, y + math.sin(a) * r_in),
               (x + math.cos(a + half) * R, y + math.sin(a + half) * R),
               (x + math.cos(a - half) * R, y + math.sin(a - half) * R)]
        lay.d.polygon([lay.p(*q) for q in pts], fill=col)


def fx_godrays(lay, p, f, W, H, rnd):
    x, y = p[0], p[1]
    R = math.hypot(W, H) * 1.5
    base = math.atan2(H / 2 - y, W / 2 - x)
    for i in range(f.get("count", 12)):
        a = base + rnd.uniform(-1.3, 1.3)
        w = math.radians(rnd.uniform(0.6, 3.5))
        al = int(255 * f.get("alpha", 0.2) * rnd.uniform(0.4, 1.0))
        pts = [(x, y), (x + math.cos(a - w) * R, y + math.sin(a - w) * R), (x + math.cos(a + w) * R, y + math.sin(a + w) * R)]
        lay.d.polygon([lay.p(*q) for q in pts], fill=rgb255(f["color"], al))


def fx_halo(lay, p, f, W, H, rnd):
    x, y = p[0], p[1]
    r = f.get("r", 0.1) * W
    c = rgb255(f["color"])
    a = f.get("alpha", 0.5)
    lay.d.ellipse([*lay.p(x - r, y - r), *lay.p(x + r, y + r)], fill=c[:3] + (int(70 * a),))
    for k, rr in enumerate([1.0, 1.12, 1.3]):
        lay.d.ellipse([*lay.p(x - r * rr, y - r * rr), *lay.p(x + r * rr, y + r * rr)], outline=c[:3] + (int(255 * a / (k + 1)),),
                      width=int(lay.s(max(1, W / 900))))


def fx_glow(lay, p, f, W, H, rnd):
    x, y = p[0], p[1]
    r = f.get("r", 0.2) * W
    c = rgb255(f["color"])
    for k in range(10):
        rr = r * (1 - k / 10)
        lay.d.ellipse([*lay.p(x - rr, y - rr), *lay.p(x + rr, y + rr)], fill=c[:3] + (int(255 * f.get("alpha", 0.4) / 10),))


def fx_sparkles(lay, p, f, W, H, rnd):
    x, y = p[0], p[1]
    R = f.get("r", 0.25) * W
    c = rgb255(f["color"])
    for _ in range(f.get("count", 40)):
        a, d = rnd.uniform(0, 2 * math.pi), R * math.sqrt(rnd.random())
        sx, sy = x + math.cos(a) * d * 1.3, y + math.sin(a) * d * 0.6
        s = rnd.uniform(0.003, 0.012) * W
        t = s * 0.12
        lay.d.polygon([lay.p(sx - s, sy), lay.p(sx, sy - t), lay.p(sx + s, sy), lay.p(sx, sy + t)], fill=c)
        lay.d.polygon([lay.p(sx, sy - s * 0.7), lay.p(sx + t, sy), lay.p(sx, sy + s * 0.7), lay.p(sx - t, sy)], fill=c)


def fx_shockwave(lay, p, f, W, H, rnd):
    x, y = p[0], p[1]
    c = rgb255(f["color"])
    for k, (rx, al) in enumerate([(0.55, 200), (0.75, 120), (1.0, 60)]):
        r = rx * W
        lay.d.ellipse([*lay.p(x - r, y - r * 0.07), *lay.p(x + r, y + r * 0.07)], outline=c[:3] + (al,),
                      width=int(lay.s(W * 0.004 * (3 - k))))
    for _ in range(90):
        a = rnd.uniform(math.pi, 2 * math.pi)
        r = rnd.uniform(0.3, 0.75) * W
        sx, sy = x + math.cos(a) * r, y + math.sin(a) * r * 0.07
        h = rnd.uniform(0.01, 0.05) * H
        lay.d.polygon([lay.p(sx - 3, sy), lay.p(sx + 3, sy), lay.p(sx + rnd.uniform(-8, 8), sy - h)], fill=c[:3] + (110,))


def fx_dust(lay, p, f, W, H, rnd, meta=None, seed=0):
    pass  # dust is painted as a full-frame pass, see paint_dust


def fx_chakra(lay, p, f, W, H, rnd):
    x, y = p[0], p[1]
    r = f.get("r", 0.06) * W
    gold, teal = rgb255(f["color"]), rgb255("#2FD3C6")
    for k in range(12):
        a = 2 * math.pi * k / 12
        b = a + 0.38
        pts = [(x + math.cos(a) * r * 0.75, y + math.sin(a) * r * 0.75), (x + math.cos(b) * r * 1.45, y + math.sin(b) * r * 1.45),
               (x + math.cos(a + 0.5) * r * 0.75, y + math.sin(a + 0.5) * r * 0.75)]
        lay.d.polygon([lay.p(*q) for q in pts], fill=teal[:3] + (200,))
    lay.d.ellipse([*lay.p(x - r, y - r), *lay.p(x + r, y + r)], outline=gold, width=int(lay.s(r * 0.22)))
    lay.d.ellipse([*lay.p(x - r * 0.25, y - r * 0.25), *lay.p(x + r * 0.25, y + r * 0.25)], fill=(255, 255, 240, 255))
    for k in range(3):
        rr = r * (1.7 + k * 0.25)
        lay.d.arc([*lay.p(x - rr, y - rr), *lay.p(x + rr, y + rr)], 200 + k * 30, 300 + k * 30, fill=gold[:3] + (120,),
                  width=int(lay.s(2)))


def eye_shape(lay, cx, cy, s, rot, col, iris):
    pts = []
    for k in range(24):
        t = 2 * math.pi * k / 24
        ex, ey = math.cos(t) * s, math.sin(t) * s * 0.42 * (1 if math.sin(t) > 0 else 0.8)
        pts.append((cx + ex * math.cos(rot) - ey * math.sin(rot), cy + ex * math.sin(rot) + ey * math.cos(rot)))
    lay.d.polygon([lay.p(*q) for q in pts], fill=col)
    r = s * 0.3
    lay.d.ellipse([*lay.p(cx - r, cy - r), *lay.p(cx + r, cy + r)], fill=iris)


def fx_yantra(lay, p, f, W, H, rnd):
    """Sacred geometry: lotus, interlocking triangles, gated square, rings of eyes."""
    x, y = p[0], p[1]
    R = f.get("r", 0.4) * W
    a = f.get("alpha", 0.8)
    gold = rgb255(f["color"], int(255 * a))
    teal = rgb255("#2FD3C6", int(220 * a))
    mag = rgb255("#E0459C", int(200 * a))
    lw = int(lay.s(max(1, W / 700)))
    # outer gated square (bhupura)
    s = R * 1.02
    g = s * 0.22
    sq = [(x - s, y - s), (x - g, y - s), (x - g, y - s - g * 0.5), (x + g, y - s - g * 0.5), (x + g, y - s), (x + s, y - s),
          (x + s, y - g), (x + s + g * 0.5, y - g), (x + s + g * 0.5, y + g), (x + s, y + g), (x + s, y + s), (x + g, y + s),
          (x + g, y + s + g * 0.5), (x - g, y + s + g * 0.5), (x - g, y + s), (x - s, y + s), (x - s, y + g),
          (x - s - g * 0.5, y + g), (x - s - g * 0.5, y - g), (x - s, y - g), (x - s, y - s)]
    lay.d.line([lay.p(*q) for q in sq], fill=gold, width=lw)
    for k, rr in enumerate([0.98, 0.92, 0.66, 0.62, 0.36, 0.33]):
        r = R * rr
        lay.d.ellipse([*lay.p(x - r, y - r), *lay.p(x + r, y + r)], outline=(gold if k % 2 == 0 else teal), width=lw)
    # lotus petals
    n = f.get("petals", 16)
    for k in range(n):
        t = 2 * math.pi * k / n
        tip = (x + math.cos(t) * R * 0.9, y + math.sin(t) * R * 0.9)
        l1 = (x + math.cos(t - math.pi / n) * R * 0.66, y + math.sin(t - math.pi / n) * R * 0.66)
        l2 = (x + math.cos(t + math.pi / n) * R * 0.66, y + math.sin(t + math.pi / n) * R * 0.66)
        mid = (x + math.cos(t) * R * 0.74, y + math.sin(t) * R * 0.74)
        lay.d.line([lay.p(*l1), lay.p(*tip), lay.p(*l2)], fill=gold, width=lw)
        lay.d.line([lay.p(*mid), lay.p(*tip)], fill=mag, width=max(1, lw // 2))
    # interlocking triangles (Sri Yantra-like, simplified, not a canonical diagram)
    for k, (rr, up) in enumerate([(0.6, 1), (0.55, -1), (0.45, 1), (0.4, -1), (0.3, 1), (0.25, -1)]):
        r = R * rr
        pts = [(x + math.cos(math.radians(-90 * up + d)) * r, y + math.sin(math.radians(-90 * up + d)) * r) for d in (0, 120, 240)]
        lay.d.polygon([lay.p(*q) for q in pts], outline=(gold if up > 0 else teal), width=lw)
    lay.d.ellipse([*lay.p(x - R * 0.03, y - R * 0.03), *lay.p(x + R * 0.03, y + R * 0.03)], fill=(255, 255, 245, int(255 * a)))
    # rings of eyes: "faces turned on all sides"
    faces = f.get("faces", 0)
    for ring, (rr, cnt) in enumerate([(1.22, faces), (1.5, int(faces * 1.4))]):
        for k in range(cnt):
            t = 2 * math.pi * (k + 0.5 * ring) / max(1, cnt)
            cx, cy = x + math.cos(t) * R * rr, y + math.sin(t) * R * rr
            eye_shape(lay, cx, cy, R * (0.06 - 0.012 * ring), t + math.pi / 2, gold, rgb255("#1A0C3A", int(255 * a)))
    # radiating arms as long tapered strokes
    if faces:
        for k in range(36):
            t = 2 * math.pi * k / 36 + 0.04
            r0, r1 = R * 1.05, R * rnd.uniform(1.7, 2.3)
            w = 0.012
            pts = [(x + math.cos(t - w) * r0, y + math.sin(t - w) * r0), (x + math.cos(t) * r1, y + math.sin(t) * r1),
                   (x + math.cos(t + w) * r0, y + math.sin(t + w) * r0)]
            lay.d.polygon([lay.p(*q) for q in pts], fill=gold[:3] + (int(110 * a),))


def fx_lightning(lay, p, f, W, H, rnd, p2=None):
    if p2 is None:
        return
    col = rgb255(f["color"])

    def bolt(a, b, depth, width):
        pts = [a, b]
        for _ in range(depth):
            new = [pts[0]]
            for i in range(len(pts) - 1):
                (x1, y1), (x2, y2) = pts[i], pts[i + 1]
                L = math.hypot(x2 - x1, y2 - y1)
                mx, my = (x1 + x2) / 2 + rnd.uniform(-0.18, 0.18) * L, (y1 + y2) / 2 + rnd.uniform(-0.18, 0.18) * L
                new += [(mx, my), (x2, y2)]
            pts = new
        lay.d.line([lay.p(*q) for q in pts], fill=col[:3] + (150,), width=int(lay.s(width * 3)))
        lay.d.line([lay.p(*q) for q in pts], fill=(240, 250, 255, 255), width=int(lay.s(width)))
        return pts

    main = bolt((p[0], p[1]), (p2[0], p2[1]), 5, max(1.5, W / 700))
    for _ in range(7):
        s = main[rnd.randint(3, len(main) - 3)]
        a = rnd.uniform(0, 2 * math.pi)
        L = rnd.uniform(0.03, 0.1) * W
        bolt(s, (s[0] + math.cos(a) * L, s[1] + math.sin(a) * L), 3, max(1, W / 1300))


FX = dict(rings=fx_rings, speedlines=fx_speedlines, godrays=fx_godrays, halo=fx_halo, glow=fx_glow,
          sparkles=fx_sparkles, shockwave=fx_shockwave, chakra=fx_chakra, yantra=fx_yantra)
BEHIND = {"godrays", "halo", "yantra"}   # drawn behind the 3D (masked by depth)
ADDITIVE = {"glow", "sparkles"}


def paint_dust(col, d_hor, W, H, color, seed, alpha=0.35):
    """Painted dust banks hugging the ground, as flat posterized shapes."""
    n = smooth_noise(H, W, max(4, H // 10), max(8, W // 7), seed + 3)
    band = np.clip(1 - np.abs(d_hor + 0.06 * H) / (0.16 * H), 0, 1)
    m = np.floor(np.clip((n - 0.38) * 2.6, 0, 1) * 3) / 3 * band * alpha
    return lerp(col, rgb(color), m[..., None])


# ---------------------------------------------------------------- main composite


def composite(shot, data, render_dir, out_dir, control_dir=None, seed=7):
    sid = shot["id"]
    act = data["acts"][shot["act"]]
    col, dep, idp, meta = load(render_dir, sid)
    H, W = dep.shape
    rnd = random.Random(seed + int(sid[2:]))
    z = depth_m(dep, meta)
    alpha = col[..., 3]
    sky, d_hor = paint_sky(meta, act, W, H, seed + int(sid[2:]), shot)

    # FX that live in the sky / behind the 3D
    fxs = shot.get("fx", [])
    for f in fxs:
        if f["type"] == "sun":
            s = draw_sun(meta, act, W, H, f)
            if s is not None:
                sky = over(sky, s)
    behind = np.zeros((H, W, 3), np.float32)
    for f in fxs:
        if f["type"] in BEHIND:
            p = anchor(meta, f.get("anchor", "sun"))
            if not p:
                continue
            lay = Layer(W, H)
            FX[f["type"]](lay, p, f, W, H, rnd)
            L = lay.done()
            if f["type"] == "godrays":
                sky = over(sky, L)
                continue
            # mask: only where the scene is farther than the anchor (or empty sky)
            m = np.where(alpha < 0.5, 1.0, (z > p[2] + 0.3).astype(np.float32))
            behind_layer = L.copy()
            behind_layer[..., 3] *= m
            sky = over(sky, behind_layer)
            behind = np.maximum(behind, L[..., :3] * L[..., 3:4] * m[..., None])

    # 3D toon render over the sky
    base = col[..., :3]
    # unify the massed armies: soften the per-soldier speckle
    army = np.zeros((H, W), bool)
    for ref in ((0, 0, 128), (128, 0, 0)):
        army |= (np.abs(idp - np.array(ref)).sum(-1) < 30)
    if army.any():
        soft = blur(base, 1.2)
        base = np.where(army[..., None], lerp(soft, rgb(act["shadow"]), 0.3), base)
    divine = (np.abs(idp - np.array((0, 128, 0))).sum(-1) < 30).astype(np.float32)
    # the divine form is light, not matter: brighten it and let the sky geometry show through
    if divine.any():
        base = np.where(divine[..., None] > 0, lerp(base, rgb("#FFF6DA"), 0.55), base)
        alpha = alpha * (1 - 0.3 * divine)
    img = sky * (1 - alpha[..., None]) + base * alpha[..., None]
    # "behind" FX also show through the sky part of the render where alpha < 1 at AA edges
    # stepped atmospheric haze
    hz = 1 - np.exp(-z / act["haze_dist"])
    hz = 0.55 * (np.round(hz * 6) / 6) + 0.45 * hz
    hz = hz * alpha * (1 - divine)
    haze_col = lerp(rgb(act["haze"]), gradient([rgb(c) for c in act["sky"]], np.clip(d_hor / (0.9 * H), 0, 1)), 0.4)
    img = lerp(img, haze_col, (hz * 0.88)[..., None])

    # colored line art from ID and depth discontinuities, fading with distance
    lnz = np.log(z)
    e = np.zeros((H, W), np.float32)
    for axis in (0, 1):
        di = np.abs(np.diff(idp, axis=axis)).sum(-1) > 40
        dz = np.abs(np.diff(lnz, axis=axis)) > 0.04
        dd = (di | dz).astype(np.float32)
        if axis == 0:
            e[:-1] = np.maximum(e[:-1], dd)
        else:
            e[:, :-1] = np.maximum(e[:, :-1], dd)
    e_all = e.copy()
    near = np.clip((math.log(160) - lnz) / (math.log(160) - math.log(30)), 0, 1)
    e = e * near * (alpha > 0.1)
    if W >= 1600:
        e = from_img(to_img(e).filter(ImageFilter.MaxFilter(3))) * 0.8
    line = rgb(act["shadow"]) * 0.55
    img = lerp(img, line, (e * 0.7)[..., None])

    # painterly breakup: stretched brush noise modulating value
    brush = smooth_noise(H, W, 3, 14, seed + 11) - 0.5
    img = img * (1 + 0.07 * brush[..., None])

    # dust banks
    for f in fxs:
        if f["type"] == "dust":
            img = paint_dust(img, d_hor, W, H, f["color"], seed + int(sid[2:]), f.get("alpha", 0.32))

    # FX over the image
    fx_over = np.zeros((H, W, 3), np.float32)
    for f in fxs:
        t = f["type"]
        if t in BEHIND or t in ("sun", "dust"):
            continue
        p = anchor(meta, f.get("anchor", "sun"))
        if not p and t != "flare":
            continue
        lay = Layer(W, H)
        if t == "lightning":
            fx_lightning(lay, p, f, W, H, rnd, anchor(meta, f.get("anchor2")))
        elif t == "flare":
            continue
        else:
            FX[t](lay, p, f, W, H, rnd)
        L = lay.done()
        if t in ADDITIVE:
            img = add(img, L)
        else:
            img = over(img, L)
            fx_over = np.maximum(fx_over, L[..., :3] * L[..., 3:4])

    # lens: bloom from the brightest areas and from all FX
    lum = img.mean(-1)
    bright = np.clip(img * (np.clip(lum - 0.72, 0, 1) / 0.28)[..., None], 0, 1)
    bright = np.maximum(bright, (fx_over + behind) * 0.8)
    bright = np.maximum(bright, img * divine[..., None] * 0.9)
    img = img + blur(bright, W / 90) * 0.55 + blur(bright, W / 30) * 0.35

    # anamorphic flare
    for f in fxs:
        if f["type"] == "flare":
            p = anchor(meta, f.get("anchor", "sun"))
            if not p:
                continue
            x, y = p[0], p[1]
            yy = np.arange(H, dtype=np.float32)[:, None]
            xx = np.arange(W, dtype=np.float32)[None, :]
            streak = np.exp(-((yy - y) / (H * 0.006)) ** 2) * np.exp(-np.abs(xx - x) / (W * 0.45))
            img = img + rgb("#A9E4FF") * streak[..., None] * 0.55 + rgb(f["color"]) * streak[..., None] * 0.35
            for k, (tpos, rr, c) in enumerate([(0.5, 0.05, "#2FD3C6"), (0.8, 0.03, "#E8862A"), (1.3, 0.08, "#6FC3FF")]):
                gx, gy = x + (W / 2 - x) * 2 * tpos, y + (H / 2 - y) * 2 * tpos
                g = np.exp(-(((xx - gx) ** 2 + (yy - gy) ** 2) / (rr * W) ** 2) ** 2)
                img = img + rgb(c) * g[..., None] * 0.12

    # chromatic fringe, vignette, grain
    img = np.clip(img, 0, 1)
    im = to_img(img)
    r, g, b = im.split()

    def scale_ch(ch, s):
        w2, h2 = int(W * s), int(H * s)
        c2 = ch.resize((w2, h2), Image.BICUBIC)
        return c2.crop(((w2 - W) // 2, (h2 - H) // 2, (w2 - W) // 2 + W, (h2 - H) // 2 + H))

    im = Image.merge("RGB", (scale_ch(r, 1.004), g, b))
    img = from_img(im)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    vr = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
    img = img * (1 - 0.22 * np.clip(vr - 0.25, 0, 1)[..., None])
    clean = np.clip(img, 0, 1)
    gr = np.random.RandomState(seed).normal(0, act.get("grain", 0.03), (H, W)).astype(np.float32)
    img = img + gr[..., None]
    final = np.clip(img, 0, 1)

    os.makedirs(out_dir, exist_ok=True)
    to_img(final).save(os.path.join(out_dir, f"{sid}.jpg"), quality=92, subsampling=0)
    written = [f"{sid}.jpg"]

    imp = shot.get("impact")
    if imp:
        to_img(impact_frame(blur(clean, 1.5), meta, imp, W, H, rnd)).save(os.path.join(out_dir, f"{sid}_impact.jpg"),
                                                                         quality=92, subsampling=0)
        written.append(f"{sid}_impact.jpg")

    if control_dir:
        os.makedirs(control_dir, exist_ok=True)
        dn = 1 - np.clip((lnz - math.log(meta["near"])) / (math.log(400) - math.log(meta["near"])), 0, 1)
        dn = dn * (alpha > 0.05)
        to_img(dn).save(os.path.join(control_dir, f"{sid}_depth.png"))
        to_img(1 - e_all * (alpha > 0.05) * np.clip(near + 0.3, 0, 1)).save(os.path.join(control_dir, f"{sid}_lineart.png"))
        Image.fromarray(idp.astype(np.uint8)).save(os.path.join(control_dir, f"{sid}_ids.png"))
    return written


def impact_frame(img, meta, imp, W, H, rnd):
    """Three flat colors: black, white and the energy color, plus radial speed lines."""
    lum = img.mean(-1)
    lo, hi = np.percentile(lum, 40), np.percentile(lum, 82)
    e = rgb(imp["color"])
    out = np.where((lum < lo)[..., None], np.zeros(3), np.where((lum < hi)[..., None], e, np.ones(3)))
    p = anchor(meta, imp.get("anchor", "sun")) or (W / 2, H / 2, 1)
    lay = Layer(W, H, 1)
    x, y = p[0], p[1]
    R = math.hypot(W, H)
    for _ in range(140):
        a = rnd.uniform(0, 2 * math.pi)
        r_in = rnd.uniform(0.12, 0.35) * W
        h = rnd.uniform(0.002, 0.01)
        pts = [(x + math.cos(a) * r_in, y + math.sin(a) * r_in), (x + math.cos(a + h) * R, y + math.sin(a + h) * R),
               (x + math.cos(a - h) * R, y + math.sin(a - h) * R)]
        lay.d.polygon(pts, fill=(0, 0, 0, 255) if rnd.random() < 0.6 else (255, 255, 255, 255))
    r = 0.08 * W
    lay.d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 255))
    return over(out, lay.done())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", default=os.path.join(ROOT, "data", "shots.json"))
    ap.add_argument("--render", default=os.path.join(ROOT, "art", "render"))
    ap.add_argument("--out", default=os.path.join(ROOT, "art", "frames"))
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--shot", action="append")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    data = json.load(open(a.shots))
    for s in data["shots"]:
        if a.all or (a.shot and s["id"] in a.shot):
            if not os.path.exists(os.path.join(a.render, f"{s['id']}_color.png")):
                print("no passes for", s["id"])
                continue
            w = composite(s, data, a.render, a.out, os.path.join(ROOT, "art", "control") if a.control else None)
            print(s["id"], "->", ", ".join(w))


if __name__ == "__main__":
    main()

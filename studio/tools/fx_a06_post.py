#!/usr/bin/env python3
"""Gate 4, shot A06: the 2D FX and grade pass over the Blender render of Karna's volley. FREE, no model call.

Input is the frame folder written by studio/tools/blender/shot_a06_volley.py (frames/0000.png ... and fx.json, which
holds the bow grip's screen position per frame). Per frame:

  grade    golden-hour grade: S-curve, warm gain, a burnt top of frame, saturation, vignette
  glow     bright parts (sun, sun-fire, trails) bloom in warm orange
  release  frames R and R+1 become two impact cards (black / white / orange) built from the render itself,
           then a white-gold flash dies off over three frames and a shock ring opens from the bow grip
  speed    thin speed lines at the frame edge while the camera rides with the arrows
  grain    light film grain, so the CG gradients do not band

  python studio/tools/fx_a06_post.py RENDER_DIR OUT.mp4
"""
import json, math, pathlib, random, subprocess, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

FPS = 24


def grade(a):
    """a: float32 HxWx3 in 0..1"""
    h, w = a.shape[:2]
    a = a ** 1.22
    a = np.clip((a - 0.5) * 1.16 + 0.5, 0, 1)                          # contrast
    a = a * a * (3 - 2 * a) * 0.35 + a * 0.65                          # gentle S-curve
    a = a * np.array([1.05, 0.96, 0.84], np.float32) + np.array([0.012, 0.0, 0.02], np.float32)
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    burn = np.clip(1 - y / 0.55, 0, 1) ** 1.6                          # the top of the frame burns toward ember orange
    a = a * (1 - 0.30 * burn) + a * np.array([1.0, 0.62, 0.38], np.float32) * 0.30 * burn
    lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    a = lum[..., None] + (a - lum[..., None]) * 1.16                   # saturation
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    a = a * (1 - 0.28 * np.clip(r - 0.55, 0, 1) ** 1.5)[..., None]     # vignette
    return np.clip(a, 0, 1)


def glow(a, strength=0.38):
    h, w = a.shape[:2]
    lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    hi = a * np.clip((lum - 0.84) / 0.16, 0, 1)[..., None]
    small = Image.fromarray((hi * 255).astype(np.uint8)).resize((w // 4, h // 4), Image.BILINEAR)
    wide = np.asarray(small.filter(ImageFilter.GaussianBlur(10)).resize((w, h), Image.BILINEAR), np.float32) / 255
    near = np.asarray(small.filter(ImageFilter.GaussianBlur(2.5)).resize((w, h), Image.BILINEAR), np.float32) / 255
    tint = np.array([1.0, 0.62, 0.30], np.float32)
    return np.clip(a + (wide * 0.9 + near * 0.6) * tint * strength, 0, 1)


def impact(a, k):
    """two-frame impact card in black, white and orange, from the render's own shapes"""
    g = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    out = np.zeros_like(a)
    cream, orange, ink = (np.array(c, np.float32) / 255 for c in ((255, 250, 235), (255, 120, 20), (12, 8, 6)))
    if k == 0:
        out[...] = cream
        out[g < 0.55] = orange
        out[g < 0.30] = ink
    else:                                                              # inverted: dark sky, white figure
        out[...] = orange
        out[g > 0.58] = ink
        out[g < 0.30] = cream
    return out


def ring_and_flash(a, t, c, w, h):
    """t frames after the impact cards: flash dies off, shock ring opens from the bow grip c (screen px)"""
    flash = max(0.0, 1 - t / 3)
    if flash:
        a = a + np.array([1.0, 0.88, 0.67], np.float32) * 0.22 * flash
    if t < 8 and c is not None:
        lay = Image.new("L", (w, h))
        d = ImageDraw.Draw(lay)
        r = 40 + 95 * t
        d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=255, width=max(2, 14 - 2 * t))
        d.ellipse([c[0] - r * 0.8, c[1] - r * 0.8, c[0] + r * 0.8, c[1] + r * 0.8], outline=120, width=max(1, 6 - t))
        m = np.asarray(lay.filter(ImageFilter.GaussianBlur(2.5)), np.float32)[..., None] / 255
        a = a + m * np.array([1.0, 0.78, 0.45], np.float32) * (1 - t / 8) ** 1.3
    return np.clip(a, 0, 1)


def speed_lines(a, t, n, seed, w, h):
    """thin white streaks at the frame edge while the camera rides with the arrows; t from 0 to n"""
    rnd = random.Random(seed)
    lay = Image.new("L", (w, h))
    d = ImageDraw.Draw(lay)
    cx, cy = w * 0.42, h * 0.52
    for _ in range(46):
        ang = rnd.uniform(0, 2 * math.pi)
        r0 = rnd.uniform(0.62, 0.8) * w * 0.6
        r1 = r0 + rnd.uniform(0.25, 0.5) * w
        d.line([(cx + math.cos(ang) * r0, cy + math.sin(ang) * r0 * 0.6), (cx + math.cos(ang) * r1, cy + math.sin(ang) * r1 * 0.6)],
               fill=rnd.randint(90, 200), width=rnd.choice((1, 2, 2, 3)))
    m = np.asarray(lay.filter(ImageFilter.GaussianBlur(0.8)), np.float32)[..., None] / 255
    k = math.sin(math.pi * min(1.0, t / n)) * 0.55
    return np.clip(a + m * k * np.array([1.0, 0.93, 0.82], np.float32), 0, 1)


def main():
    src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    if out.exists():
        raise SystemExit(f"exists, not overwriting (folder law 1): {out}")
    fx = json.loads((src / "fx.json").read_text())
    R = fx["release"]
    frames = sorted((src / "frames").glob("*.png"))
    if not frames:
        raise SystemExit("no frames")
    w, h = Image.open(frames[0]).size
    sx, sy = w / fx["size"][0], h / fx["size"][1]
    out.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
                         stdin=subprocess.PIPE)
    rng = np.random.default_rng(5)
    grip_r = fx["grip"][str(R)]
    c = (grip_r[0] * sx, grip_r[1] * sy) if grip_r[2] > 0 else None    # ring stays where the bow was at the release
    for fp in frames:
        f = int(fp.stem)
        a = np.asarray(Image.open(fp).convert("RGB"), np.float32) / 255
        a = glow(grade(a))
        if f in (R, R + 1):
            a = impact(a, f - R)
        elif f > R + 1:
            a = ring_and_flash(a, f - R - 2, c, w, h)
        if R + 2 <= f <= R + 18:
            a = speed_lines(a, f - R - 2, 16, f, w, h)
        a = np.clip(a + rng.normal(0, 0.012, a.shape[:2])[..., None].astype(np.float32), 0, 1)
        p.stdin.write((a * 255 + 0.5).astype(np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    print("wrote", out, f"{len(frames)} frames, {len(frames) / FPS:.2f} s, free (no model call)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Step 6 of the trailer plan, proof for shot A06: draw the seven-arrow release in code over a video draft. FREE, no model call.

Why: two Veo drafts of A06 both let the seven-arrow fan shrink to one arrow before the release. The video model holds
the full draw well, so the clip is used only for that. The release itself (sun-fire on the shafts, impact frames,
seven arrows leaving toward screen left, shock ring, shake) is drawn here.

  0.00-1.33 s  frames 0-31 of the draft: full draw, the seven arrows still on the string, sun-fire grows along the shafts
  1.33-1.42 s  two impact frames (black / white / orange)
  1.42-2.33 s  the seven arrows fly out of frame to screen LEFT, arrowheads leading; trails fade; camera shake decays

  python studio/tools/fx_a06_release.py --src studio/episodes/ep01_arjuna_vs_karna/renders/A06_draft_v2.mp4 \
      --out studio/episodes/ep01_arjuna_vs_karna/renders/A06_fx_proof_v1.mp4
"""
import argparse, math, pathlib, random, subprocess, tempfile

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

W, H, FPS = 1280, 720, 24
HOLD = 32                         # draft frames 0..31 are the clean full draw (the fan starts to shrink at frame 32)
HAND = (635, 285)                 # bow hand in frame 31, where the seven shafts cross the bow
TOP, BOTTOM = (395, 130), (375, 375)   # ends of the highest and the lowest arrow of the fan in frame 31
FAN_LEN = 290
FLIGHT = 22                       # frames after the impact frames
SPEED = 72                       # pixels per frame

def fan_angles():
    a0 = math.atan2(TOP[1] - HAND[1], TOP[0] - HAND[0])
    a1 = math.atan2(BOTTOM[1] - HAND[1], BOTTOM[0] - HAND[0])
    if a0 < 0:
        a0 += 2 * math.pi         # both angles on the left side of the circle, so the fan interpolates through screen left
    if a1 < 0:
        a1 += 2 * math.pi
    return [a0 + (a1 - a0) * i / 6 for i in range(7)]

ANGLES = fan_angles()

def along(a, d):
    return (HAND[0] + math.cos(a) * d, HAND[1] + math.sin(a) * d)

def add(base, layer, gain=1.0):
    """additive blend of an RGB layer on an RGB frame"""
    out = np.asarray(base, np.float32) + np.asarray(layer, np.float32) * gain
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

def sunfire(strength, seed):
    """orange-gold glow running along each nocked shaft"""
    rnd = random.Random(seed)
    lay = Image.new("RGB", (W, H)); d = ImageDraw.Draw(lay)
    for a in ANGLES:
        reach = FAN_LEN * (0.35 + 0.65 * strength) * rnd.uniform(0.9, 1.0)
        d.line([along(a, 8), along(a, reach)], fill=(255, 150, 40), width=5)
        d.line([along(a, 8), along(a, reach * 0.6)], fill=(255, 225, 150), width=2)
    d.ellipse([HAND[0] - 26, HAND[1] - 26, HAND[0] + 26, HAND[1] + 26], fill=(255, 190, 90))
    return ImageChops.add(lay.filter(ImageFilter.GaussianBlur(9)), lay.filter(ImageFilter.GaussianBlur(2)))

def clean_plate(frame):
    """frame 31 with the nocked arrows painted out: a grey closing removes thin dark lines over the bright sky"""
    closed = frame.filter(ImageFilter.MaxFilter(33)).filter(ImageFilter.MinFilter(33)).filter(ImageFilter.GaussianBlur(3))
    thin = frame.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.MinFilter(13))
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    d.polygon([(626, 258), (345, 88), (318, 418), (626, 318)], fill=255)        # the fan, left of the bow
    m = m.filter(ImageFilter.GaussianBlur(5))
    out = Image.composite(closed, frame, m)
    m2 = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m2).rectangle([664, 256, 736, 284], fill=255)               # the shafts between bow and string hand
    return Image.composite(thin, out, m2.filter(ImageFilter.GaussianBlur(3)))

def impact(plate, k):
    """two-frame impact card in black, white and orange"""
    g = np.asarray(plate.convert("L"), np.float32) / 255
    out = np.zeros((H, W, 3), np.float32)
    if k == 0:
        out[...] = (255, 250, 235); out[g < 0.55] = (255, 120, 20); out[g < 0.32] = (12, 8, 6)
    else:                                                      # the same card inverted: black sky, white figures
        out[...] = (255, 120, 20); out[g > 0.60] = (12, 8, 6); out[g < 0.32] = (255, 250, 235)
    im = Image.fromarray(out.astype(np.uint8))
    d = ImageDraw.Draw(im)
    col = (12, 8, 6) if k == 0 else (255, 250, 235)
    for a in ANGLES:                                           # the fan as hard graphic lines
        d.line([along(a, 0), along(a, 900)], fill=col, width=5 if k == 0 else 3)
    return im

def arrows(base, t):
    """the seven arrows t frames after release: orange fire trail, dark shaft with a white-hot head, shock ring"""
    trail = Image.new("L", (W, H)); td = ImageDraw.Draw(trail)             # alpha of the orange trail (normal blend, reads on a bright sky)
    body = Image.new("L", (W, H)); bd = ImageDraw.Draw(body)               # alpha of the dark arrow itself
    hot = Image.new("RGB", (W, H)); hd = ImageDraw.Draw(hot)               # additive white-hot light
    fade = max(0.0, 1 - t / FLIGHT)
    for i, a in enumerate(ANGLES):
        head = 70 + SPEED * (t + 0.5) * (1 + 0.06 * math.sin(i * 2.1))
        td.line([along(a, 14), along(a, head)], fill=int(235 * fade ** 1.3), width=9)
        for s in range(6):                                                 # motion streak behind the head
            k = 1 - s / 6
            hd.line([along(a, head - 18 * s), along(a, head - 18 * (s + 1))], fill=(int(255 * k), int(215 * k), int(120 * k)), width=5)
        bd.line([along(a, head - 70), along(a, head + 6)], fill=255, width=4)
        tip, bx, px = along(a, head + 34), along(a, head + 4), (-math.sin(a) * 9, math.cos(a) * 9)
        bd.polygon([tip, (bx[0] + px[0], bx[1] + px[1]), (bx[0] - px[0], bx[1] - px[1])], fill=255)           # arrowhead leads
        hd.polygon([tip, (bx[0] + px[0] * 0.5, bx[1] + px[1] * 0.5), (bx[0] - px[0] * 0.5, bx[1] - px[1] * 0.5)], fill=(255, 245, 210))
    r = 30 + 55 * t                                                        # shock ring from the bow
    ring = int(200 * max(0.0, 1 - t / 7))
    if ring:
        hd.ellipse([HAND[0] - r, HAND[1] - r, HAND[0] + r, HAND[1] + r], outline=(ring, int(ring * 0.7), int(ring * 0.35)), width=6)
    soft = ImageChops.lighter(trail.filter(ImageFilter.GaussianBlur(7)), trail.filter(ImageFilter.GaussianBlur(2)))
    out = Image.composite(Image.new("RGB", (W, H), (255, 105, 15)), base, soft)
    out = Image.composite(Image.new("RGB", (W, H), (70, 28, 8)), out, body.filter(ImageFilter.GaussianBlur(1.2)))
    return add(out, ImageChops.add(hot.filter(ImageFilter.GaussianBlur(5)), hot.filter(ImageFilter.GaussianBlur(1))))

def shake(im, t, seed):
    rnd = random.Random(seed)
    amp = 16 * max(0.0, 1 - t / 12) ** 2
    z = 1.035 + 0.02 * max(0.0, 1 - t / 5)                     # small punch-in, also hides the edges while shaking
    big = im.resize((int(W * z), int(H * z)), Image.LANCZOS)
    ox = (big.width - W) // 2 + int(rnd.uniform(-amp, amp)); oy = (big.height - H) // 2 + int(rnd.uniform(-amp, amp))
    ox = min(max(ox, 0), big.width - W); oy = min(max(oy, 0), big.height - H)
    return big.crop((ox, oy, ox + W, oy + H))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    if out.exists():
        raise SystemExit(f"exists, not overwriting (folder law 1): {out}")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        subprocess.run(["ffmpeg", "-v", "error", "-i", a.src, "-frames:v", str(HOLD), str(tmp / "s%03d.png")], check=True)
        src = [Image.open(tmp / f"s{i + 1:03d}.png").convert("RGB") for i in range(HOLD)]
        if src[0].size != (W, H):
            raise SystemExit(f"expected {W}x{H}, got {src[0].size}")
        frames = []
        for i, f in enumerate(src):                            # the hold: sun-fire grows, a tremble in the last half second
            s = (i / (HOLD - 1)) ** 2
            f = add(f, sunfire(s, i), 0.75 * s * (0.85 + 0.15 * math.sin(i * 2.3)))
            frames.append(shake(f, 12 - 3 * s, i) if i > HOLD - 12 else f)
        plate = clean_plate(src[-1])
        frames += [impact(src[-1], 0), impact(src[-1], 1)]
        for t in range(FLIGHT):
            f = arrows(plate, t)
            flash = max(0.0, 1 - t / 3)                        # white-gold flash dying off after the impact frames
            if flash:
                f = add(f, Image.new("RGB", (W, H), (255, 225, 170)), 0.30 * flash)
            frames.append(shake(f, t, 100 + t))
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
        for f in frames:
            p.stdin.write(f.tobytes())
        p.stdin.close(); p.wait()
    print("wrote", out, f"{len(frames)} frames, {len(frames) / FPS:.2f} s, free (no model call)")

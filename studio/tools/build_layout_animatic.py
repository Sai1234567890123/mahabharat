#!/usr/bin/env python3
"""Cut the 22 layout stills (layout_blender.py) into a 90 s animatic with the shot-card timings. Free.

  python studio/tools/build_layout_animatic.py --layout <dir with A01.png..A22.png> --out animatic_layout.mp4

Each shot gets the camera move from its card as a simple 2D move on the still (push, pan, drop, shake),
plus the flagged effects: negative flash on A13, impact frames on A20, colour drain on A18.
"""
import argparse, json, math, random, subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

EP = Path(__file__).resolve().parent.parent / "episodes" / "ep01_arjuna_vs_karna"
FPS, W, H = 24, 1280, 720
BAR = int((H - W / 2.39) / 2)          # 2.39:1 inside 16:9

def ease(t):
    return t * t * (3 - 2 * t)

# id: (zoom0, zoom1, (cx0, cy0), (cx1, cy1), options)
MOVES = {
    "A01": (1.7, 1.7, (0.5, 0.5), (0.5, 0.5), dict(snap_out=6)),
    "A02": (1.0, 1.14, (0.5, 0.52), (0.5, 0.56), {}),
    "A03": (1.0, 1.12, (0.5, 0.5), (0.47, 0.42), {}),
    "A04": (1.0, 1.12, (0.5, 0.5), (0.53, 0.42), {}),
    "A05": (1.18, 1.18, (0.42, 0.52), (0.58, 0.52), dict(linear=True, shake=3)),
    "A06": (1.0, 1.35, (0.5, 0.5), (0.56, 0.62), dict(whip=5)),
    "A07": (1.05, 1.05, (0.5, 0.5), (0.5, 0.5), dict(shake=7, hits=[0.3, 0.55, 0.8])),
    "A08": (1.6, 1.0, (0.5, 0.52), (0.5, 0.5), {}),
    "A09": (1.0, 1.03, (0.5, 0.5), (0.5, 0.5), {}),
    "A10": (1.0, 1.10, (0.5, 0.5), (0.52, 0.35), {}),
    "A11": (1.12, 1.12, (0.44, 0.5), (0.56, 0.48), {}),
    "A12": (1.3, 1.3, (0.62, 0.42), (0.38, 0.42), dict(linear=True)),
    "A13": (1.08, 1.08, (0.5, 0.42), (0.5, 0.42), dict(drop=0.5, neg=3)),
    "A14": (1.0, 1.18, (0.5, 0.5), (0.46, 0.36), dict(ramp=True, hits=[0.5])),
    "A15": (1.0, 1.12, (0.5, 0.5), (0.5, 0.42), {}),
    "A16": (1.0, 1.10, (0.5, 0.5), (0.6, 0.5), dict(shake=2)),
    "A17": (1.0, 1.06, (0.5, 0.5), (0.56, 0.48), {}),
    "A18": (1.2, 1.2, (0.5, 0.40), (0.5, 0.58), dict(drain=True)),
    "A19": (1.0, 2.3, (0.5, 0.5), (0.36, 0.52), dict(drain=True)),
    "A20": (1.0, 1.0, (0.5, 0.5), (0.5, 0.5), dict(impact=8, drain=True)),
    "A21": (1.15, 1.15, (0.5, 0.60), (0.5, 0.42), {}),
    "A22": (1.0, 1.0, (0.5, 0.5), (0.5, 0.5), {}),
}

def frame(src, sid, i, n, rnd):
    z0, z1, c0, c1, o = MOVES[sid]
    t = i / max(n - 1, 1)
    u = t if o.get("linear") else ease(t)
    if o.get("ramp"):                                   # 100 to 10 to 100 percent
        u = 0.45 * min(t / 0.25, 1) + 0.1 * min(max((t - 0.25) / 0.5, 0), 1) + 0.45 * min(max((t - 0.75) / 0.25, 0), 1)
    z = z0 + (z1 - z0) * u
    cx, cy = c0[0] + (c1[0] - c0[0]) * u, c0[1] + (c1[1] - c0[1]) * u
    if o.get("snap_out") and i >= n - o["snap_out"]:
        z = z0 + (1.0 - z0) * ((i - (n - o["snap_out"])) / (o["snap_out"] - 1))
    if o.get("whip") and i >= n - o["whip"]:
        cx += 0.09 * (i - (n - o["whip"]) + 1)
    if o.get("drop") and t >= o["drop"]:
        cy -= 0.07 * min((t - o["drop"]) * 12, 1)
    sx = sy = 0
    amp = o.get("shake", 0)
    for h in o.get("hits", []):
        d = t - h
        if 0 <= d < 0.12:
            amp = max(amp, 22 * (1 - d / 0.12))
    if amp:
        sx, sy = rnd.uniform(-amp, amp), rnd.uniform(-amp, amp)
    sw, sh = src.width, src.height
    cw, ch = sw / z, sh / z
    x0 = min(max(cx * sw - cw / 2 + sx, 0), sw - cw)
    y0 = min(max(cy * sh - ch / 2 + sy, 0), sh - ch)
    im = src.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    if o.get("drain"):
        k = 0.75 if sid != "A18" else 0.75 * t
        im = Image.blend(im, ImageOps.grayscale(im).convert("RGB"), k)
    if o.get("neg") and abs(i - int(n * o.get("drop", 0.5))) < o["neg"] / 2:
        im = ImageChops.invert(im)
    if o.get("impact") and i < o["impact"]:
        im = [Image.new("RGB", (W, H), "white"), ImageChops.invert(im), Image.new("RGB", (W, H), "black"), im][i % 4]
    for h in o.get("hits", []):
        if 0 <= t - h < 1.5 / n:
            im = Image.blend(im, Image.new("RGB", (W, H), "white"), 0.7)
    return im

def load_font(size, bold=False):
    candidates = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf"]
        if bold else
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"]
    )
    for c in candidates:
        if Path(c).exists():
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def find_still(layout_dir, sid):
    for ext in (".png", ".jpg", ".jpeg"):
        p = layout_dir / f"{sid}{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(f"Missing layout still for {sid} in {layout_dir}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--audio", default=None)
    ap.add_argument("--shots", default=None)
    a = ap.parse_args()
    shots_path = Path(a.shots) if a.shots else (EP / "shots.json")
    data = json.loads(shots_path.read_text())
    font = load_font(22, bold=True)
    small = load_font(18, bold=False)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if a.audio:
        cmd += ["-i", a.audio]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20"]
    if a.audio:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-movflags", "+faststart", a.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    rnd, total, clock = random.Random(3), 0, 0.0
    layout_dir = Path(a.layout)
    for s in data["shots"]:
        sid, n = s["id"], int(round(s["dur"] * FPS))
        src = Image.open(find_still(layout_dir, sid)).convert("RGB")
        label = f"{sid}  {clock:04.1f}s  {s['dur']}s"
        text = s["action"] if len(s["action"]) < 92 else s["action"][:89] + "..."
        for i in range(n):
            im = frame(src, sid, i, n, rnd)
            d = ImageDraw.Draw(im)
            d.rectangle((0, 0, W, BAR), fill="black")
            d.rectangle((0, H - BAR, W, H), fill="black")
            d.text((18, 30), label, fill=(255, 214, 120), font=font)
            d.text((W - 18 - d.textlength("LAYOUT, not final look", font=small), 34), "LAYOUT, not final look", fill=(170, 170, 170), font=small)
            d.text((18, H - BAR + 30), text, fill=(235, 235, 235), font=small)
            ff.stdin.write(im.tobytes())
        total += n
        clock += s["dur"]
    ff.stdin.close()
    rc = ff.wait()
    if rc != 0:
        raise SystemExit(f"ffmpeg exited with code {rc}")
    print("frames", total, "seconds", total / FPS, "->", a.out)

if __name__ == "__main__":
    main()

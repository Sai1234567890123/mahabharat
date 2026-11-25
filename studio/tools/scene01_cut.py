#!/usr/bin/env python3
"""Cut Scene 01 "Suryaputra" (scene01_3d.py frames) into one video: subtitles, then the title card. Free, local ffmpeg.

Frames are drawings on twos (12 a second); the video plays at 24 fps. Spoken lines are upright, Karna's thoughts italic
(a slanted serif, drawn by shearing the upright one), Shalya's line is named. The title card fades in after shot 9.

  python studio/tools/scene01_cut.py <frames_dir> <out.mp4>
"""
import pathlib, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
# shot: [(from_s, to_s, text, kind)], times inside the shot; kind: say | think | other
SUBS = {2: [(2.5, 4.4, "Father.", "say")],
        4: [(0.6, 4.6, "I gave away what you gave me.", "think")],
        6: [(2.0, 4.8, "Today I keep only my word.", "think")],
        7: [(0.5, 3.9, "SHALYA: The Pandavas wait, son of a charioteer.", "other")],
        8: [(1.3, 3.7, "Let them see the sun.", "say")]}
TITLE_S, FADE_S = 3.5, 1.0


def text_layer(size, text, font, slant):
    """the subtitle on a transparent layer, with a soft dark edge; slanted for thoughts"""
    W, H = size
    lay = Image.new("RGBA", size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    w = d.textlength(text, font=font); x, y = (W - w) / 2, H - 70 * H / 540
    for dx in (-2, -1, 0, 1, 2):
        for dy in (-2, -1, 0, 1, 2):
            d.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 150))
    d.text((x, y), text, font=font, fill=(255, 246, 228, 255))
    if slant:
        lay = lay.transform(size, Image.AFFINE, (1, 0.2, -0.2 * (y + 20), 0, 1, 0), Image.BICUBIC)
    return lay


src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp); i = 0; last = None
    for k in range(1, 10):
        frames = sorted((src / f"s01_{k:02d}").glob("f_*.png"))
        if not frames:
            print("missing shot", k); continue
        for j, f in enumerate(frames):
            t = j * 2 / 24
            im = Image.open(f).convert("RGBA")
            font = ImageFont.truetype(FONT, round(30 * im.width / 960))
            for t0, t1, text, kind in SUBS.get(k, []):
                if t0 <= t < t1:
                    im = Image.alpha_composite(im, text_layer(im.size, text, font, kind == "think"))
            last = im.convert("RGB"); last.save(tmp / f"{i:05d}.png"); i += 1
    # title card: the last frame darkens, the title fades in
    W, H = last.size
    big = ImageFont.truetype(FONT, round(72 * W / 960)); small = ImageFont.truetype(FONT, round(22 * W / 960))
    for j in range(int(TITLE_S * 12)):
        u = min(j / (FADE_S * 12), 1.0)
        im = Image.blend(last, Image.new("RGB", (W, H), (8, 6, 4)), 0.75 * u).convert("RGBA")
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for s, fnt, y, col in (("SURYAPUTRA", big, H / 2 - 60 * H / 540, (236, 196, 110)), ("son of the sun", small, H / 2 + 28 * H / 540, (240, 228, 205))):
            w = d.textlength(s, font=fnt); d.text(((W - w) / 2, y), s, font=fnt, fill=(*col, int(255 * u)))
        Image.alpha_composite(im, lay).convert("RGB").save(tmp / f"{i:05d}.png"); i += 1
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", str(tmp / "%05d.png"), "-r", "24",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-movflags", "+faststart", str(out)], check=True)
print("wrote", out, i, "drawings")

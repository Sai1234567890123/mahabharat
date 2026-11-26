#!/usr/bin/env python3
"""Cut the battle moves and bows test (moves_demo.py frames) into one video with a caption per sequence, ending on the
bow check still. Free, local ffmpeg. Frames are drawings on twos (12 a second); the video plays at 24 fps.

  python studio/tools/moves_demo_cut.py <frames_dir> <out.mp4>
"""
import pathlib, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

SEQ = [("arjuna_shot", "1  Arjuna: nock, draw Gandiva to the jaw, hold, loose"),
       ("karna_shot", "2  Karna: the same draw and release with Vijaya"),
       ("karna_defend", "3  Karna: block, dodge left, dodge right"),
       ("arjuna_run", "4  Arjuna: run cycle")]
src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)


def caption(im, cap):
    d = ImageDraw.Draw(im, "RGBA"); W, H = im.size
    d.rectangle((0, H - 46, W, H), fill=(0, 0, 0, 120))
    d.text((18, H - 37), cap, font=font, fill=(255, 245, 230))
    d.text((W - 330, 12), "battle moves and bows test · free", font=small, fill=(255, 255, 255, 170))
    return im


with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp); i = 0; size = None
    for name, cap in SEQ:
        frames = sorted((src / name).glob("f_*.png"))
        if not frames:
            print("missing", name); continue
        for f in frames:
            im = caption(Image.open(f).convert("RGB"), cap); size = im.size
            im.save(tmp / f"{i:05d}.png"); i += 1
    still = src / "still_bows_001.png"
    if still.exists():                                                  # 3 s on the bow check, fitted into the frame
        b = Image.open(still).convert("RGB"); b.thumbnail(size)
        card = Image.new("RGB", size, (20, 16, 12)); card.paste(b, ((size[0] - b.width) // 2, (size[1] - b.height) // 2))
        card = caption(card, "5  The bows at rest and at full draw: Gandiva (left pair), Vijaya (right pair)")
        for _ in range(36):
            card.save(tmp / f"{i:05d}.png"); i += 1
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", str(tmp / "%05d.png"), "-r", "24",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", str(out)], check=True)
print("wrote", out, i, "drawings")

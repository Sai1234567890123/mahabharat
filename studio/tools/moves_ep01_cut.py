#!/usr/bin/env python3
"""Cut the EP01 moves demo (moves_ep01_demo.py clips) into one video with a caption per clip. Free, local ffmpeg.

  python studio/tools/moves_ep01_cut.py <clips_dir> <out.mp4>
Clips play in story order, each captioned with its shot, hero and move. Drawings on twos (12 a second), video at 24 fps.
"""
import pathlib, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
ORDER = [  # (clip folder, caption)
    ("charioteer_krishna", "A02 · Krishna · the charioteer, reins in hand"),
    ("bow_salute_karna", "A03 · Karna · touches the bow to his forehead"),
    ("bow_draw_arjuna", "A04 · Arjuna · draws Gandiva"),
    ("reins_flick_krishna", "A05 · Krishna · flicks the reins"),
    ("fan_release_karna", "A06 · Karna · the seven-arrow fan"),
    ("rapid_fire_arjuna", "A07 · Arjuna · arrow after arrow"),
    ("exhausted_arjuna", "A09 · Arjuna · exhausted"),
    ("exhausted_karna", "A09 · Karna · exhausted"),
    ("quiver_draw_karna", "A10 · Karna · draws the serpent arrow"),
    ("bow_draw_ear_karna", "A11 · Karna · draws it to his ear"),
    ("foot_press_krishna", "A13 · Krishna · presses the chariot down"),
    ("head_hit_arjuna", "A14 · Arjuna · the crown is struck off"),
    ("rise_hair_push_arjuna_bare", "A15 · Arjuna · rises bare-headed"),
    ("leap_down_karna", "A16 · Karna · leaps down from the chariot"),
    ("heave_karna", "A16 · Karna · heaves the sunk wheel"),
    ("palm_wait_karna", "A17 · Karna · \"wait\""),
    ("calm_look_krishna", "A17 · Krishna · the look"),
    ("bow_draw_ear_arjuna_bare", "A19 · Arjuna · draws the Anjalika"),
    ("stand_tall_karna", "A20 · Karna · against the sun"),
    ("bow_lower_arjuna_bare", "A22 · Arjuna · lowers Gandiva"),
]

src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
tmp = pathlib.Path(tempfile.mkdtemp())
i = 0
for key, cap in ORDER:
    frames = sorted((src / key).glob("f_*.png"))
    if not frames:
        print("missing", key); continue
    for p in frames:
        im = Image.open(p).convert("RGB"); W, H = im.size
        d = ImageDraw.Draw(im); f = ImageFont.truetype(FONT, int(22 * H / 540))
        w = d.textlength(cap, font=f); x, y = (W - w) / 2, H - 44 * H / 540
        d.rectangle((x - 12, y - 6, x + w + 12, y + 30 * H / 540), fill=(10, 8, 6))
        d.text((x, y), cap, font=f, fill=(240, 228, 205))
        im.save(tmp / f"{i:05d}.png"); i += 1
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", str(tmp / "%05d.png"), "-r", "24",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-movflags", "+faststart", str(out)], check=True)
print("wrote", out, i, "drawings")

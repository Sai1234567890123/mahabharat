#!/usr/bin/env python3
"""Cut the animation test demo (anim_demo.py frames) into one video with a caption per sequence. Free, local ffmpeg.

Frames are drawings on twos (12 a second); the video plays at 24 fps, so each drawing holds two frames, as in the bible.

  python studio/tools/anim_demo_cut.py <frames_dir> <out.mp4>
"""
import pathlib, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

SEQ = [("s1_karna_speaks", "1  Karna speaks: lip-sync, blinks, sorrow to a half smile"),
       ("s2_arjuna_arrow", "2  Arjuna turns, reaches to his quiver and draws an arrow"),
       ("s3_krishna_blessing", "3  Krishna smiles and raises his hand in blessing (abhaya mudra)"),
       ("s4_karna_walk", "4  Karna walks: planted feet, swinging arms, then stops"),
       ("s5_face_off", "5  Face-off: Karna points and calls out, Arjuna clenches his fists and steps in")]
src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp); i = 0
    for name, cap in SEQ:
        frames = sorted((src / name).glob("f_*.png"))
        if not frames:
            print("missing", name); continue
        for f in frames:
            im = Image.open(f).convert("RGB"); d = ImageDraw.Draw(im, "RGBA")
            W, H = im.size
            d.rectangle((0, H - 46, W, H), fill=(0, 0, 0, 120))
            d.text((18, H - 37), cap, font=font, fill=(255, 245, 230))
            d.text((W - 300, 12), "animation test · rigs v2/v3 · free", font=small, fill=(255, 255, 255, 170))
            im.save(tmp / f"{i:05d}.png"); i += 1
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", str(tmp / "%05d.png"), "-r", "24",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", str(out)], check=True)
print("wrote", out, i, "drawings")

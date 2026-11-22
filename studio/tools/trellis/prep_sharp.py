#!/usr/bin/env python3
"""Free step before prep_input.py: upscale a model sheet 2x (Lanczos) and sharpen it, as done by hand for Karna take 3
(trellis_in/src_front_v2_up2x.png), which gave a clearly sharper face and chest on the 1536 model. Never overwrites.

  python studio/tools/trellis/prep_sharp.py studio/cast/arjuna/model/front_v1.png studio/cast/arjuna/model/trellis_in/src_front_v1_up2x.png
"""
import pathlib, sys
from PIL import Image, ImageFilter

src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
if dst.exists():
    raise SystemExit(f"exists, not overwriting (folder law 1): {dst}")
im = Image.open(src).convert("RGB")
im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=2))
dst.parent.mkdir(parents=True, exist_ok=True)
im.save(dst)
print("wrote", dst, im.size)

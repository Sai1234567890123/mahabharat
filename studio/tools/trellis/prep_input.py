#!/usr/bin/env python3
"""Free step before a TRELLIS.2 run: turn a model sheet on a plain light background into a square cut-out.

The background is removed by a flood fill from the picture's border, so white areas inside the figure (eyes, cloth) stay.
The result is a square RGBA PNG with the figure centred and a margin. The RGB under the transparent area stays white,
so the picture also works if the 3D pipeline ignores the alpha and removes the background itself.

  python studio/tools/trellis/prep_input.py studio/cast/karna/model/front_v2.png studio/cast/karna/model/trellis_in/karna_front.png
"""
import pathlib, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter

SIZE, MARGIN, THRESH = 1536, 0.07, 26
MARK = (255, 0, 255)

def cutout(im):
    work = im.convert("RGB").copy()
    w, h = work.size
    seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]
    for s in seeds:
        if work.getpixel(s) != MARK:
            ImageDraw.floodfill(work, s, MARK, thresh=THRESH)
    # enclosed background (for example between a bow and its string): any large region in the background colour
    bgcol, total = im.convert("RGB").getpixel((2, 2)), w * h
    for y in range(8, h, 16):
        for x in range(8, w, 16):
            px = work.getpixel((x, y))
            if px != MARK and sum(abs(px[i] - bgcol[i]) for i in range(3)) <= THRESH:
                trial = work.copy()
                ImageDraw.floodfill(trial, (x, y), MARK, thresh=THRESH)
                grown = sum(1 for a_, b_ in zip(trial.tobytes()[1::3], work.tobytes()[1::3]) if a_ != b_)
                if grown > 0.004 * total:
                    work = trial
    r, g, b = work.split()
    bg = ImageChops.multiply(ImageChops.multiply(r.point(lambda v: 255 if v == 255 else 0), g.point(lambda v: 255 if v == 0 else 0)),
                             b.point(lambda v: 255 if v == 255 else 0))
    alpha = ImageChops.invert(bg).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    return alpha

if __name__ == "__main__":
    src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    if dst.exists():
        raise SystemExit(f"exists, not overwriting (folder law 1): {dst}")
    im = Image.open(src).convert("RGB")
    alpha = cutout(im)
    box = alpha.point(lambda v: 255 if v > 40 else 0).getbbox()
    fig, a = im.crop(box), alpha.crop(box)
    scale = SIZE * (1 - 2 * MARGIN) / max(fig.size)
    new = (max(1, round(fig.width * scale)), max(1, round(fig.height * scale)))
    fig, a = fig.resize(new, Image.LANCZOS), a.resize(new, Image.LANCZOS)
    white = Image.new("RGB", new, (255, 255, 255))
    fig = Image.composite(fig, white, a)                       # white under the transparent area
    canvas = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 0))
    fig.putalpha(a)
    canvas.paste(fig, ((SIZE - new[0]) // 2, (SIZE - new[1]) // 2))
    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dst)
    cover = sum(1 for v in a.tobytes() if v > 128) / (new[0] * new[1])
    print("wrote", dst, canvas.size, f"figure {new[0]}x{new[1]}, {cover:.0%} of its box is opaque")

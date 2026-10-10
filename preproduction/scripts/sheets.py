"""Builds the presentation sheets from the composited frames.

  art/storyboard-1.jpg, art/storyboard-2.jpg   all pilot shots with captions
  art/color-script.jpg                         one panel per story beat
  art/silhouette-lineup.png                    hero cast in color and as pure silhouettes
  art/fx-sheet.jpg                             the 2D FX vocabulary
  art/concept-*.jpg                            hero frames with a title strip
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import compose as C

ROOT = C.ROOT
ART = os.path.join(ROOT, "art")
FR = os.path.join(ART, "frames")
SELECTED = os.path.join(ART, "selected")
APP_JSON = os.path.join(SELECTED, "APPROVED.json")
RENDER = os.environ.get("RENDER_DIR", os.path.join(ART, "render"))
PAPER = (24, 20, 26)
INK = (236, 228, 214)
MUTED = (160, 150, 140)

FONT_DIR = "/usr/share/fonts/opentype/inter"


def shot_frame(sid):
    if os.path.exists(APP_JSON):
        try:
            with open(APP_JSON) as f:
                shots_map = json.load(f).get("shots", {})
            if sid in shots_map:
                p = os.path.join(SELECTED, shots_map[sid])
                if os.path.exists(p):
                    return p
        except Exception:
            pass
    for ext in (".png", ".jpg"):
        p = os.path.join(SELECTED, f"{sid}{ext}")
        if os.path.exists(p):
            return p
    for ext in (".png", ".jpg"):
        p = os.path.join(FR, f"{sid}{ext}")
        if os.path.exists(p):
            return p
    return None


def font(size, bold=False):
    for name in (("Inter-Bold.otf" if bold else "Inter-Regular.otf"), "InterDisplay-Medium.otf"):
        p = os.path.join(FONT_DIR, name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    win_fonts = ["C:\\Windows\\Fonts\\segoeuib.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"] if bold else ["C:\\Windows\\Fonts\\segoeui.ttf", "C:\\Windows\\Fonts\\arial.ttf"]
    for p in win_fonts:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def wrap(d, text, f, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def header(d, W, title, sub):
    d.text((40, 28), title, font=font(40, True), fill=INK)
    d.text((40, 80), sub, font=font(20), fill=MUTED)


def storyboard(data):
    shots = data["shots"]
    tw, th = 600, 251
    cols, cap = 3, 150
    pages = [shots[:9], shots[9:]]
    for pi, page in enumerate(pages):
        rows = math.ceil(len(page) / cols)
        W = 40 + cols * (tw + 30) + 10
        H = 130 + rows * (th + cap + 20) + 20
        sheet = Image.new("RGB", (W, H), PAPER)
        d = ImageDraw.Draw(sheet)
        header(d, W, f"The First Conch: storyboard {pi + 1}/2",
               "Approved pilot frames: AI paint-over pass on Blender layout.")
        for k, s in enumerate(page):
            x = 40 + (k % cols) * (tw + 30)
            y = 130 + (k // cols) * (th + cap + 20)
            fp = shot_frame(s['id'])
            if fp and os.path.exists(fp):
                im = Image.open(fp).convert("RGB").resize((tw, th), Image.LANCZOS)
                sheet.paste(im, (x, y))
            act = data["acts"][s["act"]]
            d.rectangle([x, y + th, x + tw, y + th + 6], fill=C.rgb255(act["key"])[:3])
            d.text((x, y + th + 14), f"{s['id']}  {s['title']}", font=font(20, True), fill=INK)
            d.text((x + tw - 60, y + th + 14), f"{s['duration']:.0f}s", font=font(18), fill=MUTED)
            cam = s["camera"]
            d.text((x, y + th + 42), f"Act {s['act']} · beat {s['beat']} · {cam['lens']}mm · {cam['move']}", font=font(15),
                   fill=MUTED)
            for li, line in enumerate(wrap(d, s["description"], font(15), tw)[:4]):
                d.text((x, y + th + 66 + li * 20), line, font=font(15), fill=INK)
        sheet.save(os.path.join(ART, f"storyboard-{pi + 1}.jpg"), quality=90)


def color_script(data):
    beats = {}
    for s in data["shots"]:
        beats.setdefault(s["beat"], s)
    pw, ph = 300, 126
    n = len(beats)
    W = 40 + n * (pw + 8) + 32
    H = 490
    sheet = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(sheet)
    header(d, W, "The First Conch: color script", "One panel per story beat. Simplified from the concept frames: value and hue only.")
    for i, (b, s) in enumerate(sorted(beats.items())):
        x = 40 + i * (pw + 8)
        y = 140
        fp = shot_frame(s['id'])
        if fp and os.path.exists(fp):
            im = Image.open(fp).convert("RGB").resize((pw, ph), Image.LANCZOS)
            im = im.filter(ImageFilter.GaussianBlur(2.2)).quantize(7, method=Image.Quantize.MEDIANCUT).convert("RGB")
            sheet.paste(im, (x, y))
        d.text((x, y + ph + 10), f"{b}. {s['title']}", font=font(16, True), fill=INK)
    # act bands with palette swatches
    acts = []
    for i, (b, s) in enumerate(sorted(beats.items())):
        if not acts or acts[-1][0] != s["act"]:
            acts.append([s["act"], i, i])
        else:
            acts[-1][2] = i
    for a, i0, i1 in acts:
        act = data["acts"][a]
        x0, x1 = 40 + i0 * (pw + 8), 40 + i1 * (pw + 8) + pw
        y = 320
        d.rectangle([x0, y, x1, y + 8], fill=C.rgb255(act["key"])[:3])
        d.text((x0, y + 18), f"Act {a}. {act['name']}", font=font(20, True), fill=INK)
        d.text((x0, y + 46), act["mood"], font=font(16), fill=MUTED)
        for k, key in enumerate(("key", "shadow", "accent")):
            sx = x0 + k * min(120, (x1 - x0) // 3)
            d.rectangle([sx, y + 80, sx + 40, y + 110], fill=C.rgb255(act[key])[:3])
            d.text((sx, y + 116), f"{key} {act[key]}", font=font(11), fill=MUTED)
    sheet.save(os.path.join(ART, "color-script.jpg"), quality=92)


def lineup(data):
    p = os.path.join(RENDER, "lineup_color.png")
    if not os.path.exists(p):
        return
    im = Image.open(p).convert("RGBA")
    w, h = im.size
    order = ["yudhishthira", "bhima", "duryodhana", "bhishma", "arjuna", "krishna"]  # as seen by the camera
    W, H = w + 80, 2 * h + 330
    sheet = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(sheet)
    header(d, W, "Pilot cast: color and silhouette", "Proxy figures from the blockout. Top: color and energy codes. Bottom: pure silhouettes must read on their own.")
    paper = Image.new("RGBA", (w, h), (226, 218, 204, 255))
    paper.alpha_composite(im)
    sheet.paste(paper.convert("RGB"), (40, 130))
    a = np.asarray(im)[..., 3]
    sil = np.where(a[..., None] > 128, np.zeros(3), np.array([226, 218, 204])).astype(np.uint8)
    sheet.paste(Image.fromarray(sil), (40, 130 + h + 170))
    for i, k in enumerate(order):
        c = data["characters"][k]
        xw = (2.5 - i) * 1.25  # world x of the figure in blockout.py's lineup
        x = int(40 + w / 2 - xw / 8.4 * w - 70)
        y = 130 + h + 14
        d.text((x, y), c["name"], font=font(22, True), fill=INK)
        for j, key in enumerate(("skin", "costume", "accent", "energy")):
            d.rectangle([x + j * 54, y + 36, x + j * 54 + 44, y + 66], fill=C.rgb255(c[key])[:3])
            d.text((x + j * 54, y + 72), key, font=font(12), fill=MUTED)
    sheet.save(os.path.join(ART, "silhouette-lineup.png"), optimize=True)


def fx_sheet(data):
    pw, ph = 520, 360
    cols, rows = 4, 3
    W, H = 40 + cols * (pw + 20) + 20, 130 + rows * (ph + 56) + 10
    sheet = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(sheet)
    header(d, W, "2D FX vocabulary", "Drawn on twos (12 fps) over 24 fps animation. Each conch and hero has its own energy color.")
    rnd = random.Random(3)
    meta = {"anchors": {}, "sun": [pw / 2, ph / 2, 1]}

    def panel(i, title, bg, fn):
        x = 40 + (i % cols) * (pw + 20)
        y = 130 + (i // cols) * (ph + 56)
        base = np.ones((ph, pw, 3), np.float32) * C.rgb(bg)
        yy = np.linspace(0, 1, ph)[:, None, None]
        base = base * (0.75 + 0.35 * yy)
        out = fn(base)
        sheet.paste(C.to_img(np.clip(out, 0, 1)), (x, y))
        d.text((x, y + ph + 10), title, font=font(18, True), fill=INK)

    def layer_fx(kind, f, p=None, add=False):
        def fn(base):
            lay = C.Layer(pw, ph)
            pt = p or (pw / 2, ph / 2, 1)
            if kind == "lightning":
                C.fx_lightning(lay, pt, f, pw, ph, rnd, f["p2"])
            else:
                C.FX[kind](lay, pt, f, pw, ph, rnd)
            L = lay.done()
            img = C.add(base, L) if add else C.over(base, L)
            glow = L[..., :3] * L[..., 3:4]
            return img + C.blur(glow, 8) * 0.6
        return fn

    conches = [("Panchajanya (Krishna)", "#FFF4D0"), ("Devadatta (Arjuna)", "#6FC3FF"), ("Paundra (Bhima)", "#9FE3C1"),
               ("Anantavijaya (Yudhishthira)", "#F3DCA0"), ("Bhishma's conch", "#CDEFF2")]
    i = 0
    for name, col in conches:
        panel(i, f"Conch rings: {name}", "#2A2233",
              layer_fx("rings", dict(color=col, count=7, r0=0.04, r1=0.9, width=0.008, squash=0.75), (pw * 0.3, ph * 0.55, 1)))
        i += 1
    panel(i, "Divine light: hard-edged god rays", "#3E2A48",
          layer_fx("godrays", dict(color="#FFE2B0", count=16, alpha=0.4), (pw * 0.5, ph * 0.1, 1)))
    i += 1
    panel(i, "Halo forming behind Krishna", "#56606C", layer_fx("halo", dict(color="#E8C15A", r=0.22, alpha=0.9)))
    i += 1
    panel(i, "Sudarshana chakra", "#120B2E", layer_fx("chakra", dict(color="#FFE9A8", r=0.16)))
    i += 1
    panel(i, "Vishvarupa yantra with eyes", "#120B2E",
          layer_fx("yantra", dict(color="#FFE9A8", r=0.22, alpha=1.0, petals=16, faces=12)))
    i += 1
    panel(i, "Arjuna's lightning (Gandiva)", "#3A1A12",
          layer_fx("lightning", dict(color="#6FC3FF", p2=(pw * 0.8, ph * 0.85, 1)), (pw * 0.2, ph * 0.12, 1)))
    i += 1
    panel(i, "Ground shockwave and dust", "#8C4F6A", layer_fx("shockwave", dict(color="#FFF4D0"), (pw * 0.5, ph * 0.72, 1)))
    i += 1
    imp = os.path.join(FR, "SH070_impact.jpg")

    def impact(base):
        if os.path.exists(imp):
            return C.from_img(Image.open(imp).convert("RGB").resize((pw, ph), Image.LANCZOS))
        return base
    panel(i, "Impact frame: black, white, energy color", "#000000", impact)
    sheet.save(os.path.join(ART, "fx-sheet.jpg"), quality=92)


def concept_plates(data):
    """Hero frames at full size with a slim caption strip, for sharing."""
    for s in data["shots"]:
        if not s.get("hero"):
            continue
        fp = shot_frame(s['id'])
        if not fp or not os.path.exists(fp):
            continue
        im = Image.open(fp).convert("RGB")
        w, h = im.size
        sheet = Image.new("RGB", (w, h + 90), PAPER)
        sheet.paste(im, (0, 0))
        d = ImageDraw.Draw(sheet)
        d.text((30, h + 18), f"{s['id']}  {s['title']}", font=font(30, True), fill=INK)
        d.text((30, h + 56), f"Act {s['act']}: {data['acts'][s['act']]['name']} · {s['source']}", font=font(18), fill=MUTED)
        d.text((w - 560, h + 56), "Approved hero frame (AI paint-over pass)", font=font(18), fill=MUTED)
        slug = s["title"].lower().replace("'", "").replace(",", "").replace(" ", "-")
        sheet.save(os.path.join(ART, f"concept-{s['id']}-{slug}.jpg"), quality=92, subsampling=0)


def main():
    data = json.load(open(os.path.join(ROOT, "data", "shots.json")))
    storyboard(data)
    color_script(data)
    lineup(data)
    fx_sheet(data)
    concept_plates(data)
    print("sheets written to", ART)


if __name__ == "__main__":
    main()

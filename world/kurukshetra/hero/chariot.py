"""War chariots after concept images 6, 42 and 46: four wheels, lion-flanked driver's box,
raised archer's seat, swan-neck royal umbrella, standard, pole and yoke for four horses."""
import math

from mathutils import Vector

import parts as P
from hero_lib import (R, S, T, box, copy, extrude_poly, join, lathe, mirror_x, offset_outline, scroll, sphere,
                      tube, xform)

STYLES = {
    "arjuna": dict(main="MAT_Gold", trim="MAT_Gold", panel="MAT_Black", cloth="MAT_White", cushion="MAT_Red",
                   flag="MAT_Green", standard="ape", deck="MAT_GoldDark"),
    "bhishma": dict(main="MAT_White", trim="MAT_Silver", panel="MAT_Gold", cloth="MAT_White", cushion="MAT_Cream",
                    flag="MAT_White", standard="palmyra", deck="MAT_Silver"),
    "duryodhana": dict(main="MAT_Crimson", trim="MAT_Bronze", panel="MAT_Crimson", cloth="MAT_Red",
                       cushion="MAT_Black", flag="MAT_Crimson", standard="serpent", deck="MAT_Bronze"),
    "rank": dict(main="MAT_Gold", trim="MAT_GoldDark", panel="MAT_Red", cloth="MAT_Saffron", cushion="MAT_Red",
                 flag="MAT_Saffron", standard="flag", deck="MAT_Wood"),
    "rank_kaurava": dict(main="MAT_Bronze", trim="MAT_Bronze", panel="MAT_Crimson", cloth="MAT_Red", cushion="MAT_Black",
                         flag="MAT_Crimson", standard="flag", deck="MAT_Wood"),
}


def palmyra(mat="MAT_Gold", h=1.7):
    """Palmyra palm emblem with five stars (Bhishma's standard)."""
    parts = []
    trunk = [(0, 0, 0), (0.02, 0, h * 0.3), (-0.01, 0, h * 0.55), (0, 0, h * 0.72)]
    parts.append(tube(trunk, [0.06, 0.05, 0.045, 0.04], mat, segs=10, per=6))
    for i in range(9):                                  # trunk rings
        z = h * 0.72 * (i + 0.5) / 9
        parts.append(lathe([(0.045, z - 0.012), (0.066, z), (0.045, z + 0.012)], mat, 12))
    fan = []
    n = 13
    for k in range(n + 1):                              # serrated fan leaf outline in (y, z)
        a = math.radians(-70 + 140 * k / n)
        r = 0.42 if k % 2 == 0 else 0.34
        fan.append((r * math.sin(a), 0.08 + r * math.cos(a)))
    fan = [(0.03, 0.0)] + fan[::-1] + [(-0.03, 0.0)]
    for i in range(11):
        a = i / 11 * math.tau
        leaf = extrude_poly(fan, 0.012, mat)
        droop = 0.55 + 0.35 * (i % 2)
        xform(leaf, T(0, 0, h * 0.72) @ R(a, "Z") @ R(droop, "X") @ T(0, 0, 0.05) @ R(math.pi / 2, "Z"))
        parts.append(leaf)
    crown = extrude_poly(fan, 0.012, mat)
    xform(crown, T(0, 0, h * 0.74))
    parts.append(crown)
    parts.append(sphere(0.07, (0, 0, h * 0.72), mat, seg=12))
    star = []
    for k in range(10):
        a = k / 10 * math.tau
        r = 0.085 if k % 2 == 0 else 0.036
        star.append((r * math.sin(a), r * math.cos(a)))
    for k in range(5):                                  # five stars in an arc over the crown
        a = math.radians(-60 + 30 * k)
        st = extrude_poly(star, 0.02, mat)
        xform(st, T(0, 0.62 * math.sin(a), h * 0.72 + 0.62 * math.cos(a)))
        parts.append(st)
    o = join(parts, "palmyra")
    xform(o, R(math.pi / 2, "Z"))   # fan faces the side so it reads in profile and from the front quarter
    return o


def quiver(mat="MAT_Gold", arrows=9):
    parts = [lathe([(0.0, 0), (0.07, 0), (0.085, 0.05), (0.08, 0.55), (0.095, 0.58), (0.095, 0.62), (0.08, 0.62),
                    (0.08, 0.05), (0.0, 0.05)], mat, 14)]
    for z in (0.15, 0.40):
        parts.append(lathe([(0.082, z - 0.015), (0.095, z), (0.082, z + 0.015)], mat, 14))
    import random
    rng = random.Random(7)
    for i in range(arrows):
        a = i / arrows * math.tau
        x, y = 0.045 * math.cos(a), 0.045 * math.sin(a)
        top = (x * 1.6, y * 1.6, 0.86 + rng.uniform(-0.04, 0.04))
        parts.append(tube([(x, y, 0.1), top], 0.006, "MAT_Wood", segs=5, smooth=False))
        for k in range(3):                                  # fletching
            f = box((0.002, 0.03, 0.10), (0, 0, 0), "MAT_White")
            xform(f, T(top[0], top[1], top[2] - 0.07) @ R(k * math.tau / 3, "Z") @ T(0, 0.015, 0))
            parts.append(f)
    return join(parts, "quiver")


def side_panel(st):
    """Swept side wall of the archer's box, in (y, z); gold with an inlaid field and volutes."""
    out = [(-0.30, 1.02), (2.00, 1.02), (2.00, 1.95), (1.80, 2.02), (1.45, 1.86), (1.00, 1.62), (0.45, 1.50),
           (0.00, 1.56), (-0.25, 1.74), (-0.42, 1.70), (-0.40, 1.40)]
    parts = [extrude_poly(out, 0.07, st["main"], bevel=0.008)]
    parts.append(extrude_poly(offset_outline(out, 0.10), 0.082, "MAT_GoldDark" if st["main"] == "MAT_Gold" else st["trim"]))
    parts.append(extrude_poly(offset_outline(out, 0.20), 0.092, st["panel"]))
    rim = [(0, y, z) for y, z in out]
    parts.append(tube(rim, 0.022, st["trim"], segs=8, per=3, closed=True))
    parts.append(scroll((0.05, -0.30, 1.56), 0.15, 1.7, 0.03, st["trim"], "YZ", flip=1, start=1.2))
    parts.append(scroll((0.05, 1.82, 1.83), 0.13, 1.5, 0.028, st["trim"], "YZ", flip=-1, start=2.0))
    for y, z, r in ((0.55, 1.26, 0.085), (1.05, 1.30, 0.10), (1.55, 1.42, 0.115)):   # lotus bosses
        parts.append(lathe([(0.0, 0.05), (r * 0.4, 0.045), (r * 0.5, 0.02), (r, 0.015), (r, 0.0), (0, 0)], st["trim"], 16,
                           T(0.045, y, z) @ R(math.pi / 2, "Y")))
        for k in range(8):
            a = k / 8 * math.tau
            pt = sphere(1.0, (0, 0, 0), st["trim"], scale=(0.012, r * 0.30, r * 0.16), seg=8)
            xform(pt, T(0.052, y, z) @ R(a, "X") @ T(0, r * 0.68, 0))
            parts.append(pt)
    return parts


def build(style="arjuna", light=False, umbrella=True, standard=True, pole=True, as_parts=False):
    st = STYLES[style]
    main, trim = st["main"], st["trim"]
    parts = []
    wheels = []
    RW, FW = 0.95, 0.58                      # rear and front wheel radii
    RY, FY = 1.15, -1.15                     # axle positions
    RX, FX = 1.14, 1.02

    # --- running gear
    wm, wi = {"bhishma": ("MAT_Silver", "MAT_Gold"), "duryodhana": ("MAT_Bronze", "MAT_Black"),
              "rank_kaurava": ("MAT_Bronze", "MAT_Black")}.get(
        style, ("MAT_Gold", "MAT_Black"))
    rear = P.wheel(RW, 18, wm, wi, rim_inlays=22)
    front = P.wheel(FW, 12, wm, wi, width=0.10, rim_inlays=14)
    for w, x, y, r in ((rear, RX, RY, RW), (front, FX, FY, FW)):
        xform(w, T(x, y, r))
        wheels += [w] + mirror_x(w)
        parts.append(tube([(-x, y, r), (x, y, r)], 0.055, "MAT_Iron", segs=12, smooth=False))
    parts.append(tube([(0, FY, FW), (0, -0.2, 0.74), (0, RY, RW)], 0.06, "MAT_Wood", segs=10, per=6))  # perch
    for sx in (-1, 1):                       # sprung brackets from the axles up to the decks
        parts.append(tube([(sx * 0.70, RY, RW), (sx * 0.74, RY + 0.42, RW + 0.02), (sx * 0.74, RY + 0.50, 0.94),
                           (sx * 0.70, RY + 0.25, 1.00)], 0.03, trim, segs=8, per=5))
        parts.append(tube([(sx * 0.70, RY, RW), (sx * 0.74, RY - 0.50, RW - 0.06), (sx * 0.74, RY - 0.62, 0.92),
                           (sx * 0.70, RY - 0.35, 1.00)], 0.03, trim, segs=8, per=5))
        parts.append(tube([(sx * 0.60, FY, FW), (sx * 0.62, FY + 0.30, 0.64), (sx * 0.62, FY + 0.25, 0.78)], 0.028,
                          trim, segs=8, per=5))
        parts.append(tube([(sx * 0.60, FY, FW), (sx * 0.62, FY - 0.30, 0.64), (sx * 0.62, FY - 0.25, 0.78)], 0.028,
                          trim, segs=8, per=5))

    # --- decks: low driver's footboard in front, raised archer's deck behind
    parts.append(box((1.52, 1.70, 0.07), (0, -0.95, 0.80), st["deck"], bevel=0.012))
    parts.append(box((1.86, 2.40, 0.08), (0, 0.85, 1.02), st["deck"], bevel=0.012))
    parts.append(box((1.52, 0.06, 0.26), (0, -0.13, 0.92), main, bevel=0.01))           # riser between decks
    for sx in (-1, 1):                                                                    # deck edge mouldings
        parts.append(tube([(sx * 0.76, -1.80, 0.80), (sx * 0.76, -0.12, 0.80)], 0.03, trim, segs=8, smooth=False))
        parts.append(tube([(sx * 0.93, -0.35, 1.02), (sx * 0.93, 2.05, 1.02)], 0.034, trim, segs=8, smooth=False))
        if not light:
            parts += P.swag_row((sx * 0.95, -0.30, 0.985), (sx * 0.95, 2.02, 0.985), 16, trim)
            parts += P.swag_row((sx * 0.78, -1.78, 0.77), (sx * 0.78, -0.16, 0.77), 11, trim)
    parts.append(tube([(-0.93, 2.05, 1.02), (0.93, 2.05, 1.02)], 0.034, trim, segs=8, smooth=False))
    if not light:
        parts += P.swag_row((-0.90, 2.07, 0.985), (0.90, 2.07, 0.985), 12, trim)

    # --- driver's box: striding lions as the side walls, a bowed dash with a sun boss
    lion_mat = main if style in ("arjuna", "rank", "rank_kaurava") else trim
    lion = P.lion("striding", lion_mat, voxel=0.03 if light else 0.018)
    xform(lion, T(0.64, -0.78, 0.835) @ S(0.84))
    parts += [lion] + mirror_x(lion)
    dash = [(-0.40, -1.72, 0.84), (-0.25, -1.88, 0.84), (0.0, -1.94, 0.84), (0.25, -1.88, 0.84), (0.40, -1.72, 0.84)]
    for z, rr in ((0.84, 0.03), (1.10, 0.022), (1.36, 0.035)):
        parts.append(tube([(x, y, z) for x, y, _ in dash], rr, trim, segs=8, per=5))
    for i in range(len(dash) - 1):                                                        # dash skin
        a, b = Vector(dash[i]), Vector(dash[i + 1])
        mid = (a + b) / 2
        ang = math.atan2(b.y - a.y, b.x - a.x)
        pn = box(((b - a).length + 0.02, 0.03, 0.52), (mid.x, mid.y, 1.10), st["panel"], rot=R(ang, "Z"))
        parts.append(pn)
    parts.append(lathe([(0.0, 0.07), (0.07, 0.06), (0.10, 0.03), (0.20, 0.025), (0.22, 0.0), (0, 0)], trim, 24,
                       T(0, -1.95, 1.10) @ R(math.pi / 2, "X")))
    for k in range(16):                                                                   # sun rays on the boss
        a = k / 16 * math.tau
        ray = lathe([(0.02, 0), (0.0, 0.11)], trim, 6, T(0, -1.965, 1.10) @ R(a, "Y") @ T(0, 0, 0.20))
        parts.append(ray)
    # rein rail and whip socket
    parts.append(tube([(-0.36, -1.70, 1.36), (-0.36, -1.50, 1.52), (0.36, -1.50, 1.52), (0.36, -1.70, 1.36)], 0.02,
                      trim, segs=8, per=5))

    # --- archer's box: swept side panels, seat, tall back with lions
    sp = side_panel(st)
    xform(sp, T(0.90, 0, 0))
    parts += sp + mirror_x(sp)
    parts.append(box((1.50, 0.62, 0.34), (0, 1.50, 1.23), main, bevel=0.02))              # seat chest
    parts.append(box((1.40, 0.56, 0.10), (0, 1.50, 1.45), st["cushion"], bevel=0.04))     # cushion
    back = [(-0.92, 1.02), (0.92, 1.02), (0.92, 1.95), (0.70, 2.25), (0.35, 2.48), (0.0, 2.58), (-0.35, 2.48),
            (-0.70, 2.25), (-0.92, 1.95)]
    bk = extrude_poly(back, 0.08, main, bevel=0.01)
    xform(bk, T(0, 2.02, 0) @ R(math.pi / 2, "Z"))
    parts.append(bk)
    fld = extrude_poly(offset_outline(back, 0.14), 0.10, st["panel"])
    xform(fld, T(0, 2.02, 0) @ R(math.pi / 2, "Z"))
    parts.append(fld)
    parts.append(tube([(x, 2.02, z) for x, z in back], 0.03, trim, segs=8, per=3, closed=True))
    for side in (-1, 1):                                                                  # sunburst both faces
        parts.append(lathe([(0.0, 0.05), (0.10, 0.04), (0.14, 0.015), (0.26, 0.012), (0.28, 0), (0, 0)], trim, 24,
                           T(0, 2.02 + side * 0.05, 1.82) @ R(-side * math.pi / 2, "X")))
        for k in range(20):
            a = k / 20 * math.tau
            L = 0.16 if k % 2 == 0 else 0.10
            parts.append(lathe([(0.022, 0), (0.0, L)], trim, 6,
                               T(0, 2.02 + side * 0.058, 1.82) @ R(a, "Y") @ T(0, 0, 0.27)))
    seated = P.lion("seated", lion_mat, voxel=0.03 if light else 0.018)
    xform(seated, T(0.74, 1.74, 1.99) @ R(-0.30, "Z") @ S(0.60))
    for sx, src in ((1, [seated]), (-1, mirror_x(seated))):
        parts += src
        parts.append(lathe([(0.0, 0), (0.24, 0), (0.26, 0.03), (0.20, 0.06), (0.22, 0.10), (0.0, 0.10)], trim, 16,
                           T(sx * 0.74, 1.80, 1.90)))
    if not light:
        for sx in (-1, 1):
            q = quiver(trim)
            xform(q, T(sx * 0.70, 1.02, 1.06) @ R(sx * 0.18, "Y"))
            parts.append(q)

    if umbrella:
        # --- royal umbrella on a swan-neck arm
        neck = [(0, 2.06, 1.60), (0, 2.34, 2.25), (0, 2.26, 2.92), (0, 1.75, 3.22), (0, 1.15, 3.12), (0, 0.80, 3.06)]
        parts.append(tube(neck, [0.075, 0.07, 0.06, 0.05, 0.045, 0.045], trim, segs=12, per=8))
        parts.append(scroll((0, 2.42, 2.55), 0.16, 1.6, 0.03, trim, "YZ", flip=-1, start=3.3))
        parts.append(scroll((0, 1.62, 2.98), 0.14, 1.5, 0.026, trim, "YZ", flip=1, start=4.4))
        parts.append(lathe([(0.045, 3.02), (0.09, 3.06), (0.05, 3.10), (0.04, 3.38), (0.10, 3.42), (0.0, 3.43)], trim, 14,
                           T(0, 0.80, 0)))
        par = P.parasol(1.18, 16, st["cloth"], trim if style != "arjuna" else "MAT_Gold")
        xform(par, T(0, 0.80, 3.02))
        parts.append(par)

    if standard:
        # --- standard
        top = 3.02 + 0.42 + 0.50
        if st["standard"] in ("ape", "flag"):
            parts.append(tube([(0, 0.80, top - 0.05), (0, 0.80, top + 1.55)], 0.022, trim, segs=8, smooth=False))
            fl = P.flag(2.2, 1.15, st["flag"], emblem=None if light else ("ape" if st["standard"] == "ape" else "sun"),
                        border=not light, mark="MAT_Gold" if st["standard"] == "ape" else "MAT_Red")
            xform(fl, T(0, 0.80, top + 1.50))
            parts.append(fl)
            for z in (top + 1.50, top + 0.50):
                parts.append(lathe([(0.022, z - 0.03), (0.04, z), (0.022, z + 0.03)], trim, 10, T(0, 0.80, 0)))
            if st["standard"] == "ape":
                ap = P.ape(trim, voxel=0.02)
                xform(ap, T(0, 0.80, top + 1.60) @ S(0.55))
                parts.append(ap)
                parts.append(lathe([(0.0, 0), (0.16, 0), (0.18, 0.03), (0.10, 0.06), (0.0, 0.06)], trim, 14,
                                   T(0, 0.80, top + 1.55)))
            else:
                parts.append(lathe([(0.03, 0), (0.06, 0.05), (0.0, 0.18)], trim, 10, T(0, 0.80, top + 1.55)))
        else:
            py = 2.20                                                                        # mast behind the seat back
            parts.append(tube([(0.55, py, 1.02), (0.55, py, 5.2)], [0.05, 0.035], trim, segs=10, smooth=False))
            for z in (1.6, 2.6, 3.6, 4.6):
                parts.append(lathe([(0.04, z - 0.04), (0.07, z), (0.04, z + 0.04)], trim, 12, T(0.55, py, 0)))
            parts.append(lathe([(0.0, 0), (0.20, 0), (0.22, 0.04), (0.12, 0.08), (0.0, 0.08)], trim, 16, T(0.55, py, 5.2)))
            if st["standard"] == "palmyra":
                em = palmyra("MAT_Gold", 2.3)
            else:
                em = P.serpent("MAT_Gold", 1.9)
            xform(em, T(0.55, py, 5.28))
            parts.append(em)
            fl = P.flag(1.7, 0.9, st["flag"], emblem=None if light else "sun", border=not light, mark="MAT_Gold")
            xform(fl, T(0.55, py + 0.04, 5.05))
            parts.append(fl)

    if pole:
        # --- pole and yoke for four horses abreast
        pole = [(0, FY, FW + 0.04), (0, -2.1, 0.74), (0, -3.4, 0.98), (0, -4.75, 1.22)]
        parts.append(tube(pole, [0.06, 0.055, 0.05, 0.045], trim, segs=10, per=8))
        for y, z in ((-2.1, 0.74), (-2.9, 0.88), (-3.7, 1.04)):
            parts.append(lathe([(0.05, -0.03), (0.075, 0.0), (0.05, 0.03)], trim, 12, T(0, y, z) @ R(1.4, "X")))
        yoke = [(-1.55, -4.62, 1.30), (-1.125, -4.72, 1.42), (-0.75, -4.70, 1.30), (-0.375, -4.76, 1.42), (0, -4.75, 1.26),
                (0.375, -4.76, 1.42), (0.75, -4.70, 1.30), (1.125, -4.72, 1.42), (1.55, -4.62, 1.30)]
        parts.append(tube(yoke, 0.045, trim, segs=10, per=6))
        for x in (-1.55, 1.55):
            parts.append(scroll((x, -4.62, 1.36), 0.10, 1.3, 0.03, trim, "XZ", flip=1 if x > 0 else -1, start=-1.2))
        parts.append(lathe([(0.0, 0), (0.07, 0.02), (0.05, 0.10), (0.09, 0.16), (0.0, 0.30)], trim, 12, T(0, -4.75, 1.26)))
        for x in (-1.125, -0.375, 0.375, 1.125):                                             # neck collars
            arc = [(x + 0.24 * math.cos(a), -4.72, 1.34 - 0.36 * math.sin(a)) for a in
                   (math.radians(d) for d in range(0, 181, 20))]
            parts.append(tube(arc, 0.028, st["cushion"] if st["cushion"] != "MAT_Black" else "MAT_Crimson", segs=8, per=2))
    if as_parts:
        return wheels, parts
    return join(wheels + parts, f"chariot_{style}")

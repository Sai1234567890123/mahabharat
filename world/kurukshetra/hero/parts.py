"""Reusable sculpted parts: lion, ape, serpent, wheel, parasol, flags, bells."""
import math
import random

from mathutils import Vector

from hero_lib import (R, S, T, blob, box, copy, extrude_poly, join, lathe, mirror_x, offset_outline,
                      scroll, sphere, tube, xform)


# ------------------------------------------------------------ creatures
def lion(pose="striding", mat="MAT_Gold", voxel=0.018, roar=True):
    """Stylised temple lion facing -Y. striding: about 2.0 m long, 1.3 m tall. seated: 1.35 m tall."""
    P = []
    if pose == "striding":
        hx, hy, hz = 0.0, -0.86, 1.10          # head centre
        P += [("s", (0, 0.15, 0.74), (0.23, 0.62, 0.26)),      # barrel
              ("s", (0, -0.40, 0.80), (0.27, 0.34, 0.34)),     # chest
              ("s", (0, 0.64, 0.76), (0.24, 0.30, 0.28)),      # hips
              ("s", (0, -0.64, 0.99), (0.33, 0.30, 0.35))]     # mane mass
        # legs: left fore forward, right fore back, hind opposite
        for sx, fy, hy2 in ((-1, -0.78, 0.86), (1, -0.38, 0.50)):
            P += [("c", (sx * 0.19, -0.42, 0.62), (sx * 0.19, fy + 0.06, 0.30), 0.10, 0.075),
                  ("c", (sx * 0.19, fy + 0.06, 0.30), (sx * 0.19, fy, 0.08), 0.075, 0.07),
                  ("s", (sx * 0.19, fy - 0.07, 0.055), (0.095, 0.14, 0.06)),
                  ("s", (sx * 0.21, 0.62, 0.55), (0.13, 0.22, 0.28)),
                  ("c", (sx * 0.21, 0.72, 0.42), (sx * 0.21, hy2 + 0.10, 0.26), 0.09, 0.065),
                  ("c", (sx * 0.21, hy2 + 0.10, 0.26), (sx * 0.21, hy2, 0.08), 0.065, 0.06),
                  ("s", (sx * 0.21, hy2 - 0.07, 0.055), (0.09, 0.14, 0.06))]
        tail = [(0, 0.90, 0.80), (0, 1.12, 0.95), (0, 1.16, 1.25), (0, 0.98, 1.45), (0, 0.80, 1.38)]
    else:  # seated
        hx, hy, hz = 0.0, -0.40, 1.12
        P += [("s", (0, 0.32, 0.40), (0.31, 0.42, 0.38)),      # haunches
              ("s", (0, -0.08, 0.66), (0.27, 0.30, 0.42)),     # chest, upright
              ("s", (0, -0.20, 1.00), (0.33, 0.30, 0.34))]     # mane
        for sx in (-1, 1):
            P += [("c", (sx * 0.17, -0.22, 0.60), (sx * 0.17, -0.34, 0.10), 0.095, 0.07),
                  ("s", (sx * 0.17, -0.42, 0.055), (0.095, 0.14, 0.06)),
                  ("s", (sx * 0.28, 0.26, 0.26), (0.14, 0.30, 0.25)),
                  ("s", (sx * 0.28, -0.04, 0.055), (0.09, 0.17, 0.06))]
        tail = [(0, 0.70, 0.22), (0.15, 0.90, 0.30), (0.30, 0.80, 0.55), (0.28, 0.60, 0.75), (0.2, 0.5, 0.7)]
    # head: broad skull, square muzzle, angry brows, snarling cheeks
    P += [("s", (hx, hy, hz), (0.20, 0.21, 0.19)),
          ("s", (hx, hy - 0.19, hz - 0.035), (0.125, 0.15, 0.095)),         # muzzle
          ("s", (hx - 0.07, hy - 0.27, hz - 0.05), (0.07, 0.07, 0.065)),    # whisker pads
          ("s", (hx + 0.07, hy - 0.27, hz - 0.05), (0.07, 0.07, 0.065)),
          ("s", (hx, hy - 0.33, hz + 0.005), (0.06, 0.04, 0.045)),          # nose
          ("s", (hx, hy - 0.20, hz + 0.045), (0.05, 0.14, 0.04)),           # nose bridge
          ("s", (hx - 0.09, hy - 0.13, hz + 0.105), (0.085, 0.07, 0.035), R(-0.45, "Y")),  # brows, angled in
          ("s", (hx + 0.09, hy - 0.13, hz + 0.105), (0.085, 0.07, 0.035), R(0.45, "Y")),
          ("s", (hx - 0.14, hy - 0.08, hz - 0.02), (0.07, 0.09, 0.08)),     # cheeks
          ("s", (hx + 0.14, hy - 0.08, hz - 0.02), (0.07, 0.09, 0.08)),
          ("s", (hx - 0.16, hy + 0.03, hz + 0.19), (0.065, 0.04, 0.075)),   # ears
          ("s", (hx + 0.16, hy + 0.03, hz + 0.19), (0.065, 0.04, 0.075))]
    if roar:
        P.append(("s", (hx, hy - 0.16, hz - 0.20), (0.10, 0.14, 0.045), R(0.55, "X")))  # dropped jaw
        P.append(("s", (hx, hy - 0.27, hz - 0.265), (0.07, 0.05, 0.04)))                 # chin
    else:
        P.append(("s", (hx, hy - 0.17, hz - 0.11), (0.095, 0.12, 0.05)))
    # mane: three rings of pointed flame locks swept back from the face
    for ring, (rr, back, ln, th) in enumerate(((0.21, 0.00, 0.13, 0.062), (0.27, 0.13, 0.15, 0.07),
                                               (0.30, 0.28, 0.15, 0.07))):
        n = 11 + ring * 2
        for i in range(n):
            a = i / n * math.tau + ring * 0.28
            if math.sin(a) < -0.80 and ring == 0:
                continue
            c, sn = math.cos(a), math.sin(a)
            p0 = (hx + rr * c, hy + back, hz - 0.02 + rr * sn)
            p1 = (hx + (rr + ln) * c, hy + back + 0.16, hz - 0.02 + (rr + ln) * sn - 0.05)
            P.append(("c", p0, p1, th, 0.026))
    P.append(("t", tail, [0.05, 0.045, 0.04, 0.035, 0.03]))
    P.append(("s", tail[-1], (0.07, 0.10, 0.07)))
    body = blob(P, voxel=voxel, smooth=3, mat=mat)
    extras = []
    # eyes, fangs and tongue read at hero distance
    for sx in (-1, 1):
        extras.append(sphere(0.03, (hx + sx * 0.085, hy - 0.185, hz + 0.05), "MAT_Black", scale=(1, 0.7, 0.75), seg=10))
        if roar:
            extras.append(lathe([(0.017, 0), (0.0, -0.075)], "MAT_White", 8, T(hx + sx * 0.06, hy - 0.30, hz - 0.085)))
            extras.append(lathe([(0.014, 0), (0.0, 0.055)], "MAT_White", 8, T(hx + sx * 0.055, hy - 0.25, hz - 0.235)))
    if roar:
        extras.append(sphere(1.0, (hx, hy - 0.20, hz - 0.165), "MAT_Red", scale=(0.055, 0.10, 0.02), seg=10, rot=R(0.5, "X")))
    return join([body] + extras, "lion")


def ape(mat="MAT_Gold", voxel=0.014):
    """Crouching, roaring ape (Hanuman emblem) for the banner top; about 0.9 m tall, faces -Y."""
    P = [("s", (0, 0.05, 0.42), (0.21, 0.20, 0.27)),       # torso
         ("s", (0, 0.00, 0.62), (0.24, 0.19, 0.17)),       # shoulders
         ("s", (0, 0.08, 0.22), (0.20, 0.20, 0.17)),       # hips
         ("s", (0, -0.07, 0.83), (0.135, 0.14, 0.14)),     # head
         ("s", (0, -0.19, 0.79), (0.085, 0.09, 0.075)),    # muzzle
         ("s", (0, -0.19, 0.715), (0.07, 0.08, 0.03), R(0.5, "X")),  # open jaw
         ("s", (0, -0.04, 0.955), (0.07, 0.07, 0.05)),     # crown bump
         ("s", (-0.13, -0.04, 0.85), (0.03, 0.02, 0.045)),
         ("s", (0.13, -0.04, 0.85), (0.03, 0.02, 0.045))]
    for sx in (-1, 1):
        P += [("c", (sx * 0.22, -0.02, 0.63), (sx * 0.34, -0.12, 0.40), 0.075, 0.06),   # upper arm
              ("c", (sx * 0.34, -0.12, 0.40), (sx * 0.24, -0.26, 0.20), 0.06, 0.05),    # forearm
              ("s", (sx * 0.24, -0.29, 0.17), (0.06, 0.07, 0.05)),                      # fist on knee
              ("c", (sx * 0.15, 0.06, 0.22), (sx * 0.27, -0.20, 0.26), 0.095, 0.075),   # thigh
              ("c", (sx * 0.27, -0.20, 0.26), (sx * 0.24, -0.12, 0.05), 0.07, 0.055),   # shin
              ("s", (sx * 0.24, -0.20, 0.035), (0.06, 0.12, 0.04))]                     # foot
    tail = [(0, 0.22, 0.15), (0, 0.42, 0.25), (0, 0.50, 0.55), (0, 0.42, 0.85), (0, 0.28, 1.02), (0, 0.16, 0.98)]
    P.append(("t", tail, [0.045, 0.04, 0.036, 0.032, 0.028, 0.03]))
    body = blob(P, voxel=voxel, smooth=4, mat=mat)
    eyes = [sphere(0.016, (sx * 0.055, -0.185, 0.865), "MAT_Black", seg=8) for sx in (-1, 1)]
    mace = [tube([(0.24, -0.29, 0.17), (0.36, -0.36, 0.95)], 0.02, mat, segs=8, smooth=False),
            sphere(0.085, (0.375, -0.37, 1.02), mat, scale=(1, 1, 1.15), seg=14)]
    return join([body] + eyes + mace, "ape")


def serpent(mat="MAT_Gold", height=1.3):
    """Coiled, hooded cobra (Duryodhana's emblem), rising on its coils; faces -Y."""
    pts, rad = [], []
    for i in range(40):  # three stacked coils
        t = i / 39
        a = t * 3 * math.tau
        r = 0.26 - 0.10 * t
        pts.append((r * math.cos(a), r * math.sin(a), 0.06 + 0.26 * t))
        rad.append(0.062 - 0.012 * t)
    neck = [(0.0, 0.10, 0.42), (0.0, 0.14, 0.62), (0.0, 0.06, 0.82), (0.0, -0.06, 0.98), (0.0, -0.16, 1.05)]
    pts += neck
    rad += [0.05, 0.048, 0.046, 0.044, 0.04]
    body = tube(pts, rad, mat, segs=12, per=3)
    hood = sphere(1.0, (0, 0.02, 0.86), mat, scale=(0.20, 0.035, 0.24), seg=20, rot=R(-0.35, "X"))
    head = sphere(1.0, (0, -0.20, 1.06), mat, scale=(0.06, 0.10, 0.045), seg=14)
    eyes = [sphere(0.012, (sx * 0.04, -0.25, 1.08), "MAT_Red", seg=8) for sx in (-1, 1)]
    tongue = tube([(0, -0.29, 1.05), (0, -0.36, 1.04)], 0.006, "MAT_Red", segs=5, smooth=False)
    o = join([body, hood, head, tongue] + eyes, "serpent")
    xform(o, S(height / 1.3))
    return o


# ------------------------------------------------------------ wheel
def wheel(radius=0.95, spokes=16, mat="MAT_Gold", inlay="MAT_Black", width=0.11, rim_inlays=20):
    """Ornate spoked wheel lying in the YZ plane, axle along X, centred on the origin."""
    R0 = radius
    rw = 0.17 * R0           # rim depth, radial
    parts = []
    w2 = width / 2
    # rim: stepped profile with tyre band; lathe is built around Z, then turned so the axle is X
    prof = [(R0 - rw, -w2 * 0.8), (R0 - rw, w2 * 0.8), (R0 - rw * 0.75, w2), (R0 - 0.02, w2),
            (R0, w2 * 0.75), (R0, -w2 * 0.75), (R0 - 0.02, -w2), (R0 - rw * 0.75, -w2), (R0 - rw, -w2 * 0.8)]
    parts.append(lathe(prof, mat, 64))
    parts.append(lathe([(R0 + 0.012, -w2 * 0.5), (R0 + 0.012, w2 * 0.5), (R0 - 0.005, w2 * 0.55),
                        (R0 - 0.005, -w2 * 0.55), (R0 + 0.012, -w2 * 0.5)], "MAT_Iron", 64))  # iron tyre
    # black inlay plates on both faces
    rm = R0 - rw * 0.47
    for i in range(rim_inlays):
        a = (i + 0.5) / rim_inlays * math.tau
        arc = math.tau / rim_inlays * rm * 0.72
        for side in (-1, 1):
            p = box((arc, rw * 0.50, 0.012), (0, 0, 0), inlay, bevel=0.003)
            xform(p, R(a, "Z") @ T(0, rm, side * (w2 + 0.002)) )
            parts.append(p)
    # bead rings
    for rr in (R0 - rw * 0.80, R0 - rw * 0.13):
        for side in (-1, 1):
            parts.append(lathe([(rr - 0.012, 0), (rr, 0.012), (rr + 0.012, 0), (rr, -0.012), (rr - 0.012, 0)],
                               mat, 64, T(0, 0, side * w2)))
    # turned spokes
    hub_r = 0.17 * R0
    L = R0 - rw - hub_r
    sp_prof = [(0.020, 0), (0.030, 0.06 * L), (0.022, 0.12 * L), (0.022, 0.38 * L), (0.040, 0.47 * L),
               (0.046, 0.52 * L), (0.040, 0.57 * L), (0.020, 0.66 * L), (0.018, 0.88 * L), (0.032, 0.95 * L),
               (0.032, L + 0.01)]
    for i in range(spokes):
        a = i / spokes * math.tau
        s = lathe(sp_prof, mat, 10)
        xform(s, R(a, "Z") @ T(0, hub_r, 0) @ R(-math.pi / 2, "X"))
        parts.append(s)
    # mid ring that ties the spokes
    rmid = hub_r + 0.52 * L
    parts.append(lathe([(rmid - 0.022, -0.016), (rmid - 0.022, 0.016), (rmid + 0.022, 0.016),
                        (rmid + 0.022, -0.016), (rmid - 0.022, -0.016)], mat, 48))
    # hub with lotus boss on the outer (+Z before turning -> +X) face
    hub = [(0.0, -w2 * 1.4), (hub_r * 0.75, -w2 * 1.4), (hub_r, -w2 * 0.9), (hub_r, w2 * 0.9),
           (hub_r * 0.92, w2 * 1.5), (hub_r * 0.62, w2 * 1.9), (hub_r * 0.62, w2 * 2.5), (hub_r * 0.36, w2 * 3.0),
           (hub_r * 0.30, w2 * 3.6), (hub_r * 0.18, w2 * 4.0), (0.0, w2 * 4.1)]
    parts.append(lathe(hub, mat, 32))
    for i in range(12):
        a = i / 12 * math.tau
        petal = sphere(1.0, (0, 0, 0), mat, scale=(0.028, 0.055, 0.016), seg=10)
        xform(petal, R(a, "Z") @ T(0, hub_r * 0.62, w2 * 1.75) @ R(0.5, "X"))
        parts.append(petal)
    parts.append(lathe([(0.0, 0), (hub_r * 0.3, 0), (hub_r * 0.3, 0.012), (0, 0.012)], inlay, 16, T(0, 0, w2 * 1.95)))
    w = join(parts, "wheel")
    xform(w, R(math.pi / 2, "Y"))   # axle along X, outer face +X
    return w


# ------------------------------------------------------------ parasol and flags
def parasol(radius=1.15, ribs=16, cloth="MAT_White", mat="MAT_Gold", rise=0.42):
    """Royal umbrella (chhatra), apex at z=rise, rim at z=0, centred on Z."""
    parts = []
    n = 14
    dome = [(radius * math.sin(t / n * math.pi / 2) ** 0.9, rise * math.cos(t / n * math.pi / 2) ** 1.4)
            for t in range(n + 1)]
    under = [(r * 0.985, z - 0.02) for r, z in reversed(dome)]
    parts.append(lathe(dome + under, cloth, ribs * 3))
    for i in range(ribs):                         # gold ribs over the cloth
        a = i / ribs * math.tau
        pts = [(r * math.cos(a), r * math.sin(a), z + 0.006) for r, z in dome]
        parts.append(tube(pts, 0.014, mat, segs=6, per=1, smooth=False))
        parts.append(sphere(0.03, (radius * math.cos(a), radius * math.sin(a), 0.0), mat, seg=8))
    # valance: deep gold band, bead rows, scalloped pendants and a leaf crest
    parts.append(lathe([(radius, 0.03), (radius + 0.025, 0.02), (radius + 0.03, -0.10), (radius + 0.012, -0.13),
                        (radius - 0.01, -0.12), (radius - 0.012, 0.0), (radius, 0.03)], mat, ribs * 4))
    for z in (0.035, -0.045, -0.125):
        parts.append(lathe([(radius + 0.018, z - 0.012), (radius + 0.034, z), (radius + 0.018, z + 0.012)],
                           mat, ribs * 4))
    for i in range(ribs * 2):
        a = (i + 0.5) / (ribs * 2) * math.tau
        c, s = math.cos(a), math.sin(a)
        parts.append(lathe([(0.0, 0.0), (0.03, -0.035), (0.022, -0.075), (0.0, -0.12)], mat, 8,
                           T((radius + 0.01) * c, (radius + 0.01) * s, -0.12)))
        leaf = sphere(1.0, (0, 0, 0), mat, scale=(0.05, 0.012, 0.075), seg=8)
        xform(leaf, T((radius + 0.015) * c, (radius + 0.015) * s, 0.085) @ R(a + math.pi / 2, "Z") @ R(0.25, "X"))
        parts.append(leaf)
    # finial: stacked kalash
    parts.append(lathe([(0.0, rise - 0.01), (0.13, rise), (0.15, rise + 0.03), (0.07, rise + 0.07), (0.05, rise + 0.10),
                        (0.10, rise + 0.15), (0.11, rise + 0.19), (0.05, rise + 0.25), (0.03, rise + 0.29),
                        (0.06, rise + 0.33), (0.045, rise + 0.38), (0.012, rise + 0.44), (0.0, rise + 0.50)], mat, 20))
    return join(parts, "parasol")


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy + 1e-9)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _emblem_mask(shape, x, y):
    """True where the emblem covers (x, y); unit square about the origin, y up."""
    if shape == "sun":
        r, a = math.hypot(x, y), math.atan2(y, x)
        return r < 0.42 or (0.52 < r < 0.98 and abs(((a / math.tau * 12) % 1) - 0.5) < 0.5 * (1.05 - r))
    if shape == "ape":                                   # leaping ape, mace raised, tail curled
        if (x / 0.30) ** 2 + ((y + 0.08) / 0.40) ** 2 < 1 or math.hypot(x - 0.06, y - 0.50) < 0.21:
            return True
        if math.hypot(x + 0.62, y - 0.92) < 0.15:        # mace head
            return True
        limbs = [((-0.18, 0.22), (-0.50, 0.50)), ((-0.50, 0.50), (-0.60, 0.88)),          # raised arm and mace
                 ((0.18, 0.20), (0.55, 0.30)), ((0.55, 0.30), (0.72, 0.05)),              # forward arm
                 ((-0.12, -0.40), (-0.42, -0.62)), ((-0.42, -0.62), (-0.30, -0.98)),      # legs
                 ((0.14, -0.40), (0.48, -0.55)), ((0.48, -0.55), (0.66, -0.92)),
                 ((-0.26, -0.30), (-0.74, -0.34)), ((-0.74, -0.34), (-0.98, -0.02)),      # tail
                 ((-0.98, -0.02), (-0.90, 0.30))]
        return any(_seg_dist(x, y, *p, *q) < 0.085 for p, q in limbs)
    return False


def flag(w=1.5, h=0.9, cloth="MAT_Green", emblem=None, swallow=True, wave=0.12, border=False, mark="MAT_Gold"):
    """War pennant built in the YZ plane, hoist at y=0 flying toward +Y, top edge at z=0.

    emblem: None, "sun" or "ape": drawn into the cloth as faces of the `mark` material, so it follows the wave.
    border: a band of `mark` along the top, bottom and hoist edges."""
    import bmesh
    from hero_lib import M, apply_modifiers, obj_from_bm
    nx, nz = (176, 88) if emblem else (28, 12)
    bm = bmesh.new()
    grid = []
    for j in range(nz + 1):
        row = []
        for i in range(nx + 1):
            u, v = i / nx, j / nz
            y = w * u
            if swallow:  # swallow-tail: the fly end is notched
                y = w * u * (1 - 0.30 * (1 - abs(2 * v - 1)) * u)
            z = -h * v + 0.10 * math.sin(u * 5.0) * u - 0.18 * u * u * w * 0.3
            x = wave * math.sin(u * 7.5 + v * 1.3) * u + 0.04 * math.sin(u * 17 + v * 4) * u
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    unit = 0.37 * h
    for j in range(nz):
        for i in range(nx):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            u, v = (i + 0.5) / nx, (j + 0.5) / nz
            on = border and (v < 0.075 or v > 0.925 or u * w < 0.075 * h)
            if emblem and not on:
                on = _emblem_mask(emblem, (u * w - 0.40 * w) / unit, (0.5 - v) * h / unit)
            f.material_index = 1 if on else 0
    o = obj_from_bm(bm, cloth)
    o.data.materials.append(M(mark))
    sol = o.modifiers.new("t", "SOLIDIFY")
    sol.thickness = 0.012
    sol.offset = 0
    apply_modifiers(o)
    return o


def bell(mat="MAT_Gold", s=1.0):
    return lathe([(0.0, 0.0), (0.012 * s, -0.005 * s), (0.016 * s, -0.03 * s), (0.03 * s, -0.06 * s),
                  (0.034 * s, -0.075 * s), (0.0, -0.07 * s)], mat, 10)


def swag_row(p0, p1, n, mat="MAT_Gold", drop=0.06, bells=True):
    """Garland of beads with bells between two points."""
    p0, p1 = Vector(p0), Vector(p1)
    parts = []
    for i in range(n):
        a = p0.lerp(p1, i / n)
        b = p0.lerp(p1, (i + 1) / n)
        mid = (a + b) / 2 - Vector((0, 0, drop))
        parts.append(tube([a, mid, b], 0.008, mat, segs=5, per=4))
        if bells:
            bl = bell(mat)
            xform(bl, T(*mid))
            parts.append(bl)
    return parts

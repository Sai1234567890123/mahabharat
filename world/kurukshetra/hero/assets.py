"""Battle assets besides the hero chariots: ape banner, soldiers, war tent, drum cart, wreck, rank chariot."""
import math
import random

import bmesh
from mathutils import Vector

import chariot as C
import parts as P
from hero_lib import (R, S, T, apply_modifiers, blob, box, copy, decimated, extrude_poly, join, lathe, mirror_x,
                      obj_from_bm, scroll, sphere, tube, xform)


# ------------------------------------------------------------ K01 ape banner
def gonfalon(w=1.5, h=3.2, cloth="MAT_Saffron", trim="MAT_Gold"):
    """Hanging war banner in the XZ plane, top edge at z=0, centred on x; swallow-tailed foot."""
    nx, nz = 14, 26
    bm = bmesh.new()
    grid = []
    for j in range(nz + 1):
        row = []
        for i in range(nx + 1):
            u, v = i / nx, j / nz
            foot = 0.28 * h * (1 - abs(2 * u - 1)) if v > 0.999 else 0.0
            z = -h * v + (0.28 * h * (1 - abs(2 * u - 1)) * max(0, (v - 0.8) / 0.2))
            y = 0.07 * math.sin(v * 9 + u * 2.0) * v + 0.05 * math.sin(u * 6.0) * v
            row.append(bm.verts.new(((u - 0.5) * w, y, z)))
        grid.append(row)
    for j in range(nz):
        for i in range(nx):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            border = i in (0, nx - 1) or j in (0, 1) or j >= nz - 2
            f.material_index = 1 if border else 0
    o = obj_from_bm(bm, cloth)
    from hero_lib import M
    o.data.materials.append(M(trim))
    sol = o.modifiers.new("t", "SOLIDIFY")
    sol.thickness = 0.014
    sol.offset = 0
    apply_modifiers(o)
    return o


def ape_banner(cloth="MAT_Saffron"):
    parts = []
    H = 9.0
    parts.append(lathe([(0.0, 0), (0.55, 0), (0.55, 0.10), (0.42, 0.14), (0.42, 0.24), (0.30, 0.30), (0.24, 0.48),
                        (0.16, 0.56), (0.12, 0.70), (0.0, 0.70)], "MAT_Gold", 24))
    parts.append(tube([(0, 0, 0.6), (0, 0, H)], [0.085, 0.055], "MAT_Gold", segs=14, smooth=False))
    for z in (1.4, 2.6, 3.8, 5.0, 6.2, 7.4):
        parts.append(lathe([(0.06, z - 0.07), (0.11, z - 0.03), (0.12, z), (0.11, z + 0.03), (0.06, z + 0.07)],
                           "MAT_Gold", 16))
    # lotus capital and the ape
    parts.append(lathe([(0.05, H - 0.2), (0.14, H - 0.12), (0.34, H - 0.02), (0.40, H + 0.05), (0.36, H + 0.10),
                        (0.0, H + 0.10)], "MAT_Gold", 24))
    for k in range(14):
        a = k / 14 * math.tau
        pt = sphere(1.0, (0, 0, 0), "MAT_Gold", scale=(0.07, 0.15, 0.03), seg=8)
        xform(pt, T(0, 0, H - 0.02) @ R(a, "Z") @ T(0, 0.30, 0) @ R(-0.5, "X"))
        parts.append(pt)
    ap = P.ape("MAT_Gold", voxel=0.016)
    xform(ap, T(0, 0, H + 0.10) @ S(1.35))
    parts.append(ap)
    # cross-yard with the hanging banner, streamers and bells
    yz = H - 0.75
    parts.append(tube([(-1.0, 0, yz), (1.0, 0, yz)], 0.035, "MAT_Gold", segs=10, smooth=False))
    for sx in (-1, 1):
        parts.append(lathe([(0.035, 0), (0.07, 0.04), (0.03, 0.10), (0.0, 0.20)], "MAT_Gold", 10,
                           T(sx * 1.0, 0, yz) @ R(sx * math.pi / 2, "Y")))
        parts.append(tube([(sx * 0.95, 0, yz), (sx * 0.5, 0, H - 0.25), (0, 0, H - 0.15)], 0.012, "MAT_Gold", segs=6))
        st = P.flag(2.6, 0.22, cloth, swallow=False, wave=0.25)                      # long streamers
        xform(st, T(sx * 0.98, 0.03, yz - 0.05))
        parts.append(st)
    g = gonfalon(1.7, 3.4, cloth)
    xform(g, T(0, -0.04, yz - 0.04))
    parts.append(g)
    for i in range(9):
        x = -0.8 + i * 0.2
        bl = P.bell("MAT_Gold", 1.6)
        xform(bl, T(x, -0.04, yz - 0.05))
        parts.append(bl)
    return join(parts, "ape_banner")


# ------------------------------------------------------------ soldiers
def soldier(side="kaurava", pose="attention", seed=0, legs="stand"):
    """Low-poly foot soldier, about 1.75 m, facing -Y. Skin, cloth and armour are separate fused shells."""
    kau = side == "kaurava"
    cloth, armour, trimc = ("MAT_Crimson", "MAT_Bronze", "MAT_Bronze") if kau else ("MAT_Saffron", "MAT_Gold", "MAT_Gold")
    stride = {"attention": 0.0, "advance": 0.22}[pose]
    lf, rf = -stride, stride                                # left foot forward when advancing
    skin = [("s", (0, 0, 1.63), (0.095, 0.105, 0.12)),      # head
            ("c", (0, 0, 1.50), (0, 0, 1.55), 0.055, 0.05)]  # neck
    # arms: right holds the weapon upright (or level), left carries shield or bow
    if kau:
        r_el, r_hand = (0.27, -0.02, 1.16), (0.30, -0.20, 1.08)
        if pose == "advance":
            r_el, r_hand = (0.28, 0.05, 1.20), (0.26, -0.22, 1.12)
        l_el, l_hand = (-0.27, -0.06, 1.18), (-0.20, -0.26, 1.16)
    else:
        l_el, l_hand = (-0.26, -0.10, 1.22), (-0.24, -0.38, 1.30)
        r_el, r_hand = (0.27, 0.0, 1.16), (0.26, -0.10, 0.90)
        if pose == "advance":                               # drawing the bow
            l_el, l_hand = (-0.30, -0.30, 1.42), (-0.22, -0.60, 1.45)
            r_el, r_hand = (0.30, 0.10, 1.40), (0.10, -0.10, 1.46)
    for sh, el, hand in (((0.20, 0, 1.44), r_el, r_hand), ((-0.20, 0, 1.44), l_el, l_hand)):
        skin += [("c", sh, el, 0.066, 0.055), ("c", el, hand, 0.054, 0.042), ("s", hand, (0.045, 0.055, 0.05))]
    ride = legs == "ride"                                   # astride a horse: knees out and forward
    knee = {sx: (sx * 0.31, -0.20, 0.66) if ride else (sx * 0.10, fy * 0.5, 0.50) for sx, fy in ((-1, lf), (1, rf))}
    foot = {sx: (sx * 0.33, -0.12, 0.26) if ride else (sx * 0.10, fy, 0.09) for sx, fy in ((-1, lf), (1, rf))}
    for sx in (-1, 1):                                      # shins and feet
        skin += [("c", knee[sx], foot[sx], 0.072, 0.05),
                 ("s", (foot[sx][0], foot[sx][1] - 0.06, foot[sx][2] - 0.05), (0.05, 0.11, 0.04))]
    body = blob(skin, voxel=0.022, smooth=2, mat="MAT_Skin")
    low = [("s", (0, 0, 0.95), (0.19, 0.14, 0.16))]         # dhoti: hips and thighs
    for sx in (-1, 1):
        low.append(("c", (sx * 0.10, 0, 0.90), knee[sx], 0.095, 0.075))
    low.append(("s", (0, -0.10, 0.80), (0.07, 0.03, 0.22)))  # front sash fall
    legs = blob(low, voxel=0.024, smooth=2, mat=cloth)
    top = [("s", (0, 0, 1.30), (0.19, 0.13, 0.20)), ("s", (0, 0, 1.12), (0.165, 0.12, 0.14)),
           ("s", (-0.20, 0, 1.44), (0.085, 0.075, 0.07)), ("s", (0.20, 0, 1.44), (0.085, 0.075, 0.07))]
    cuirass = blob(top, voxel=0.024, smooth=2, mat=armour)
    parts = [decimated(body, 0.16), decimated(legs, 0.14), decimated(cuirass, 0.14)]
    parts.append(lathe([(0.20, 1.01), (0.21, 1.06), (0.19, 1.09)], trimc if kau else "MAT_Red", 10))       # belt
    # face: eyes, nose, moustache and hair, so the head does not read as a blank egg
    for sx in (-1, 1):
        parts.append(sphere(0.014, (sx * 0.036, -0.093, 1.655), "MAT_Black", scale=(1.3, 0.6, 0.8), seg=6))
        parts.append(box((0.045, 0.012, 0.010), (sx * 0.036, -0.096, 1.682), "MAT_Black", rot=R(sx * -0.25, "Y")))
        parts.append(tube([(0, -0.104, 1.588), (sx * 0.035, -0.100, 1.582), (sx * 0.062, -0.086, 1.600)],
                          [0.012, 0.011, 0.004], "MAT_Black", segs=4, per=2))
    parts.append(sphere(0.02, (0, -0.108, 1.622), "MAT_Skin", scale=(0.9, 1.0, 1.7), seg=6))
    parts.append(sphere(0.10, (0, 0.03, 1.62), "MAT_Black", scale=(0.97, 0.95, 1.05), seg=8))               # hair
    for sx in (-1, 1):                                                                                      # arm bands
        parts.append(lathe([(0.066, -0.02), (0.074, 0.0), (0.066, 0.02)], trimc, 8, T(sx * 0.215, 0, 1.33)))
    if kau and not ride:                                                                                    # armour skirt
        parts.append(lathe([(0.20, 1.02), (0.235, 0.86), (0.245, 0.80), (0.225, 0.80), (0.19, 1.0)], armour, 12, S(1, 0.78, 1)))
        for k in range(12):
            a = k / 12 * math.tau
            parts.append(box((0.07, 0.012, 0.16), (0.243 * math.cos(a), 0.19 * math.sin(a), 0.76), "MAT_Crimson",
                             rot=R(a + math.pi / 2, "Z")))
    else:                                                                                                   # chest sash
        parts.append(tube([(-0.19, -0.06, 1.44), (-0.05, -0.145, 1.30), (0.12, -0.13, 1.12), (0.19, -0.03, 1.07)],
                          0.028, "MAT_Red", segs=5, per=3))
        parts.append(tube([(-0.19, 0.06, 1.44), (-0.03, 0.14, 1.28), (0.14, 0.12, 1.12), (0.19, 0.03, 1.07)],
                          0.028, "MAT_Red", segs=5, per=3))
    # helmet with plume (Kaurava) or crown-helmet (Pandava)
    if kau:
        parts.append(lathe([(0.112, 1.63), (0.115, 1.70), (0.09, 1.77), (0.04, 1.81), (0.0, 1.86)], armour, 10))
        parts.append(tube([(0, 0.0, 1.85), (0, 0.06, 1.95), (0, 0.16, 1.92)], [0.03, 0.035, 0.012], "MAT_Red",
                          segs=5, per=3))
        parts.append(box((0.02, 0.03, 0.10), (0, -0.112, 1.63), armour))                                  # nasal
    else:
        parts.append(lathe([(0.108, 1.66), (0.112, 1.72), (0.085, 1.78), (0.05, 1.83), (0.035, 1.90), (0.0, 1.94)],
                           armour, 10))
    # weapons
    if kau:
        if pose == "attention":
            a, b = Vector((0.30, -0.20, 0.02)), Vector((0.30, -0.20, 2.75))
        else:
            a, b = Vector((0.26, 0.55, 0.95)), Vector((0.26, -1.55, 1.25))
        parts.append(tube([a, b], 0.016, "MAT_Wood", segs=5, smooth=False))
        tip = lathe([(0.016, 0), (0.04, 0.05), (0.0, 0.28)], "MAT_Iron", 6)
        d = (b - a).normalized()
        xform(tip, T(*b) @ Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4())
        parts.append(tip)
        sh = lathe([(0.0, 0.07), (0.07, 0.065), (0.10, 0.03), (0.30, 0.0), (0.33, -0.02), (0.0, -0.02)], armour, 14)
        xform(sh, T(-0.24, -0.33, 1.16) @ R(math.pi / 2, "X") @ R(0.25, "Y"))
        parts.append(sh)
        parts.append(tube([(0.12, 0.10, 1.02), (0.16, 0.14, 0.50)], [0.03, 0.015], "MAT_Iron", segs=5, smooth=False))  # sword
    else:
        c = Vector(l_hand)
        bow = [c + Vector((0, 0.10, 0.80)), c + Vector((0, -0.04, 0.45)), c, c + Vector((0, -0.04, -0.45)),
               c + Vector((0, 0.10, -0.80))]
        parts.append(tube(bow, [0.010, 0.018, 0.022, 0.018, 0.010], "MAT_Wood", segs=5, per=4))
        string_mid = c + Vector((0, 0.10, 0)) if pose == "attention" else Vector(r_hand)
        parts.append(tube([bow[0], string_mid, bow[-1]], 0.004, "MAT_White", segs=3, smooth=False))
        if pose == "advance":
            parts.append(tube([Vector(r_hand), c + Vector((0, -0.25, 0))], 0.006, "MAT_Wood", segs=4, smooth=False))
        q = lathe([(0.0, 0), (0.05, 0), (0.06, 0.5), (0.0, 0.5)], "MAT_Red", 8)
        xform(q, T(0.06, 0.15, 1.10) @ R(0.35, "Y"))
        parts.append(q)
        for k in range(4):
            parts.append(tube([(0.19 + k * 0.012, 0.15 + (k % 2) * 0.02, 1.55), (0.27 + k * 0.012, 0.15, 1.78)],
                              0.005, "MAT_White", segs=3, smooth=False))
        parts.append(lathe([(0.0, 0.03), (0.10, 0.02), (0.12, 0.0), (0.0, 0.0)], armour, 10,
                           T(0, -0.125, 1.32) @ R(math.pi / 2, "X")))                                     # chest disc
    return join(parts, f"soldier_{side}_{pose}")


def bowman(side="pandava", pose="advance", legs="stand"):
    """The archer figure in either army's colours (the Kaurava one is the same bowman in crimson and bronze)."""
    o = soldier("pandava", pose, legs=legs)
    if side == "kaurava":
        from hero_lib import M
        names = [m.name for m in o.data.materials]
        for src, dst in (("MAT_Saffron", "MAT_Crimson"), ("MAT_Gold", "MAT_Bronze"), ("MAT_Red", "MAT_Black")):
            if src in names:
                o.data.materials[names.index(src)] = M(dst)
    return o


# ------------------------------------------------------------ K06 war tent
def war_tent(c1="MAT_Saffron", c2="MAT_Cream"):
    parts = []
    W, Hh, RH = 3.6, 3.0, 2.6            # half width, wall height, roof rise
    n = 12                                # stripes per wall
    for side in range(4):
        rot = R(side * math.pi / 2, "Z")
        for i in range(n):
            if side == 0 and 4 <= i <= 7:   # doorway on the front (-Y) wall
                continue
            x0 = -W + i * (2 * W / n)
            p = box((2 * W / n + 0.004, 0.035, Hh), (x0 + W / n, -W, Hh / 2), c1 if i % 2 == 0 else c2)
            xform(p, rot)
            parts.append(p)
    # swept pyramid roof with a bell curve, striped in 4 x 8 gores
    segs = 32
    prof = [(W * 1.10 * (1 - t) ** 0.75 + 0.06, Hh - 0.12 + RH * (t ** 1.6)) for t in (k / 10 for k in range(11))]
    roof = lathe(prof, c1, 4)
    xform(roof, R(math.pi / 4, "Z") @ S(math.sqrt(2) * 0.72, math.sqrt(2) * 0.72, 1))
    parts.append(roof)
    for side in range(4):                 # contrasting gore stripes and scalloped valance
        rot = R(side * math.pi / 2, "Z")
        for i in range(n):
            x0 = -W * 1.12 + (i + 0.5) * (2 * W * 1.12 / n)
            sc = extrude_poly([(-0.33, 0.0), (0.33, 0.0), (0.33, -0.30), (0.0, -0.62), (-0.33, -0.30)], 0.03,
                              c2 if i % 2 == 0 else "MAT_Red")
            xform(sc, rot @ T(x0, -W * 1.12, Hh - 0.10) @ R(math.pi / 2, "Z"))
            parts.append(sc)
            parts.append(sphere(0.045, tuple((rot @ Vector((x0, -W * 1.12, Hh - 0.76)))), "MAT_Gold", seg=8))
        parts.append(xform(tube([(-W * 1.13, -W * 1.13, Hh - 0.09), (W * 1.13, -W * 1.13, Hh - 0.09)], 0.035,
                                "MAT_Gold", segs=8, smooth=False), rot)[0])
        ridge = [(W * 1.12 * (1 - t) ** 0.75 + 0.06, Hh - 0.10 + RH * (t ** 1.6)) for t in (k / 10 for k in range(11))]
        rp = tube([(-r, -r, z) for r, z in ridge], 0.04, "MAT_Gold", segs=6, per=2)
        parts.append(xform(rp, rot)[0])
    # finial, corner posts, pennants
    parts.append(lathe([(0.0, 0), (0.22, 0), (0.28, 0.12), (0.12, 0.26), (0.09, 0.36), (0.20, 0.50), (0.22, 0.62),
                        (0.08, 0.80), (0.05, 0.95), (0.10, 1.05), (0.02, 1.30), (0.0, 1.45)], "MAT_Gold", 20,
                       T(0, 0, Hh + RH - 0.25)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(tube([(sx * W, sy * W, 0), (sx * W, sy * W, Hh + 0.9)], 0.09, "MAT_Wood", segs=10, smooth=False))
            parts.append(lathe([(0.09, 0), (0.15, 0.08), (0.07, 0.2), (0.11, 0.3), (0.0, 0.5)], "MAT_Gold", 12,
                               T(sx * W, sy * W, Hh + 0.9)))
            fl = P.flag(1.1, 0.5, "MAT_Red" if c1 == "MAT_Saffron" else c1, wave=0.08)
            xform(fl, T(sx * W, sy * W, Hh + 1.30) @ R(0.4 * sx, "Z"))
            parts.append(fl)
            # guy ropes and pegs
            end = (sx * (W + 2.2), sy * (W + 2.2), 0.05)
            parts.append(tube([(sx * W, sy * W, Hh), end], 0.015, "MAT_Hide", segs=5, smooth=False))
            parts.append(tube([end, (end[0], end[1], 0.35)], 0.03, "MAT_Wood", segs=6, smooth=False))
    # doorway: tied-back curtains, awning on two poles, carpet and steps
    for sx in (-1, 1):
        cur = [(sx * 1.2, -W - 0.02, Hh), (sx * 1.25, -W - 0.06, 1.9), (sx * 1.45, -W - 0.05, 1.3),
               (sx * 1.25, -W - 0.04, 0.0)]
        parts.append(tube(cur, [0.42, 0.30, 0.13, 0.30], "MAT_Red", segs=10, per=6, flat=0.25))
        parts.append(lathe([(0.15, -0.04), (0.17, 0), (0.15, 0.04)], "MAT_Gold", 10, T(sx * 1.45, -W - 0.05, 1.3)))
        parts.append(tube([(sx * 1.9, -W - 2.4, 0), (sx * 1.9, -W - 2.4, 2.7)], 0.06, "MAT_Wood", segs=8, smooth=False))
        parts.append(lathe([(0.06, 0), (0.11, 0.06), (0.0, 0.30)], "MAT_Gold", 10, T(sx * 1.9, -W - 2.4, 2.7)))
    aw = box((4.2, 2.6, 0.03), (0, -W - 1.2, 2.82), c2, rot=R(-0.12, "X"))
    parts.append(aw)
    for i in range(8):
        sc = extrude_poly([(-0.26, 0.0), (0.26, 0.0), (0.0, -0.40)], 0.03, c1)
        xform(sc, T(-1.84 + i * 0.525, -W - 2.48, 2.68) @ R(math.pi / 2, "Z"))
        parts.append(sc)
    parts.append(box((6.4, 6.4, 0.03), (0, 0, 0.015), "MAT_Crimson"))
    parts.append(box((2.6, 3.0, 0.035), (0, -W - 1.2, 0.017), "MAT_Red"))
    # standards planted by the door: two spears and a round shield
    for sx in (-1, 1):
        parts.append(tube([(sx * 2.6, -W - 0.3, 0), (sx * 2.6, -W - 0.3, 3.4)], 0.02, "MAT_Wood", segs=5, smooth=False))
        parts.append(lathe([(0.02, 0), (0.05, 0.06), (0.0, 0.34)], "MAT_Iron", 6, T(sx * 2.6, -W - 0.3, 3.4)))
        sh = lathe([(0.0, 0.08), (0.08, 0.07), (0.12, 0.03), (0.40, 0.0), (0.43, -0.02), (0.0, -0.02)], "MAT_Bronze", 16)
        xform(sh, T(sx * 2.6, -W - 0.36, 1.0) @ R(math.pi / 2 - 0.2, "X"))
        parts.append(sh)
    return join(parts, "war_tent")


# ------------------------------------------------------------ K07 war drum cart
def drum_cart():
    parts = []
    wr = 0.78
    w = P.wheel(wr, 12, "MAT_Bronze", "MAT_Red", width=0.10, rim_inlays=14)
    xform(w, T(1.15, 0, wr))
    parts += [w] + mirror_x(w)
    parts.append(tube([(-1.15, 0, wr), (1.15, 0, wr)], 0.06, "MAT_Iron", segs=10, smooth=False))
    parts.append(box((1.9, 2.6, 0.10), (0, 0, wr + 0.14), "MAT_Wood", bevel=0.015))
    for sx in (-1, 1):
        parts.append(tube([(sx * 0.95, -1.3, wr + 0.14), (sx * 0.95, 1.3, wr + 0.14)], 0.04, "MAT_Bronze", segs=8, smooth=False))
        parts += P.swag_row((sx * 0.97, -1.25, wr + 0.10), (sx * 0.97, 1.25, wr + 0.10), 12, "MAT_Bronze")
    # cradle and the kettle drum (dundubhi)
    z0 = wr + 0.19
    parts.append(lathe([(0.0, 0), (0.55, 0), (0.60, 0.06), (0.50, 0.14), (0.52, 0.22), (0.0, 0.22)], "MAT_Bronze", 24,
                       T(0, 0.15, z0)))
    Rr = 0.95
    bowl = [(0.30, 0.0)] + [(Rr * math.sin(a), Rr * 0.95 * (1 - math.cos(a)) + 0.02) for a in
                            (math.radians(d) for d in range(25, 91, 6))] + [(Rr, Rr * 0.95 + 0.10)]
    topz = Rr * 0.95 + 0.10
    parts.append(lathe(bowl, "MAT_Bronze", 40, T(0, 0.15, z0 + 0.16)))
    parts.append(lathe([(0.0, topz + 0.02), (Rr * 0.6, topz + 0.03), (Rr + 0.01, topz + 0.01), (Rr + 0.03, topz - 0.08),
                        (Rr, topz - 0.10)], "MAT_Hide", 40, T(0, 0.15, z0 + 0.16)))
    for z in (topz - 0.10, topz * 0.55, topz * 0.25):
        rr = Rr if z > topz * 0.6 else (Rr * 0.93 if z > topz * 0.4 else Rr * 0.70)
        parts.append(lathe([(rr + 0.005, z - 0.03), (rr + 0.04, z), (rr + 0.005, z + 0.03)], "MAT_Gold", 40,
                           T(0, 0.15, z0 + 0.16)))
    for k in range(20):                    # lacing zigzag and bosses
        a0, a1 = k / 20 * math.tau, (k + 0.5) / 20 * math.tau
        p0 = (Rr * 1.03 * math.cos(a0), 0.15 + Rr * 1.03 * math.sin(a0), z0 + 0.16 + topz - 0.10)
        p1 = (Rr * 0.96 * math.cos(a1), 0.15 + Rr * 0.96 * math.sin(a1), z0 + 0.16 + topz * 0.55)
        a2 = (k + 1) / 20 * math.tau
        p2 = (Rr * 1.03 * math.cos(a2), 0.15 + Rr * 1.03 * math.sin(a2), z0 + 0.16 + topz - 0.10)
        parts.append(tube([p0, p1, p2], 0.012, "MAT_Hide", segs=4, smooth=False))
        parts.append(sphere(0.035, p0, "MAT_Gold", seg=8))
    skirt = lathe([(Rr * 0.72, topz * 0.25), (Rr * 0.80, 0.16), (Rr * 0.86, 0.02)], "MAT_Red", 40, T(0, 0.15, z0 + 0.16))
    parts.append(skirt)
    for k in range(16):                    # tassels on the skirt
        a = k / 16 * math.tau
        parts.append(lathe([(0.0, 0), (0.03, -0.04), (0.02, -0.14), (0.0, -0.18)], "MAT_Gold", 6,
                           T(Rr * 0.87 * math.cos(a), 0.15 + Rr * 0.87 * math.sin(a), z0 + 0.20)))
    # drumsticks crossed on the head
    for sgn in (-1, 1):
        a, b = (sgn * 0.55, -0.25, z0 + 0.16 + topz + 0.06), (-sgn * 0.35, 0.60, z0 + 0.16 + topz + 0.10)
        parts.append(tube([a, b], 0.022, "MAT_Wood", segs=6, smooth=False))
        parts.append(sphere(0.07, b, "MAT_Hide", seg=10))
    # two great horns on cradles at the sides
    for sx in (-1, 1):
        horn = [(sx * 0.80, 1.20, z0 + 0.30), (sx * 0.84, 0.30, z0 + 0.42), (sx * 0.88, -0.90, z0 + 0.85),
                (sx * 0.92, -1.75, z0 + 1.60), (sx * 0.94, -2.00, z0 + 2.15)]
        parts.append(tube(horn, [0.025, 0.035, 0.05, 0.09, 0.19], "MAT_Gold", segs=14, per=8))
        parts.append(lathe([(0.18, -0.02), (0.23, 0.0), (0.18, 0.02)], "MAT_Gold", 16,
                           T(sx * 0.94, -2.00, z0 + 2.15) @ R(0.45, "X")))
        for y, z in ((0.30, z0 + 0.42), (-0.90, z0 + 0.85)):
            parts.append(tube([(sx * 0.86, y, z0), (sx * 0.86, y, z - 0.03)], 0.03, "MAT_Wood", segs=6, smooth=False))
            parts.append(lathe([(0.06, -0.02), (0.08, 0), (0.06, 0.02)], "MAT_Bronze", 10, T(sx * 0.86, y, z) @ R(1.2, "X")))
    # draught pole and prop
    parts.append(tube([(0, -1.3, wr + 0.10), (0, -2.4, wr + 0.05), (0, -3.6, wr + 0.30)], 0.05, "MAT_Wood", segs=8, per=6))
    parts.append(tube([(-0.9, -3.55, wr + 0.34), (0, -3.6, wr + 0.30), (0.9, -3.55, wr + 0.34)], 0.04, "MAT_Wood", segs=8, per=4))
    parts.append(tube([(0, -2.4, wr + 0.05), (0, -2.5, 0.0)], 0.035, "MAT_Wood", segs=6, smooth=False))
    parts.append(tube([(0, 1.3, wr + 0.10), (0, 1.5, 0.0)], 0.035, "MAT_Wood", segs=6, smooth=False))
    return join(parts, "drum_cart")


# ------------------------------------------------------------ K08 wreck and rank chariot
def chariot_wreck():
    rng = random.Random(11)
    wheels, body = C.build("rank", light=True, umbrella=False, standard=False, pole=False, as_parts=True)
    # body pitched onto its broken rear corner
    tilt = T(0, 0, -0.42) @ R(math.radians(-17), "Y") @ R(math.radians(7), "X")
    xform(body, tilt)
    rear_r, rear_l, front_r, front_l = wheels                 # order from chariot.build
    xform(rear_l, tilt)                                       # still on its axle (left side stays up)
    xform(front_l, tilt)
    # the right rear wheel has snapped off and lies flat a little way off
    xform(rear_r, T(2.6, 1.9, 0.07) @ R(math.pi / 2, "Y") @ R(0.5, "X") @ T(-1.14, -1.15, -0.95))
    # the right front wheel leans against the body
    xform(front_r, T(1.45, -1.35, 0.50) @ R(math.radians(62), "Y") @ T(-1.02, 1.15, -0.58))
    parts = list(body) + [rear_r, rear_l, front_r, front_l]
    # snapped draught pole, fallen umbrella, torn banner
    parts.append(tube([(0, -1.2, 0.45), (0.1, -2.3, 0.30), (0.25, -3.0, 0.05)], 0.055, "MAT_Wood", segs=8, per=5))
    parts.append(tube([(1.3, -3.3, 0.05), (0.6, -4.4, 0.06)], 0.05, "MAT_Wood", segs=8, smooth=False))
    par = P.parasol(1.18, 16, "MAT_Saffron", "MAT_GoldDark")
    xform(par, T(-2.5, 1.1, 0.78) @ R(math.radians(-34), "Y") @ R(math.radians(12), "X") @ R(0.4, "Z"))
    parts.append(par)
    parts.append(tube([(-2.4, 1.1, 0.75), (-1.6, 1.5, 0.30), (-0.6, 2.0, 0.85)], 0.05, "MAT_GoldDark", segs=8, per=5))
    fl = P.flag(2.0, 1.0, "MAT_Saffron", wave=0.3)
    xform(fl, T(-1.0, -2.2, 0.06) @ R(math.pi / 2, "Y") @ R(0.6, "X"))
    parts.append(fl)
    parts.append(tube([(-1.0, -2.2, 0.05), (-1.3, -0.2, 0.06)], 0.022, "MAT_GoldDark", segs=6, smooth=False))
    # arrows stuck in the body and the ground, a dropped shield and helmet
    for i in range(34):
        if i < 20:
            base = Vector((rng.uniform(-0.8, 0.8), rng.uniform(-1.6, 1.9), rng.uniform(0.6, 1.5)))
        else:
            base = Vector((rng.uniform(-3.2, 3.2), rng.uniform(-3.5, 3.0), 0.0))
        d = Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.9, -0.2), rng.uniform(0.5, 1.0))).normalized()
        end = base + d * 0.75
        parts.append(tube([base, end], 0.007, "MAT_Wood", segs=4, smooth=False))
        m = T(*end) @ Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
        for k in range(3):
            f = box((0.002, 0.035, 0.12), (0, 0, 0), "MAT_White")
            xform(f, m @ R(k * math.tau / 3, "Z") @ T(0, 0.018, -0.07))
            parts.append(f)
    sh = lathe([(0.0, 0.08), (0.08, 0.07), (0.12, 0.03), (0.36, 0.0), (0.39, -0.02), (0.0, -0.02)], "MAT_Bronze", 16)
    xform(sh, T(1.9, -1.9, 0.10) @ R(0.3, "X"))
    parts.append(sh)
    parts.append(lathe([(0.112, 0), (0.115, 0.07), (0.09, 0.14), (0.04, 0.18), (0.0, 0.23)], "MAT_Bronze", 10,
                       T(-1.8, -1.2, 0.09) @ R(1.9, "X")))
    for _ in range(14):                                       # scorched debris
        p = (rng.uniform(-2.5, 2.5), rng.uniform(-2.5, 2.5), 0.04)
        parts.append(box((rng.uniform(0.1, 0.5), rng.uniform(0.05, 0.12), 0.05), p, "MAT_Soot",
                         rot=R(rng.uniform(0, 3), "Z")))
    o = join(parts, "wreck")
    # scorch: the deck and timber read as burnt
    names = [m.name for m in o.data.materials]
    from hero_lib import M
    for src in ("MAT_Wood", "MAT_Red"):
        if src in names:
            o.data.materials[names.index(src)] = M("MAT_Soot")
    return o


def rank_chariot(target_tris=30000, style="rank", crew=True):
    """Lighter chariot for the army lines, with a driver on the footboard and a bowman on the archer's deck."""
    from hero_lib import tri_count
    o = C.build(style, light=True)
    n = tri_count(o)
    if n > target_tris:
        decimated(o, target_tris / n)
    if crew:
        side = "kaurava" if style == "rank_kaurava" else "pandava"
        driver = bowman(side, "attention")
        xform(driver, T(0, -0.95, 0.835))
        archer = bowman(side, "advance")
        xform(archer, T(0.05, 0.40, 1.06) @ R(-0.5, "Z"))
        o = join([o, driver, archer], "rank_chariot")
    return o


# ------------------------------------------------------------ batch 2: cavalry and battle props
def cavalry(side="kaurava"):
    """Mounted warrior: Kaurava lancer on a bay, Pandava horse-archer on a dun."""
    import creatures as CR
    if side == "kaurava":
        h = CR.horse("MAT_Bay", "MAT_Bronze", "MAT_Crimson", pose="trot", tris=8000)
        r = soldier("kaurava", "advance", legs="ride")
    else:
        h = CR.horse("MAT_Hide", "MAT_Gold", "MAT_Saffron", pose="trot", tris=8000)
        r = bowman("pandava", "advance", legs="ride")
    xform(r, T(0, 0.08, 0.70))
    return join([h, r], f"cavalry_{side}")


def _arrow(base, d, length=0.8, shaft="MAT_Wood"):
    base, d = Vector(base), Vector(d).normalized()
    end = base + d * length
    out = [tube([base, end], 0.007, shaft, segs=4, smooth=False)]
    m = T(*end) @ Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
    for k in range(3):
        f = box((0.002, 0.035, 0.12), (0, 0, 0), "MAT_White")
        xform(f, m @ R(k * math.tau / 3, "Z") @ T(0, 0.018, -0.07))
        out.append(f)
    return out


def arrow_cluster(n=14, seed=5):
    """Arrows and a broken spear stuck in the ground, for the middle strip in battle shots."""
    rng = random.Random(seed)
    parts = []
    for _ in range(n):
        a, r = rng.uniform(0, math.tau), rng.uniform(0.05, 0.9)
        d = (rng.uniform(-0.4, 0.4), rng.uniform(-0.9, -0.3), rng.uniform(0.6, 1.0))
        parts += _arrow((r * math.cos(a), r * math.sin(a), -0.05), d)
    parts.append(tube([(0.3, 0.2, -0.05), (0.42, -0.25, 1.25)], 0.017, "MAT_Wood", segs=5, smooth=False))
    parts.append(lathe([(0.0, 0.07), (0.07, 0.065), (0.10, 0.03), (0.30, 0.0), (0.33, -0.02), (0.0, -0.02)],
                       "MAT_Bronze", 14, T(-0.5, 0.35, 0.10) @ R(0.35, "X")))
    return join(parts, "arrows")


def conch():
    """Krishna's conch Panchajanya, 0.34 m: white shell, spiral spire, gold mounts."""
    prof = [(0.0, 0.165), (0.012, 0.155), (0.030, 0.132), (0.050, 0.105), (0.074, 0.070), (0.091, 0.030),
            (0.095, 0.0), (0.086, -0.040), (0.062, -0.085), (0.038, -0.125), (0.020, -0.155), (0.0, -0.168)]
    parts = [lathe(prof, "MAT_White", 28)]
    hel = []
    for i in range(60):                                                         # raised spiral on the spire
        t = i / 59
        z = 0.035 + 0.118 * t
        r = 0.090 - 0.073 * t ** 0.9
        a = t * math.tau * 3.4
        hel.append((r * math.cos(a), r * math.sin(a), z))
    parts.append(tube(hel, [0.011 - 0.007 * (i / 59) for i in range(60)], "MAT_White", segs=6, smooth=False))
    parts.append(sphere(1.0, (0.088, 0.012, -0.050), "MAT_Cream", scale=(0.034, 0.066, 0.125), seg=14, rot=R(-0.20, "Y")))  # flared lip
    parts.append(sphere(1.0, (0.104, 0.018, -0.050), "MAT_Red", scale=(0.016, 0.036, 0.095), seg=12, rot=R(-0.20, "Y")))   # aperture
    parts.append(lathe([(0.0, 0.215), (0.008, 0.20), (0.02, 0.19), (0.012, 0.175), (0.026, 0.16), (0.034, 0.142),
                        (0.030, 0.128), (0.0, 0.128)], "MAT_Gold", 16))        # spire cap
    parts.append(lathe([(0.0, -0.20), (0.012, -0.19), (0.016, -0.175), (0.026, -0.16), (0.040, -0.125),
                        (0.044, -0.112), (0.0, -0.112)], "MAT_Gold", 16))      # mouthpiece
    for z, r in ((0.0, 0.097), (0.072, 0.075)):
        parts.append(lathe([(r - 0.004, z - 0.012), (r + 0.006, z), (r - 0.004, z + 0.012)], "MAT_Gold", 28))
    for k in range(12):
        a = k / 12 * math.tau
        parts.append(sphere(0.008, (0.103 * math.cos(a), 0.103 * math.sin(a), 0.0), "MAT_Gold", seg=6))
    o = join(parts, "conch")
    xform(o, T(0, 0, 0.10) @ R(math.radians(78), "X") @ R(math.radians(70), "Z"))    # on its side, mouth up
    return o


def gada():
    """Bhima's mace, 1.35 m: ribbed gold head, banded shaft, red grip."""
    parts = [tube([(0, 0, 0.06), (0, 0, 1.0)], [0.026, 0.03], "MAT_GoldDark", segs=10, smooth=False),
             lathe([(0.0, 0.0), (0.045, 0.01), (0.055, 0.04), (0.03, 0.075), (0.026, 0.09), (0.0, 0.09)], "MAT_Gold", 14),
             tube([(0, 0, 0.12), (0, 0, 0.40)], 0.031, "MAT_Red", segs=10, smooth=False)]
    for z in (0.11, 0.41, 0.62, 0.84):
        parts.append(lathe([(0.028, z - 0.015), (0.042, z), (0.028, z + 0.015)], "MAT_Gold", 14))
    head = [(0.03, 0.92), (0.08, 0.95), (0.145, 1.02), (0.17, 1.10), (0.16, 1.18), (0.11, 1.25), (0.05, 1.29),
            (0.035, 1.31), (0.0, 1.31)]
    parts.append(lathe(head, "MAT_Gold", 24))
    for k in range(10):                                                         # ribs
        a = k / 10 * math.tau
        pts = [((r + 0.006) * math.cos(a), (r + 0.006) * math.sin(a), z) for r, z in head[1:7]]
        parts.append(tube(pts, [0.008, 0.016, 0.02, 0.02, 0.016, 0.008], "MAT_GoldDark", segs=6, per=3))
    parts.append(lathe([(0.0, 1.30), (0.045, 1.31), (0.05, 1.335), (0.02, 1.36), (0.03, 1.38), (0.0, 1.43)],
                       "MAT_Gold", 12))
    o = join(parts, "gada")
    xform(o, T(0, 0, 0.17) @ R(math.radians(90), "X"))                           # lying down, head toward -Y
    return o


def great_bow():
    """Gandiva, 1.95 m recurve: gold limbs, red grip, scrolled tips, strung."""
    c = Vector((0, 0, 1.0))
    pts = [c + Vector((0, y, z)) for y, z in ((-0.20, 0.97), (-0.02, 0.86), (0.16, 0.55), (0.10, 0.20), (0.0, 0.0),
                                              (0.10, -0.20), (0.16, -0.55), (-0.02, -0.86), (-0.20, -0.97))]
    parts = [tube(pts, [0.008, 0.014, 0.022, 0.026, 0.030, 0.026, 0.022, 0.014, 0.008], "MAT_Gold", segs=8, per=6),
             tube([c + Vector((0, 0.02, -0.11)), c, c + Vector((0, 0.02, 0.11))], 0.034, "MAT_Red", segs=8, per=3),
             tube([pts[0], pts[-1]], 0.003, "MAT_White", segs=3, smooth=False)]
    for z in (0.14, -0.14, 0.42, -0.42, 0.70, -0.70):
        y = 0.07 + (0.08 if abs(z) > 0.3 else 0) - (0.10 if abs(z) > 0.6 else 0)
        parts.append(sphere(0.034, (0, y, 1.0 + z), "MAT_GoldDark", scale=(1, 1, 0.45), seg=8))
    o = join(parts, "bow")
    xform(o, T(0, 0, 0.05) @ R(math.radians(-82), "Y") @ T(0, 0, -1.0))          # lying nearly flat
    return o


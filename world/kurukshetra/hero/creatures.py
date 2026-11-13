"""Battle animals after concept images 24, 33, 34, 40 and 42: harnessed chariot horses and armoured
war elephants with a caparison and an archers' tower. All face -Y and stand on Z=0."""
import math

import bmesh
from mathutils import Vector

import parts as P
from hero_lib import (M, R, S, T, apply_modifiers, blob, box, decimated, extrude_poly, join, lathe, obj_from_bm,
                      sphere, tube, xform)


def ring(centre, rx, rz, radius, mat, n=28, tilt=0.0, flat=1.0):
    """Closed strap around the body in the XZ plane (optionally tilted about X)."""
    c = Vector(centre)
    m = R(tilt, "X")
    pts = [c + m @ Vector((rx * math.cos(a), 0, rz * math.sin(a))) for a in (k / n * math.tau for k in range(n))]
    return tube(pts, radius, mat, segs=6, closed=True, smooth=False, flat=flat)


def drape(surf, y0, y1, half_w, hem_z, mat, trim, ny=26, ntop=22, ndrop=8, lift=0.05, border=0.10):
    """Cloth laid over a back: follows surf(x, y) over the top, then hangs straight down to hem_z.
    half_w(y) is where it leaves the body. Faces near the edge take the trim material."""
    bm = bmesh.new()
    rows = []
    for j in range(ny + 1):
        y = y0 + (y1 - y0) * j / ny
        hw = half_w(y) * 0.955
        row = []
        zs = surf(hw, y) + lift
        for k in range(ndrop, 0, -1):                       # left drop, hem upward
            row.append((-hw - lift, y, hem_z + (zs - hem_z) * (1 - k / ndrop)))
        for i in range(ntop + 1):
            x = -hw + 2 * hw * i / ntop
            row.append((x * (1 + lift / max(hw, 1e-3)), y, surf(x, y) + lift))
        for k in range(1, ndrop + 1):
            row.append((hw + lift, y, hem_z + (zs - hem_z) * (1 - k / ndrop)))
        rows.append([bm.verts.new(p) for p in row])
    n = len(rows[0])
    for j in range(ny):
        for i in range(n - 1):
            f = bm.faces.new((rows[j][i], rows[j + 1][i], rows[j + 1][i + 1], rows[j][i + 1]))
            edge_y = min(j, ny - 1 - j) * (y1 - y0) / ny < border
            edge_h = min(i, n - 2 - i) < 1.5
            f.material_index = 1 if (edge_y or edge_h) else 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = obj_from_bm(bm, mat)
    o.data.materials.append(M(trim))
    sol = o.modifiers.new("t", "SOLIDIFY")
    sol.thickness = 0.03
    sol.offset = 1
    apply_modifiers(o)
    return o


# ------------------------------------------------------------------ horse
def horse(coat="MAT_White", trim="MAT_Gold", cloth="MAT_Red", harness=True, pose="trot", tris=14000):
    """Chariot horse, 1.55 m at the withers, facing -Y. pose: stand | trot (near fore lifted)."""
    B = [("s", (0, 0.10, 1.18), (0.27, 0.64, 0.30)),          # barrel
         ("s", (0, -0.44, 1.20), (0.25, 0.32, 0.34)),         # chest
         ("s", (0, 0.62, 1.23), (0.27, 0.38, 0.33)),          # croup
         ("s", (0, -0.30, 1.42), (0.12, 0.26, 0.13)),         # withers
         ("t", [(0, -0.46, 1.30), (0, -0.70, 1.60), (0, -0.88, 1.86), (0, -0.98, 2.00)], [0.23, 0.17, 0.13, 0.11]),  # neck
         ("s", (0, -1.05, 1.97), (0.10, 0.15, 0.125)),        # poll
         ("s", (0, -1.12, 1.84), (0.085, 0.11, 0.13)),        # cheek
         ("c", (0, -1.12, 1.92), (0, -1.36, 1.63), 0.095, 0.062),   # face
         ("s", (0, -1.385, 1.60), (0.066, 0.07, 0.06)),       # muzzle
         ("s", (0, -1.33, 1.56), (0.05, 0.06, 0.04))]         # chin
    for sx in (-1, 1):
        B.append(("c", (sx * 0.065, -0.99, 2.06), (sx * 0.085, -1.02, 2.19), 0.032, 0.012))     # ears
        B.append(("s", (sx * 0.19, 0.64, 1.02), (0.12, 0.24, 0.30)))                            # thigh
    # legs: (hip/shoulder, knee/hock, fetlock, hoof)
    lift = pose == "trot"
    legs = {
        "fl": [(-0.15, -0.46, 1.02), (-0.15, -0.74, 0.74), (-0.15, -0.62, 0.36), (-0.15, -0.70, 0.27)] if lift else
              [(-0.15, -0.46, 1.02), (-0.15, -0.50, 0.60), (-0.15, -0.50, 0.17), (-0.15, -0.53, 0.06)],
        "fr": [(0.15, -0.46, 1.02), (0.15, -0.44, 0.60), (0.15, -0.40, 0.17), (0.15, -0.43, 0.06)],
        "hl": [(-0.18, 0.70, 0.90), (-0.18, 0.92, 0.58), (-0.18, 0.86, 0.17), (-0.18, 0.83, 0.06)],
        "hr": [(0.18, 0.66, 0.90), (0.18, 0.74, 0.58), (0.18, 0.60, 0.17), (0.18, 0.57, 0.06)] if lift else
              [(0.18, 0.70, 0.90), (0.18, 0.92, 0.58), (0.18, 0.86, 0.17), (0.18, 0.83, 0.06)],
    }
    for k, (a, b, c, d) in legs.items():
        fore = k[0] == "f"
        B += [("c", a, b, 0.10 if fore else 0.095, 0.058), ("s", b, (0.062, 0.066, 0.07)),
              ("c", b, c, 0.052, 0.040), ("s", c, (0.052, 0.058, 0.055)), ("c", c, d, 0.045, 0.05)]
    # tail and mane, flowing
    B.append(("t", [(0, 0.96, 1.36), (0, 1.16, 1.34), (0, 1.27, 1.02), (0.03, 1.25, 0.62), (0.05, 1.32, 0.38)],
              [0.055, 0.075, 0.09, 0.07, 0.03]))
    for i in range(9):
        t = i / 8
        p = Vector((0, -0.50, 1.52)).lerp(Vector((0, -1.00, 2.10)), t) + Vector((0, 0.05, 0.03))
        B.append(("c", tuple(p), (p.x + 0.13, p.y + 0.14, p.z - 0.30 - 0.06 * math.sin(i * 1.7)), 0.06, 0.022))
    B.append(("c", (0, -1.08, 2.09), (0.02, -1.20, 1.96), 0.04, 0.015))        # forelock
    body = blob(B, voxel=0.02, smooth=3, mat=coat)
    n = sum(len(p.vertices) - 2 for p in body.data.polygons)
    if n > tris:
        decimated(body, tris / n)
    parts = [body]
    for a, b, c, d in legs.values():                                           # hooves
        hf = lathe([(0.0, 0.0), (0.066, 0.0), (0.058, 0.07), (0.05, 0.10), (0.0, 0.10)], "MAT_Black", 10)
        tilt = math.atan2(-(c[1] - d[1]), c[2] - d[2]) if lift else 0.0
        xform(hf, T(d[0], d[1] - 0.012, d[2] - 0.06) @ R(tilt * 0.5, "X"))
        parts.append(hf)
    for sx in (-1, 1):
        parts.append(sphere(0.022, (sx * 0.083, -1.14, 1.93), "MAT_Black", scale=(0.6, 1, 1), seg=8))   # eyes
        parts.append(sphere(0.012, (sx * 0.04, -1.435, 1.60), "MAT_Black", seg=6))                     # nostrils
    if harness:
        # bridle: noseband, browband, cheek straps and a plume
        parts.append(ring((0, -1.29, 1.71), 0.082, 0.085, 0.012, trim, 14, tilt=math.radians(50)))
        parts.append(ring((0, -1.09, 1.93), 0.108, 0.15, 0.012, trim, 16, tilt=math.radians(50)))
        for sx in (-1, 1):
            parts.append(tube([(sx * 0.07, -1.30, 1.70), (sx * 0.092, -1.16, 1.86), (sx * 0.085, -1.04, 2.02)],
                              0.011, trim, segs=5, per=3))
            parts.append(lathe([(0.0, 0.012), (0.035, 0.008), (0.04, 0.0), (0.0, 0.0)], trim, 10,
                               T(sx * 0.094, -1.16, 1.86) @ R(sx * math.pi / 2, "Y")))             # rosette
        parts.append(lathe([(0.0, 0.0), (0.03, 0.02), (0.02, 0.06), (0.035, 0.10), (0.0, 0.20)], trim, 8,
                           T(0, -1.06, 2.08)))                                                       # poll finial
        parts.append(lathe([(0.0, 0.014), (0.05, 0.01), (0.06, 0.0), (0.0, 0.0)], trim, 12,
                           T(0, -1.20, 1.90) @ R(math.radians(-138), "X") @ T(0, 0, 0.088)))        # brow disc
        # breast collar with pendants, girth and a short saddle cloth
        parts.append(ring((0, -0.56, 1.30), 0.275, 0.40, 0.030, trim, 24, tilt=math.radians(-24), flat=0.45))
        for i in range(7):
            a = math.radians(-150 + i * 20)
            p = Vector((0, -0.56, 1.30)) + R(math.radians(-24), "X") @ Vector((0.285 * math.cos(a), 0, 0.41 * math.sin(a)))
            b = P.bell(trim, 1.4)
            xform(b, T(p.x, p.y - 0.02, p.z - 0.02))
            parts.append(b)
        parts.append(ring((0, -0.16, 1.185), 0.285, 0.315, 0.022, trim, 24, flat=0.5))
        sc = drape(lambda x, y: 1.18 + 0.30 * math.sqrt(max(0.0, 1 - (x / 0.275) ** 2)), -0.12, 0.34,
                   lambda y: 0.262, 0.98, cloth, trim, ny=12, ntop=12, ndrop=4, lift=0.02, border=0.035)
        parts.append(sc)
        parts.append(tube([(0, 0.34, 1.50), (0, 0.70, 1.56), (0, 0.97, 1.40)], 0.014, trim, segs=5, per=4))  # crupper
        for a, b, c, d in legs.values():                                                           # fetlock bands
            parts.append(lathe([(0.052, -0.02), (0.062, 0.0), (0.052, 0.02)], trim, 8, T(c[0], c[1], c[2] + 0.07)))
    return join(parts, "horse")


def horse_team(coat="MAT_White", trim="MAT_Gold", cloth="MAT_Red", yoke_y=-4.72, yoke_z=1.62):
    """Four horses abreast under a chariot yoke, with traces and reins back to the car.
    The origin is the chariot's origin, so the team is placed with the chariot's own transform."""
    parts = []
    hy = yoke_y + 0.53                                  # the yoke rides just ahead of the withers
    for i, x in enumerate((-1.125, -0.375, 0.375, 1.125)):
        h = horse(coat, trim, cloth, pose="trot" if i % 2 == 0 else "stand", tris=11000)
        xform(h, T(x, hy, 0))
        parts.append(h)
        for sx in (-1, 1):                              # traces from the collar back to the splinter bar
            parts.append(tube([(x + sx * 0.27, hy - 0.42, 1.22), (x + sx * 0.30, hy + 0.9, 1.05),
                               (x * 0.55 + sx * 0.12, -1.95, 0.84)], 0.012, "MAT_Wood", segs=4, per=4))
        parts.append(tube([(x, hy - 1.30, 1.70), (x * 0.9, hy - 0.2, 1.72), (x * 0.45, -2.6, 1.55),
                           (x * 0.16, -1.25, 1.75)], 0.008, trim, segs=4, per=5))                    # rein
    return join(parts, "team")


# ------------------------------------------------------------------ war elephant
ELEPHANT_STYLES = {
    "pandava": dict(cloth="MAT_Saffron", cloth2="MAT_Blue", trim="MAT_Gold", tower="MAT_Gold", wood="MAT_Wood",
                    flag="MAT_Saffron", side="pandava"),
    "kaurava": dict(cloth="MAT_Crimson", cloth2="MAT_Black", trim="MAT_Bronze", tower="MAT_Bronze", wood="MAT_Wood",
                    flag="MAT_Red", side="kaurava"),
}
# body ellipsoids, also used to lay the caparison: (centre, radii)
_EL_BODY = [((0, 0.30, 1.95), (0.86, 1.38, 0.90)), ((0, -0.78, 2.05), (0.80, 0.78, 0.96)),
            ((0, 1.28, 1.85), (0.78, 0.72, 0.86)), ((0, 0.20, 2.55), (0.52, 1.25, 0.38))]


def _el_surf(x, y):
    """Height of the elephant's back at (x, y)."""
    best = 0.0
    for (cx, cy, cz), (rx, ry, rz) in _EL_BODY:
        q = 1 - ((x - cx) / rx) ** 2 - ((y - cy) / ry) ** 2
        if q > 0:
            best = max(best, cz + rz * math.sqrt(q))
    return best


def _el_halfw(y):
    best = 0.3
    for (cx, cy, cz), (rx, ry, rz) in _EL_BODY[:3]:
        q = 1 - ((y - cy) / ry) ** 2
        if q > 0:
            best = max(best, rx * math.sqrt(q))
    return best


def howdah(st, crew=True):
    """Archers' tower: railed box on a cushion, four posts and a pagoda roof. Stands on z=0, centred."""
    trim, tower, wood = st["trim"], st["tower"], st["wood"]
    W, L, Hh = 1.70, 2.20, 0.80
    parts = [box((W + 0.16, L + 0.16, 0.16), (0, 0, 0.08), st["cloth"], bevel=0.05),          # cushion
             box((W, L, 0.10), (0, 0, 0.21), wood, bevel=0.01)]
    z0 = 0.26
    for sx, sy, w, ax in ((0, 1, W, "y"), (0, -1, W, "y"), (1, 0, L, "x"), (-1, 0, L, "x")):   # four panelled walls
        cx, cy = sx * W / 2, sy * L / 2
        size = (0.05, w, Hh) if ax == "x" else (w, 0.05, Hh)
        parts.append(box(size, (cx, cy, z0 + Hh / 2), wood, bevel=0.008))
        n = 3 if w > 2 else 2
        for i in range(n):                                                                     # gold bosses
            u = (i + 0.5) / n - 0.5
            px, py = (cx + sx * 0.03, u * w) if ax == "x" else (u * w, cy + sy * 0.03)
            rot = R(sx * math.pi / 2, "Y") if ax == "x" else R(-sy * math.pi / 2, "X")
            parts.append(lathe([(0.0, 0.05), (0.08, 0.04), (0.11, 0.015), (0.22, 0.012), (0.24, 0.0), (0.0, 0.0)],
                               trim, 16, T(px, py, z0 + Hh / 2) @ rot))
        for zz in (z0 + 0.03, z0 + Hh - 0.03):                                                 # rails
            a = (cx - (w / 2 if ax == "y" else 0), cy - (w / 2 if ax == "x" else 0), zz)
            b = (cx + (w / 2 if ax == "y" else 0), cy + (w / 2 if ax == "x" else 0), zz)
            parts.append(tube([a, b], 0.035, tower, segs=8, smooth=False))
    for sx in (-1, 1):
        for sy in (-1, 1):                                                                     # posts
            parts.append(tube([(sx * W / 2, sy * L / 2, 0.16), (sx * W / 2, sy * L / 2, 2.05)], [0.05, 0.04], tower,
                              segs=8, smooth=False))
            parts.append(lathe([(0.04, 0), (0.075, 0.04), (0.04, 0.08)], trim, 10, T(sx * W / 2, sy * L / 2, 1.10)))
    roof = lathe([(1.62, 1.97), (1.66, 2.05), (1.30, 2.17), (0.85, 2.38), (0.42, 2.64), (0.16, 2.82), (0.0, 2.85)],
                 tower, 4, R(math.pi / 4, "Z"))
    xform(roof, S(1.0, L / W, 1.0))
    parts.append(roof)
    parts.append(lathe([(1.60, 1.95), (1.66, 1.99), (1.60, 2.03)], trim, 4, S(1.0, L / W, 1.0) @ R(math.pi / 4, "Z")))
    parts.append(lathe([(0.0, 2.80), (0.13, 2.84), (0.16, 2.90), (0.07, 2.98), (0.11, 3.06), (0.04, 3.16), (0.0, 3.34)],
                       trim, 14))
    for sx in (-1, 1):                                                                         # war flags aft
        parts.append(tube([(sx * W / 2, L / 2, 1.9), (sx * (W / 2 + 0.25), L / 2 + 0.35, 4.0)], 0.022, wood, segs=6,
                          smooth=False))
        fl = P.flag(1.1, 0.55, st["flag"], wave=0.10)
        xform(fl, T(sx * (W / 2 + 0.25), L / 2 + 0.36, 3.98))
        parts.append(fl)
    if crew:
        import assets as A
        a1 = A.bowman(st["side"], "advance")
        xform(a1, T(-0.30, -0.55, 0.26))
        a2 = A.bowman(st["side"], "attention")
        xform(a2, T(0.35, 0.45, 0.26) @ R(0.5, "Z"))
        parts += [a1, a2]
    return join(parts, "howdah")


def elephant(style="pandava", pose="walk", tower=True, tris=30000):
    """Armoured war elephant, about 3 m at the shoulder and 6 m nose to tail, facing -Y.
    pose: walk (trunk curled down) | charge (trunk raised)."""
    st = ELEPHANT_STYLES[style]
    trim = st["trim"]
    B = [("s", c, r) for c, r in _EL_BODY]
    B += [("s", (0, -1.78, 2.42), (0.56, 0.62, 0.64)),                 # skull
          ("s", (-0.23, -1.72, 2.95), (0.27, 0.32, 0.24)),             # twin domes
          ("s", (0.23, -1.72, 2.95), (0.27, 0.32, 0.24)),
          ("s", (0, -2.18, 2.22), (0.37, 0.36, 0.46)),                 # trunk root
          ("s", (0, -1.95, 1.78), (0.26, 0.32, 0.20)),                 # lower jaw
          ("s", (0, -1.20, 2.35), (0.62, 0.50, 0.70))]                 # neck
    if pose == "charge":
        trunk = [(0, -2.28, 2.05), (0, -2.74, 1.62), (0, -3.22, 1.46), (0, -3.70, 1.62), (0, -3.98, 2.02),
                 (0, -3.92, 2.38)]
    else:
        trunk = [(0, -2.28, 2.05), (0, -2.58, 1.52), (0, -2.64, 0.98), (0, -2.54, 0.52), (0, -2.74, 0.30),
                 (0, -3.00, 0.42)]
    B.append(("t", trunk, [0.31, 0.25, 0.20, 0.155, 0.125, 0.10]))
    feet = []
    for sx, fy, hy in ((-1, -1.15, 1.50), (1, -0.70, 1.10)):           # columns, walking stride
        B += [("c", (sx * 0.50, -0.85, 1.55), (sx * 0.50, fy, 0.22), 0.31, 0.245),
              ("s", (sx * 0.50, fy - 0.04, 0.13), (0.275, 0.30, 0.15)),
              ("c", (sx * 0.48, 1.25, 1.45), (sx * 0.48, hy, 0.22), 0.31, 0.235),
              ("s", (sx * 0.48, hy - 0.04, 0.13), (0.265, 0.29, 0.15))]
        feet += [(sx * 0.50, fy - 0.04, 0.275), (sx * 0.48, hy - 0.04, 0.265)]
    B.append(("t", [(0, 1.92, 2.10), (0, 2.14, 1.70), (0, 2.16, 1.15)], [0.08, 0.06, 0.04]))
    B.append(("s", (0, 2.16, 1.02), (0.07, 0.07, 0.14)))
    body = blob(B, voxel=0.042, smooth=3, mat="MAT_Elephant")
    n = sum(len(p.vertices) - 2 for p in body.data.polygons)
    if n > tris:
        decimated(body, tris / n)
    parts = [body]
    ear = [(0.0, 0.50), (0.30, 0.66), (0.62, 0.52), (0.80, 0.12), (0.72, -0.38), (0.46, -0.78), (0.22, -0.86),
           (0.08, -0.50), (0.0, -0.20)]
    for sx in (-1, 1):                                                                         # ears, fanned out
        e = extrude_poly(ear, 0.07, "MAT_Elephant", bevel=0.02)
        xform(e, T(sx * 0.50, -1.92, 2.42) @ R(-sx * 0.62, "Z") @ T(-0.035, 0, 0))
        parts.append(e)
    for sx in (-1, 1):
        tk = [(sx * 0.30, -2.02, 1.92), (sx * 0.37, -2.48, 1.56), (sx * 0.38, -2.96, 1.48), (sx * 0.33, -3.34, 1.70)]
        parts.append(tube(tk, [0.088, 0.078, 0.058, 0.012], "MAT_Ivory", segs=10, per=6))    # tusks, gold banded
        for t in (0.30, 0.52):
            p = Vector(tk[1]).lerp(Vector(tk[2]), (t - 0.3) / 0.3) if t > 0.3 else Vector(tk[1])
            parts.append(sphere(0.092 - 0.02 * t, tuple(p), trim, scale=(1, 0.45, 1), seg=10))
        parts.append(sphere(0.035, (sx * 0.45, -2.10, 2.40), "MAT_Black", seg=8))             # eyes
    for fx, fy, fr in feet:                                                                    # anklets, toenails
        parts.append(lathe([(fr - 0.01, 0.30), (fr + 0.035, 0.34), (fr - 0.01, 0.38)], trim, 16, T(fx, fy + 0.04, 0)))
        for k in (-1, 0, 1):
            a = math.radians(-90 + k * 32)
            parts.append(sphere(0.055, (fx + (fr + 0.01) * math.cos(a), fy + (fr + 0.03) * math.sin(a), 0.07),
                                "MAT_Ivory", scale=(1, 0.6, 1.1), seg=6))
    # forehead armour (nettipattam): shield of gold scales wrapped onto the brow and down the trunk
    bm = bmesh.new()
    rows = []
    nz, nx = 22, 10
    for j in range(nz + 1):
        v = j / nz
        z = 2.98 - (1.85 if pose == "walk" else 0.98) * v
        w = 0.36 * (1 - 0.70 * v ** 1.3) + 0.03
        rows.append([bm.verts.new((-w + 2 * w * i / nx, -4.2 if pose == "walk" else -2.95, z)) for i in range(nx + 1)])
    for j in range(nz):
        for i in range(nx):
            f = bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
            f.material_index = 1 if (i in (0, nx - 1) or j % 4 == 3) else 0
    plate = obj_from_bm(bm, trim)
    plate.data.materials.append(M("MAT_Red"))
    sw = plate.modifiers.new("wrap", "SHRINKWRAP")
    sw.target = body
    sw.wrap_method = "PROJECT"
    sw.use_project_x, sw.use_project_y, sw.use_project_z = False, True, False
    sw.use_positive_direction, sw.use_negative_direction = True, False
    sw.offset = 0.035
    sol = plate.modifiers.new("t", "SOLIDIFY")
    sol.thickness = 0.03
    apply_modifiers(plate)
    bm = bmesh.new()
    bm.from_mesh(plate.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -3.9], context="VERTS")   # rows that hit nothing
    bm.to_mesh(plate.data)
    bm.free()
    parts.append(plate)
    parts.append(lathe([(0.0, 0.10), (0.10, 0.08), (0.15, 0.03), (0.20, 0.0), (0.0, 0.0)], trim, 16,
                       T(0, -2.50, 2.42) @ R(math.radians(70), "X")))                          # brow boss
    # bell collar, girths and the caparison with a gold fringe
    parts.append(ring((0, -1.30, 2.12), 0.84, 0.98, 0.05, trim, 30))
    for i in range(11):
        a = math.radians(-165 + i * 15)
        b = P.bell(trim, 4.0)
        xform(b, T(0.87 * math.cos(a), -1.33, 2.12 + 1.01 * math.sin(a)))
        parts.append(b)
    hem = 1.12
    cap = drape(_el_surf, -0.55, 1.75, _el_halfw, hem, st["cloth"], trim, ny=34, ntop=26, ndrop=10, lift=0.045,
                border=0.16)
    parts.append(cap)
    inner = drape(_el_surf, -0.20, 1.40, _el_halfw, hem + 0.30, st["cloth2"], trim, ny=20, ntop=20, ndrop=7,
                  lift=0.075, border=0.10)
    parts.append(inner)
    for sx in (-1, 1):
        for i in range(24):                                                                    # scale fringe
            y = -0.50 + i * (2.20 / 23)
            leaf = sphere(1.0, (0, 0, 0), trim, scale=(0.02, 0.055, 0.10), seg=6)
            xform(leaf, T(sx * (_el_halfw(y) + 0.06), y, hem - 0.07))
            parts.append(leaf)
        parts.append(lathe([(0.0, 0.07), (0.10, 0.06), (0.16, 0.02), (0.30, 0.015), (0.33, 0.0), (0.0, 0.0)], trim, 20,
                           T(sx * (_el_halfw(0.6) + 0.085), 0.60, 1.78) @ R(sx * math.pi / 2, "Y")))   # medallion
    for y in (-0.42, 1.60):
        parts.append(ring((0, y, 1.95), _el_halfw(y) + 0.07, 0.96, 0.045, st["wood"], 30))    # girth ropes
    if tower:
        hd = howdah(st)
        top = max(_el_surf(0, 0.1), _el_surf(0, 0.9))
        xform(hd, T(0, 0.50, top - 0.02))
        parts.append(hd)
    return join(parts, f"elephant_{style}")

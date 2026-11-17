#!/usr/bin/env python3
"""Free 3D layout of the 22 shots of ep01 (Arjuna vs Karna). No paid generation.

Builds the duel on the Kurukshetra field from the existing hero models (world/kurukshetra/hero),
poses simple colour-coded mannequins for @arjuna, @arjuna_bare, @krishna, @karna and Shalya,
sets one real camera per shot card and renders one still per shot with Cycles on the CPU.
The stills fix composition, lens and screen direction. They are the layout input for the
paint-over step. They are NOT the final look.

  pip install bpy pillow
  python studio/tools/layout_blender.py --models <dir with SM_krk_*.blend> --out <dir> [--only A02,A16] [--blend]

Screen direction (bible): Arjuna and Krishna on the LEFT facing right (+X), Karna on the RIGHT
facing left (-X), cameras on the -Y side, low sun behind Karna.
"""
import argparse, json, math, random, sys
from pathlib import Path

import bpy, bmesh
from mathutils import Vector, Matrix

HERE = Path(__file__).resolve().parent
EP = HERE.parent / "episodes" / "ep01_arjuna_vs_karna"

# ---------------------------------------------------------------- colours
def hexc(h):
    h = h.lstrip("#")
    return tuple(pow(int(h[i:i + 2], 16) / 255, 2.2) for i in (0, 2, 4)) + (1,)

PAL = dict(
    earth="#B8743C", dust="#E9CF9A", gold="#D9A21B", golddark="#9A6F12", black="#14110E",
    skin="#7A4A2B", white="#F2EEE2", green="#1F5A3C", saffron="#E9982A", crimson="#8E1B2A",
    blue="#8C96C8", grey="#9A9A98", bronze="#8A5A2B", wood="#5A3A22", hair="#17120F",
    e_blue="#6FC3FF", e_gold="#FFB02E", e_white="#FFF6D8", e_red="#FF4A1E", e_green="#7CFF6A",
)
_mats = {}

def mat(name):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new("LAY_" + name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    col = hexc(PAL[name])
    if name.startswith("e_"):
        nt.nodes.remove(bsdf)
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs[0].default_value = col
        em.inputs[1].default_value = 12 if name == "e_white" else 3.5
        nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs[0])
    else:
        bsdf.inputs["Base Color"].default_value = col
        bsdf.inputs["Roughness"].default_value = 0.45 if "gold" in name else 0.8
        bsdf.inputs["Metallic"].default_value = 0.7 if "gold" in name else 0.0
    _mats[name] = m
    return m

# ---------------------------------------------------------------- mesh builder
class Build:
    """Collects primitives into one mesh with several material slots."""

    def __init__(self, name):
        self.name, self.bm, self.slots = name, bmesh.new(), []

    def _slot(self, m):
        if m not in self.slots:
            self.slots.append(m)
        return self.slots.index(m)

    def _tag(self, geom, m):
        i = self._slot(m)
        for f in geom:
            if isinstance(f, bmesh.types.BMFace):
                f.material_index = i

    def cyl(self, a, b, r0, r1=None, m="gold", seg=10):
        a, b = Vector(a), Vector(b)
        r1 = r0 if r1 is None else r1
        d = b - a
        if d.length < 1e-5:
            return
        rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        mtx = Matrix.Translation((a + b) / 2) @ rot
        g = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=d.length, matrix=mtx)
        self._tag([f for v in g["verts"] for f in v.link_faces], m)

    def ball(self, c, r, m="skin", sx=1, sy=1, sz=1):
        mtx = Matrix.Translation(Vector(c)) @ Matrix.Diagonal((sx, sy, sz, 1))
        g = bmesh.ops.create_uvsphere(self.bm, u_segments=12, v_segments=8, radius=r, matrix=mtx)
        self._tag([f for v in g["verts"] for f in v.link_faces], m)

    def quad(self, pts, m):
        vs = [self.bm.verts.new(Vector(p)) for p in pts]
        f = self.bm.faces.new(vs)
        f.material_index = self._slot(m)

    def done(self, coll, loc=(0, 0, 0), rz=0.0, rot=None):
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for s in self.slots:
            me.materials.append(mat(s))
        ob = bpy.data.objects.new(self.name, me)
        ob.location = loc
        ob.rotation_euler = rot if rot else (0, 0, rz)
        coll.objects.link(ob)
        return ob

def ik(s, h, l1, l2, hint):
    """Elbow or knee for a two-bone limb from s to h, bent toward hint."""
    s, h, hint = Vector(s), Vector(h), Vector(hint)
    d = h - s
    L = min(d.length, (l1 + l2) * 0.999)
    if L < 1e-4:
        return s + hint.normalized() * l1, s
    dn = d.normalized()
    h = s + dn * L
    a = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    hgt = math.sqrt(max(l1 * l1 - a * a, 0))
    side = hint - dn * hint.dot(dn)
    side = side.normalized() if side.length > 1e-4 else Vector((0, 0, -1))
    return s + dn * a + side * hgt, h

# ---------------------------------------------------------------- figures
COSTUME = dict(
    arjuna=dict(skin="skin", torso="gold", legs="white", sash="green", crown="tall", bow="black"),
    arjuna_bare=dict(skin="skin", torso="gold", legs="white", sash="green", crown="band", bow="black"),
    karna=dict(skin="skin", torso="gold", legs="saffron", sash="black", crown="round", bow="black", disc=False)   # sai 2026-11-17: nothing on his back,
    krishna=dict(skin="blue", torso="gold", legs="crimson", sash="gold", crown="feather"),
    shalya=dict(skin="skin", torso="bronze", legs="grey", sash="black", crown="round", beard=True),
)

# Poses are written for a figure that faces +X (left hand is +Y). Hands and feet are targets in metres.
POSES = dict(
    idle=dict(lh=(0.22, 0.30, 0.95), rh=(0.05, -0.30, 0.86), bow="low"),
    draw=dict(lh=(0.70, 0.10, 1.46), rh=(-0.06, -0.14, 1.56), lf=(0.30, 0.12, 0), rf=(-0.32, -0.12, 0), bow="drawn"),
    drawn_up=dict(lh=(0.62, 0.10, 1.74), rh=(-0.10, -0.14, 1.52), lf=(0.30, 0.12, 0), rf=(-0.32, -0.12, 0), bow="drawn", lean=-0.12),
    loosed=dict(lh=(0.70, 0.10, 1.46), rh=(-0.22, -0.22, 1.60), lf=(0.30, 0.12, 0), rf=(-0.32, -0.12, 0), bow="held"),
    salute=dict(lh=(0.24, 0.14, 1.74), rh=(0.24, -0.14, 1.74), bow="salute", head=(0.0, 0.0, 0.25)),
    reins=dict(lh=(0.46, 0.14, 0.84), rh=(0.46, -0.14, 0.84), lean=0.14, drop=0.42, lf=(0.40, 0.13, 0), rf=(0.40, -0.13, 0), reins=True),
    press=dict(lh=(0.50, 0.16, 1.02), rh=(0.50, -0.16, 1.02), lean=0.42, drop=0.22, lf=(-0.15, 0.14, 0), rf=(0.42, -0.10, 0), reins=True),
    quiver=dict(lh=(0.45, 0.24, 1.20), rh=(-0.16, -0.10, 1.74), bow="held"),
    recoil=dict(lh=(0.25, 0.42, 1.15), rh=(-0.20, -0.45, 1.25), lean=-0.38, drop=0.12, bow="held", head=(0, 0, -0.2)),
    bind=dict(lh=(0.30, 0.26, 1.20), rh=(0.02, -0.16, 1.78), head=(0, 0, -0.1), bow="held"),   # one hand pushes his hair back, the other lifts the bow
    heave=dict(lh=(0.50, 0.26, 0.86), rh=(0.50, -0.26, 0.60), lean=0.75, drop=0.30, lf=(0.20, 0.16, 0), rf=(-0.55, -0.16, 0)),
    palm=dict(lh=(0.10, 0.34, 0.70), rh=(0.56, -0.16, 1.26), lean=0.15, drop=0.42, lf=(0.30, 0.14, 0), rf=(-0.40, -0.14, 0)),
    stand=dict(lh=(0.10, 0.38, 0.92), rh=(0.10, -0.38, 0.92)),
    lower=dict(lh=(0.26, 0.26, 0.90), rh=(0.02, -0.28, 0.86), bow="rest", head=(0, 0, -0.12)),
    look_up=dict(lh=(0.20, 0.20, 1.00), rh=(0.20, -0.20, 1.00), head=(0, 0, 0.5)),
)

def figure(coll, who, pose, loc, face=0.0, name=None, scale=1.0):
    c, p = COSTUME[who], POSES[pose]
    b = Build(name or f"FIG_{who}_{pose}")
    lean, drop = p.get("lean", 0.0), p.get("drop", 0.0)
    pel = Vector((0, 0, 0.98 - drop))
    up = Vector((math.sin(lean), 0, math.cos(lean)))
    chest, neck = pel + up * 0.46, pel + up * 0.60
    hd = Vector(p.get("head", (0, 0, 0)))
    head = neck + (up + hd * 0.3).normalized() * 0.14
    sh = [chest + up * 0.08 + Vector((0, s * 0.22, 0)) for s in (1, -1)]
    hip = [pel + Vector((0, s * 0.11, 0)) for s in (1, -1)]
    # legs (cloth), feet
    for i, key in enumerate(("lf", "rf")):
        foot = Vector(p.get(key, (0.02, (0.13, -0.13)[i], 0))) + Vector((0, 0, 0.05))
        knee, foot = ik(hip[i], foot, 0.47, 0.47, (1, 0, 0.2))
        b.cyl(hip[i], knee, 0.13, 0.10, c["legs"])
        b.cyl(knee, foot, 0.10, 0.07, c["legs"])
        b.ball(foot + Vector((0.07, 0, 0)), 0.07, "black", sx=1.6, sz=0.6)
    # pelvis sash, torso, neck, head
    b.cyl(pel - up * 0.10, pel + up * 0.08, 0.19, 0.18, c["sash"], seg=14)
    b.cyl(pel + up * 0.08, chest + up * 0.10, 0.17, 0.21, c["torso"], seg=14)
    b.cyl(chest + up * 0.10, neck + up * 0.03, 0.06, 0.055, c["skin"])
    b.ball(head, 0.115, c["skin"], sz=1.15)
    fwd = Vector((1, 0, 0))
    b.ball(head + fwd * 0.10 + Vector((0, 0, -0.01)), 0.03, c["skin"])          # nose, shows facing
    if c.get("beard"):
        b.ball(head + fwd * 0.07 + Vector((0, 0, -0.10)), 0.07, "grey")
    top = head + up * 0.10
    if c["crown"] == "tall":
        b.cyl(top - up * 0.03, top + up * 0.30, 0.125, 0.03, "gold", seg=12)
        b.ball(top + fwd * 0.11 + up * 0.02, 0.025, "crimson")
    elif c["crown"] == "round":
        b.ball(top + up * 0.02, 0.135, "gold", sz=0.9)
        b.cyl(top + up * 0.10, top + up * 0.24, 0.04, 0.02, "gold")
        b.cyl(top + fwd * 0.12 + up * 0.03, top + fwd * 0.14 + up * 0.03, 0.06, 0.06, "gold")
    elif c["crown"] == "feather":
        b.cyl(top - up * 0.03, top + up * 0.24, 0.125, 0.07, "gold", seg=12)
        b.cyl(top + Vector((0.08, 0.06, 0.10)), top + Vector((0.10, 0.10, 0.38)), 0.035, 0.01, "green")
    elif c["crown"] == "band":
        b.ball(top - up * 0.04, 0.125, "hair")                # bare head, loose hair, no cloth band (sai, 2026-11-16)
        b.ball(head - Vector((0.07, 0, 0.02)), 0.12, "hair")
    if c.get("disc"):
        back = chest - fwd * 0.24 + up * 0.02
        b.cyl(back, back - fwd * 0.03, 0.26, 0.26, "gold", seg=20)
    # arms
    hands = []
    for i, key in enumerate(("lh", "rh")):
        elbow, hand = ik(sh[i], p[key], 0.31, 0.29, (-0.3, (1, -1)[i] * 0.6, -1))
        b.ball(sh[i], 0.085, "gold")
        b.cyl(sh[i], elbow, 0.055, 0.048, c["skin"])
        b.cyl(elbow, hand, 0.050, 0.040, "gold")
        b.ball(hand, 0.05, c["skin"])
        hands.append(hand)
    lh, rh = hands
    # bow, string, arrow
    mode = p.get("bow") if c.get("bow") else None
    if mode:
        if mode == "salute":
            mid, axis, belly = (lh + rh) / 2 + Vector((0.02, 0, 0.02)), Vector((0, 1, 0)), Vector((1, 0, 0))
        elif mode == "low":
            mid, axis, belly = lh, Vector((0.25, 0, 1)).normalized(), Vector((1, 0, -0.25)).normalized()
        elif mode == "rest":
            mid, axis, belly = lh, Vector((0.35, 0, 1)).normalized(), Vector((1, 0, -0.35)).normalized()
        else:
            aim = (lh - rh).normalized() if mode == "drawn" else Vector((1, 0, 0.05)).normalized()
            mid, belly = lh, aim
            axis = Vector((0, 0.12, 1)) - aim * aim.z
            axis.normalize()
        pts = []
        for k in range(-6, 7):
            t = k / 6
            pts.append(mid + axis * (0.98 * t) - belly * (0.30 * t * t) + belly * 0.02)
        for a, bb in zip(pts, pts[1:]):
            b.cyl(a, bb, 0.022, 0.022, "black", seg=6)
        for k in (1, 3, 5, 7, 9, 11):
            b.ball(pts[k], 0.03, "gold")
        if mode == "drawn":
            b.cyl(pts[0], rh, 0.006, 0.006, "white", seg=4)
            b.cyl(rh, pts[-1], 0.006, 0.006, "white", seg=4)
            tip = lh + (lh - rh).normalized() * 0.28
            b.cyl(rh, tip, 0.010, 0.010, "wood", seg=5)
            b.cyl(tip, tip + (lh - rh).normalized() * 0.10, 0.03, 0.0, "white", seg=6)
        else:
            b.cyl(pts[0], pts[-1], 0.006, 0.006, "white", seg=4)
    if p.get("reins"):
        for h in (lh, rh):
            b.cyl(h, h + Vector((2.6, h.y * 4.0, 0.25)), 0.012, 0.012, "black", seg=4)
    ob = b.done(coll, loc, face)
    ob.scale = (scale, scale, scale)
    return ob

# ---------------------------------------------------------------- props
def arrow(b, tail, tip, m="wood", r=0.012, head="white"):
    tail, tip = Vector(tail), Vector(tip)
    d = (tip - tail).normalized()
    b.cyl(tail, tip, r, r, m, seg=5)
    b.cyl(tip, tip + d * (r * 9), r * 3, 0.0, head, seg=6)
    b.quad([tail, tail + Vector((0, 0, r * 5)) + d * r * 8, tail + d * r * 14], "white")

def banner(coll, base, height=5.6, cut=None, name="PROP_karna_banner", flag="gold", fx=1.0):
    """Karna's standard: a plain gold flag on a pole. cut = fraction where the pole is cut (A18)."""
    b = Build(name)
    base = Vector(base)
    top = base + Vector((0, 0, height))
    if cut is None:
        b.cyl(base, top, 0.045, 0.035, "golddark")
        f0 = top - Vector((0, 0, 0.1))
        b.quad([f0, f0 + Vector((1.9 * fx, 0.0, -0.15)), f0 + Vector((1.8 * fx, 0.0, -1.25)), f0 + Vector((0, 0, -1.2))], flag)
        b.ball(top, 0.10, "gold")
    else:
        mid = base + Vector((0, 0, height * cut))
        b.cyl(base, mid, 0.045, 0.04, "golddark")
        # falling upper part, tipped toward -X and -Y
        d = Vector((-0.62, -0.25, 0.74)).normalized()
        m2 = mid + Vector((-0.25, -0.1, 0.25))
        t2 = m2 + d * (height * (1 - cut))
        b.cyl(m2, t2, 0.04, 0.035, "golddark")
        side = Vector((-0.55, -0.2, -0.8)).normalized()
        b.quad([t2, t2 + side * 1.9, t2 + side * 1.9 - d * 1.2, t2 - d * 1.2], "gold")
        b.ball(t2, 0.10, "gold")
    return b.done(coll)

# ---------------------------------------------------------------- scene
class Stage:
    def __init__(self, models, res=(1600, 900), samples=24):
        self.models = Path(models)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.sc = bpy.context.scene
        sc = self.sc
        sc.render.engine = "CYCLES"
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 3
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.image_settings.file_format = "PNG"
        try:
            sc.view_settings.view_transform = "Standard"
        except Exception:
            pass
        self.base = bpy.data.collections.new("BASE")
        sc.collection.children.link(self.base)
        self.cache = {}
        self._world()
        self._ground()
        self._armies()

    # sky: gradient from horizon to zenith, plus a sun lamp and a visible sun disc behind Karna
    def _world(self):
        w = bpy.data.worlds.new("LAY_world")
        self.sc.world = w
        w.use_nodes = True
        nt = w.node_tree
        bg = nt.nodes["Background"]
        geo = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(geo.outputs["Generated"], sep.inputs[0])
        nt.links.new(sep.outputs["Z"], ramp.inputs[0])
        nt.links.new(ramp.outputs[0], bg.inputs[0])
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[1].position = 0.45
        self.ramp, self.bg = ramp, bg
        self.sun_dir = Vector((200, 300, 58)).normalized()
        sd = bpy.data.lights.new("LAY_sun", "SUN")
        sd.angle = math.radians(4)
        self.sun = bpy.data.objects.new("LAY_sun", sd)
        self.sun.rotation_euler = (-self.sun_dir).to_track_quat("-Z", "Y").to_euler()
        self.base.objects.link(self.sun)
        fd = bpy.data.lights.new("LAY_fill", "SUN")
        fd.angle = math.radians(40)
        self.fill = bpy.data.objects.new("LAY_fill", fd)
        self.fill.rotation_euler = (math.radians(55), 0, math.radians(-25))   # from the camera side
        self.base.objects.link(self.fill)
        b = Build("LAY_sun_disc")
        b.ball(self.sun_dir * 900, 42, "e_white")
        self.disc = b.done(self.base)
        self.disc.visible_shadow = False
        self.sky()

    def sky(self, horizon="#F4E6C8", zenith="#A9C4DD", strength=1.0, sun=4.0, fill=1.6, disc=True):
        e = self.ramp.color_ramp.elements
        e[0].color, e[1].color = hexc(horizon), hexc(zenith)
        self.bg.inputs[1].default_value = strength
        self.sun.data.energy, self.fill.data.energy = sun, fill
        self.sun.data.color = (1.0, 0.86, 0.66)
        self.disc.hide_render = not disc

    def _ground(self):
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=90, y_segments=90, size=320)
        rnd = random.Random(7)
        for v in bm.verts:
            r = math.hypot(v.co.x, v.co.y)
            if r > 30:
                v.co.z = (rnd.random() - 0.5) * 0.5 + 0.9 * math.sin(v.co.x * 0.045) * math.cos(v.co.y * 0.05)
        me = bpy.data.meshes.new("LAY_ground")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat("earth"))
        self.ground = bpy.data.objects.new("LAY_ground", me)
        self.base.objects.link(self.ground)

    def mesh(self, name):
        if name not in self.cache:
            with bpy.data.libraries.load(str(self.models / f"{name}.blend")) as (src, dst):
                dst.objects = [name]
            self.cache[name] = dst.objects[0].data
        return self.cache[name]

    def open_chariot_mesh(self, model):
        """A hero chariot without its parasol and banner, so the crew reads clearly in the layout.
        Banners are added as props; the paint-over prompt puts the parasol back where the paintings have one."""
        if "open_" + model not in self.cache:
            me = self.mesh(model).copy()
            bm = bmesh.new()
            bm.from_mesh(me)
            seen, kill = set(), []
            for v in bm.verts:
                if v.index in seen:
                    continue
                st, comp = [v], []
                seen.add(v.index)
                while st:
                    a = st.pop()
                    comp.append(a)
                    for e in a.link_edges:
                        o = e.other_vert(a)
                        if o.index not in seen:
                            seen.add(o.index)
                            st.append(o)
                xs = [c.co.x for c in comp]; ys = [c.co.y for c in comp]; zs = [c.co.z for c in comp]
                cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
                if max(zs) > 2.95 or min(zs) > 2.2:
                    kill += comp
            bmesh.ops.delete(bm, geom=kill, context="VERTS")
            bm.to_mesh(me)
            bm.free()
            self.cache["open_" + model] = me
        return self.cache["open_" + model]

    def place(self, coll, me, loc, rz=0.0, name=None, rot=None, scale=1.0):
        ob = bpy.data.objects.new(name or me.name, me)
        ob.location = loc
        ob.rotation_euler = rot if rot else (0, 0, rz)
        ob.scale = (scale,) * 3
        coll.objects.link(ob)
        return ob

    def _armies(self):
        rnd = random.Random(11)
        kinds = dict(
            p=[self.mesh("SM_krk_pandava_archer"), self.mesh("SM_krk_pandava_archer_b")],
            k=[self.mesh("SM_krk_kaurava_soldier"), self.mesh("SM_krk_kaurava_soldier_b")],
        )
        n = 0
        for ring in range(14):
            r = 34 + ring * 2.6
            steps = int(2 * math.pi * r / 1.5)
            for i in range(steps):
                a = 2 * math.pi * i / steps
                x, y = r * math.cos(a) + rnd.uniform(-0.4, 0.4), r * math.sin(a) + rnd.uniform(-0.4, 0.4)
                if y < -6 and abs(x) < 30 + (-(y) - 6) * 1.1:   # open wedge for the wide cameras
                    continue
                if abs(x) < 2.5:                                 # lane between the two hosts
                    continue
                side = "p" if x < 0 else "k"
                self.place(self.base, rnd.choice(kinds[side]), (x, y, 0.3), math.atan2(-y, -x) + math.pi / 2 + rnd.uniform(-0.2, 0.2), name=f"ARMY_{n}")
                n += 1
        ele = dict(p=self.mesh("SM_krk_war_elephant"), k=self.mesh("SM_krk_war_elephant_red"))
        rc = dict(p=self.mesh("SM_krk_rank_chariot"), k=self.mesh("SM_krk_rank_chariot_red"))
        for i in range(26):
            a = rnd.uniform(0.15, math.pi - 0.15) if i % 3 else rnd.choice([rnd.uniform(-0.5, 0.1), rnd.uniform(math.pi - 0.1, math.pi + 0.5)])
            r = rnd.uniform(40, 66)
            x, y = r * math.cos(a), r * math.sin(a)
            side = "p" if x < 0 else "k"
            self.place(self.base, (ele if i % 2 else rc)[side], (x, y, 0.3), math.atan2(-y, -x) + math.pi / 2, name=f"ARMYBIG_{i}")
        ban = self.mesh("SM_krk_ape_banner")
        for i in range(10):
            a = math.pi - 0.9 + i * 0.2
            self.place(self.base, ban, (46 * math.cos(a), 46 * math.sin(a), 0.3), 0, name=f"ARMYBAN_{i}", scale=0.8)
        self.army_count = n

# chariot helpers: model forward is -Y. heading +X needs rz=+90 deg, heading -X needs rz=-90 deg.
def chariot(st, coll, who, x, sink=0.0, roll=0.0, pitch=0.0, horses=True, kneel=0.0, y=0.0):
    if who == "arjuna":
        me, hm, rz = st.open_chariot_mesh("SM_krk_arjuna_chariot"), st.mesh("SM_krk_horse_team"), math.radians(90)
    else:
        me, hm, rz = st.open_chariot_mesh("SM_krk_duryodhana_chariot"), st.mesh("SM_krk_horse_team_dark"), math.radians(-90)
    ob = st.place(coll, me, (x, y, -sink), name=f"CHARIOT_{who}", rot=(roll, pitch, rz))
    if horses:
        st.place(coll, hm, (x, y, -kneel), name=f"HORSES_{who}", rot=(math.radians(-10) if kneel else 0, 0, rz))
    return ob

def spot(who, x, sink=0.0, y=0.0):
    """World positions on a chariot: warrior, driver, left rear wheel hub, banner base."""
    s = 1 if who == "arjuna" else -1          # arjuna heads +X, karna heads -X
    return dict(
        warrior=Vector((x - s * 0.35, y, 1.07 - sink)),
        driver=Vector((x + s * 1.0, y, 0.85 - sink)),
        wheel=Vector((x - s * 1.15, y + s * 1.14, 0.96 - sink)),     # left rear wheel hub
        wheel_cam=Vector((x - s * 1.15, y - 1.14, 0.96 - sink)),     # the rear wheel on the camera side
        banner=Vector((x - s * 2.2, y + 0.55, 1.03 - sink)),
        face=0.0 if who == "arjuna" else math.pi,
    )

def crews(st, coll, ax, kx, arj=("arjuna", "idle"), kri="reins", kar=("karna", "idle"), shalya=True, asink=0.0, ksink=0.0, karna_banner=True):
    A, K = spot("arjuna", ax, asink), spot("karna", kx, ksink)
    out = {}
    if arj:
        out["arjuna"] = figure(coll, arj[0], arj[1], A["warrior"], A["face"])
    if kri:
        out["krishna"] = figure(coll, "krishna", kri, A["driver"], A["face"])
    if kar:
        out["karna"] = figure(coll, kar[0], kar[1], K["warrior"], K["face"])
    if shalya:
        out["shalya"] = figure(coll, "shalya", "reins", K["driver"], K["face"])
    banner(coll, A["banner"], name="PROP_arjuna_banner", flag="green", fx=-1.0)
    if karna_banner:
        banner(coll, K["banner"])
    return out

# ---------------------------------------------------------------- shots
FAR, NEAR = 12.0, 6.5       # half-distance between the chariots: acts I-II, acts III-IV

def base_duel(st, coll, d=FAR, **kw):
    chariot(st, coll, "arjuna", -d, sink=kw.get("asink", 0.0), kneel=kw.pop("akneel", 0.0))
    chariot(st, coll, "karna", d, sink=kw.get("ksink", 0.0))
    return crews(st, coll, -d, d, **kw)

def head(v):
    return v + Vector((0, 0, 1.62))

def volley(coll, start, end, n, spread=1.2, seed=1, m="wood", headm="white", length=0.95, name="PROP_arrows", arc=2.0, r=0.012):
    rnd, b = random.Random(seed), Build(name)
    start, end = Vector(start), Vector(end)
    for i in range(n):
        t = rnd.uniform(0.05, 0.95)
        p = start.lerp(end, t) + Vector((0, rnd.uniform(-spread, spread), rnd.uniform(-spread, spread) * 0.6 + arc * 4 * t * (1 - t)))
        d = (end - start).normalized() + Vector((0, 0, arc * 0.15 * (1 - 2 * t)))
        d.normalize()
        arrow(b, p - d * length, p, m, r=r, head=headm)
    return b.done(coll)

def shot_A01(st, c):
    st.sky("#050506", "#020203", strength=0.02, sun=0, fill=0, disc=False)
    b = Build("PROP_clash")
    arrow(b, (-0.9, 0, 1.6), (-0.055, 0, 1.6), "e_blue", r=0.005, head="e_blue")
    arrow(b, (0.9, 0, 1.6), (0.055, 0, 1.6), "e_gold", r=0.005, head="e_gold")
    b.ball((0, 0, 1.6), 0.014, "e_white")
    b.done(c)
    return dict(cam=(0, -1.6, 1.6), at=(0, 0, 1.6), lens=100, solo=True)

def shot_A02(st, c):
    base_duel(st, c)
    return dict(cam=(0, -27, 1.7), at=(0, 0, 4.2), lens=24)

def shot_A03(st, c):
    f = base_duel(st, c, kar=("karna", "salute"))
    k = spot("karna", FAR)["warrior"]
    return dict(cam=k + Vector((-3.3, -4.5, 1.15)), at=head(k) + Vector((0, 0, -0.12)), lens=85)

def shot_A04(st, c):
    base_duel(st, c, arj=("arjuna", "draw"))
    a = spot("arjuna", -FAR)["warrior"]
    return dict(cam=a + Vector((3.3, -4.5, 1.15)), at=head(a) + Vector((0, 0, -0.12)), lens=85)

def shot_A05(st, c):
    base_duel(st, c, kri="reins")
    return dict(cam=(-5.2, -2.9, 0.55), at=(-9.4, 0.0, 1.45), lens=18)

def shot_A06(st, c):
    # first frame of the shot card: Karna at full draw, seven arrows nocked as a fan, the sun behind him.
    base_duel(st, c, kar=("karna", "draw"), arj=("arjuna", "draw"))
    k = spot("karna", FAR)["warrior"]
    rh, lh = k + Vector((0.06, 0.14, 1.56)), k + Vector((-0.70, -0.10, 1.46))     # his hands in the draw pose, facing -X
    aim = (lh - rh).normalized()
    b = Build("PROP_fan")
    for i in (-3, -2, -1, 1, 2, 3):
        d = (aim + Vector((0, 0, math.tan(math.radians(6.5 * i))))).normalized()
        arrow(b, rh, rh + d * 1.05, "wood", r=0.010, head="e_gold")
    b.done(c)
    return dict(cam=k + Vector((-3.3, -3.4, 1.05)), at=head(k) + Vector((-0.55, 0, -0.12)), lens=35)

def shot_A07(st, c):
    base_duel(st, c, arj=("arjuna", "loosed"), kar=("karna", "draw"))
    volley(c, (-10.5, 0, 2.7), (-3.5, 0, 3.0), 9, spread=0.5, seed=3, headm="e_blue", name="PROP_arjuna_arrows", arc=0.3, r=0.014)
    volley(c, (4.0, 0, 3.0), (-3.0, 0, 3.0), 9, spread=0.5, seed=4, headm="e_gold", name="PROP_karna_arrows", arc=0.3, r=0.014)
    b = Build("PROP_hits")
    for x in (-3.6, -2.4, -1.4):
        b.ball((x, random.Random(int(x * 10)).uniform(-0.4, 0.4), 3.0), 0.12, "e_white")
    b.done(c)
    return dict(cam=(-5.6, -10.5, 2.1), at=(-7.8, 0, 2.9), lens=35)

def shot_A08(st, c):
    st.sky("#8E7B62", "#3C4654", strength=0.55, sun=1.2, fill=0.8, disc=False)
    base_duel(st, c, arj=("arjuna", "drawn_up"), kar=("karna", "drawn_up"))
    volley(c, (-11, 0, 4), (11, 0, 4), 260, spread=9, seed=5, headm="e_blue", name="PROP_net_a", arc=5.5, r=0.03, length=1.4)
    volley(c, (11, 0, 4), (-11, 0, 4), 260, spread=9, seed=6, headm="e_gold", name="PROP_net_k", arc=5.5, r=0.03, length=1.4)
    return dict(cam=(0, -9, 44), at=(0, 1.5, 0), lens=24)

def shot_A09(st, c):
    st.sky("#6B5A47", "#2B323D", strength=0.4, sun=1.0, fill=1.2, disc=False)
    base_duel(st, c, arj=("arjuna", "idle"), kar=("karna", "idle"))
    a, k = spot("arjuna", -FAR)["warrior"], spot("karna", FAR)["warrior"]
    return dict(split=[dict(cam=a + Vector((3.6, -1.9, 1.5)), at=head(a), lens=85),
                       dict(cam=k + Vector((-3.6, -1.9, 1.5)), at=head(k), lens=85)])

def shot_A10(st, c):
    base_duel(st, c, kar=("karna", "quiver"))
    k = spot("karna", FAR)["warrior"]
    b = Build("PROP_snake_arrow")
    q0 = k + Vector((0.30, 0.10, 1.05))
    b.cyl(q0, q0 + Vector((0.10, 0.0, 0.62)), 0.075, 0.085, "gold", seg=12)       # golden quiver on his back
    hand = k + Vector((0.16, 0.10, 1.74))
    tip = hand + Vector((0.02, 0.0, 0.30))
    b.cyl(q0 + Vector((0.08, 0, 0.5)), tip, 0.012, 0.012, "black", seg=6)
    b.ball(tip + Vector((0, 0, 0.05)), 0.04, "green", sz=1.9)                       # serpent head
    b.ball(tip + Vector((-0.03, -0.03, 0.08)), 0.012, "e_green")                    # the eye
    b.done(c)
    return dict(cam=k + Vector((1.25, -1.15, 2.1)), at=tip + Vector((0, 0, -0.10)), lens=100)

def shot_A11(st, c):
    st.sky("#C7502A", "#4A1512", strength=0.8, sun=3.0, fill=1.0)
    base_duel(st, c, kar=("karna", "drawn_up"))
    b = Build("PROP_meteors")
    rnd = random.Random(8)
    for i in range(16):
        p = Vector((rnd.uniform(-10, 40), rnd.uniform(15, 90), rnd.uniform(14, 48)))
        d = Vector((-0.45, -0.1, -0.88))
        b.cyl(p, p - d * rnd.uniform(4, 9), 0.25, 0.02, "e_red", seg=6)
        b.ball(p, 0.4, "e_gold")
    b.done(c)
    k = spot("karna", FAR)["warrior"]
    return dict(cam=k + Vector((-1.5, -2.5, -0.2)), at=head(k) + Vector((-0.2, 0, 0.1)), lens=24)

def shot_A12(st, c):
    st.sky("#C7502A", "#4A1512", strength=0.8, sun=3.0, fill=1.0)
    base_duel(st, c, kar=("karna", "loosed"), arj=("arjuna", "draw"))
    b = Build("PROP_snake_flight")
    k = spot("karna", FAR)["warrior"] + Vector((-0.8, 0, 1.6))
    p = Vector((-1.0, 0, 7.4))
    b.cyl(k, p, 0.05, 0.10, "e_red", seg=6)
    arrow(b, p + Vector((0.9, 0, 0.1)), p + Vector((-0.6, 0, -0.06)), "black", r=0.03, head="e_green")
    b.done(c)
    return dict(cam=(1.5, -30, 1.6), at=(0, 0, 6.0), lens=24)

def shot_A13(st, c):
    base_duel(st, c, d=NEAR, asink=0.45, akneel=0.5, kri="press", arj=("arjuna", "draw"))
    a = spot("arjuna", -NEAR, 0.45)
    return dict(cam=a["driver"] + Vector((2.0, -2.1, 1.45)), at=a["driver"] + Vector((-0.25, 0, 0.75)), lens=18, flag="neg")

def shot_A14(st, c):
    base_duel(st, c, d=NEAR, asink=0.45, akneel=0.5, kri="press", arj=("arjuna_bare", "recoil"))
    a = spot("arjuna", -NEAR, 0.45)["warrior"]
    b = Build("PROP_crown_and_arrow")
    cr = a + Vector((-0.75, 0.1, 2.15))
    b.cyl(cr, cr + Vector((-0.22, 0, 0.26)), 0.125, 0.03, "gold", seg=12)          # the crown, struck off
    arrow(b, a + Vector((1.4, 0.05, 2.0)), a + Vector((-0.35, 0.05, 2.06)), "black", r=0.022, head="e_green")
    b.done(c)
    return dict(cam=a + Vector((2.6, -3.3, 1.75)), at=head(a) + Vector((-0.2, 0, 0.1)), lens=50)

def shot_A15(st, c):
    base_duel(st, c, d=NEAR, asink=0.45, akneel=0.5, arj=("arjuna_bare", "bind"))
    a = spot("arjuna", -NEAR, 0.45)["warrior"]
    return dict(cam=a + Vector((4.2, -2.8, 1.5)), at=head(a) + Vector((0, 0, -0.1)), lens=85)

KROLL = math.radians(14)     # Karna's chariot leans onto its sunk left wheel (the camera side)

def karna_down(st, c, pose, face, arj=("arjuna_bare", "draw"), kri="reins", cut=None):
    chariot(st, c, "arjuna", -NEAR, sink=0.45)
    chariot(st, c, "karna", NEAR, sink=0.50, pitch=KROLL)
    crews(st, c, -NEAR, NEAR, arj=arj, kri=kri, kar=None, shalya=True, asink=0.45, ksink=0.45, karna_banner=False)
    K = spot("karna", NEAR, 0.45)
    banner(c, K["banner"], cut=cut)
    w = K["wheel"] + Vector((0, 0, -0.45))
    pos = Vector((w.x + (0.0 if pose == "heave" else -0.9), w.y - 0.95, 0.0))
    return figure(c, "karna", pose, pos, face), w, pos

def shot_A16(st, c):
    _, w, pos = karna_down(st, c, "heave", math.radians(90))
    # close and low behind Karna, as in painting 37: his back and the sun disc toward the camera, horses running off screen left
    return dict(cam=pos + Vector((-2.3, -3.3, 0.45)), at=w + Vector((-1.2, 0, 0.75)), lens=18, roll=math.radians(7))

def shot_A17(st, c):
    _, w, pos = karna_down(st, c, "palm", math.pi)
    a = spot("arjuna", -NEAR, 0.45)["warrior"]
    cam = a + Vector((-1.3, -0.62, 1.86))
    return dict(cam=cam, at=Vector((cam.x + 10, cam.y + 1.23, pos.z + 1.3)), lens=50)

def shot_A18(st, c):
    _, w, pos = karna_down(st, c, "stand", math.pi, cut=0.55)
    K = spot("karna", NEAR, 0.45)
    top = K["banner"] + Vector((-1.2, -0.5, 5.2))
    cam = top - st.sun_dir * 10
    cam.z = max(cam.z, 0.7)
    return dict(cam=cam, at=top + Vector((0, 0, -0.6)), lens=35, flag="drain")

def shot_A19(st, c):
    karna_down(st, c, "stand", math.pi, cut=0.55)
    a = spot("arjuna", -NEAR, 0.45)["warrior"]
    b = Build("PROP_rings")
    o = a + Vector((0.7, 0.1, 1.46))
    for i, r in enumerate((0.5, 0.9, 1.4)):
        x = o.x + 0.25 * i
        pts = [Vector((x, o.y + r * math.cos(t / 24 * 2 * math.pi), o.z + r * math.sin(t / 24 * 2 * math.pi))) for t in range(25)]
        for p, q in zip(pts, pts[1:]):
            b.cyl(p, q, 0.02, 0.02, "e_blue", seg=4)
    b.done(c)
    return dict(cam=a + Vector((5.6, -4.4, 1.2)), at=head(a) + Vector((0.3, 0, -0.1)), lens=50)

def shot_A20(st, c):
    st.sky("#7A3B1E", "#1A1210", strength=0.25, sun=5.0, fill=0.05)
    _, w, pos = karna_down(st, c, "stand", math.pi, cut=0.55)
    h = pos + Vector((0, 0, 1.35))
    flat = Vector((st.sun_dir.x, st.sun_dir.y, 0)).normalized()
    cam = h - flat * 11
    cam.z = h.z - 11 * (st.sun_dir.z / math.hypot(st.sun_dir.x, st.sun_dir.y))
    cam.z = max(cam.z, 0.35)
    return dict(cam=cam, at=h, lens=50)

def shot_A21(st, c):
    st.sky("#E8792E", "#5B6E8C", strength=0.7, sun=2.5, fill=1.0)
    _, w, pos = karna_down(st, c, "stand", math.pi, arj=("arjuna_bare", "lower"), kri="look_up", cut=0.55)
    bpy.data.objects.remove(_)
    b = Build("PROP_light_column")
    top = pos + st.sun_dir * 150
    b.cyl(pos + Vector((0, 0, 0.1)), top, 0.55, 0.9, "e_white", seg=12)
    b.done(c)
    return dict(cam=(-7.5, -30, 5.5), at=(5.0, 0, 13.5), lens=24)

def shot_A22(st, c):
    st.sky("#E8792E", "#5B6E8C", strength=0.7, sun=2.5, fill=1.2)
    k, w, pos = karna_down(st, c, "stand", math.pi, arj=("arjuna_bare", "lower"), kri="look_up", cut=0.55)
    bpy.data.objects.remove(k)
    b = Build("PROP_light_column")
    b.cyl(pos + Vector((0, 0, 0.1)), pos + st.sun_dir * 150, 0.55, 0.9, "e_white", seg=12)
    b.done(c)
    a = spot("arjuna", -NEAR, 0.45)["warrior"]
    return dict(cam=a + Vector((-2.2, -6.6, 1.25)), at=a + Vector((1.9, 0, 1.45)), lens=50)

SHOTS = {f"A{i:02d}": globals()[f"shot_A{i:02d}"] for i in range(1, 23)}

# ---------------------------------------------------------------- camera and render
def camera(coll, sid, cam, at, lens, roll=0.0):
    cd = bpy.data.cameras.new("CAM_" + sid)
    cd.lens, cd.sensor_width, cd.clip_start, cd.clip_end = lens, 36.0, 0.05, 3000
    ob = bpy.data.objects.new("CAM_" + sid, cd)
    cam, at = Vector(cam), Vector(at)
    ob.location = cam
    q = (at - cam).to_track_quat("-Z", "Y")
    ob.rotation_euler = (q @ Matrix.Rotation(roll, 4, "Z").to_quaternion()).to_euler()
    coll.objects.link(ob)
    return ob

def render(st, path, cam, res=None):
    sc = st.sc
    sc.camera = cam
    if res:
        sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--samples", type=int, default=24)
    ap.add_argument("--blend", action="store_true", help="also save layout.blend with every shot in its own collection")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    want = [s for s in a.only.split(",") if s] or list(SHOTS)
    cards = {s["id"]: s for s in json.loads((EP / "shots.json").read_text())["shots"]}
    st = Stage(a.models, samples=a.samples)
    full = (st.sc.render.resolution_x, st.sc.render.resolution_y)
    meta = {}
    for sid in want:
        coll = bpy.data.collections.new("SHOT_" + sid)
        st.sc.collection.children.link(coll)
        st.sky()
        spec = SHOTS[sid](st, coll)
        st.base.hide_render = bool(spec.get("solo"))
        png = out / f"{sid}.png"
        if "split" in spec:
            from PIL import Image
            halves = []
            for i, sp in enumerate(spec["split"]):
                cam = camera(coll, f"{sid}{'ab'[i]}", sp["cam"], sp["at"], sp["lens"])
                cam.data.sensor_fit = "VERTICAL"
                cam.data.sensor_height = 20.25
                tmp = out / f"_{sid}{'ab'[i]}.png"
                render(st, tmp, cam, (full[0] // 2, full[1]))
                halves.append(Image.open(tmp).convert("RGB"))
                tmp.unlink()
            im = Image.new("RGB", full)
            im.paste(halves[0], (0, 0))
            im.paste(halves[1], (full[0] // 2, 0))
            im.save(png)
            st.sc.render.resolution_x, st.sc.render.resolution_y = full
            cams = spec["split"]
        else:
            cam = camera(coll, sid, spec["cam"], spec["at"], spec["lens"], spec.get("roll", 0.0))
            render(st, png, cam, full)
            cams = [spec]
        meta[sid] = dict(
            card=cards[sid]["camera"], action=cards[sid]["action"], flag=spec.get("flag"),
            cameras=[dict(pos=[round(v, 2) for v in c["cam"]], look_at=[round(v, 2) for v in c["at"]], lens_mm=c["lens"],
                          roll_deg=round(math.degrees(c.get("roll", 0.0)), 1)) for c in cams])
        print("LAYOUT", sid, "ok", flush=True)
        # keep the collection for the .blend, but out of the next render
        coll.hide_render = True
        coll.hide_viewport = True
    (out / "cameras.json").write_text(json.dumps(dict(
        note="Metres. X runs from Arjuna (negative) to Karna (positive), cameras sit on the -Y side, Z is up. 36 mm sensor width.",
        soldiers=st.army_count, shots=meta), indent=1))
    if a.blend:
        st.base.hide_render = False
        bpy.ops.wm.save_as_mainfile(filepath=str(out / "layout.blend"), compress=True)
    print("LAYOUT done", len(want), "shots", flush=True)

if __name__ == "__main__":
    main()

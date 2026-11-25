"""The heroes' bows and arrows, rigged so the string pulls back and the limbs flex. Free, cloud Blender.

  b = Bow.vijaya(path_to_glb)        Karna's bow: his TRELLIS model (karna_bow_1536.glb), 1.55 m
  b = Bow.gandiva()                  Arjuna's bow: built here, silver steel with gold bands, 1.70 m
  b.attach(hero)                     into the hero's LEFT fist (call with the hero posed at full draw, e.g. moves.bow_draw t=1.6)
  b.draw_to(world_point, f)          string centre pulled to a point (clamped to the draw length) and keyed at frame f
  b.rest(f)                          string straight, limbs relaxed
  a = make_arrow("steel"|"gold")     a 0.8 m arrow; a_on_string(a, b, f) keeps it nocked; fly(a, start, dir, t) for the shot

Every bow lives in the same local layout: length along local Z (from -0.5 to 0.5 before scale), grip at the origin,
the string on the +X side (toward the archer), limbs bowing to -X. Two hooks bend it: one pulls the string centre
(string vertices weighted 1 at the centre to 0 at the tips, so it makes a clean V), and one per limb turns that limb
toward the archer in proportion to the draw.
"""
import math
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

DRAW_MAX = 0.74                                                       # longest draw (m)
FLEX = 0.16                                                           # limb turn (radians) at the longest draw


def _mat(name, col, metal=0.0, rough=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    return m


def _hook(obj, name, group, at):
    """a hook empty parented to the bow at local point at, driving the vertex group"""
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
    e.empty_display_size = 0.05
    e.parent = obj; e.matrix_parent_inverse.identity(); e.location = at
    bpy.context.view_layer.update()
    md = obj.modifiers.new(name, "HOOK"); md.object = e; md.vertex_group = group; md.falloff_type = "NONE"
    md.matrix_inverse = e.matrix_world.inverted() @ obj.matrix_world
    md.center = at
    return e


class Bow:
    def __init__(self, obj, length, string_x):
        self.obj, self.length, self.sx = obj, length, string_x
        obj.scale = (length, length, length)
        bpy.context.view_layer.update()
        me = obj.data
        co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
        x, y, z = co[:, 0], co[:, 1], co[:, 2]
        string = (x > string_x - 0.006) & (np.abs(z) < 0.43) & (np.abs(y) < 0.008)
        w_string = np.where(string, np.clip(1 - np.abs(z) / 0.47, 0, 1), 0.0)
        top = np.clip((z - 0.07) / 0.38, 0, 1) ** 1.5                 # the string's ends ride with the limb tips
        bot = np.clip((-z - 0.07) / 0.38, 0, 1) ** 1.5
        for name, w in (("string", w_string), ("limb_top", top), ("limb_bot", bot)):
            g = obj.vertex_groups.new(name=name)
            for wv in np.unique(np.round(w[w > 0.002], 3)):
                idx = np.nonzero(np.abs(np.round(w, 3) - wv) < 1e-6)[0].tolist()
                g.add(idx, float(wv), "REPLACE")
        print("bow", obj.name, "string verts", int(string.sum()), flush=True)
        self.nock0 = Vector((string_x, 0, 0))
        self.top = _hook(obj, obj.name + "_flex_top", "limb_top", Vector((-0.06, 0, 0.07)))
        self.bot = _hook(obj, obj.name + "_flex_bot", "limb_bot", Vector((-0.06, 0, -0.07)))
        self.nock = _hook(obj, obj.name + "_nock", "string", self.nock0)

    # ---- builders ------------------------------------------------------------------------------------------------------------
    @classmethod
    def vijaya(cls, glb):
        bpy.ops.import_scene.gltf(filepath=str(glb))
        o = max((o for o in bpy.context.selected_objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
        o.parent = None; o.rotation_mode = "XYZ"; o.rotation_euler = (0, 0, 0); o.name = "VIJAYA"
        me = o.data
        co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
        c = (co.max(0) + co.min(0)) / 2; c[0] = 0.0                    # centre along the length, keep the grip/string x
        L = float(co[:, 2].max() - co[:, 2].min())
        me.transform(Matrix.Scale(1 / L, 4) @ Matrix.Translation(Vector((0, -c[1], -c[2]))))
        return cls(o, 1.55, 0.107 / L)

    @classmethod
    def gandiva(cls):
        """a long recurve in silver steel, gold bands at the grip and below the tips, leather grip, waxed string"""
        bm = bmesh.new()
        steel, gold, leather, cord = (_mat("gandiva_steel", (0.62, 0.66, 0.72), 0.9, 0.28), _mat("gandiva_gold", (0.85, 0.6, 0.18), 1.0, 0.3),
                                      _mat("gandiva_grip", (0.12, 0.06, 0.03), 0.0, 0.7), _mat("gandiva_string", (0.85, 0.82, 0.72), 0.0, 0.5))
        N, R = 96, 10
        tip_x = 0.095

        def centre(z):
            a = abs(z) * 2                                             # 0 at the grip, 1 at the tips
            return -0.085 + 0.15 * a ** 2.3 + 0.03 * max(0.0, (a - 0.86) / 0.14) ** 2

        def radius(z):
            a = abs(z) * 2
            return (0.018 if a < 0.14 else 0.014 - 0.009 * (a - 0.14) / 0.86, 0.011 - 0.006 * a)

        def band(z):
            a = abs(z) * 2
            if a < 0.14:
                return 2
            if 0.14 <= a < 0.19 or 0.78 < a < 0.83:
                return 1
            return 0
        rings = []
        for i in range(N + 1):
            z = -0.5 + i / N
            dz = 1e-3; t = Vector((centre(z + dz) - centre(z - dz), 0, 2 * dz)).normalized()
            n = Vector((t.z, 0, -t.x))
            rw, rt = radius(z)
            ring = [bm.verts.new(Vector((centre(z), 0, z)) + n * (rt * math.cos(2 * math.pi * k / R)) +
                                 Vector((0, rw * math.sin(2 * math.pi * k / R), 0))) for k in range(R)]
            rings.append((ring, band(z)))
        for (a, ba), (b, _) in zip(rings, rings[1:]):
            for k in range(R):
                f = bm.faces.new((a[k], a[(k + 1) % R], b[(k + 1) % R], b[k])); f.material_index = ba
        for ring, _ in (rings[0], rings[-1]):
            bm.faces.new(ring).material_index = 1
        # string: a thin tube from tip to tip on the +X side
        sr, SN = 0.0018, 60
        sring = []
        for i in range(SN + 1):
            z = -0.47 + 0.94 * i / SN
            sring.append([bm.verts.new(Vector((tip_x + sr * math.cos(2 * math.pi * k / 6), sr * math.sin(2 * math.pi * k / 6), z))) for k in range(6)])
        for a, b in zip(sring, sring[1:]):
            for k in range(6):
                bm.faces.new((a[k], a[(k + 1) % 6], b[(k + 1) % 6], b[k])).material_index = 3
        me = bpy.data.meshes.new("GANDIVA"); bm.to_mesh(me); bm.free()
        for m in (steel, gold, leather, cord):
            me.materials.append(m)
        for p in me.polygons:
            p.use_smooth = True
        o = bpy.data.objects.new("GANDIVA", me); bpy.context.scene.collection.objects.link(o)
        return cls(o, 1.70, tip_x)

    # ---- use -------------------------------------------------------------------------------------------------------------------
    def attach(self, h, side="L"):
        """put the grip in the hero's fist, vertical across it, string toward him; parent to his hand bone"""
        bpy.context.view_layer.update()
        mw = h.rig.matrix_world
        hand = mw @ h.pb[f"DEF-hand.{side}"].matrix
        A = hand.to_3x3().col[1].normalized()                         # along the hand, toward the target
        h.fingers(side, 0)                                             # palm normal from the open hand (a fist turns the finger axes)
        bpy.context.view_layer.update()
        P = (mw @ h.pb[f"f_middle.01.{side}"].matrix).to_3x3().col[2].normalized()
        U = A.cross(P).normalized()
        if U.z < 0:
            U = -U
        X = -A                                                         # string side toward the archer
        Y = U.cross(X).normalized(); X = Y.cross(U).normalized()
        knuck = [mw @ h.pb[f"{f}.01.{side}"].head for f in ("f_index", "f_middle", "f_ring", "f_pinky") if f"{f}.01.{side}" in h.pb]
        G = sum(knuck, Vector()) / len(knuck) + P * 0.028 - A * 0.01
        M = Matrix((X, Y, U)).transposed().to_4x4(); M.translation = G
        M = M @ Matrix.Scale(self.length, 4)
        self.obj.parent = h.rig; self.obj.parent_type = "BONE"; self.obj.parent_bone = f"DEF-hand.{side}"
        bpy.context.view_layer.update()
        self.obj.matrix_world = M
        self.hero = h

    def string_world(self):
        bpy.context.view_layer.update()
        return self.obj.matrix_world @ self.nock0

    def grip_world(self):
        bpy.context.view_layer.update()
        return self.obj.matrix_world @ Vector((-0.06, 0, 0.02))

    def draw_to(self, p, f):
        """pull the string centre to world point p (only along the bow's +X, clamped); bends the limbs; keys frame f"""
        bpy.context.view_layer.update()
        inv = self.obj.matrix_world.inverted()
        lp = inv @ Vector(p)
        d = max(0.0, min(lp.x - self.nock0.x, DRAW_MAX / self.length))
        self.nock.location = (self.nock0.x + d, 0, 0)
        a = FLEX * d / (DRAW_MAX / self.length)
        self.top.rotation_euler = (0, a, 0); self.bot.rotation_euler = (0, -a, 0)
        for e in (self.nock, self.top, self.bot):
            e.keyframe_insert("location", frame=f); e.keyframe_insert("rotation_euler", frame=f)
        return d * self.length

    def rest(self, f):
        self.nock.location = self.nock0; self.top.rotation_euler = (0, 0, 0); self.bot.rotation_euler = (0, 0, 0)
        for e in (self.nock, self.top, self.bot):
            e.keyframe_insert("location", frame=f); e.keyframe_insert("rotation_euler", frame=f)


def make_arrow(kind="steel", length=0.82):
    """an arrow along local +Y, its nock (tail) at the origin; kind picks the head and fletching colours"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.0042, radius2=0.0042, depth=length,
                          matrix=Matrix.Translation((0, length / 2, 0)) @ Matrix.Rotation(-math.pi / 2, 4, "X"))
    head = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.011, radius2=0.0, depth=0.055,
                                 matrix=Matrix.Translation((0, length + 0.02, 0)) @ Matrix.Rotation(-math.pi / 2, 4, "X"))
    fl = []
    for k in range(3):
        r = bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Rotation(2 * math.pi * k / 3, 4, "Y") @
                                  Matrix.Translation((0, 0.08, 0.016)) @ Matrix.Diagonal((0.0012, 0.1, 0.028, 1)))
        fl += r["verts"]
    me = bpy.data.meshes.new("arrow"); bm.to_mesh(me); bm.free()
    shaft = _mat("arrow_shaft", (0.40, 0.27, 0.13), 0.0, 0.6)
    tip = _mat("arrow_head", (0.75, 0.77, 0.8) if kind == "steel" else (0.85, 0.6, 0.2), 0.9, 0.25)
    feather = _mat("arrow_feather", (0.88, 0.85, 0.78) if kind == "steel" else (0.55, 0.1, 0.06), 0.0, 0.7)
    for m in (shaft, tip, feather):
        me.materials.append(m)
    for p in me.polygons:
        c = p.center
        p.material_index = 1 if c.y > length - 0.01 else (2 if abs(c.x) > 0.005 or abs(c.z) > 0.005 and c.y < 0.2 else 0)
    o = bpy.data.objects.new("arrow", me); bpy.context.scene.collection.objects.link(o)
    o.rotation_mode = "QUATERNION"
    return o


def place_arrow(a, tail, toward, f=None):
    """arrow nock at tail, pointing toward the world point toward; keyed at frame f"""
    d = (Vector(toward) - Vector(tail)).normalized()
    a.location = tail; a.rotation_quaternion = Vector((0, 1, 0)).rotation_difference(d)
    if f is not None:
        a.keyframe_insert("location", frame=f); a.keyframe_insert("rotation_quaternion", frame=f)

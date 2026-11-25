"""Scene 01 "Suryaputra" in 3D on the rigged heroes (sai, 2026-11-25: task 1 of 6). Free, cloud Blender (Cycles CPU).

Follows story_scene_01_karna_dawn.md shot for shot (9 shots, 45 s), with the key frames as layout guides:
  1 wide river at blue pre-dawn, camp fires on the far bank, Karna waist-deep, palms joined     5 s
  2 his cupped hands lift water to the horizon, it pours back; he says "Father."               5 s
  3 extreme close-up of his eyes; he closes them                                               4 s
  4 profile close-up, gold light rising across his face (thought: "I gave away what you gave me.")  5 s
  5 low medium profile facing frame left: the sun clears the horizon, the sun-face on his chest glints  5 s
  6 his hand closes on the bow Vijaya resting on a stone (thought: "Today I keep only my word.")  5 s
  7 he wades out toward the shore; Shalya in silhouette by the chariot and the dun horses       4 s
  8 close-up, half gold, half blue shadow, a small smile; he says "Let them see the sun."      5 s
  9 the chariot rolls out toward the sunrise, dust rising                                     7 s
Karna wears his crown and cuirass throughout: they are fused into the 3D model (sai's choice, 2026-11-25; a prayer-costume
model can replace him later). Sun in the east = world -X; Karna faces it. Subtitles and the title card go on in the cut.

  python scene01_3d.py <out_dir> [1 2 ...] [--preview | --still]
"""
import math, pathlib, random, sys
import bpy
from mathutils import Vector, Quaternion

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from anim_lib import Hero, ease, track, mix

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
PREVIEW = "--preview" in args or "--still" in args
STILL = "--still" in args                                         # three frames per shot, for layout checks
args = [a for a in args if not a.startswith("--")]
OUT = pathlib.Path(args[0]).resolve()
ONLY = [int(a) for a in args[1:]]
STUDIO = pathlib.Path(__file__).resolve().parents[2]
KARNA = STUDIO / "cast/karna/model/rig/karna_hero_v3.blend"
BOW = STUDIO / "cast/karna/model/trellis_out/karna_bow_1536.glb"
KIT = pathlib.Path("/mnt/project-files/kurukshetra/hero/blend")
FPS = 24
EYE = 1.69                                                         # Karna's eye height on his rig (m)


def mat(name, col, rough=0.6, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = strength
    return m


def obj_add(kind, name, m=None, **kw):
    getattr(bpy.ops.mesh, f"primitive_{kind}_add")(**kw)
    o = bpy.context.object; o.name = name
    if m:
        o.data.materials.append(m)
    return o


def append_kit(name):
    with bpy.data.libraries.load(str(KIT / f"SM_{name}.blend"), link=False) as (src, dst):
        dst.objects = [n for n in src.objects]
    for o in dst.objects:
        bpy.context.scene.collection.objects.link(o)
    return dst.objects[0]


# ---- stage -------------------------------------------------------------------------------------------------------------------
class Stage:
    def __init__(self, river=True):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.preferences.addon_enable(module="rigify")
        sc = self.sc = bpy.context.scene
        sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
        sc.cycles.samples = 4 if PREVIEW else 16
        sc.cycles.use_denoising = True; sc.render.use_persistent_data = True
        sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 12
        sc.render.resolution_x, sc.render.resolution_y = (480, 270) if PREVIEW else (960, 540)
        sc.render.fps = FPS
        sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
        # sky: gradient by height, its colours keyed per shot
        w = bpy.data.worlds.new("sky"); sc.world = w; w.use_nodes = True
        N, L = w.node_tree.nodes, w.node_tree.links
        self.bg = N["Background"]; self.bg.inputs["Strength"].default_value = 1.0
        tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ")
        mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = 0.35
        L.new(tc.outputs["Generated"], sep.inputs[0]); L.new(sep.outputs["Z"], mr.inputs["Value"])
        self.mixc = N.new("ShaderNodeMix"); self.mixc.data_type = "RGBA"
        L.new(mr.outputs["Result"], self.mixc.inputs[0]); L.new(self.mixc.outputs[2], self.bg.inputs["Color"])
        # sun lamp and the sun disc far away in the east (-X)
        self.sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(self.sun)
        self.sun.data.angle = math.radians(2)
        self.fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "SUN")); sc.collection.objects.link(self.fill)
        self.fill.data.color = (0.45, 0.6, 1.0); self.fill.rotation_euler = (math.radians(55), 0, math.radians(-90))
        self.disc_m = mat("sun_disc", (1, 0.7, 0.4), emit=(1.0, 0.64, 0.34), strength=9)
        self.disc = obj_add("uv_sphere", "sun_disc", self.disc_m, radius=5.5, segments=32, ring_count=16)
        self.disc.visible_shadow = False
        self.river = river
        if river:
            self.make_river()
        else:
            self.make_plain()
        self.cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(self.cam); sc.camera = self.cam
        self.cam.data.sensor_width = 36

    def make_river(self):
        m = bpy.data.materials.new("water"); m.use_nodes = True; nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.015, 0.035, 0.055, 1); b.inputs["Roughness"].default_value = 0.08
        b.inputs["IOR"].default_value = 1.33
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = 6.0
        nz.inputs["Detail"].default_value = 4
        mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 3.0, 1.0)
        tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
        bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.12
        nt.links.new(nz.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
        self.wave = nz
        self.water = obj_add("plane", "river", m, size=900)
        # far bank in the east, low and dark, with a ragged tree line and the camp fires
        bank_m = mat("bank", (0.035, 0.045, 0.05), rough=0.95)
        bank = obj_add("cube", "far_bank", bank_m, size=1); bank.scale = (30, 900, 1.6); bank.location = (-190, 0, 0.6)
        rnd = random.Random(3)
        for i in range(70):
            t = obj_add("uv_sphere", f"tree{i}", bank_m, radius=1, segments=8, ring_count=6)
            t.scale = (rnd.uniform(3, 6), rnd.uniform(4, 9), rnd.uniform(2, 5)); t.location = (-178 - rnd.uniform(0, 8), rnd.uniform(-260, 260), 1.6)
        fire_m = mat("fire", (1, 0.4, 0.1), emit=(1.0, 0.42, 0.12), strength=60)
        for i in range(9):
            f = obj_add("uv_sphere", f"fire{i}", fire_m, radius=0.6, segments=8, ring_count=6)
            f.location = (-176, rnd.uniform(-90, 40), 1.4); f.visible_shadow = False
        # near shore behind him (west, +X), sand, where the chariot waits
        sand = mat("shore", (0.42, 0.31, 0.2), rough=0.95)
        shore = obj_add("cube", "shore", sand, size=1); shore.scale = (40, 300, 1); shore.location = (24.5, 0, -0.47)
        shore.rotation_euler = (0, math.radians(-1.5), 0)
        # mist: thin noisy veils over the water
        mm = bpy.data.materials.new("mist"); mm.use_nodes = True; nt = mm.node_tree
        out = nt.nodes["Material Output"]; nt.nodes.remove(nt.nodes["Principled BSDF"])
        tr = nt.nodes.new("ShaderNodeBsdfTransparent"); em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (0.75, 0.8, 0.9, 1); em.inputs["Strength"].default_value = 0.6
        nzm = nt.nodes.new("ShaderNodeTexNoise"); nzm.inputs["Scale"].default_value = 0.05; nzm.inputs["Detail"].default_value = 3
        rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs["From Min"].default_value = 0.45; rr.inputs["From Max"].default_value = 0.75
        rr.inputs["To Max"].default_value = 0.12
        ms = nt.nodes.new("ShaderNodeMixShader")
        tc2 = nt.nodes.new("ShaderNodeNewGeometry"); nt.links.new(tc2.outputs["Position"], nzm.inputs["Vector"])
        nt.links.new(nzm.outputs["Fac"], rr.inputs["Value"]); nt.links.new(rr.outputs["Result"], ms.inputs[0])
        nt.links.new(tr.outputs[0], ms.inputs[1]); nt.links.new(em.outputs[0], ms.inputs[2]); nt.links.new(ms.outputs[0], out.inputs["Surface"])
        self.mist_m, self.mist = mm, []
        for i, z in enumerate((0.2, 0.55, 1.1)):                     # from 12 m east of Karna out to the far bank
            p = obj_add("plane", f"mist{i}", mm, size=1); p.scale = (165, 600, 1); p.location = (-94.5, 0, z)
            p.visible_shadow = False
            self.mist.append(p)

    def make_plain(self):
        m = bpy.data.materials.new("plain"); m.use_nodes = True; nt = m.node_tree
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 10
        cr = nt.nodes.new("ShaderNodeValToRGB")
        cr.color_ramp.elements[0].color = (0.32, 0.17, 0.08, 1); cr.color_ramp.elements[1].color = (0.62, 0.38, 0.18, 1)
        nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
        nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
        obj_add("plane", "plain", m, size=2000)

    def light(self, f, elev, energy, horizon, top, fill=0.6, azim=0.0):
        """sun at elevation elev (deg) in the east, azimuth offset azim (deg, toward +Y); sky colours"""
        e, a = math.radians(elev), math.radians(azim)
        d = Vector((-math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))
        self.disc.location = d * 520; self.disc.keyframe_insert("location", frame=f)
        self.sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler(); self.sun.keyframe_insert("rotation_euler", frame=f)
        self.sun.data.energy = energy; self.sun.data.keyframe_insert("energy", frame=f)
        self.sun.data.color = mix((1.0, 0.55, 0.3), (1.0, 0.85, 0.65), min(max(elev / 12, 0), 1))
        self.sun.data.keyframe_insert("color", frame=f)
        self.fill.data.energy = fill; self.fill.data.keyframe_insert("energy", frame=f)
        self.mixc.inputs[6].default_value = (*horizon, 1); self.mixc.inputs[7].default_value = (*top, 1)
        self.mixc.inputs[6].keyframe_insert("default_value", frame=f); self.mixc.inputs[7].keyframe_insert("default_value", frame=f)
        if self.river:
            self.wave.inputs["W"].default_value = f / 70; self.wave.inputs["W"].keyframe_insert("default_value", frame=f)
            for i, p in enumerate(self.mist):
                p.location.y = f * 0.02 * (i + 1); p.keyframe_insert("location", frame=f)


def look(cam, pos, target, lens):
    cam.location = pos
    cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens


def key_cam(cam, f):
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f); cam.data.keyframe_insert("lens", frame=f)


def arm(h, s, up, fo, ha, roll=0.0, palm=None):
    """aim the FK arm (directions for his left side, mirrored for the right); palm: where the palm faces"""
    sx = 1 if s == "L" else -1
    h.aim(f"upper_arm_fk.{s}", (up[0] * sx, up[1], up[2]))
    h.aim(f"forearm_fk.{s}", (fo[0] * sx, fo[1], fo[2]))
    h.aim(f"hand_fk.{s}", (ha[0] * sx, ha[1], ha[2]), roll * sx)
    if palm:
        palm_to(h, s, (palm[0] * sx, palm[1], palm[2]))


def palm_to(h, s, want):
    """turn the hand about its own length so the palm (the fingers' +Z, toward the palm) faces direction want"""
    bpy.context.view_layer.update()
    pb = h.pb[f"hand_fk.{s}"]; M = h.rig.matrix_world @ pb.matrix
    y = M.to_3x3().col[1].normalized()
    n = (h.rig.matrix_world @ h.pb[f"f_middle.01.{s}"].matrix).to_3x3().col[2].normalized()
    w = h.W(want)
    n = (n - y * n.dot(y)).normalized(); w = (w - y * w.dot(y)).normalized()
    ang = math.atan2(y.dot(n.cross(w)), n.dot(w))
    R = Quaternion(y, ang).to_matrix() @ M.to_3x3()
    Mn = R.to_4x4(); Mn.translation = M.translation
    h._set(pb, Mn)


def lerp_arm(a, b, u):
    return tuple(mix(x, y, u) for x, y in zip(a, b))


def blink(t, times, dur=0.16):
    return max([1 - abs((t - b) / (dur / 2)) for b in times if abs(t - b) < dur / 2] + [0.0])


DOWN = ((0.15, 0.02, -1), (0.08, -0.15, -1), (0.05, -0.12, -1))
NAMASKAR = ((0.10, -0.30, -1), (-0.85, -0.55, 0.45), (-0.25, -0.35, 1))
CUP_LOW = ((0.06, -0.55, -0.85), (-0.6, -0.8, -0.1), (-0.35, -0.93, 0.0))
CUP_HIGH = ((0.04, -0.92, 0.05), (-0.6, -0.78, 0.2), (-0.35, -0.93, 0.1))
PALM_IN, PALM_UP = (-1, 0, 0), (-0.3, 0, 1)


def karna(face=-90.0, loc=(0, 0, -0.95)):
    return Hero.load(KARNA, "KARNA", loc=loc, face=face)


def L(h, x, y, z):
    """a point in Karna's own frame (front -Y, his left +X, feet at z=0) in world space"""
    return h.rig.matrix_world @ Vector((x, y, z))


def breathe(h, t, amt=1.2):
    h.turn("chest", "X", amt * math.sin(2 * math.pi * 0.22 * t))


# ---- shots -----------------------------------------------------------------------------------------------------------------------
def shot1(st):                                                     # 5 s wide, pre-dawn
    h = karna(); n = 5 * FPS
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        h.reset(); breathe(h, t)
        arm(h, "R", *NAMASKAR, palm=PALM_IN); arm(h, "L", *NAMASKAR, palm=PALM_IN); h.fingers("L", 5); h.fingers("R", 5)
        h.turn("head", "X", 6)                                       # head bowed a little
        h.key_all(f)
        st.light(f, -2.5 + t * 0.1, 0.6, (0.62, 0.5, 0.52), (0.08, 0.13, 0.27), fill=0.35)
        look(st.cam, (mix(7.5, 6.0, ease(t, 0, 5)), 2.4, 0.55), (-30, -1.2, 0.5), 38); key_cam(st.cam, f)
    return n


def shot2(st):                                                     # 5 s cupped hands lift water: "Father."
    h = karna(); n = 5 * FPS
    drops_m = bpy.data.materials.new("drop"); drops_m.use_nodes = True
    b = drops_m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.9, 0.95, 1, 1); b.inputs["Roughness"].default_value = 0.02
    b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["IOR"].default_value = 1.33
    drops = [obj_add("uv_sphere", f"drop{i}", drops_m, radius=0.006 + 0.004 * (i % 3), segments=8, ring_count=6) for i in range(26)]
    line = [(2.6, "G"), (2.72, "D"), (2.92, "B"), (3.02, "C"), (3.2, "X")]
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        h.reset(); breathe(h, t)
        u = ease(t, 0.4, 2.4)
        pose = lerp_arm(CUP_LOW, CUP_HIGH, u)
        arm(h, "R", *pose, palm=PALM_UP); arm(h, "L", *pose, palm=PALM_UP)
        h.fingers("L", 22, thumb=8); h.fingers("R", 22, thumb=8)
        h.turn("head", "X", mix(8, -6, ease(t, 0.6, 2.6)))            # eyes follow the water up to the horizon
        face = h.say(line, t)
        face.update(brow_sad=0.35, blink_L=blink(t, [1.2, 4.3]), blink_R=blink(t, [1.2, 4.3]))
        h.keys(face); h.key_all(f)
        bpy.context.view_layer.update()
        cup = (h.rig.matrix_world @ h.pb["hand_fk.R"].tail + h.rig.matrix_world @ h.pb["hand_fk.L"].tail) / 2
        for i, d in enumerate(drops):                                 # water pours from between his fingers
            if t < 2.3:
                d.location = (0, 0, -5)
            else:
                age = ((t - 2.3) * 1.0 + i / 26) % 0.55
                d.location = cup + Vector(((i % 5 - 2) * 0.01, ((i * 7) % 5 - 2) * 0.008, -0.03 - 4.9 * age * age))
            d.keyframe_insert("location", frame=f)
        st.light(f, -1.0 + t * 0.15, 1.2, (0.85, 0.62, 0.5), (0.12, 0.18, 0.33), fill=0.4)
        look(st.cam, L(h, 0.95, -1.5, 1.42), L(h, 0.0, -0.5, mix(1.2, 1.38, u)), 42); key_cam(st.cam, f)
    return n


def shot3(st):                                                     # 4 s eyes; he closes them
    h = karna(); n = 4 * FPS
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        h.reset(); breathe(h, t, 0.5)
        arm(h, "R", *DOWN); arm(h, "L", *DOWN)
        cl = ease(t, 1.6, 2.6)
        h.keys(dict(blink_L=max(cl, blink(t, [0.5])), blink_R=max(cl, blink(t, [0.5])), brow_sad=mix(0.3, 0.6, cl)))
        h.key_all(f)
        st.light(f, 0.2, 2.0, (0.95, 0.66, 0.45), (0.15, 0.22, 0.38), fill=0.35)
        look(st.cam, L(h, 0.0, mix(-0.62, -0.55, ease(t, 0, 4)), EYE), L(h, 0, 0, EYE - 0.005), 90); key_cam(st.cam, f)
    return n


def shot4(st):                                                     # 5 s profile, gold light rises across his face
    h = karna(); n = 5 * FPS
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        h.reset(); breathe(h, t, 0.8)
        arm(h, "R", *DOWN); arm(h, "L", *DOWN)
        h.turn("head", "X", mix(4, -3, ease(t, 0.5, 4.5)))
        h.keys(dict(blink_L=blink(t, [3.6]), blink_R=blink(t, [3.6]), brow_sad=0.45, frown=0.2))
        h.key_all(f)
        st.light(f, mix(-0.5, 2.0, ease(t, 0, 5)), mix(0.8, 3.2, ease(t, 0, 5)), (0.98, 0.62, 0.38), (0.16, 0.24, 0.42), fill=0.3)
        look(st.cam, L(h, 1.15, -0.1, EYE - 0.06), L(h, 0, -0.1, EYE - 0.07), 68); key_cam(st.cam, f)
    return n


def shot5(st):                                                     # 5 s low profile, the sun clears the horizon
    h = karna(); n = 5 * FPS
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        h.reset(); breathe(h, t)
        arm(h, "R", *DOWN); arm(h, "L", *DOWN); h.fingers("L", 20); h.fingers("R", 20)
        h.turn("head", "X", -4); h.turn("chest", "X", -3, keep=True)
        h.keys(dict(blink_L=blink(t, [2.2]), blink_R=blink(t, [2.2])))
        h.key_all(f)
        st.light(f, mix(-0.6, 2.8, ease(t, 0, 5)), mix(2.0, 4.0, ease(t, 0, 5)), (1.0, 0.6, 0.32), (0.2, 0.3, 0.5), fill=0.3, azim=30)
        look(st.cam, (2.2, -3.2, 0.25), (-1.2, 0.3, mix(0.72, 0.78, ease(t, 0, 5))), 35); key_cam(st.cam, f)
    return n


def shot6(st):                                                     # 5 s his hand closes on Vijaya on the stone
    h = karna(); n = 5 * FPS
    G = L(h, -0.29, -0.40, 1.12)                                      # where his right hand closes on the grip (within reach)
    rock_m = bpy.data.materials.new("rock"); rock_m.use_nodes = True; nt = rock_m.node_tree
    b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.8
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9; nz.inputs["Detail"].default_value = 8
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (0.03, 0.028, 0.026, 1); cr.color_ramp.elements[1].color = (0.13, 0.115, 0.1, 1)
    nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
    bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.5
    nt.links.new(nz.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    rock = obj_add("ico_sphere", "rock", rock_m, subdivisions=5, radius=1)
    tx = bpy.data.textures.new("rockdisp", "CLOUDS"); tx.noise_scale = 0.45
    dm = rock.modifiers.new("d", "DISPLACE"); dm.texture = tx; dm.strength = 0.18
    rock.scale = (0.5, 0.42, 0.32)
    rock.location = G + (h.rig.matrix_world.to_3x3() @ Vector((-0.06, -0.05, 0))) - Vector((0, 0, 0.06 + 0.32 * 1.05))
    bpy.ops.import_scene.gltf(filepath=str(BOW))
    bow = max((o for o in bpy.context.selected_objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
    bow.parent = None
    bow.scale = Vector(bow.scale) * (1.55 / max(bow.dimensions))
    bow.rotation_mode = "XYZ"                                         # the importer leaves it in quaternion mode
    bow.rotation_euler = (math.radians(90), 0, math.radians(12))      # length (local Z) across in front of him, lying flat
    bpy.context.view_layer.update()
    bb = [bow.matrix_world @ Vector(c) for c in bow.bound_box]
    ctr = sum(bb, Vector()) / 8
    bow.location = Vector(bow.location) + (G - Vector((0, 0, 0.03)) - ctr)
    h.pb["upper_arm_parent.R"]["IK_FK"] = 0.0                       # this arm on IK: the hand goes to the grip
    inv = h.rig.matrix_world.to_3x3().inverted()
    off = Vector()

    def reach(P):
        """move the IK hand until the palm (the hand bone's tail) is at P"""
        nonlocal off
        for _ in range(4):
            h.move("hand_ik.R", tuple(off)); h.turn("hand_ik.R", "X", 75)   # palm down onto the grip
            bpy.context.view_layer.update()
            off = off + inv @ (P - h.rig.matrix_world @ h.pb["DEF-hand.R"].tail)
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        h.reset(); breathe(h, t)
        arm(h, "L", *DOWN); h.fingers("L", 25)
        u = ease(t, 0.3, 1.8)
        reach(G + Vector((0, 0, mix(0.15, 0.02, u))))
        h.fingers("R", track(t, [(0, 10), (1.9, 15), (2.6, 78), (5, 85)]), thumb=track(t, [(1.9, 10), (2.6, 55)]))
        h.turn("chest", "Z", 8, keep=True); h.turn("chest", "X", 9 * ease(t, 0.2, 1.8), keep=True)   # leans to it
        h.keys(dict(brow_angry=track(t, [(2.0, 0), (3.0, 0.45)])))
        h.key_all(f)
        st.light(f, 4.0, 4.0, (1.0, 0.66, 0.4), (0.22, 0.32, 0.52), fill=0.35)
        look(st.cam, L(h, -0.95, -1.1, 1.35), G + Vector((0, 0, 0.08)), 42); key_cam(st.cam, f)
    return n


def chariot_team(at, face_deg):
    """Karna's chariot (the kit chariot carries a crew) and its team, recoloured dun; front is the kit's -Y"""
    ch = append_kit("krk_rank_chariot"); hs = append_kit("krk_horse_team_dark")
    for m in hs.data.materials:
        if m and m.name.startswith("MAT_Bay"):
            m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.22, 0.13, 0.05, 1)   # dun
            m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.75
    for m in ch.data.materials:
        if m and m.name.startswith("MAT_Saffron"):
            m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.55, 0.12, 1)  # gold standard
    root = bpy.data.objects.new("team", None); bpy.context.scene.collection.objects.link(root)
    ch.parent = root; hs.parent = ch
    hs.location = (0, -(ch.dimensions.y * 0.5 + hs.dimensions.y * 0.5) + 4.5, 0)   # astride the pole
    root.location = at; root.rotation_euler = (0, 0, math.radians(face_deg))
    return root, ch, hs


def shot7(st):                                                     # 4 s he wades to the shore; Shalya and the chariot
    h = karna(face=90, loc=(-3.5, 0, -0.9)); n = 4 * FPS
    chariot_team((9.5, 6.0, 0.05), 180)                             # team heads away, out of frame right
    sh = append_kit("krk_kaurava_soldier"); sh.location = (11.0, 2.6, 0.05); sh.rotation_euler = (0, 0, math.radians(-100))
    dark = mat("silhouette", (0.01, 0.01, 0.012), rough=0.8)
    sh.data.materials.clear(); sh.data.materials.append(dark)
    T, S = 1.2, 0.5
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        h.reset()
        x = -3.5 + (S / (T / 2)) * t                                  # body wades forward (+X)
        h.rig.location = (x, 0, mix(-0.9, -0.45, ease(x, -3.5, 1.0))); h.rig.keyframe_insert("location", frame=f)
        ph = 2 * math.pi * t / T
        h.move("torso", (0.015 * math.sin(ph), 0, -0.02 + 0.015 * abs(math.sin(ph))))
        h.turn("hips", "Z", 5 * math.sin(ph)); h.turn("chest", "Z", -4 * math.sin(ph))
        sw = 0.3 * math.sin(ph)
        arm(h, "L", (0.18, sw, -1), (0.1, sw - 0.25, -1), (0.05, sw - 0.2, -1))
        arm(h, "R", (0.18, -sw, -1), (0.1, -sw - 0.25, -1), (0.05, -sw - 0.2, -1))
        h.fingers("L", 30); h.fingers("R", 30)
        h.keys(dict(brow_angry=0.25, blink_L=blink(t, [1.4]), blink_R=blink(t, [1.4])))
        h.key_all(f)
        st.light(f, 6.0, 4.0, (1.0, 0.7, 0.45), (0.25, 0.36, 0.58), fill=0.5, azim=-6)
        look(st.cam, (15.0, 1.4, 1.8), (mix(-2.0, -1.0, ease(t, 0, 4)), 0.2, 0.9), 32); key_cam(st.cam, f)
    return n


LINE8 = [(1.4, "H"), (1.5, "C"), (1.6, "B"), (1.72, "B"), (1.8, "C"), (1.9, "A"), (2.02, "B"), (2.1, "C"), (2.26, "B"),
         (2.34, "C"), (2.44, "B"), (2.52, "C"), (2.68, "B"), (2.8, "X")]   # "Let them see the sun."


def shot8(st):                                                     # 5 s close-up, half gold, half blue; a small smile
    h = karna(face=0, loc=(6.0, -1.0, 0.0)); n = 5 * FPS
    chariot_team((8.6, 4.5, 0.05), 0)
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        h.reset(); breathe(h, t)
        arm(h, "R", *DOWN); arm(h, "L", *DOWN); h.fingers("L", 30); h.fingers("R", 30)
        h.turn("head", "Z", track(t, [(0, -14), (1.0, -6)]))
        face = h.say(LINE8, t)
        face.update(smile_L=track(t, [(3.0, 0), (3.8, 0.75)]), smile_R=track(t, [(3.2, 0), (3.9, 0.25)]),
                    brow_angry=track(t, [(0, 0.2), (3.0, 0.05)]), blink_L=blink(t, [0.7, 4.4]), blink_R=blink(t, [0.7, 4.4]))
        h.keys(face); h.key_all(f)
        st.light(f, 9.0, 4.5, (1.0, 0.74, 0.5), (0.25, 0.38, 0.6), fill=1.4, azim=10)
        look(st.cam, L(h, -0.28, -1.05, EYE + 0.02), L(h, 0, 0, EYE - 0.05), 75); key_cam(st.cam, f)
    return n


def shot9(st):                                                     # 7 s the chariot rolls out toward the sunrise
    n = 7 * FPS
    root, ch, hs = chariot_team((0, 0, 0), -90)                       # kit front -Y turned to face -X (east)
    dust_m = bpy.data.materials.new("dust"); dust_m.use_nodes = True; nt = dust_m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    vol = nt.nodes.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (0.72, 0.55, 0.38, 1)
    oi = nt.nodes.new("ShaderNodeObjectInfo"); sp = nt.nodes.new("ShaderNodeSeparateColor")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 4
    tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; nt.links.new(tc.outputs["Object"], ln.inputs[0])
    fall = nt.nodes.new("ShaderNodeMapRange"); fall.inputs["From Min"].default_value = 1.0; fall.inputs["From Max"].default_value = 0.3
    nt.links.new(ln.outputs["Value"], fall.inputs["Value"])
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"; nt.links.new(nz.outputs["Fac"], m1.inputs[0]); nt.links.new(fall.outputs["Result"], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; nt.links.new(m1.outputs[0], m2.inputs[0])
    nt.links.new(oi.outputs["Color"], sp.inputs[0]); nt.links.new(sp.outputs[0], m2.inputs[1])
    nt.links.new(m2.outputs[0], vol.inputs["Density"])
    nt.links.new(vol.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    rnd = random.Random(9)
    puffs = []
    for i in range(14):
        p = obj_add("ico_sphere", f"dust{i}", dust_m, subdivisions=2, radius=1)
        p.visible_shadow = False
        puffs.append((p, 1.0 + i * 0.42, rnd.uniform(-1.4, 1.4), rnd.uniform(1.4, 2.2)))
    speed = 3.5
    pos = lambda tt: -(speed * max(tt - 0.9, 0) + speed * 0.35 * ease(tt, 0.2, 1.6))
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        go = ease(t, 0.2, 1.6)
        root.location = (pos(t), 0, 0); root.keyframe_insert("location", frame=f)
        hs.location.z = 0.05 * abs(math.sin(t * 7.0)) * go; hs.keyframe_insert("location", frame=f)   # horses gallop
        for p, born, side, sz in puffs:                               # dust kicked up behind the wheels, rising and thinning
            age = t - born
            if age < 0:
                p.location = (0, 0, -20); p.scale = (0.01, 0.01, 0.01); p.color = (0, 0, 0, 1)
            else:
                bx = pos(born) + 3.2
                p.location = (bx + age * 0.5, side * (1 + age * 0.4), 0.5 + age * 0.35)
                s = sz * (0.5 + age * 0.6); p.scale = (s * 1.3, s, s * 0.6)
                p.color = (1.2 * min(age / 0.3, 1) * max(0.0, 1 - age / 4.5), 0, 0, 1)
            p.keyframe_insert("location", frame=f); p.keyframe_insert("scale", frame=f); p.keyframe_insert("color", frame=f)
        st.light(f, 12.0, 4.5, (1.0, 0.72, 0.45), (0.3, 0.45, 0.68), fill=0.5)
        look(st.cam, (7.0, 7.5, 1.7), (pos(t) - 3.0, 0, mix(1.4, 2.4, ease(t, 1, 7))), 35); key_cam(st.cam, f)
    return n


SHOTS = {1: shot1, 2: shot2, 3: shot3, 4: shot4, 5: shot5, 6: shot6, 7: shot7, 8: shot8, 9: shot9}

for k, fn in SHOTS.items():
    if ONLY and k not in ONLY:
        continue
    st = Stage(river=(k != 9))
    n = fn(st)
    sc = st.sc
    sc.frame_start, sc.frame_end = 1, n
    sc.frame_step = 4 if PREVIEW else 2
    d = OUT / f"s01_{k:02d}"
    d.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f"s01_{k:02d}.blend"), compress=True)
    sc.render.filepath = str(d / "f_"); sc.render.image_settings.file_format = "PNG"
    print("rendering shot", k, n, "frames", flush=True)
    if STILL:
        for fr in (1, n // 2, n):
            sc.frame_set(fr); sc.render.filepath = str(OUT / f"still_{k:02d}_{fr:03d}.png"); bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
    print("done shot", k, flush=True)

"""Animation test demo for the rigged series heroes (sai, 2026-11-25: "try animate different sequences test demo"). Free.

Five short sequences, keyframed with anim_lib.py on the latest rigs (Arjuna v2, Krishna v2, Karna v3):
  s1_karna_speaks     6 s  close-up: looks up, speaks a line with lip-sync, blinks, sorrow to resolve, half smile
  s2_arjuna_arrow     5 s  medium: hears something, turns, reaches over his shoulder to the quiver, draws an arrow
  s3_krishna_blessing 5 s  medium: calm smile, raises his right hand in abhaya mudra (palm out), nods
  s4_karna_walk       6 s  tracking: walks forward (IK feet stay planted), arms swing, then stops
  s5_face_off         6 s  wide: Karna points at Arjuna and calls his name, Arjuna clenches his fists and steps in
Keys are set on every frame at 24 fps; frames are rendered on twos (12 drawings a second, the anime look in the bible)
in Cycles on the CPU. Each sequence's scene is saved next to its frames so it can be opened and re-timed in Blender.

  python anim_demo.py <out_dir> [s1 s2 ...] [--preview]      # --preview: 480x270, every 4th frame, 4 samples
"""
import math, pathlib, sys
import bpy
from mathutils import Vector

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from anim_lib import Hero, ease, track, mix

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
PREVIEW = "--preview" in args
args = [a for a in args if not a.startswith("--")]
OUT = pathlib.Path(args[0]).resolve()
ONLY = args[1:]
CAST = pathlib.Path(__file__).resolve().parents[2] / "cast"
RIGS = {"ARJUNA": CAST / "arjuna/model/rig/arjuna_hero_v2.blend",
        "KRISHNA": CAST / "krishna/model/rig/krishna_hero_v2.blend",
        "KARNA": CAST / "karna/model/rig/karna_hero_v3.blend"}
FPS = 24


# ---- the stage: dawn sky, dry field, warm key and cool rim ---------------------------------------------------------------------
def stage():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.preferences.addon_enable(module="rigify")
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
    sc.cycles.samples = 4 if PREVIEW else 16
    sc.cycles.use_denoising = True
    sc.render.use_persistent_data = True
    sc.render.resolution_x, sc.render.resolution_y = (480, 270) if PREVIEW else (960, 540)
    sc.render.fps = FPS
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
    w = bpy.data.worlds.new("dawn"); sc.world = w; w.use_nodes = True
    N, L = w.node_tree.nodes, w.node_tree.links
    bg = N["Background"]; bg.inputs["Strength"].default_value = 0.9
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); ramp = N.new("ShaderNodeValToRGB")
    L.new(tc.outputs["Generated"], sep.inputs[0]); L.new(sep.outputs["Z"], ramp.inputs["Fac"])
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (0.98, 0.58, 0.34, 1)          # warm horizon
    els[1].position, els[1].color = 0.30, (0.22, 0.36, 0.62, 1)          # cool sky above
    mid = els.new(0.07); mid.color = (0.96, 0.74, 0.55, 1)
    L.new(ramp.outputs["Color"], bg.inputs["Color"])
    bpy.ops.mesh.primitive_plane_add(size=120)
    g = bpy.context.object; g.name = "field"
    m = bpy.data.materials.new("field"); m.use_nodes = True; nt = m.node_tree
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 6
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (0.30, 0.16, 0.07, 1); cr.color_ramp.elements[1].color = (0.62, 0.40, 0.19, 1)
    nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
    g.data.materials.append(m)
    for e, col, rot in ((3.2, (1.0, 0.82, 0.62), (58, 0, -35)), (1.6, (0.55, 0.68, 1.0), (60, 0, 150))):
        l = bpy.data.lights.new("sun", "SUN"); l.energy = e; l.color = col; l.angle = math.radians(3)
        o = bpy.data.objects.new("sun", l); sc.collection.objects.link(o); o.rotation_euler = [math.radians(a) for a in rot]
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.sensor_width = 36
    return sc, cam


def look(cam, pos, target, lens):
    cam.location = pos
    cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens


def key_cam(cam, f):
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f); cam.data.keyframe_insert("lens", frame=f)


def arm(h, s, up, fo, ha, roll=0.0):
    """aim one arm; directions written for his RIGHT arm with x toward his side (mirrored for the left)"""
    sx = 1 if s == "L" else -1
    h.aim(f"upper_arm_fk.{s}", (up[0] * sx, up[1], up[2]))
    h.aim(f"forearm_fk.{s}", (fo[0] * sx, fo[1], fo[2]))
    h.aim(f"hand_fk.{s}", (ha[0] * sx, ha[1], ha[2]), roll * sx)


DOWN = ((0.15, 0.02, -1), (0.08, -0.15, -1), (0.05, -0.12, -1))       # arms hanging, relaxed


def lerp_arm(a, b, u):
    return tuple(mix(x, y, u) for x, y in zip(a, b))


def breathe(h, t, rate=0.25, amt=1.5):
    h.turn("chest", "X", amt * math.sin(2 * math.pi * rate * t))


def blink(t, times, dur=0.16):
    return max([1 - abs((t - b) / (dur / 2)) for b in times if abs(t - b) < dur / 2] + [0.0])


# ---- sequences -----------------------------------------------------------------------------------------------------------------
LINE_KARNA = [(1.60, "B"), (1.68, "F"), (1.78, "B"), (1.86, "D"), (2.02, "C"), (2.14, "D"), (2.34, "C"), (2.48, "B"),
              (2.56, "C"), (2.70, "A"), (2.84, "E"), (2.98, "B"), (3.06, "H"), (3.14, "C"), (3.26, "A"), (3.36, "D"),
              (3.52, "C"), (3.62, "F"), (3.74, "E"), (3.92, "B"), (4.04, "X")]          # "Today I keep only my word."


def s1_karna_speaks(sc, cam):
    h = Hero.load(RIGS["KARNA"], "KARNA")
    n = 6 * FPS
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        h.reset()
        breathe(h, t)
        h.turn("neck", "X", track(t, [(0, 9), (0.7, 9), (1.3, 0)]), )           # looks down, then lifts his gaze
        h.turn("head", "Z", track(t, [(0, -8), (1.3, 3), (4.4, 0), (5.2, -4)]))
        h.turn("head", "X", 2.0 * math.sin(2 * math.pi * 0.9 * t) * ease(t, 1.6, 1.8) * (1 - ease(t, 3.9, 4.1)), keep=True)
        arm(h, "R", *DOWN); arm(h, "L", *DOWN); h.fingers("L", 25); h.fingers("R", 25)
        face = h.say(LINE_KARNA, t)
        face.update(blink_L=blink(t, [0.55, 1.25, 4.5]), blink_R=blink(t, [0.55, 1.25, 4.5]),
                    brow_sad=track(t, [(0, 0.7), (1.4, 0.6), (3.6, 0.15)]),
                    brow_angry=track(t, [(3.4, 0), (4.1, 0.45)]),
                    smile_L=track(t, [(4.5, 0), (5.3, 0.55)]), frown=track(t, [(0, 0.3), (1.6, 0.1), (4.4, 0)]))
        h.keys(face); h.key_all(f)
        z = 1.72
        look(cam, mix((0.55, -1.55, z - 0.02), (0.42, -1.15, z - 0.02), ease(t, 0, 6)), (0.0, 0, z - 0.05), 70)
        key_cam(cam, f)
    return n


def s2_arjuna_arrow(sc, cam):
    h = Hero.load(RIGS["ARJUNA"], "ARJUNA")
    n = 5 * FPS
    # the arrow: a shaft with a steel head and feathers, shown once his hand closes on it
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0045, depth=0.78, vertices=8)
    shaft = bpy.context.object; shaft.name = "arrow"
    bpy.ops.mesh.primitive_cone_add(radius1=0.011, depth=0.05, vertices=8, location=(0, 0, 0.415))
    tip = bpy.context.object
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.33)); fl = bpy.context.object; fl.scale = (0.002, 0.03, 0.09)
    for o, col in ((shaft, (0.42, 0.28, 0.14)), (tip, (0.7, 0.72, 0.75)), (fl, (0.85, 0.82, 0.74))):
        m = bpy.data.materials.new(o.name); m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*col, 1)
        if o is tip:
            m.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.8
        o.data.materials.append(m)
    bpy.ops.object.select_all(action="DESELECT")
    for o in (shaft, tip, fl):
        o.select_set(True)
    bpy.context.view_layer.objects.active = shaft
    bpy.ops.object.join()
    arrow = bpy.context.object
    arrow.parent = h.rig; arrow.parent_type = "BONE"; arrow.parent_bone = "DEF-hand.R"
    REACH = ((0.25, 0.05, 1), (-0.45, 0.55, 0.45), (-0.35, 0.65, 0.35))    # up and back over his right shoulder
    DRAWN = ((0.35, -0.45, -0.55), (0.2, -0.95, 0.05), (0.1, -1, 0.0))     # arrow brought forward, low and ready
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        h.reset()
        breathe(h, t, amt=1.2)
        yaw = track(t, [(0, 0), (0.55, 0), (0.85, -32), (3.1, -32), (3.6, -12)])  # snaps toward something on his right
        h.turn("chest", "Z", yaw * 0.25, keep=True)
        h.turn("head", "Z", yaw * 0.75)
        u1, u2 = ease(t, 1.2, 1.9), ease(t, 2.45, 3.3)
        pose = lerp_arm(lerp_arm(DOWN, REACH, u1), DRAWN, u2)
        arm(h, "R", *pose)
        arm(h, "L", *lerp_arm(DOWN, ((0.3, -0.35, -0.85), (0.1, -0.9, -0.25), (0.05, -1, -0.1)), ease(t, 2.8, 3.6)))
        grip = track(t, [(0, 20), (1.6, 5), (2.0, 70), (5, 70)])
        h.fingers("R", grip); h.fingers("L", track(t, [(0, 20), (2.9, 20), (3.6, 55)]))
        h.keys(dict(brow_angry=track(t, [(0.5, 0), (0.9, 0.7)]), blink_L=blink(t, [0.95, 3.9]), blink_R=blink(t, [0.95, 3.9]),
                    frown=track(t, [(0.5, 0), (1.0, 0.35)]), mouth_press=track(t, [(2.0, 0), (2.4, 0.5)])))
        h.key_all(f)
        shown = t >= 2.05
        arrow.hide_render = not shown; arrow.keyframe_insert("hide_render", frame=f)
        look(cam, mix((1.35, -2.6, 1.45), (1.15, -2.2, 1.45), ease(t, 0, 5)), (-0.05, 0, 1.35), 50)
        key_cam(cam, f)
    # the arrow sits across his closed fist: along the hand bone's X, a little toward the palm
    arrow.matrix_parent_inverse.identity()
    arrow.location = (0.0, -0.035, 0.0)                                  # bone children sit at the tail: back into the fist
    arrow.rotation_euler = (0, math.radians(90), 0)
    return n


def s3_krishna_blessing(sc, cam):
    h = Hero.load(RIGS["KRISHNA"], "KRISHNA")
    n = 5 * FPS
    ABHAYA = ((0.35, -0.35, -1), (0.15, -0.25, 1), (0.05, -0.1, 1))
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        h.reset()
        breathe(h, t, rate=0.2, amt=1.0)
        h.turn("head", "Y", track(t, [(0, 0), (1.0, -5), (5, -5)]))                 # a gentle tilt
        h.turn("head", "X", track(t, [(3.3, 0), (3.6, 6), (4.0, 0)]), keep=True)    # a slow nod
        u = ease(t, 0.9, 2.2)
        arm(h, "R", *lerp_arm(DOWN, ABHAYA, u))
        arm(h, "L", *DOWN)
        h.fingers("R", track(t, [(0, 25), (1.6, 0)]), spread=track(t, [(1.6, 0), (2.2, 2)])); h.fingers("L", 25)
        sm = track(t, [(0.3, 0), (1.5, 0.55)])
        h.keys(dict(smile_L=sm, smile_R=sm, blink_L=blink(t, [0.4, 2.9]), blink_R=blink(t, [0.4, 2.9]),
                    brow_up=track(t, [(0.3, 0), (1.2, 0.25), (3.0, 0.1)]), mouth_press=0.35))
        h.key_all(f)
        look(cam, mix((0.9, -2.75, 1.32), (0.75, -2.3, 1.36), ease(t, 0, 5)), (-0.05, 0, 1.25), 45)
        key_cam(cam, f)
    return n


def s4_karna_walk(sc, cam):
    h = Hero.load(RIGS["KARNA"], "KARNA")
    n = 6 * FPS
    T, S = 1.1, 0.62                                                   # cycle seconds, one step length (m)
    v = S / (T / 2)                                                    # body speed
    stop = 4.4                                                         # last step lands, then he stands

    def foot_y(t, phase):
        """forward position (-Y is forward) of a foot that lifts at the given phase of each cycle"""
        tt = min(t, stop)
        k = math.floor((tt / T) - phase)
        u = (tt / T) - phase - k                                       # 0..1 through this cycle
        base = (k * 2 + 1) * S + phase * 2 * S - S                     # planted spot for this cycle
        swing = 0.42
        if u < swing:
            a = ease(u, 0, swing); return base + 2 * S * a, math.sin(math.pi * u / swing) * 0.09
        return base + 2 * S, 0.0

    for f in range(1, n + 1):
        t = (f - 1) / FPS
        h.reset()
        tb = min(t, stop)
        body = v * tb + S * 0.5                                        # between the planted feet
        yl, zl = foot_y(t, 0.0)
        yr, zr = foot_y(t, 0.5)
        ph = 2 * math.pi * min(t, stop) / T
        walking = 1 - ease(t, stop, stop + 0.5)
        h.move("foot_ik.L", (0, -yl, zl)); h.move("foot_ik.R", (0, -yr, zr))
        h.move("torso", (0.02 * math.sin(ph) * walking, -body, -0.03 + 0.022 * abs(math.sin(ph)) * walking - 0.01 * walking))
        h.turn("hips", "Z", 6 * math.sin(ph) * walking)
        h.turn("chest", "Z", -5 * math.sin(ph) * walking)
        sw = 0.38 * math.sin(ph) * walking
        arm(h, "L", (0.15, sw, -1), (0.08, sw - 0.25, -1), (0.05, sw - 0.2, -1))
        arm(h, "R", (0.15, -sw, -1), (0.08, -sw - 0.25, -1), (0.05, -sw - 0.2, -1))
        h.fingers("L", 30); h.fingers("R", 30)
        h.turn("head", "Z", track(t, [(0, 0), (4.6, 0), (5.3, -18)]))  # stops and looks toward camera side
        h.keys(dict(blink_L=blink(t, [1.0, 3.3, 5.2]), blink_R=blink(t, [1.0, 3.3, 5.2]), brow_angry=0.3))
        h.key_all(f)
        cy = -body
        look(cam, (3.2, cy - 2.6, 1.25), (0, cy - 0.4, 1.05), 40)
        key_cam(cam, f)
    return n


LINE_ARJUNA = [(1.30, "D"), (1.48, "B"), (1.56, "F"), (1.72, "B"), (1.80, "D"), (2.00, "X")]       # "Arjuna!"


def s5_face_off(sc, cam):
    a = Hero.load(RIGS["ARJUNA"], "ARJUNA", loc=(-1.25, 0, 0), face=90)    # faces +X
    k = Hero.load(RIGS["KARNA"], "KARNA", loc=(1.25, 0, 0), face=-90)      # faces -X
    n = 6 * FPS
    POINT = ((0.1, -1, 0.12), (0.02, -1, 0.1), (0.0, -1, 0.06))
    FIST = ((0.25, -0.15, -1), (0.12, -0.6, -0.8), (0.05, -0.7, -0.7))
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        for h in (a, k):
            h.reset(); breathe(h, t + (0.7 if h is k else 0))
        # Karna: raises his arm and points, calls out, lowers it
        u = ease(t, 0.8, 1.35) * (1 - ease(t, 4.4, 5.3))
        arm(k, "L", *lerp_arm(DOWN, POINT, u)); arm(k, "R", *DOWN)          # his left is the arm nearer the camera
        k.fingers("L", mix(25, 80, u), point=u > 0.3); k.fingers("R", 30)
        k.turn("head", "X", -4 * ease(t, 1.2, 1.5) * (1 - ease(t, 2.0, 2.6)))
        kf = k.say(LINE_ARJUNA, t)
        kf.update(brow_angry=track(t, [(0, 0.2), (1.1, 0.75), (3, 0.5)]), blink_L=blink(t, [0.4, 3.4]), blink_R=blink(t, [0.4, 3.4]))
        k.keys(kf); k.key_all(f)
        # Arjuna: head lifts, fists close, a half step in
        a.turn("head", "X", track(t, [(0, 6), (1.6, 6), (2.0, 0)]))
        g = ease(t, 2.0, 2.6)
        arm(a, "R", *lerp_arm(DOWN, FIST, g * 0.6)); arm(a, "L", *lerp_arm(DOWN, FIST, g * 0.4))
        a.fingers("R", mix(20, 85, g)); a.fingers("L", mix(20, 80, g))
        st = ease(t, 3.0, 3.7)
        a.move("foot_ik.R", (0, -0.32 * st, 0.07 * math.sin(math.pi * st)))
        a.move("torso", (0, -0.16 * st, -0.02 * st))
        a.turn("chest", "X", 4 * st, keep=True)
        a.keys(dict(brow_angry=track(t, [(1.6, 0), (2.1, 0.8)]), mouth_press=track(t, [(2.0, 0), (2.4, 0.6)]),
                    blink_L=blink(t, [1.0, 4.6]), blink_R=blink(t, [1.0, 4.6])))
        a.key_all(f)
        look(cam, mix((0.0, -4.9, 0.95), (0.0, -4.4, 1.0), ease(t, 0, 6)), (0.0, 0, 1.0), 40)
        key_cam(cam, f)
    return n


SEQS = [s1_karna_speaks, s2_arjuna_arrow, s3_krishna_blessing, s4_karna_walk, s5_face_off]

for fn in SEQS:
    tag = fn.__name__.split("_")[0]
    if ONLY and tag not in ONLY:
        continue
    sc, cam = stage()
    n = fn(sc, cam)
    sc.frame_start, sc.frame_end = 1, n
    sc.frame_step = 4 if PREVIEW else 2
    d = OUT / fn.__name__
    d.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f"{fn.__name__}.blend"), compress=True)
    sc.render.filepath = str(d / "f_")
    sc.render.image_settings.file_format = "PNG"
    print("rendering", fn.__name__, n, "frames, step", sc.frame_step, flush=True)
    bpy.ops.render.render(animation=True)
    print("done", fn.__name__, flush=True)

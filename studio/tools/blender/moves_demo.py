"""Battle moves and bows test: the moves library (moves.py) on the rigged heroes with their rigged bows (bows.py).

  1 arjuna_shot   Arjuna nocks, draws Gandiva to his jaw, holds, looses; the arrow flies out of frame       3.4 s
  2 karna_shot    the same with Karna and Vijaya, seen from his bow side                                      3.4 s
  3 karna_defend  Karna blocks, then dodges to his left and to his right                                     3.8 s
  4 arjuna_run    Arjuna runs past the camera                                                                 3.0 s
  5 bows          check: Gandiva and Vijaya at rest and at full draw, side by side (one still)

  python moves_demo.py <out_dir> [names...] [--preview | --still]
Free, cloud Blender (Cycles CPU). Drawings on twos, 960x540.
"""
import math, pathlib, sys
import bpy
from mathutils import Vector

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from anim_lib import Hero, ease, track, mix
import moves
from bows import Bow, make_arrow, place_arrow

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
STILL = "--still" in args
PREVIEW = "--preview" in args or STILL
args = [a for a in args if not a.startswith("--")]
OUT = pathlib.Path(args[0]).resolve()
ONLY = args[1:]
STUDIO = pathlib.Path(__file__).resolve().parents[2]
CAST = STUDIO / "cast"
RIGS = {"ARJUNA": CAST / "arjuna/model/rig/arjuna_hero_v2.blend", "KARNA": CAST / "karna/model/rig/karna_hero_v3.blend"}
VIJAYA = CAST / "karna/model/trellis_out/karna_bow_1536.glb"
FPS = 24


def stage():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.preferences.addon_enable(module="rigify")
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 4 if PREVIEW else 16
    sc.cycles.use_denoising = True; sc.render.use_persistent_data = True
    sc.render.resolution_x, sc.render.resolution_y = (480, 270) if PREVIEW else (960, 540)
    sc.render.fps = FPS
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
    w = bpy.data.worlds.new("sky"); sc.world = w; w.use_nodes = True
    N, L = w.node_tree.nodes, w.node_tree.links
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); ramp = N.new("ShaderNodeValToRGB")
    L.new(tc.outputs["Generated"], sep.inputs[0]); L.new(sep.outputs["Z"], ramp.inputs["Fac"])
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (0.95, 0.72, 0.5, 1); e[1].position, e[1].color = 0.3, (0.3, 0.45, 0.7, 1)
    L.new(ramp.outputs["Color"], N["Background"].inputs["Color"])
    bpy.ops.mesh.primitive_plane_add(size=200); g = bpy.context.object
    m = bpy.data.materials.new("field"); m.use_nodes = True; nt = m.node_tree
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.4; nz.inputs["Detail"].default_value = 8
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (0.3, 0.17, 0.08, 1); cr.color_ramp.elements[1].color = (0.6, 0.4, 0.2, 1)
    nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95; g.data.materials.append(m)
    for en, col, rot in ((3.4, (1.0, 0.85, 0.66), (55, 0, -40)), (1.4, (0.55, 0.68, 1.0), (60, 0, 145))):
        l = bpy.data.lights.new("sun", "SUN"); l.energy = en; l.color = col; l.angle = math.radians(3)
        o = bpy.data.objects.new("sun", l); sc.collection.objects.link(o); o.rotation_euler = [math.radians(a) for a in rot]
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.sensor_width = 36
    return sc, cam


def look(cam, pos, target, lens, f=None):
    cam.location = pos; cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler(); cam.data.lens = lens
    if f is not None:
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f); cam.data.keyframe_insert("lens", frame=f)


def blink(t, times, dur=0.16):
    return max([1 - abs((t - b) / (dur / 2)) for b in times if abs(t - b) < dur / 2] + [0.0])


T_LOOSE = 2.2                                                          # draw 0-1.4, hold to 2.2, then the release


def shoot(h, bow, arrow, t, f):
    h.reset()
    if t < T_LOOSE:
        moves.bow_draw(h, t)
    else:
        moves.bow_release(h, t - T_LOOSE)
    h.keys(dict(blink_L=blink(t, [0.5]), blink_R=blink(t, [0.5])))
    h.key_all(f)
    if t < T_LOOSE:
        p = moves.bow_string_point(h) if t > 0.9 else bow.string_world()
        bow.draw_to(p, f)
        bpy.context.view_layer.update(); nock = bow.nock.matrix_world.translation.copy()
        place_arrow(arrow, nock, bow.grip_world(), f)                 # nocked on the string, resting over his fist
        arrow.hide_render = t < 0.35
        shoot.last = (nock.copy(), (bow.grip_world() - nock).normalized())
    else:
        bow.rest(f)
        tail, d = shoot.last
        place_arrow(arrow, tail + d * 48.0 * (t - T_LOOSE), tail + d * (48.0 * (t - T_LOOSE) + 1), f)
        arrow.hide_render = t - T_LOOSE > 0.35
    arrow.keyframe_insert("hide_render", frame=f)


def setup_archer(tag, bow):
    h = Hero.load(RIGS[tag], tag)
    h.reset(); moves.bow_draw(h, 1.6); bow.attach(h)
    return h


def arjuna_shot(sc, cam):
    bow = Bow.gandiva(); h = setup_archer("ARJUNA", bow); arrow = make_arrow("steel")
    n = int(3.4 * FPS)
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        shoot(h, bow, arrow, t, f)
        look(cam, mix((-1.3, -3.1, 1.45), (-0.9, -2.6, 1.5), ease(t, 0, 3.4)), (0.35, 0, 1.38), 38, f)
    return n


def karna_shot(sc, cam):
    bow = Bow.vijaya(VIJAYA); h = setup_archer("KARNA", bow); arrow = make_arrow("gold")
    n = int(3.4 * FPS)
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        shoot(h, bow, arrow, t, f)
        look(cam, mix((2.6, -2.4, 1.5), (2.2, -2.0, 1.5), ease(t, 0, 3.4)), (0.25, 0, 1.4), 40, f)
    return n


def karna_defend(sc, cam):
    h = Hero.load(RIGS["KARNA"], "KARNA")
    n = int(3.8 * FPS)
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        h.reset()
        if t < 1.3:
            moves.block(h, t)
        elif t < 2.55:
            moves.dodge(h, t - 1.3, side=1)
        else:
            moves.dodge(h, t - 2.55, side=-1)
        h.keys(dict(blink_L=blink(t, [1.25, 3.0]), blink_R=blink(t, [1.25, 3.0])))
        h.key_all(f)
        look(cam, (0.9, -3.6, 1.2), (0.0, 0, 1.05), 36, f)
    return n


def arjuna_run(sc, cam):
    h = Hero.load(RIGS["ARJUNA"], "ARJUNA", face=90)                    # runs toward +X
    n = int(3.0 * FPS)
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        h.reset(); moves.run(h, t)
        h.rig.location = (-4.0 + moves.RUN_SPEED * t, 0, 0); h.rig.keyframe_insert("location", frame=f)
        h.keys(dict(brow_angry=0.4, mouth_press=0.3)); h.key_all(f)
        x = -4.0 + moves.RUN_SPEED * t
        look(cam, (mix(-1.0, 3.0, ease(t, 0, 3)), -4.2, 1.1), (x + 0.3, 0, 1.0), 35, f)
    return n


def bows(sc, cam):
    """still: each bow at rest (left) and at full draw (right)"""
    g1 = Bow.gandiva(); g2 = Bow.gandiva(); v1 = Bow.vijaya(VIJAYA); v2 = Bow.vijaya(VIJAYA)
    for i, b in enumerate((g1, g2, v1, v2)):
        b.obj.location = (-1.5 + i * 1.0, 0, 1.0); b.obj.rotation_euler = (0, 0, 0)                  # side on: string to the right (+X)
    bpy.context.view_layer.update()
    for b in (g1, v1):
        b.rest(1)
    for b in (g2, v2):
        b.draw_to(b.obj.matrix_world @ Vector((0.6, 0, 0)), 1)
        a = make_arrow("steel" if b is g2 else "gold")
        bpy.context.view_layer.update()
        place_arrow(a, b.nock.matrix_world.translation, b.grip_world(), 1)
    sc.render.resolution_x, sc.render.resolution_y = 1400, 600
    look(cam, (0.1, -5.4, 1.05), (0.1, 0, 1.0), 40, 1)
    return 1


STILLS = {"karna_defend": [10, 40, 70, 88], "arjuna_shot": [12, 30, 52, 56], "karna_shot": [12, 30, 52, 56]}
SEQS = [arjuna_shot, karna_shot, karna_defend, arjuna_run, bows]
for fn in SEQS:
    if ONLY and fn.__name__ not in ONLY:
        continue
    sc, cam = stage()
    n = fn(sc, cam)
    sc.frame_start, sc.frame_end = 1, n
    sc.frame_step = 4 if (PREVIEW and not STILL) else 2
    d = OUT / fn.__name__; d.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f"{fn.__name__}.blend"), compress=True)
    print("rendering", fn.__name__, n, flush=True)
    if STILL or n == 1:
        for fr in STILLS.get(fn.__name__, sorted({1, max(1, n // 3), max(1, (2 * n) // 3), n})):
            sc.frame_set(fr); sc.render.filepath = str(OUT / f"still_{fn.__name__}_{fr:03d}.png"); bpy.ops.render.render(write_still=True)
    else:
        sc.render.filepath = str(d / "f_"); bpy.ops.render.render(animation=True)
    print("done", fn.__name__, flush=True)

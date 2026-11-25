"""EP01 moves demo: every move in moves_ep01.MOVES on its hero (and bow), one clip each. Free, cloud Blender.

  python moves_ep01_demo.py <out_dir> [move or move_hero ...] [--still] [--resume]
--still renders 3 small frames a clip for a pose check (contact sheet: still_sheet.jpg). Drawings on twos, 960x540.
Rigs: the newest detail-pass rig of each hero (karna v4, arjuna v4, krishna v3), else the older one.
"""
import math, pathlib, sys
import bpy
from mathutils import Vector

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from anim_lib import Hero
import moves, moves_ep01
from bows import Bow, make_arrow, place_arrow

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
STILL = "--still" in args
RESUME = "--resume" in args
args = [a for a in args if not a.startswith("--")]
OUT = pathlib.Path(args[0]).resolve()
ONLY = args[1:]
CAST = pathlib.Path(__file__).resolve().parents[2] / "cast"
VIJAYA = CAST / "karna/model/trellis_out/karna_bow_1536.glb"
FPS = 24


def rig(hero):
    for v in (4, 3, 2):
        p = CAST / f"{hero}/model/rig/{hero}_hero_v{v}.blend"
        if p.exists():
            return p


def stage():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.preferences.addon_enable(module="rigify")
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 4 if STILL else 16
    sc.cycles.use_denoising = True; sc.render.use_persistent_data = True
    sc.render.resolution_x, sc.render.resolution_y = (480, 270) if STILL else (960, 540)
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


def look(cam, pos, target, lens):
    cam.location = pos; cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler(); cam.data.lens = lens


def box(name, size, loc, col):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.object; o.name = name; o.scale = size
    m = bpy.data.materials.new(name); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*col, 1); o.data.materials.append(m)
    return o


def wheel():
    """a plain chariot wheel standing in front of him, half sunk; lifted by the heave"""
    bpy.ops.mesh.primitive_torus_add(major_radius=0.72, minor_radius=0.05, major_segments=48, minor_segments=8)
    w = bpy.context.object; w.name = "wheel"
    gold = bpy.data.materials.new("wheel"); gold.use_nodes = True; b = gold.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.7, 0.45, 0.12, 1); b.inputs["Metallic"].default_value = 0.8; b.inputs["Roughness"].default_value = 0.35
    w.data.materials.append(gold)
    for i in range(8):                                                 # spokes in the wheel's own plane, before it is turned
        bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=1.4, vertices=8, rotation=(math.pi / 2, 0, math.pi / 8 * i))
        s = bpy.context.object; s.data.materials.append(gold); s.parent = w
    w.rotation_euler = (0, math.pi / 2, 0)                             # side on to him: he grips the near edge of the rim
    return w


# camera per clip: (position, target, lens)
FULL = ((2.7, -4.6, 1.35), (0, 0, 0.95), 38)
FACE = ((0.75, -1.9, 1.7), (0, 0, 1.6), 55)
ARCH = ((-1.2, -4.4, 1.45), (0.4, 0, 1.25), 38)                       # archers: from the front, the target to frame right
CAMS = {"bow_salute": FACE, "exhausted": FACE, "quiver_draw": ((1.6, -3.0, 1.5), (0, 0, 1.25), 40), "calm_look": FACE,
        "leap_down": ((4.2, -4.4, 1.9), (0, -0.8, 1.0), 32), "heave": ((3.4, -0.9, 1.1), (0, -0.7, 0.65), 34),
        "palm_wait": ((1.4, -3.2, 1.45), (0, 0, 1.25), 40), "head_hit": FULL, "rise_hair_push": FULL,
        "bow_draw": ARCH, "bow_draw_ear": ARCH, "fan_release": ARCH, "rapid_fire": ARCH, "bow_lower": ARCH,
        "stand_tall": ((0.5, -3.3, 0.45), (0, 0, 1.2), 35), "charioteer": FULL, "reins_flick": FULL, "foot_press": FULL}
DRAW = {"bow_draw": lambda t: t > 0.9, "bow_draw_ear": lambda t: t > 1.15, "fan_release": lambda t: 0.9 < t < 1.8,
        "rapid_fire": lambda t: 0.3 < (t % 0.7) / 0.7 < 0.8}


def clip(name, hero):
    fn, dur, _, has_bow = moves_ep01.MOVES[name]
    sc, cam = stage()
    tag = hero.upper()
    h = Hero.load(rig(hero), tag)
    bow = arrow = None
    if has_bow:
        bow = Bow.vijaya(VIJAYA) if hero == "karna" else Bow.gandiva()
        h.reset(); moves.bow_draw(h, 1.6); bow.attach(h)
        arrow = make_arrow("gold" if hero == "karna" else "steel")
    base = Vector((0, 0, 0))
    if name == "leap_down":
        box("chariot_floor", (1.4, 1.6, 1.0), (0, 0.2, 0.5), (0.35, 0.08, 0.06)); base = Vector((0, 0, 1.0))
    w = wheel() if name == "heave" else None
    look(cam, *CAMS[name])
    n = int(round(dur * FPS))
    for f in range(1, n + 1):
        t = (f - 1) / FPS
        h.reset()
        off = fn(h, t)
        h.rig.location = base + (Vector(off) if off else Vector()); h.rig.keyframe_insert("location", frame=f)
        h.key_all(f)
        if w is not None:
            from anim_lib import ease
            w.location = (0, -1.2, 0.4 + 0.3 * ease(t, 0.8, 3.0)); w.keyframe_insert("location", frame=f)
        if name == "quiver_draw":                                      # the arrow he pulls from the quiver, in his right fist
            bpy.context.view_layer.update()
            hb = h.pb["DEF-hand.R"]; a0 = h.rig.matrix_world @ hb.head; a1 = h.rig.matrix_world @ hb.tail
            g = a1 + (a1 - a0).normalized() * 0.02; up = (h.rig.matrix_world @ h.pb["DEF-forearm.R"].head - g).normalized()
            place_arrow(arrow, g + up * 0.25, g - up * 0.55, f)       # tail low behind the fist, head up past it
            arrow.hide_render = t < 0.7; arrow.keyframe_insert("hide_render", frame=f)
            continue
        if bow is not None:
            drawn = DRAW.get(name, lambda t: False)(t)
            if drawn:
                bow.draw_to(moves.bow_string_point(h), f)
                bpy.context.view_layer.update(); nock = bow.nock.matrix_world.translation.copy()
                place_arrow(arrow, nock, bow.grip_world(), f)
            else:
                bow.rest(f)
            arrow.hide_render = not drawn; arrow.keyframe_insert("hide_render", frame=f)
    sc.frame_start, sc.frame_end, sc.frame_step = 1, n, 2
    return sc, n


jobs = [(m, hero) for m, (_, _, heroes, _) in moves_ep01.MOVES.items() for hero in heroes]
for m, hero in jobs:
    key = f"{m}_{hero}"
    if ONLY and m not in ONLY and key not in ONLY:
        continue
    d = OUT / key
    sc, n = clip(m, hero)
    print("clip", key, n, flush=True)
    if STILL:
        for fr in sorted({1, n // 2 + 1 - (n // 2) % 2, n - 1 + n % 2}):
            sc.frame_set(fr); sc.render.filepath = str(OUT / f"still_{key}_{fr:03d}.png"); bpy.ops.render.render(write_still=True)
    else:
        d.mkdir(parents=True, exist_ok=True)
        sc.render.use_overwrite = not RESUME
        sc.render.filepath = str(d / "f_"); bpy.ops.render.render(animation=True)
    print("done", key, flush=True)

if STILL:
    from PIL import Image, ImageDraw
    shots = sorted(OUT.glob("still_*.png"))
    rows = {}
    for p in shots:
        rows.setdefault(p.stem.rsplit("_", 1)[0][6:], []).append(p)
    W, H = 480, 270
    sheet = Image.new("RGB", (W * 3, H * len(rows)), (20, 20, 20)); dr = ImageDraw.Draw(sheet)
    for r, (k, ps) in enumerate(rows.items()):
        for c, p in enumerate(ps[:3]):
            sheet.paste(Image.open(p).convert("RGB"), (c * W, r * H))
        dr.text((8, r * H + 6), k, fill=(255, 255, 0))
    sheet.save(OUT / "still_sheet.jpg", quality=85)
    print("sheet", OUT / "still_sheet.jpg")

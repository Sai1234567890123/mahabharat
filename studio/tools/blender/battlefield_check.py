"""Check renders of the Kurukshetra backdrop (battlefield.py): a wide aerial, a ground view past Arjuna's chariot toward
the Kaurava line, and a low side view down the gap between the hosts. Free, cloud Blender.

  python battlefield_check.py <out_dir> [--preview]
"""
import math, pathlib, sys
import bpy
from mathutils import Vector

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import battlefield

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
PREVIEW = "--preview" in args
OUT = pathlib.Path([a for a in args if not a.startswith("--")][0]).resolve(); OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 6 if PREVIEW else 24; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = (480, 270) if PREVIEW else (1280, 720)
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
w = bpy.data.worlds.new("sky"); sc.world = w; w.use_nodes = True
N, L = w.node_tree.nodes, w.node_tree.links
tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); ramp = N.new("ShaderNodeValToRGB")
L.new(tc.outputs["Generated"], sep.inputs[0]); L.new(sep.outputs["Z"], ramp.inputs["Fac"])
e = ramp.color_ramp.elements
e[0].position, e[0].color = 0.0, (0.95, 0.78, 0.58, 1); e[1].position, e[1].color = 0.35, (0.32, 0.48, 0.75, 1)
L.new(ramp.outputs["Color"], N["Background"].inputs["Color"]); N["Background"].inputs["Strength"].default_value = 1.0

bf = battlefield.build(seed=3)
bf.sun(elev=30, azim=35)


def kit(name, at, yaw):
    with bpy.data.libraries.load(battlefield.KIT.format(name), link=False) as (src, dst):
        dst.objects = list(src.objects)
    o = next(x for x in dst.objects if x.type == "MESH"); sc.collection.objects.link(o)
    o.location = at; o.rotation_euler = (0, 0, math.radians(yaw))
    return o


kit("krk_arjuna_chariot", (-4, -22, 0), 180)                           # faces +Y, toward the Kauravas
for dx in (-1.1, -0.37, 0.37, 1.1):                                    # his four white horses, astride the pole
    kit("krk_horse_white", (-4 + dx, -22 + 2.4, 0), 180)
kit("krk_rank_chariot_red", (6, 24, 0), 0); kit("krk_horse_team_dark", (6, 24 - 1.6, 0), 0)

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_width = 36; cam.data.clip_end = 3000
for name, pos, tgt, lens in (("wide", (150, -230, 45), (0, 30, 0), 32),
                             ("ground", (-8, -42, 2.4), (0, 60, 4), 45),
                             ("gap", (-110, -6, 1.7), (40, 8, 2.5), 35)):
    cam.location = pos; cam.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler(); cam.data.lens = lens
    sc.render.filepath = str(OUT / f"battlefield_{name}.png"); bpy.ops.render.render(write_still=True)
    print("rendered", name, flush=True)

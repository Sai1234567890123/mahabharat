"""Check render: Shalya driving Karna's chariot (dun team, elephant's-rope standard), mid-ground, as in A02, A06, A16.

  EGL_PLATFORM=surfaceless python3 shalya_chariot_check.py <out.jpg>
The kit chariot carries a generic driver; it is cut out and Shalya stands in his place, reins in both hands
(moves_ep01.charioteer). EEVEE, 1280x720, three angles side by side.
"""
import math, pathlib, sys
import bpy, bmesh
from mathutils import Vector

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from anim_lib import Hero                     # noqa: E402
import banners, moves_ep01                     # noqa: E402

STUDIO = HERE.parent.parent
KIT = pathlib.Path("/mnt/project-files/kurukshetra/hero/blend")
OUT = pathlib.Path(sys.argv[-1]).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="rigify")
sc = bpy.context.scene


def append_kit(name):
    with bpy.data.libraries.load(str(KIT / f"SM_{name}.blend"), link=False) as (src, dst):
        dst.objects = list(src.objects)
    for o in dst.objects:
        sc.collection.objects.link(o)
    return dst.objects[0]


ch = append_kit("krk_rank_chariot"); hs = append_kit("krk_horse_team_dark")
for m in hs.data.materials:                                              # Karna's dun team (passport choice)
    if m and m.name.startswith("MAT_Bay"):
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.22, 0.13, 0.05, 1)
for m in ch.data.materials:
    if m and m.name.startswith("MAT_Saffron"):
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.36, 0.05, 0.06, 1)
hs.parent = ch; hs.location = (0, -(ch.dimensions.y * 0.5 + hs.dimensions.y * 0.5) + 4.5, 0)
std = banners.make("elephant_rope", height=7.0); std.parent = ch; std.location = (1.25, 2.9, 0.6)

# cut the kit's own driver (the loose parts standing at the front of the car)
bm = bmesh.new(); bm.from_mesh(ch.data); bm.verts.ensure_lookup_table()
seed = [v for v in bm.verts if abs(v.co.x) < 0.8 and -1.6 < v.co.y < -0.4 and 0.95 < v.co.z < 2.8]
part, stack = set(), list(seed)
while stack:
    v = stack.pop()
    if v in part:
        continue
    part.add(v); stack.extend(e.other_vert(v) for e in v.link_edges)
if 0 < len(part) < 0.2 * len(bm.verts):
    bmesh.ops.delete(bm, geom=list(part), context="VERTS"); print("cut kit driver verts", len(part))
else:
    print("kit driver not cut (connected to the car):", len(part), "of", len(bm.verts))
bm.to_mesh(ch.data); bm.free()

h = Hero.load(STUDIO / "cast/shalya/model/rig/shalya_hero_v1.blend", "SHALYA", loc=(0, -1.0, 0.84), face=0)
h.reset(); moves_ep01.charioteer(h, 0.4); h.key_all(1)

gnd_mat = bpy.data.materials.new("earth"); gnd_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.32, 0.16, 0.08, 1)
bpy.ops.mesh.primitive_plane_add(size=200); bpy.context.object.data.materials.append(gnd_mat)
sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 4.5; sun.color = (1.0, 0.8, 0.6); sun.angle = 0.05
so = bpy.data.objects.new("sun", sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(62), 0, math.radians(-120))
sc.world = bpy.data.worlds.new("sky"); sc.world.color = (0.55, 0.62, 0.75)
sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = 16
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
cam = bpy.data.cameras.new("cam"); co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
shots = []
for name, pos, aim, lens in (("mid_front34", (-9, -12, 3.0), (0, -1.5, 1.6), 50),
                             ("mid_back34", (8, 9, 3.2), (0, -1.0, 1.8), 50),
                             ("close_driver", (-3.0, -4.2, 2.6), (0, -1.0, 2.0), 45)):
    co.location = pos; co.rotation_euler = (Vector(aim) - Vector(pos)).to_track_quat("-Z", "Y").to_euler(); cam.lens = lens
    p = OUT.with_name(f"_{name}.png"); sc.render.filepath = str(p); bpy.ops.render.render(write_still=True); shots.append(p)
from PIL import Image
ims = [Image.open(p).convert("RGB") for p in shots]
sheet = Image.new("RGB", (1280 * 3, 720))
for i, im in enumerate(ims):
    sheet.paste(im, (1280 * i, 0))
sheet.save(OUT, quality=88)
for p in shots:
    p.unlink()
print("checks", OUT)

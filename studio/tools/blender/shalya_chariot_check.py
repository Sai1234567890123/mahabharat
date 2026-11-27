"""Check render: Shalya driving Karna's chariot (dun team of Hastinapur TRELLIS horses, elephant's-rope standard), mid-ground, as in A02, A06, A16.

  EGL_PLATFORM=surfaceless python3 shalya_chariot_check.py <out.jpg>
Scene from karna_chariot.build: kit driver cut out, Shalya at the reins (moves_ep01.charioteer), reins to each bit. EEVEE, 1280x720, three angles side by side.
"""
import math, pathlib, sys
import bpy
from mathutils import Vector

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import karna_chariot                          # noqa: E402

OUT = pathlib.Path(sys.argv[-1]).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="rigify")
sc = bpy.context.scene
ch, h, team = karna_chariot.build(rigged=True, reins_on=True)       # rigged Hastinapur horses standing, reins strung

gnd_mat = bpy.data.materials.new("earth"); gnd_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.32, 0.16, 0.08, 1)
bpy.ops.mesh.primitive_plane_add(size=200); bpy.context.object.data.materials.append(gnd_mat)
sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 4.5; sun.color = (1.0, 0.8, 0.6); sun.angle = 0.05
so = bpy.data.objects.new("sun", sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(62), 0, math.radians(-120))
sc.world = bpy.data.worlds.new("sky"); sc.world.color = (0.55, 0.62, 0.75)
sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = 16
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
cam = bpy.data.cameras.new("cam"); co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
shots = []
for name, pos, aim, lens in (("mid_front34", (-10, -14, 3.0), (0, -2.6, 1.5), 45),
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

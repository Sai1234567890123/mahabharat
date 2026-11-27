"""A05 check: Karna's chariot at full gallop. Shalya drives, four rigged Hastinapur horses (dun) gallop, reins strung.

  EGL_PLATFORM=surfaceless python3 chariot_gallop_check.py <out.mp4|out.jpg> [--frames 48]
A .jpg writes a 4x2 sheet of one stride (and the standing team with reins); an .mp4 renders a tracking shot.
"""
import math, pathlib, subprocess, sys
import bpy
from mathutils import Vector

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from anim_lib import Hero                                  # noqa: E402
import banners, horse_gaits, horse_team, moves_ep01, reins  # noqa: E402
import karna_chariot                                       # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OUT = pathlib.Path(args[0]).resolve()
FRAMES = int(args[args.index("--frames") + 1]) if "--frames" in args else 48
FPS, SPEED = 24, 9.0                      # m/s: a chariot team at full gallop

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="rigify")
sc = bpy.context.scene
sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, FRAMES
ch, h, team = karna_chariot.build(rigged=True, reins_on=True)
rigs = [bpy.data.objects[n] for n in team["rigs"]]

for f in range(1, FRAMES + 1):
    t = (f - 1) / FPS
    ch.location = (0, -SPEED * t, 0); ch.keyframe_insert("location", frame=f)
    h.reset(); moves_ep01.charioteer(h, t, sway=1.6); h.key_all(f)
for i, r in enumerate(rigs):                                   # the four do not step in lockstep
    horse_gaits.key(r, "gallop", 1, FRAMES, FPS, phase=(0.0, 0.07, 0.03, 0.11)[i])
for fc in ch.animation_data.action.fcurves if hasattr(ch.animation_data.action, "fcurves") else []:
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"

# ground with enough grain to read speed
gm = bpy.data.materials.new("earth"); nt = gm.node_tree
noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 1.2; noise.inputs["Detail"].default_value = 8
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.20, 0.10, 0.05, 1); ramp.color_ramp.elements[1].color = (0.42, 0.24, 0.12, 1)
nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
bpy.ops.mesh.primitive_plane_add(size=400); bpy.context.object.data.materials.append(gm)
sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 4.5; sun.color = (1.0, 0.82, 0.62); sun.angle = 0.05
so = bpy.data.objects.new("sun", sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(55), 0, math.radians(-60))
sc.world = bpy.data.worlds.new("sky"); sc.world.color = (0.55, 0.62, 0.75)
sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = 8
sc.render.resolution_x, sc.render.resolution_y = 960, 540
cam = bpy.data.cameras.new("cam"); co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
co.parent = ch; pos, aim = Vector((-13.5, -4.2, 2.4)), Vector((0, -2.6, 1.4))   # tracking alongside, as A05
co.location = pos; co.rotation_euler = (aim - pos).to_track_quat("-Z", "Y").to_euler(); cam.lens = 35

tmp = OUT.with_suffix(""); tmp.mkdir(exist_ok=True)
frames = range(1, FRAMES + 1) if OUT.suffix == ".mp4" else [1 + round(i * 0.48 * FPS / 8) for i in range(8)]
for f in frames:
    sc.frame_set(f); reins.update()
    sc.render.filepath = str(tmp / f"f{f:04d}.png"); bpy.ops.render.render(write_still=True)
if OUT.suffix == ".mp4":
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(OUT)], check=True)
else:
    from PIL import Image
    ims = [Image.open(tmp / f"f{f:04d}.png").convert("RGB") for f in frames]
    W, H = ims[0].size; sheet = Image.new("RGB", (W * 4, H * 2))
    for i, im in enumerate(ims):
        sheet.paste(im, (W * (i % 4), H * (i // 4)))
    sheet.save(OUT, quality=88)
for p in tmp.glob("f*.png"):
    p.unlink()
tmp.rmdir()
print("gallop check", OUT)

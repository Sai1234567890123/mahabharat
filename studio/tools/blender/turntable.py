#!/usr/bin/env python3
"""Free check render of a GLB: N views around the model, warm key light, cool rim light, plain backdrop.

  python studio/tools/blender/turntable.py MODEL.glb OUT_PREFIX [--views 4] [--samples 32] [--size 900]
Writes OUT_PREFIX_<angle>.png and OUT_PREFIX_sheet.jpg. The model is scaled to 1.9 m tall (a 3D model of Karna is about
human height) and stands on the floor. Uses Cycles on the CPU, so it runs in the cloud with `pip install bpy`.
"""
import argparse, math, pathlib, sys
import bpy
from mathutils import Vector

ap = argparse.ArgumentParser()
ap.add_argument("glb"); ap.add_argument("out")
ap.add_argument("--views", type=int, default=4); ap.add_argument("--samples", type=int, default=32)
ap.add_argument("--size", type=int, default=900); ap.add_argument("--height", type=float, default=1.9)
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a.glb)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
s = a.height / max(hi.z - lo.z, 1e-6)
root = bpy.data.objects.new("ROOT", None); bpy.context.scene.collection.objects.link(root)
for o in bpy.context.scene.objects:
    if o.parent is None and o is not root:
        o.parent = root
root.scale = (s, s, s)
root.location = (-(lo.x + hi.x) / 2 * s, -(lo.y + hi.y) / 2 * s, -lo.z * s)
bpy.context.view_layer.update()
print("dims (m)", [round(v * s, 3) for v in (hi - lo)], "meshes", len(objs),
      "verts", sum(len(o.data.vertices) for o in objs))

sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.samples = a.samples; sc.cycles.device = "CPU"
sc.render.resolution_x, sc.render.resolution_y = a.size * 3 // 4, a.size
sc.view_settings.view_transform = "AgX"
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.52, 0.48, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
bpy.ops.mesh.primitive_plane_add(size=20); fl = bpy.context.object
m = bpy.data.materials.new("floor"); m.use_nodes = True
m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.38, 0.33, 1); fl.data.materials.append(m)

def light(name, kind, energy, color, loc, rot):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = color
    if kind == "AREA": d.size = 3
    o = bpy.data.objects.new(name, d); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = [math.radians(r) for r in rot]
light("key", "SUN", 3.2, (1.0, 0.86, 0.68), (0, 0, 5), (50, 0, -35))
light("rim", "SUN", 2.4, (0.62, 0.74, 1.0), (0, 0, 5), (60, 0, 160))

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
tgt = Vector((0, 0, a.height * 0.52)); dist = a.height * 2.25
paths = []
for i in range(a.views):
    ang = 2 * math.pi * i / a.views                         # 0 = front: the model faces -Y after the glTF import
    cam.location = tgt + Vector((math.sin(ang) * dist, -math.cos(ang) * dist, 0.15))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{a.out}_{round(math.degrees(ang)):03d}.png"; bpy.ops.render.render(write_still=True)
    paths.append(sc.render.filepath)

from PIL import Image
ims = [Image.open(p).convert("RGB") for p in paths]
sheet = Image.new("RGB", (sum(i.width for i in ims), ims[0].height))
for k, im in enumerate(ims):
    sheet.paste(im, (k * im.width, 0))
sheet.save(f"{a.out}_sheet.jpg", quality=88); print("wrote", f"{a.out}_sheet.jpg")

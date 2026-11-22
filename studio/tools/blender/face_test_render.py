"""Free check renders of a face rig: an expression sheet and, optionally, a short lip-sync test from a mouth-shape track.

  python face_test_render.py <face.blend> <out_dir> sheet
  python face_test_render.py <face.blend> <out_dir> line "<track>"     track: "shape:seconds ..." with Rhubarb shapes A-H, X
"""
import json, math, pathlib, sys
import bpy

blend, out, mode = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3]
out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
for o in sc.objects:
    if o.name.startswith("WGT"):
        o.hide_render = True
cam = bpy.data.cameras.new("face_cam"); co = bpy.data.objects.new("face_cam", cam); sc.collection.objects.link(co)
co.location = (0.25, -0.82, 1.64); co.rotation_euler = (math.radians(90), 0, math.radians(17)); cam.lens = 85
sc.camera = co
for e, rz, rx in ((3.2, -35, 62), (0.9, 45, 75)):
    l = bpy.data.lights.new("face_key", "SUN"); l.energy = e; lo = bpy.data.objects.new("face_key", l); sc.collection.objects.link(lo)
    lo.rotation_euler = (math.radians(rx), 0, math.radians(rz))
sc.render.engine = "CYCLES"; sc.cycles.samples = 24; sc.cycles.device = "CPU"
sc.render.resolution_x = sc.render.resolution_y = 384
keys = bpy.data.objects["KARNA_body"].data.shape_keys.key_blocks
visemes = json.loads(pathlib.Path(blend).with_suffix(".visemes.json").read_text())

def pose(mix):
    for k in keys[1:]:
        k.value = mix.get(k.name, 0.0)

if mode == "sheet":
    cells = [("neutral", {}), ("jaw_open", {"jaw_open": 1}), ("AA (D)", visemes["D"]), ("OO (F)", visemes["F"]),
             ("EE wide", {"mouth_wide": 1, "jaw_open": 0.2}), ("M press", visemes["A"]),
             ("smile", {"smile_L": 1, "smile_R": 1, "brow_up": 0.3}), ("sorrow", {"brow_sad": 1, "frown": 0.7}),
             ("anger", {"brow_angry": 1, "frown": 0.4, "jaw_open": 0.15}), ("blink", {"blink_L": 1, "blink_R": 1}),
             ("surprise", {"brow_up": 1, "jaw_open": 0.6}), ("proud half smile", {"smile_L": 0.8, "brow_angry": 0.2})]
    for i, (name, mix) in enumerate(cells):
        pose(mix)
        sc.render.filepath = str(out / f"sheet_{i:02d}.png"); bpy.ops.render.render(write_still=True)
    (out / "sheet_labels.json").write_text(json.dumps([c[0] for c in cells]))
else:
    track = [(t.split(":")[0], float(t.split(":")[1])) for t in sys.argv[4].split()]
    fps = 24; t = 0.0; frame = 0
    for shape, dur in track:
        n = max(1, round(dur * fps))
        for j in range(n):
            pose(visemes[shape]); keys["blink_L"].value = keys["blink_R"].value = 1.0 if 30 <= frame <= 32 else 0.0
            sc.render.filepath = str(out / f"line_{frame:04d}.png"); bpy.ops.render.render(write_still=True); frame += 1

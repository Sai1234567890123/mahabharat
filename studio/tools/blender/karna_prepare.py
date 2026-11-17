#!/usr/bin/env python3
"""Free step after TRELLIS.2: make Karna's raw mesh ready for rigging (cloud Blender, `pip install bpy`).

  python studio/tools/blender/karna_prepare.py IN.glb OUT_DIR [--height 1.9] [--faces 120000]

1. Import, scale to HEIGHT metres, origin between the feet, front faces -Y, transforms applied.
2. Texture fixes on copies (the TRELLIS textures stay untouched):
   - base colour: the blue patches TRELLIS invented on the gold back plate are turned to gold (hue shift, value kept);
   - metal/rough: TRELLIS marked the whole body as metal (skin and cloth too). Metal is rebuilt from the base colour:
     gold and bronze areas are metal, skin, cloth and hair are not.
3. A lighter copy for rigging and animation, about FACES triangles, UVs kept.
Writes OUT_DIR/karna_work.blend, OUT_DIR/karna_basecolor.png, OUT_DIR/karna_metalrough.png. Never overwrites.
"""
import argparse, pathlib, sys
import bpy, numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("glb"); ap.add_argument("out")
ap.add_argument("--height", type=float, default=1.9); ap.add_argument("--faces", type=int, default=120000)
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
out = pathlib.Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
blend = out / "karna_work.blend"
if blend.exists():
    raise SystemExit(f"exists, not overwriting: {blend}")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(pathlib.Path(a.glb).resolve()))
body = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
body.name = body.data.name = "KARNA_body"
for o in list(bpy.context.scene.objects):
    if o is not body and o.type == "EMPTY":
        body.parent = None
bpy.context.view_layer.objects.active = body; body.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
v = np.empty(len(body.data.vertices) * 3); body.data.vertices.foreach_get("co", v); v = v.reshape(-1, 3)
lo, hi = v.min(0), v.max(0)
s = a.height / (hi[2] - lo[2])
v = (v - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])) * s
body.data.vertices.foreach_set("co", v.ravel()); body.data.update()
# front check: the chest (sun-face relief) sticks out further than the back plate; front must be -Y
chest = v[(v[:, 2] > 0.68 * a.height) & (v[:, 2] < 0.78 * a.height) & (np.abs(v[:, 0]) < 0.08 * a.height)]
if chest.size and abs(chest[:, 1].min()) < abs(chest[:, 1].max()):
    print("front was +Y, turning 180 degrees")
    v[:, :2] *= -1; body.data.vertices.foreach_set("co", v.ravel()); body.data.update()
print("dims (m)", np.round(v.max(0) - v.min(0), 3), "verts", len(v))

# ---- textures ----
mat = body.data.materials[0]
tex = {l.to_socket.name: n for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" for l in n.outputs[0].links}
base, mr = tex["Base Color"].image, tex["Color"].image
def arr(img):
    w, h = img.size; p = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(p); return p.reshape(h, w, 4)
def rgb2hsv(c):
    mx, mn = c.max(-1), c.min(-1); d = mx - mn + 1e-8
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    h = np.where(mx == r, (g - b) / d % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, np.where(mx > 0, d / (mx + 1e-8), 0), mx
B = arr(base); h, sat, val = rgb2hsv(B[..., :3])
blue = (h > 180) & (h < 265) & (sat > 0.22) & (val > 0.08)
gold_lum = val[blue]
B[blue, 0], B[blue, 1], B[blue, 2] = gold_lum * 1.0, gold_lum * 0.78, gold_lum * 0.30
print("blue texels turned gold:", int(blue.sum()))
h, sat, val = rgb2hsv(B[..., :3])
gold = (h > 28) & (h < 62) & (sat > 0.38) & (val > 0.22)
M = arr(mr)
M[..., 2] = np.where(gold, 0.85, 0.0)                    # glTF: blue channel = metal
M[..., 1] = np.where(gold, np.clip(M[..., 1], 0.30, 0.55), np.clip(M[..., 1], 0.55, 0.9))   # green = roughness
print("metal share of texels:", round(float(gold.mean()), 3))
for img, data, name in ((base, B, "karna_basecolor.png"), (mr, M, "karna_metalrough.png")):
    new = bpy.data.images.new(name[:-4], img.size[0], img.size[1], alpha=True)
    new.pixels.foreach_set(data.ravel()); new.filepath_raw = str(out / name); new.file_format = "PNG"; new.save()
    new.colorspace_settings.name = img.colorspace_settings.name
    (tex["Base Color"] if img is base else tex["Color"]).image = new

# ---- lighter copy for the rig ----
tris = len(body.data.polygons)
dec = body.modifiers.new("decimate", "DECIMATE"); dec.ratio = min(1.0, a.faces / tris)
bpy.ops.object.modifier_apply(modifier=dec.name)
print("faces", tris, "->", len(body.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=str(blend), relative_remap=True)
bpy.ops.file.make_paths_relative(); bpy.ops.wm.save_mainfile()
print("wrote", blend)

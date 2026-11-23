"""Karna's crown: richer gold with shaded recesses, and the stray scrap of his old crown removed (cloud Blender, free).

sai, 2026-11-23 (yes to "Karna's flat crown is the next free fix"). On karna_hero_v2.blend the crown was one flat beige
gold (hue 40, saturation 0.50, value 0.61-0.69 over the whole crown), while his chest armour and his locked head design
(cast/karna/model/web_head_v2.png) are a deep yellow gold with dark recesses (value 0.16-0.79). Also, a green leafy
scrap floated beside his left ear: what was left of the body model's own crown outside the new head's outline.

  1. the body's vertices above HEIGHT (the scrap; nothing else of the body reaches that high) are deleted;
  2. ambient occlusion is baked into the head's own UV layout;
  3. in a copy of the head's colour texture, every gold texel (hue 30-52, saturation over 0.3, bright) is repainted:
     hue 43, saturation 0.64, value from the baked occlusion (recesses down to about 0.30, raised edges up to 0.86),
     keeping the original's small brush variation. Skin, hair and the moustache are not gold, so they are untouched.

  python hero_crown.py <hero> <in.blend> <out.blend> [scrap_above_z]

Check renders next to <out>: _crown.jpg (front, three-quarter, side, back), and the AO bake as _crown_ao.png.
"""
import colorsys, math, pathlib, sys
import bpy, bmesh
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
HERO, IN, OUT = args[:3]
SCRAP_Z = float(args[3]) if len(args) > 3 else 1.62
TAG = HERO.upper()
if pathlib.Path(OUT).exists():
    sys.exit(f"exists, not overwriting (folder law 1): {OUT}")
out = pathlib.Path(OUT).resolve()
bpy.ops.wm.open_mainfile(filepath=str(pathlib.Path(IN).resolve()))
bpy.ops.preferences.addon_enable(module="rigify")
scene = bpy.context.scene
body, head = bpy.data.objects[f"{TAG}_body"], bpy.data.objects[f"{TAG}_head"]
for o in list(scene.objects):
    if o.type in ("CAMERA", "LIGHT"):
        bpy.data.objects.remove(o)


def select_only(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.hide_set(False); o.hide_viewport = False; o.select_set(True)
    bpy.context.view_layer.objects.active = o


# ---- 1. the scrap ------------------------------------------------------------------------------------------------------------
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
scrap = [v for v in bm.verts if (body.matrix_world @ v.co).z > SCRAP_Z]
print("scrap verts removed:", len(scrap), flush=True)
bmesh.ops.delete(bm, geom=scrap, context="VERTS"); bm.to_mesh(body.data); bm.free()

# ---- 2. ambient occlusion in the head's UVs -----------------------------------------------------------------------------------
mat = head.active_material
nt = mat.node_tree
tex = next(n for n in nt.nodes if n.type == "TEX_IMAGE" and any(l.to_socket.name == "Base Color" for l in n.outputs[0].links))
W, H = tex.image.size
ao_img = bpy.data.images.new(f"{TAG}_head_ao", 2048, 2048, float_buffer=False)
ao_node = nt.nodes.new("ShaderNodeTexImage"); ao_node.image = ao_img; nt.nodes.active = ao_node
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = 48
scene.render.bake.margin = 6
hidden = []
for o in scene.objects:                                            # occlusion from the head itself only (not the shoulders)
    if o is not head and o.type == "MESH" and not o.hide_render:
        o.hide_render = True; hidden.append(o)
select_only(head)
bpy.ops.object.bake(type="AO")
for o in hidden:
    o.hide_render = False
ao_img.filepath_raw = str(out.with_name(out.stem + "_crown_ao.png")); ao_img.file_format = "PNG"; ao_img.save()
ao = np.empty(2048 * 2048 * 4, np.float32); ao_img.pixels.foreach_get(ao); ao = ao.reshape(2048, 2048, 4)[..., 0]
nt.nodes.remove(ao_node); bpy.data.images.remove(ao_img)
yy = (np.arange(H) * 2048 // H).clip(0, 2047); xx = (np.arange(W) * 2048 // W).clip(0, 2047)
ao = ao[yy][:, xx]                                                 # nearest upscale to the colour texture
print("ao baked, mean", round(float(ao.mean()), 3), flush=True)

# ---- 3. repaint the gold ------------------------------------------------------------------------------------------------------
img = tex.image.copy(); img.name = f"{TAG}_head_colour_crown"
px = np.empty(W * H * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(H, W, 4)
rgb = px[..., :3]
mx, mn = rgb.max(-1), rgb.min(-1)
sat = np.where(mx > 1e-4, (mx - mn) / np.maximum(mx, 1e-4), 0)
d = np.maximum(mx - mn, 1e-6)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
gold = np.clip((sat - 0.30) / 0.08, 0, 1) * np.clip((mx - 0.38) / 0.08, 0, 1) * \
       np.clip((hue - 30) / 4, 0, 1) * np.clip((52 - hue) / 4, 0, 1)
print("gold texels:", int((gold > 0.5).sum()), "of", W * H, flush=True)
var = mx / max(float(np.median(mx[gold > 0.5])), 1e-4)            # the original's small brush variation, around 1
shade = np.clip((ao - 0.35) / 0.6, 0, 1) ** 1.3
val = np.clip((0.30 + 0.56 * shade) * var, 0, 1)
h_, s_ = 43 / 60.0, 0.64
i_ = int(h_); f_ = h_ - i_                                         # hue 43 lies in sector 0 (red to yellow)
new = np.stack([val, val * (1 - s_ * (1 - f_)), val * (1 - s_)], -1)
px[..., :3] = rgb * (1 - gold[..., None]) + new * gold[..., None]
img.pixels.foreach_set(px.ravel()); img.pack()
tex.image = img
print("crown repainted", flush=True)

# ---- 4. checks -----------------------------------------------------------------------------------------------------------------
hc = np.empty(len(head.data.vertices) * 3, np.float32); head.data.vertices.foreach_get("co", hc); hc = hc.reshape(-1, 3)
c = Vector((float(np.median(hc[:, 0])), float(np.median(hc[:, 1])), float(hc[:, 2].max()) - 0.12))
cam = bpy.data.cameras.new("chk"); camo = bpy.data.objects.new("chk", cam); scene.collection.objects.link(camo); scene.camera = camo
cam.type = "ORTHO"; cam.ortho_scale = 0.40
for e, rz in ((3, -25), (1.5, 140)):
    l = bpy.data.lights.new("k", "SUN"); l.energy = e; lo_ = bpy.data.objects.new("k", l); scene.collection.objects.link(lo_)
    lo_.rotation_euler = (math.radians(55), 0, math.radians(rz))
scene.world.color = (0.32, 0.32, 0.35); scene.cycles.samples = 24
scene.render.resolution_x = scene.render.resolution_y = 500
shots = []
for az, el in ((0, 10), (40, 20), (90, 10), (180, 30)):
    a, e = math.radians(az), math.radians(el)
    dv = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    camo.location = c + dv * 3; camo.rotation_euler = dv.to_track_quat("Z", "Y").to_euler()
    p = out.with_name(out.stem + f"_crown_{az:03d}.png"); scene.render.filepath = str(p); bpy.ops.render.render(write_still=True)
    shots.append(p)
bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
print("saved", OUT, flush=True)
print("shots", " ".join(map(str, shots)), flush=True)

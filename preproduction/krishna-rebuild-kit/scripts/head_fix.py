"""Clean up a joined Krishna head (run after head_join.py), headless Blender.

Usage:
  blender -b --python scripts/head_fix.py -- JOINED.blend OUT.blend [PREVIEW_DIR]

What it does:
  1. Finds the blue "feather card" that TRELLIS baked into the head mesh (blue-dominant texels
     near the top left of the crown) and deletes it.
  2. Adds a proper peacock feather: a curved oval mesh with a procedural eye pattern,
     placed where the card was.
  3. Repaints the grey-green jaw and chin texels toward the forehead's skin tone, keeping the
     original shading detail (a colour shift, not a flat fill).
  4. Saves OUT.blend and, with PREVIEW_DIR, renders front, three-quarter, side and back close-ups.
"""

import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
if len(argv) < 2:
    raise SystemExit("usage: blender -b --python head_fix.py -- JOINED.blend OUT.blend [PREVIEW_DIR]")
in_blend, out_blend = argv[0], argv[1]
preview_dir = argv[2] if len(argv) > 2 else None

bpy.ops.wm.open_mainfile(filepath=in_blend)
head = bpy.data.objects["KRISHNA_head"]
me = head.data

# ---- per-vertex positions, UVs and texel colours -------------------------------------
nv = len(me.vertices)
co = np.empty(nv * 3, dtype=np.float32)
me.vertices.foreach_get("co", co)
co = co.reshape(nv, 3)
nl = len(me.loops)
loop_vert = np.empty(nl, dtype=np.int32)
me.loops.foreach_get("vertex_index", loop_vert)
uv = np.empty(nl * 2, dtype=np.float32)
me.uv_layers[0].data.foreach_get("uv", uv)
uv = uv.reshape(nl, 2)

mat = me.materials[0]
img = next(n.image for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and "Image_0" in n.image.name)
W, H = img.size
pix = np.empty(W * H * 4, dtype=np.float32)
img.pixels.foreach_get(pix)
pix = pix.reshape(H, W, 4)
px = np.clip((uv[:, 0] * W).astype(np.int32), 0, W - 1)
py = np.clip((uv[:, 1] * H).astype(np.int32), 0, H - 1)
loop_rgb = pix[py, px, :3]

vsum = np.zeros((nv, 3), dtype=np.float64)
vcnt = np.zeros(nv, dtype=np.float64)
np.add.at(vsum, loop_vert, loop_rgb)
np.add.at(vcnt, loop_vert, 1.0)
vrgb = vsum / np.maximum(vcnt, 1)[:, None]

zs, xs, ys = co[:, 2], co[:, 0], co[:, 1]
z_top = float(zs.max())
cx = float(np.median(xs[zs > z_top - 0.2]))

# ---- 1. remove the feather card ---------------------------------------------------------
r, g, b = vrgb[:, 0], vrgb[:, 1], vrgb[:, 2]
blue = (b > 0.22) & (b > r * 1.12) & (b > g * 0.9)
region = (zs > z_top - 0.12) & (xs < cx + 0.005)
feather = blue & region
print("FEATHER verts", int(feather.sum()), flush=True)
if feather.sum() > 50:
    fc = co[feather]
    f_centre = fc.mean(axis=0)
    f_base = fc[np.argmin(fc[:, 2])]
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    kill = [bm.verts[i] for i in np.nonzero(feather)[0]]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(me)
    bm.free()
    me.update()
else:
    f_centre = np.array([cx - 0.07, 0.0, z_top - 0.04])
    f_base = f_centre
print("FEATHER centre", f_centre, "base", f_base, flush=True)

# ---- 2. new peacock feather ------------------------------------------------------------
LEN, WID = 0.17, 0.045
seg_u, seg_v = 24, 10
verts, faces, uvs = [], [], []
for i in range(seg_u + 1):
    t = i / seg_u
    # spine curves up and slightly outward; width follows a leaf profile
    sx = -0.035 * t * t
    sz = LEN * t
    w = WID * math.sin(math.pi * min(1.0, 0.18 + 0.82 * t) ** 0.9) * (1.0 if t > 0.12 else t / 0.12)
    for j in range(seg_v + 1):
        s = j / seg_v * 2 - 1
        verts.append((sx + s * w * 0.5, 0.0, sz))
        uvs.append((j / seg_v, t))
for i in range(seg_u):
    for j in range(seg_v):
        a = i * (seg_v + 1) + j
        faces.append((a, a + 1, a + seg_v + 2, a + seg_v + 1))
fm = bpy.data.meshes.new("KRISHNA_feather_mesh")
fm.from_pydata(verts, [], faces)
fm.update()
uvl = fm.uv_layers.new(name="UVMap")
for poly in fm.polygons:
    for li in poly.loop_indices:
        uvl.data[li].uv = uvs[fm.loops[li].vertex_index]
feather_obj = bpy.data.objects.new("KRISHNA_feather", fm)
bpy.context.scene.collection.objects.link(feather_obj)
feather_obj.location = Vector((float(f_base[0]), float(f_base[1]), float(f_base[2])))
feather_obj.rotation_euler = (0.0, math.radians(-12), 0.0)
for p in fm.polygons:
    p.use_smooth = True

# Paint the feather texture with numpy so it also works in Workbench, FBX and Unreal.
FW, FH = 256, 512
yy, xx = np.mgrid[0:FH, 0:FW].astype(np.float32)
u, v = xx / (FW - 1), yy / (FH - 1)
ecx, ecy = 0.5, 0.72
d = np.sqrt(((u - ecx) * 1.5) ** 2 + (v - ecy) ** 2)
stops = [
    (0.00, (0.02, 0.05, 0.20)),  # dark blue eye centre
    (0.07, (0.05, 0.25, 0.75)),  # bright blue
    (0.14, (0.02, 0.50, 0.45)),  # teal
    (0.22, (0.80, 0.62, 0.12)),  # gold ring
    (0.34, (0.03, 0.40, 0.18)),  # green body
    (1.00, (0.02, 0.28, 0.12)),
]
rgb = np.zeros((FH, FW, 3), dtype=np.float32)
for k in range(3):
    rgb[..., k] = np.interp(d, [t for t, _ in stops], [c[k] for _, c in stops])
barbs = 0.88 + 0.12 * np.sin(u * 140.0 + v * 6.0)  # fine barb lines
rgb *= barbs[..., None]
fimg = bpy.data.images.new("T_Krishna_Feather", FW, FH, alpha=False)
fimg.pixels.foreach_set(np.dstack([rgb, np.ones((FH, FW, 1), np.float32)]).reshape(-1))
fimg.pack()
fmat = bpy.data.materials.new("M_Krishna_Feather")
fmat.use_nodes = True
nt = fmat.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = fimg
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
feather_obj.data.materials.append(fmat)

# shaft: thin gold quill under the feather
qverts = [(0.0, 0.0, -0.02), (0.0, 0.0, LEN * 0.30)]
quill = bpy.data.curves.new("KRISHNA_quill_curve", "CURVE")
quill.dimensions = "3D"
sp = quill.splines.new("POLY")
sp.points.add(1)
sp.points[0].co = (0.0, 0.0, -0.015, 1)
sp.points[1].co = (-0.004, 0.0, LEN * 0.95, 1)
quill.bevel_depth = 0.0012
quill_obj = bpy.data.objects.new("KRISHNA_feather_quill", quill)
quill_obj.parent = feather_obj
qm = bpy.data.materials.new("M_Krishna_Quill")
qm.diffuse_color = (0.75, 0.58, 0.15, 1)
quill_obj.data.materials.append(qm)
bpy.context.scene.collection.objects.link(quill_obj)

# ---- 3. repaint the jaw ----------------------------------------------------------------
# Front-facing skin only: the face is on the -Y side of the head.
face_front = ys < float(np.percentile(ys[zs > z_top - 0.3], 35))
fx = np.abs(xs - cx)
# Heights are read from the head mesh itself so this works for other characters too.
# The head was scaled so crown-top to chin equals the body's head height (0.30 m for 1.75 m).
z_chin = z_top - float(os.environ.get("HEAD_HEIGHT", "0.30")) * float(os.environ.get("HEAD_SCALE_MULT", "1.0"))
K = float(os.environ.get("HEAD_SCALE_MULT", "1.0"))  # all offsets below were tuned at 1.0
# Jaw region: from just above the chin to about a third of the face height up, narrow column.
jaw = face_front & (zs > z_chin) & (zs < z_chin + 0.075 * K) & (fx < 0.065 * K)
# Reference: the cheeks just under the eyes, which TRELLIS kept warm.
ref = face_front & (zs > z_chin + 0.082 * K) & (zs < z_chin + 0.098 * K) & (fx > 0.015 * K) & (fx < 0.055 * K)
print("JAW verts", int(jaw.sum()), "REF verts", int(ref.sum()), flush=True)
if jaw.sum() > 100 and ref.sum() > 100:
    ref_mean = vrgb[ref].mean(axis=0)
    jaw_mean = vrgb[jaw].mean(axis=0)
    delta = (ref_mean - jaw_mean).astype(np.float32)
    print("JAW mean", jaw_mean, "REF mean", ref_mean, flush=True)
    # weight per vertex: smooth falloff toward the region edges
    wz = np.clip((zs - z_chin + 0.004 * K) / (0.012 * K), 0, 1) * np.clip((z_chin + 0.075 * K - zs) / (0.02 * K), 0, 1)
    wx = np.clip((0.065 * K - fx) / (0.02 * K), 0, 1)
    wv = (wz * wx * face_front).astype(np.float32)
    lw = wv[loop_vert]
    sel = lw > 0.01
    mask = np.zeros((H, W), dtype=np.float32)
    np.maximum.at(mask, (py[sel], px[sel]), lw[sel])
    for _ in range(2):  # fill the gaps between vertices
        m = mask.copy()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            m = np.maximum(m, np.roll(mask, (dy, dx), axis=(0, 1)))
        mask = m
    # Keep each texel's shading (luminance), take the reference skin colour.
    lum = pix[..., :3] @ np.array([0.30, 0.59, 0.11], dtype=np.float32)
    lum_mean = float(np.mean(vrgb[jaw] @ np.array([0.30, 0.59, 0.11])))
    target = np.clip(ref_mean[None, None, :] * (lum / max(lum_mean, 1e-3))[..., None], 0.0, 1.0)
    pix[..., :3] = pix[..., :3] * (1 - mask[..., None]) + target * mask[..., None]
    img.pixels.foreach_set(pix.reshape(-1))
    img.update()
    img.pack()
    print("JAW repainted, texels touched", int((mask > 0).sum()), flush=True)

bpy.ops.wm.save_as_mainfile(filepath=out_blend)
print("SAVED", out_blend, flush=True)

# ---- previews --------------------------------------------------------------------------
if preview_dir:
    os.makedirs(preview_dir, exist_ok=True)
    scene = bpy.context.scene
    for o in scene.objects:
        if o.type == "ARMATURE":
            o.hide_render = True
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light = "FLAT"
    sh.color_type = "TEXTURE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.world = scene.world or bpy.data.worlds.new("w")
    scene.world.color = (0.6, 0.6, 0.6)
    cd = bpy.data.cameras.new("c")
    cd.type = "ORTHO"
    cd.ortho_scale = 0.5 * K
    cam = bpy.data.objects.new("c", cd)
    scene.collection.objects.link(cam)
    scene.camera = cam
    zc = z_top - 0.15 * K
    cy = float((ys.max() + ys.min()) * 0.5)
    views = {
        "fix_front": ((cx, cy - 5, zc), (math.radians(90), 0, 0)),
        "fix_three_quarter": ((cx + 3.5, cy - 3.5, zc), (math.radians(90), 0, math.radians(45))),
        "fix_side": ((cx + 5, cy, zc), (math.radians(90), 0, math.radians(90))),
        "fix_back": ((cx, cy + 5, zc), (math.radians(90), 0, math.radians(180))),
    }
    for name, (loc, rot) in views.items():
        cam.location, cam.rotation_euler = loc, rot
        scene.render.filepath = os.path.join(preview_dir, name + ".png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", scene.render.filepath, flush=True)

"""Join a separate high-detail head mesh onto the Krishna body mesh (headless Blender).

Usage:
  blender -b --python scripts/head_join.py -- BODY.blend HEAD.glb OUT.blend [PREVIEW_DIR]

What it does:
  1. Opens BODY.blend (made by character_prepare.py: body at 1.75 m, origin at the feet).
  2. Imports HEAD.glb (a TRELLIS mesh of a head-and-shoulders image).
  3. Finds the neck on both meshes (the narrowest horizontal slice between chin and chest)
     and scales and moves the head so its neck lines up with the body's neck and its
     crown-top-to-neck height matches the body's.
  4. Deletes the body's own head above the neck and the head mesh's shoulders below its neck.
  5. Saves OUT.blend. If PREVIEW_DIR is given, renders front and three-quarter close-ups.

This is a first-pass fit. Check the result in Blender and nudge the head object if needed.
Uses numpy for the measuring, so it runs in seconds on meshes with hundreds of thousands of vertices.
"""

import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
if len(argv) < 3:
    raise SystemExit("usage: blender -b --python head_join.py -- BODY.blend HEAD.glb OUT.blend [PREVIEW_DIR]")
body_blend, head_glb, out_blend = argv[0], argv[1], argv[2]
preview_dir = argv[3] if len(argv) > 3 else None


def world_points(obj):
    """All vertex positions of obj in world space as an (N, 3) numpy array."""
    n = len(obj.data.vertices)
    co = np.empty(n * 3, dtype=np.float32)
    obj.data.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    mw = np.array(obj.matrix_world, dtype=np.float32)
    return co @ mw[:3, :3].T + mw[:3, 3]


def neck_z(points, z_lo, z_hi, centre_x, half_width, step=0.01):
    """Height of the narrowest slice (by x extent) between z_lo and z_hi, using points near the centre line."""
    near = points[np.abs(points[:, 0] - centre_x) < half_width]
    best_z, best_w = None, 1e9
    z = z_lo
    while z < z_hi:
        band = near[(near[:, 2] >= z) & (near[:, 2] < z + step)]
        if len(band) > 20:
            w = float(band[:, 0].max() - band[:, 0].min())
            if w < best_w:
                best_z, best_w = z, w
        z += step
    if best_z is None:
        raise SystemExit("could not measure the neck")
    return best_z


bpy.ops.wm.open_mainfile(filepath=body_blend)
body = next(o for o in bpy.context.scene.objects if o.type == "MESH")
body.name = "KRISHNA_body_full"

# ---- body measurements -------------------------------------------------------
bp = world_points(body)
b_top = float(bp[:, 2].max())
upper = bp[bp[:, 2] > b_top - 0.35]
b_cx = float(upper[:, 0].mean())
# The neck sits roughly 0.30 to 0.45 m below the top of a 1.75 m figure that wears a crown.
# Searching higher than that finds the narrowing at the forehead, not the neck.
b_neck = neck_z(bp, b_top - 0.46, b_top - 0.28, b_cx, 0.12)
head_region = bp[bp[:, 2] > b_neck]
b_cy = float((head_region[:, 1].max() + head_region[:, 1].min()) * 0.5)
print("BODY: top %.3f  neck %.3f  head+crown height %.3f" % (b_top, b_neck, b_top - b_neck), flush=True)

# ---- import head -------------------------------------------------------------
before = set(o.name for o in bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=head_glb)
head_objs = [o for o in bpy.data.objects if o.name not in before and o.type == "MESH"]
if not head_objs:
    raise SystemExit("no mesh in head file")
head = head_objs[0]
head.name = "KRISHNA_head"
bpy.ops.object.select_all(action="DESELECT")
head.select_set(True)
bpy.context.view_layer.objects.active = head
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

hp = world_points(head)
h_top, h_bottom = float(hp[:, 2].max()), float(hp[:, 2].min())
h_cx = float((hp[:, 0].max() + hp[:, 0].min()) * 0.5)
h_cy = float((hp[:, 1].max() + hp[:, 1].min()) * 0.5)
h_span = h_top - h_bottom
h_width = float(hp[:, 0].max() - hp[:, 0].min())
# Chin level of the head mesh. The head image is framed crown-to-collarbones, so the chin sits
# a fixed fraction of the way down from the top (about 70% for the prompt-7 image). Measuring
# the narrowest slice instead finds the base of the neck on a bare-neck head, which is wrong.
# Override with the environment variable HEAD_CHIN_FRACTION if the framing changes.
chin_fraction = float(os.environ.get("HEAD_CHIN_FRACTION", "0.70"))
h_neck = h_top - chin_fraction * h_span
print("HEAD: top %.3f  neck %.3f  head+crown height %.3f" % (h_top, h_neck, h_top - h_neck), flush=True)

scale = (b_top - b_neck) / (h_top - h_neck)
# The head is first fitted so crown-top to chin equals the body's. A tall crown makes the face
# itself small, so HEAD_SCALE_MULT (default 1.0) enlarges the whole head about the chin.
scale *= float(os.environ.get("HEAD_SCALE_MULT", "1.0"))
print("SCALE head by %.4f" % scale, flush=True)
head.scale = (scale, scale, scale)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
head.location = Vector((b_cx - h_cx * scale, b_cy - h_cy * scale, b_neck - h_neck * scale))
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)


def keep_only(obj, above, z):
    """Delete vertices below z (above=True keeps the top) or above z (above=False keeps the bottom)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    mw = obj.matrix_world
    kill = [v for v in bm.verts if ((mw @ v.co).z < z) == above]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


# "b_neck" and "h_neck" are really the CHIN level: the narrowest slice near the centre line
# is the chin tip, which is narrower than the neck. The same landmark is measured on both
# meshes, so aligning them lines up the chins. The cut is then made about 6 cm lower, in the
# neck, with a 3 cm overlap so there is no visible seam.
cut_below_chin = float(os.environ.get("CUT_BELOW_CHIN", "0.045"))
overlap = float(os.environ.get("CUT_OVERLAP", "0.01"))
keep_only(body, above=False, z=b_neck - cut_below_chin + overlap)  # body keeps what is below this


def clip_below_cut(obj, z_cut, chin_z, hw_top, hw_bottom, hair_drop):
    """Tidy the head mesh under the chin.

    Skin and ornaments below the cut are removed (the body supplies them). Between the chin and the
    cut the neck column tapers from hw_top to hw_bottom so it does not stick out past the body's
    neck. Dark texels (hair) are kept down to hair_drop below the cut so the hair flows into the
    body's hair instead of ending in a flat edge.
    """
    mw = np.array(obj.matrix_world, dtype=np.float32)
    n = len(obj.data.vertices)
    co = np.empty(n * 3, dtype=np.float32)
    obj.data.vertices.foreach_get("co", co)
    co = co.reshape(n, 3) @ mw[:3, :3].T + mw[:3, 3]
    # vertex colour from the base texture (first loop per vertex)
    img = next(i for i in (nd.image for nd in obj.data.materials[0].node_tree.nodes if nd.type == "TEX_IMAGE") if "Image_0" in i.name)
    W, H = img.size
    pb = np.empty(W * H * 4, dtype=np.float32)
    img.pixels.foreach_get(pb)
    pb = pb.reshape(H, W, 4)
    nl = len(obj.data.loops)
    lv = np.empty(nl, dtype=np.int32)
    obj.data.loops.foreach_get("vertex_index", lv)
    uv = np.empty(nl * 2, dtype=np.float32)
    obj.data.uv_layers[0].data.foreach_get("uv", uv)
    uv = uv.reshape(nl, 2)
    vuv = np.zeros((n, 2), dtype=np.float32)
    vuv[lv[::-1]] = uv[::-1]
    px = np.clip((vuv[:, 0] * W).astype(int), 0, W - 1)
    py = np.clip((vuv[:, 1] * H).astype(int), 0, H - 1)
    rgb = pb[py, px, :3]
    lum = rgb @ np.array([0.30, 0.59, 0.11], dtype=np.float32)
    dark = lum < 0.17
    z = co[:, 2]
    dx = np.abs(co[:, 0] - centre_x_for_clip)
    t = np.clip((z - z_cut) / max(chin_z - z_cut, 1e-6), 0, 1)
    hw = hw_bottom + (hw_top - hw_bottom) * t
    below = z < z_cut
    kill = (below & ~(dark & (z > z_cut - hair_drop))) | (~below & (z < chin_z) & (dx > hw) & ~dark)
    print("CLIP killed", int(kill.sum()), "of", n, flush=True)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.nonzero(kill)[0]], context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


centre_x_for_clip = b_cx
Kh = float(os.environ.get("HEAD_SCALE_MULT", "1.0"))
hw_top = float(os.environ.get("NECK_HALF_WIDTH", "0.075"))
hw_bot = float(os.environ.get("NECK_HALF_WIDTH_BOTTOM", "0.058"))
clip_below_cut(head, z_cut=b_neck - cut_below_chin - overlap, chin_z=b_neck - 0.005, hw_top=hw_top, hw_bottom=hw_bot, hair_drop=0.14 * Kh)
body.name = "KRISHNA_body"
print("BODY verts after cut:", len(body.data.vertices), " HEAD verts after cut:", len(head.data.vertices), flush=True)

bpy.ops.wm.save_as_mainfile(filepath=out_blend)
print("SAVED", out_blend, flush=True)

# ---- preview renders ---------------------------------------------------------
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
    cd.ortho_scale = 0.9
    cam = bpy.data.objects.new("c", cd)
    scene.collection.objects.link(cam)
    scene.camera = cam
    zc = b_neck + (b_top - b_neck) * 0.45
    views = {
        "head_front": ((b_cx, b_cy - 6, zc), (math.radians(90), 0, 0)),
        "head_three_quarter": ((b_cx + 4.2, b_cy - 4.2, zc), (math.radians(90), 0, math.radians(45))),
    }
    for name, (loc, rot) in views.items():
        cam.location, cam.rotation_euler = loc, rot
        scene.render.filepath = os.path.join(preview_dir, name + ".png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED", scene.render.filepath, flush=True)

"""Arjuna bare-headed (passport cast/arjuna_bare, A14 on): the crown and ear-guards come off, loose black wavy hair to the
nape, a few strands across the forehead, nothing on his head. Free, cloud Blender.

  python hero_bare.py <in arjuna_hero_v4.blend> <out.blend>
  1 the head mesh loses everything above the brow line (the crown) and the steel ear-guards at the sides
  2 a skull cap (an egg-shaped shell, a little deeper at the front) closes the head under the hair
  3 hair: ~6000 strands (Cycles curves) grow from the cap, flow back over the skull to the nape and hang there in loose
    waves; ~40 short strands fall across the forehead
Cap and hair ride the head bone (DEF-spine.006), so they turn with the head. Check render next to <out>: _bare_checks.jpg.
"""
import math, pathlib, sys
import bpy
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
IN, OUT = args[:2]
if pathlib.Path(OUT).exists():
    sys.exit(f"exists, not overwriting (folder law 1): {OUT}")
out = pathlib.Path(OUT).resolve()
bpy.ops.wm.open_mainfile(filepath=str(pathlib.Path(IN).resolve()))
bpy.ops.preferences.addon_enable(module="rigify")
scene = bpy.context.scene
TAG = "ARJUNA"
rig = bpy.data.objects[f"{TAG}_rig"]; head = bpy.data.objects[f"{TAG}_head"]
# measured on arjuna_hero_v4 (rest pose, world metres): brows ~1.60, crown band from ~1.61 up to 1.85, skull back y ~0.09
CUT_Z = 1.603                                                          # everything above this on the head mesh is crown
C = np.array([0.0, -0.02, 1.598])                                      # skull egg: centre and radii (front, back, side, up)
R_FRONT, R_BACK, R_SIDE, R_UP = 0.124, 0.116, 0.086, 0.108
HAIRLINE = 1.652                                                       # the cap below this at the front is forehead skin

# ---- 1 the crown comes off -------------------------------------------------------------------------------------------------
me = head.data
nv = len(me.vertices)
co = np.empty(nv * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
M = np.array(head.matrix_world); cw = co @ M[:3, :3].T + M[:3, 3]
img = next(n for n in head.active_material.node_tree.nodes if n.type == "TEX_IMAGE" and n.image
           and n.image.colorspace_settings.name != "Non-Color").image                  # the colour map, not metal/rough
IW, IH = img.size
px = np.empty(IW * IH * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(IH, IW, 4)
luv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get("uv", luv); luv = luv.reshape(-1, 2)
lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", lv)
rgb = px[np.clip((luv[:, 1] * IH).astype(int), 0, IH - 1), np.clip((luv[:, 0] * IW).astype(int), 0, IW - 1), :3]
col = np.zeros((nv, 3)); np.add.at(col, lv, rgb); col /= np.maximum(np.bincount(lv, None, nv), 1)[:, None]
del px
mx, mn = col.max(1), col.min(1); sat = (mx - mn) / np.maximum(mx, 1e-4)
fh = (cw[:, 2] > 1.585) & (cw[:, 2] < 1.605) & (cw[:, 1] < -0.1) & (np.abs(cw[:, 0]) < 0.04) & (sat > 0.25)
FOREHEAD = np.median(col[fh], axis=0) if fh.sum() > 20 else np.array([0.57, 0.35, 0.26])   # his skin just above the brows
FOREHEAD = np.where(FOREHEAD <= 0.04045, FOREHEAD / 12.92, ((FOREHEAD + 0.055) / 1.055) ** 2.4)   # texture sRGB to linear
print("forehead colour", FOREHEAD.round(3), int(fh.sum()), flush=True)
steel = (sat < 0.25) & (mx > 0.3)
nrm = np.empty(nv * 3, np.float32); me.vertices.foreach_get("normal", nrm); nrm = nrm.reshape(-1, 3) @ M[:3, :3].T
old_hair = (mx < 0.12) & (cw[:, 1] > -0.09) & (cw[:, 2] < CUT_Z) & (cw[:, 2] > 1.42)   # TRELLIS hair lobes at the back and sides
OLD_P, OLD_N = cw[old_hair], nrm[old_hair] / np.maximum(np.linalg.norm(nrm[old_hair], axis=1, keepdims=True), 1e-6)
hue = np.where(mx - mn > 1e-4, ((col[:, 1] - col[:, 2]) / np.maximum(mx - mn, 1e-4)) / 6.0, 0)
gold_trim = (sat > 0.35) & (hue > 0.085) & (hue < 0.2) & (mx > 0.2) & (cw[:, 2] > 1.55) & (cw[:, 1] < 0.03)   # crown rim and ear-guard gold
skin_attr = np.empty(nv, np.float32); me.attributes["skin"].data.foreach_get("value", skin_attr)   # from hero_detail.py
forehead = (skin_attr > 0.5) & (cw[:, 1] < -0.07) & (cw[:, 2] < CUT_Z + 0.02)    # keep his own forehead and brows
drop = ((cw[:, 2] > CUT_Z) & ~forehead) | (cw[:, 2] > CUT_Z + 0.02) | gold_trim | (steel & (np.abs(cw[:, 0] - 0.0) > 0.07) & (cw[:, 2] > 1.5))
print("crown verts removed", int(drop.sum()), "of", nv, flush=True)
bpy.context.view_layer.objects.active = head
for o in bpy.context.selected_objects:
    o.select_set(False)
head.select_set(True)
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT"); bpy.ops.object.mode_set(mode="OBJECT")
sel = np.zeros(nv, bool); sel[drop] = True; me.vertices.foreach_set("select", sel)
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.delete(type="VERT"); bpy.ops.object.mode_set(mode="OBJECT")


# crown gold painted onto the brow and temple texels: turned back into skin there (and not metal)
me = head.data
nv2 = len(me.vertices)
c2 = np.empty(nv2 * 3, np.float32); me.vertices.foreach_get("co", c2); c2 = c2.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
bz = ((c2[:, 2] > 1.588) & (c2[:, 2] < 1.63) & (c2[:, 1] < 0.03)).astype(np.float32)   # above the eyes
at = me.attributes.new("brow_zone", "FLOAT", "POINT"); at.data.foreach_set("value", bz)
mat = head.active_material; nt0 = mat.node_tree; bs0 = nt0.nodes["Principled BSDF"]
tex = next(n for n in nt0.nodes if n.type == "TEX_IMAGE" and n.image and n.image.colorspace_settings.name != "Non-Color")
hsv = nt0.nodes.new("ShaderNodeSeparateColor"); hsv.mode = "HSV"; nt0.links.new(tex.outputs["Color"], hsv.inputs["Color"])
def mr_(src, a0, a1, b0, b1):
    n = nt0.nodes.new("ShaderNodeMapRange"); n.interpolation_type = "SMOOTHSTEP"
    n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = a0, a1
    n.inputs["To Min"].default_value, n.inputs["To Max"].default_value = b0, b1
    nt0.links.new(src, n.inputs["Value"]); return n.outputs["Result"]
def mul_(x, y):
    n = nt0.nodes.new("ShaderNodeMath"); n.operation = "MULTIPLY"; nt0.links.new(x, n.inputs[0])
    if isinstance(y, float):
        n.inputs[1].default_value = y
    else:
        nt0.links.new(y, n.inputs[1])
    return n.outputs[0]
atn = nt0.nodes.new("ShaderNodeAttribute"); atn.attribute_name = "brow_zone"
gold_t = mul_(mr_(hsv.outputs[0], 0.075, 0.095, 0.0, 1.0), mr_(hsv.outputs[1], 0.3, 0.4, 0.0, 1.0))
steel_t = mul_(mr_(hsv.outputs[1], 0.18, 0.28, 1.0, 0.0), mr_(hsv.outputs[2], 0.25, 0.35, 0.0, 1.0))   # the silver rim
mxn = nt0.nodes.new("ShaderNodeMath"); mxn.operation = "MAXIMUM"; nt0.links.new(gold_t, mxn.inputs[0]); nt0.links.new(steel_t, mxn.inputs[1])
g = mul_(mxn.outputs[0], atn.outputs["Fac"])
for sock, val in (("Base Color", None), ("Metallic", 0.0)):
    link = next((l for l in nt0.links if l.to_node == bs0 and l.to_socket.name == sock), None)
    if sock == "Base Color":
        mx_ = nt0.nodes.new("ShaderNodeMix"); mx_.data_type = "RGBA"; nt0.links.new(g, mx_.inputs["Factor"])
        nt0.links.new(link.from_socket, mx_.inputs["A"]); mx_.inputs["B"].default_value = (*FOREHEAD, 1)
        nt0.links.new(mx_.outputs["Result"], bs0.inputs["Base Color"])
    elif link is not None:
        inv = nt0.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0; nt0.links.new(g, inv.inputs[1])
        nt0.links.new(mul_(link.from_socket, inv.outputs[0]), bs0.inputs["Metallic"])


def egg(d):
    """surface point of the skull egg along unit direction d from C (front -Y has its own radius)"""
    ry = np.where(d[..., 1] < 0, R_FRONT, R_BACK)
    rz = np.where(d[..., 2] > 0, R_UP, R_UP * 1.05)
    s = 1.0 / np.sqrt((d[..., 0] / R_SIDE) ** 2 + (d[..., 1] / ry) ** 2 + (d[..., 2] / rz) ** 2)
    return C + d * s[..., None]


def bone_parent(o):
    bpy.context.view_layer.update(); mw = o.matrix_world.copy()
    o.parent = rig; o.parent_type = "BONE"; o.parent_bone = "DEF-spine.006"
    bpy.context.view_layer.update(); o.matrix_world = mw


# ---- 2 the skull cap -------------------------------------------------------------------------------------------------------
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=40, radius=1, location=(0, 0, 0))
cap = bpy.context.object; cap.name = f"{TAG}_hair_cap"
cm = cap.data
v = np.empty(len(cm.vertices) * 3, np.float32); cm.vertices.foreach_get("co", v); v = v.reshape(-1, 3)
d = v / np.linalg.norm(v, axis=1, keepdims=True)
p = egg(d)
cm.vertices.foreach_set("co", p.astype(np.float32).ravel())
# keep the part above the brow line at the front, down to the nape at the back
keep_z = np.where(p[:, 1] < -0.06, CUT_Z + 0.006, np.where(p[:, 1] < 0.0, 1.56, 1.47))
low = p[:, 2] < keep_z
bpy.context.view_layer.objects.active = cap
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT"); bpy.ops.object.mode_set(mode="OBJECT")
s2 = np.zeros(len(cm.vertices), bool); s2[low] = True; cm.vertices.foreach_set("select", s2)
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.delete(type="VERT"); bpy.ops.object.mode_set(mode="OBJECT")
for f in cm.polygons:
    f.use_smooth = True
hm = bpy.data.materials.new("hair_cap"); hm.use_nodes = True; nt = hm.node_tree
b = nt.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.014, 0.010, 0.008, 1)
b.inputs["Roughness"].default_value = 0.42
wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Y"
wv.inputs["Scale"].default_value = 60; wv.inputs["Distortion"].default_value = 6
bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5
nt.links.new(wv.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
# the front band of the cap below the hairline is his forehead: skin colour, fading into hair at the hairline
tc = nt.nodes.new("ShaderNodeTexCoord"); sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sx.inputs[0])
mr = nt.nodes.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHSTEP"
mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = HAIRLINE - 0.006, HAIRLINE + 0.004
mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 1.0, 0.0
nt.links.new(sx.outputs["Z"], mr.inputs["Value"])
fr = nt.nodes.new("ShaderNodeMapRange"); fr.inputs["From Min"].default_value, fr.inputs["From Max"].default_value = -0.07, -0.05
fr.inputs["To Min"].default_value, fr.inputs["To Max"].default_value = 1.0, 0.0; nt.links.new(sx.outputs["Y"], fr.inputs["Value"])
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
nt.links.new(mr.outputs["Result"], mul.inputs[0]); nt.links.new(fr.outputs["Result"], mul.inputs[1])
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; nt.links.new(mul.outputs[0], mix.inputs["Factor"])
mix.inputs["A"].default_value = (0.014, 0.010, 0.008, 1); mix.inputs["B"].default_value = (*FOREHEAD, 1)
nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
rmix = nt.nodes.new("ShaderNodeMix"); rmix.data_type = "FLOAT"; nt.links.new(mul.outputs[0], rmix.inputs["Factor"])
rmix.inputs["A"].default_value = 0.42; rmix.inputs["B"].default_value = 0.55; nt.links.new(rmix.outputs["Result"], b.inputs["Roughness"])
sss = nt.nodes.new("ShaderNodeMath"); sss.operation = "MULTIPLY"; sss.inputs[1].default_value = 0.3
nt.links.new(mul.outputs[0], sss.inputs[0]); nt.links.new(sss.outputs[0], b.inputs["Subsurface Weight"])
b.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.25); b.inputs["Subsurface Scale"].default_value = 0.012
inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 0.5   # no hair grain on the forehead
nt.links.new(mul.outputs[0], inv.inputs[1]); nt.links.new(inv.outputs[0], bp.inputs["Strength"])
cm.materials.append(hm)
bone_parent(cap)

# ---- 3 hair strands --------------------------------------------------------------------------------------------------------
rng = np.random.default_rng(17)
NPT = 10
strands = []


def grow(root, length, front=False):
    pts = [root]; q = root.copy()
    step = length / (NPT - 1)
    side = rng.normal(0, 1)
    phase = rng.uniform(0, 2 * math.pi)
    for k in range(1, NPT):
        s = k / (NPT - 1)
        if front:                                                      # falls forward and down across the brow, curls aside
            dirv = np.array([0.35 * side, -0.55, -0.8])
        else:
            dn = q - C; dn /= np.linalg.norm(dn)
            w = min(max((q[1] - (C[1] - 0.02)) / 0.07, 0.0), 1.0)    # 0 in front of the crown of the head, 1 behind it
            v = (1 - w) * np.array([0.0, 1.0, 0.15]) + w * np.array([0.0, 0.2, -1.0])    # combed back, then down to the nape
            dirv = v - dn * v.dot(dn) if np.linalg.norm(q - C) < 0.2 else v
        dirv = dirv / np.linalg.norm(dirv)
        q = q + dirv * step
        if not front:                                                  # stays on (just above) the skull until past the nape
            dn = q - C; dn /= np.linalg.norm(dn)
            surf = egg(dn)
            lift = 0.003 + 0.006 * s
            if np.linalg.norm(q - C) < np.linalg.norm(surf - C) + lift:
                q = surf + dn * lift
        wave = 0.005 * math.sin(2 * math.pi * s * length / 0.035 + phase) * s
        q = q + np.array([wave, 0, 0])
        pts.append(q.copy())
    strands.append(np.array(pts))


n = 0
while n < 6000:
    d = rng.normal(size=3); d /= np.linalg.norm(d)
    r = egg(d)
    zmin = HAIRLINE + 0.004 if r[1] < -0.06 else (1.575 if r[1] < 0.0 else 1.5)
    if r[2] < zmin:
        continue
    back = min(max((r[1] - C[1]) / R_BACK, 0.0), 1.0)                  # strands from further back hang longer, over the nape
    grow(r + d * 0.002, rng.uniform(0.2, 0.28) + 0.08 * back); n += 1
THICK = len(strands)
for lock in ():                                                         # forehead locks read as cracks at this scale: left out
    for i in range(6):
        a = lock + rng.normal(0, 0.03)
        d = np.array([math.sin(a) * 0.6, -0.8, 0.25]); d /= np.linalg.norm(d)
        r = egg(d); r[2] = max(r[2], HAIRLINE + 0.004)
        grow(r, rng.uniform(0.05, 0.07), front=True)
LOBE = len(strands)
pick = rng.choice(len(OLD_P), size=min(3500, len(OLD_P)), replace=False)   # strands over the old hair lobes, hanging down
for i in pick:
    p0, n0 = OLD_P[i], OLD_N[i]
    g = np.array([0.0, 0.1, -1.0]); t = g - n0 * g.dot(n0); t /= (np.linalg.norm(t) + 1e-6)
    L = rng.uniform(0.06, 0.11); pts = []
    for k in range(NPT):
        s = k / (NPT - 1)
        pts.append(p0 + n0 * (0.002 + 0.006 * s) + t * L * s + np.array([0, 0, -0.25 * L * s * s]))
    strands.append(np.array(pts))

hc = bpy.data.hair_curves.new(f"{TAG}_hair")
hc.add_curves([NPT] * len(strands))
P = np.concatenate(strands).astype(np.float32)
hc.attributes["position"].data.foreach_set("vector", P.ravel())
if "radius" not in hc.attributes:
    hc.attributes.new("radius", "FLOAT", "POINT")
rad = np.tile(np.linspace(0.00045, 0.00018, NPT), len(strands)).astype(np.float32).reshape(-1, NPT)
rad[THICK:LOBE] *= 2.2                                                  # forehead locks read as locks, not cracks
rad = rad.ravel()
hc.attributes["radius"].data.foreach_set("value", rad)
hair = bpy.data.objects.new(f"{TAG}_hair", hc); scene.collection.objects.link(hair)
hmat = bpy.data.materials.new("hair_strands"); hmat.use_nodes = True; nt = hmat.node_tree
for nd in list(nt.nodes):
    if nd.type == "BSDF_PRINCIPLED":
        nt.nodes.remove(nd)
hb = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
hb.model = "CHIANG"; hb.parametrization = "MELANIN"
for k, val in (("Melanin", 0.93), ("Melanin Redness", 0.35), ("Roughness", 0.32), ("Radial Roughness", 0.45), ("Random Color", 0.15)):
    sk = next((i for i in hb.inputs if i.name == k), None)
    if sk is not None:
        sk.default_value = val
    else:
        print("hair input missing", k, [i.name for i in hb.inputs], flush=True)
nt.links.new(hb.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
hc.materials.append(hmat)
bone_parent(hair)
print("hair strands", len(strands), flush=True)

# ---- check renders -----------------------------------------------------------------------------------------------------------
for o in list(scene.objects):
    if o.type in ("CAMERA", "LIGHT"):
        bpy.data.objects.remove(o)
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = 32; scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.resolution_x, scene.render.resolution_y = 520, 620
cam = bpy.data.cameras.new("chk"); camo = bpy.data.objects.new("chk", cam); scene.collection.objects.link(camo); scene.camera = camo
cam.type = "ORTHO"; cam.ortho_scale = 0.46
for e, rot, colr in ((4.0, (50, 0, -35), (1, 0.93, 0.82)), (2.5, (70, 0, 150), (0.75, 0.85, 1.0))):
    l = bpy.data.lights.new("k", "SUN"); l.energy = e; l.color = colr; l.angle = math.radians(3)
    lo = bpy.data.objects.new("k", l); scene.collection.objects.link(lo); lo.rotation_euler = [math.radians(a) for a in rot]
scene.world.color = (0.16, 0.15, 0.17)
shots = []
for az in (25, 0, 90, 160):
    a = math.radians(az); dv = Vector((math.sin(a), -math.cos(a), 0.1)).normalized()
    aim = Vector((0, -0.02, 1.6))
    camo.location = aim + dv * 3; camo.rotation_euler = (-dv).to_track_quat("-Z", "Y").to_euler()
    pth = out.with_name(f"{out.stem}_bare_{az:03d}.png"); scene.render.filepath = str(pth); bpy.ops.render.render(write_still=True)
    shots.append(pth)
from PIL import Image
ims = [Image.open(x).convert("RGB") for x in shots]
sheet = Image.new("RGB", (520 * len(ims), 620))
for i, im in enumerate(ims):
    sheet.paste(im, (520 * i, 0))
sheet.save(out.with_name(out.stem + "_bare_checks.jpg"), quality=88)
for x in shots:
    x.unlink()
for o in list(scene.objects):
    if o.type in ("CAMERA", "LIGHT"):
        bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
print("saved", OUT, flush=True)

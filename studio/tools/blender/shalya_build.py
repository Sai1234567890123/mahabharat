"""Shalya, king of Madra and Karna's charioteer, built from the Krishna hero rig. Free, cloud Blender.

The passport (cast/karna/passport.md) keeps him "grey-bearded, mid-ground only", so he is a repaint and re-dress of an
existing rig, not a new model:
  crown   Krishna's crown and peacock feather are cut off above the brow; a plain ivory turban with a gold band replaces it
  skin    blue becomes warm brown (the rig's own per-vertex "skin" mask drives it)
  hair    black hair and dark texels turn iron-grey; a grey beard is added on the jaw
  cloth   Krishna's red dhoti becomes ivory, so the two charioteers never read alike
Gold armour stays: he is a king. Everything rides the same Rigify rig, so moves_ep01.charioteer() poses him.

  EGL_PLATFORM=surfaceless python3 shalya_build.py <krishna_hero_v3.blend> <out shalya_hero_v1.blend>
Writes <out> plus <out>_checks.jpg (front, side, back, full figure). Never overwrites (folder law 1).
"""
import math, pathlib, shutil, sys
import bpy
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
IN, OUT = (pathlib.Path(a).resolve() for a in args[:2])
if OUT.exists():
    sys.exit(f"exists, not overwriting (folder law 1): {OUT}")
bpy.ops.wm.open_mainfile(filepath=str(IN))
bpy.ops.preferences.addon_enable(module="rigify")
sc = bpy.context.scene
for o in list(sc.objects):
    if o.type in ("CAMERA", "LIGHT"):
        bpy.data.objects.remove(o)

# ---- rename KRISHNA_* to SHALYA_* so anim_lib.Hero.load(path, "SHALYA") finds him ------------------------------------
for o in bpy.data.objects:
    if o.name.startswith("KRISHNA_"):
        o.name = "SHALYA_" + o.name[len("KRISHNA_"):]
rig, body, head = (bpy.data.objects[f"SHALYA_{n}"] for n in ("rig", "body", "head"))
for o in (body, head):                                                  # own materials, so Krishna's file is never shared
    for i, m in enumerate(o.data.materials):
        o.data.materials[i] = m.copy(); o.data.materials[i].name = "SHALYA_" + o.name.split("_")[1] + "_detail"


def attr(mesh, name):
    a = mesh.attributes[name]; v = np.zeros(len(a.data)); a.data.foreach_get("value", v); return v


# ---- cut the crown off above the brow -----------------------------------------------------------------------------------
mw = head.matrix_world
co = np.array([tuple(mw @ v.co) for v in head.data.vertices])
skin_v = attr(head.data, "skin")
skin_pt = skin_v if len(skin_v) == len(co) else None
if skin_pt is None:                                                     # stored per corner: average to the vertices
    acc = np.zeros(len(co)); cnt = np.zeros(len(co)); vi = np.zeros(len(head.data.loops), int)
    head.data.loops.foreach_get("vertex_index", vi); np.add.at(acc, vi, skin_v); np.add.at(cnt, vi, 1); skin_pt = acc / np.maximum(cnt, 1)
cy = np.median(co[:, 1])
front_skin = co[(skin_pt > 0.5) & (co[:, 1] < cy)]
brow = float(np.percentile(front_skin[:, 2], 99.0))                     # the top of the forehead skin
kb = head.data.shape_keys.key_blocks                                    # the chin: what moves most when the jaw opens
jaw = np.linalg.norm(np.array([v.co[:] for v in kb["jaw_open"].data]) - np.array([v.co[:] for v in kb["Basis"].data]), axis=1)
jv = co[jaw > jaw.max() * 0.6]
chin = np.array([float(np.median(jv[:, 0])), float(jv[:, 1].min()) + 0.012, float(jv[:, 2].min())])


def texel_colours(obj):
    """the base colour texture under each vertex (the first image feeding Base Color), as HSV-ish numpy arrays"""
    img = next(n.image for n in obj.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE")
    w, h = img.size; px = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(h, w, 4)[..., :3]
    uv = np.empty(len(obj.data.loops) * 2); obj.data.uv_layers.active.data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
    vi = np.empty(len(obj.data.loops), int); obj.data.loops.foreach_get("vertex_index", vi)
    rgb_l = px[np.clip((uv[:, 1] % 1) * h, 0, h - 1).astype(int), np.clip((uv[:, 0] % 1) * w, 0, w - 1).astype(int)]
    rgb = np.zeros((len(obj.data.vertices), 3)); cnt = np.zeros(len(obj.data.vertices))
    np.add.at(rgb, vi, rgb_l); np.add.at(cnt, vi, 1); rgb /= np.maximum(cnt, 1)[:, None]
    mx, mn = rgb.max(1), rgb.min(1); sat = (mx - mn) / np.maximum(mx, 1e-4)
    r, g, b = rgb.T
    hue = np.where(mx == r, ((g - b) / np.maximum(mx - mn, 1e-4)) % 6, np.where(mx == g, (b - r) / np.maximum(mx - mn, 1e-4) + 2,
                   (r - g) / np.maximum(mx - mn, 1e-4) + 4)) / 6.0
    return hue, sat, mx


hue, sat, val = texel_colours(head)
gold = (hue > 0.04) & (hue < 0.17) & (sat > 0.35) & (val > 0.25) & (skin_pt < 0.5)
print(f"brow {brow:.3f} chin {chin.round(3)} gold verts {int(gold.sum())}", flush=True)
bpy.context.view_layer.objects.active = head
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT"); bpy.ops.object.mode_set(mode="OBJECT")
for v, p, s, gd in zip(head.data.vertices, co, skin_pt, gold):
    v.select = bool((p[2] > brow + 0.004 and s < 0.5) or (gd and p[2] > chin[2] + 0.06))   # crown, its side flaps, feather
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.delete(type="VERT"); bpy.ops.object.mode_set(mode="OBJECT")
co = np.array([tuple(mw @ v.co) for v in head.data.vertices])
# Krishna's tilak (the white and red forehead mark) is painted on: treat the forehead strip as skin so it turns brown
sk_attr = head.data.attributes["skin"]
tilak = (co[:, 2] > brow - 0.05) & (co[:, 2] < brow + 0.02) & (co[:, 1] < np.median(co[:, 1]) - 0.04) & (np.abs(co[:, 0] - chin[0]) < 0.03)
if sk_attr.domain == "POINT":
    for k in np.flatnonzero(tilak): sk_attr.data[k].value = 1.0
else:
    vi = np.empty(len(head.data.loops), int); head.data.loops.foreach_get("vertex_index", vi)
    for k in np.flatnonzero(tilak[vi]): sk_attr.data[k].value = 1.0
print("tilak verts", int(tilak.sum()), flush=True)
# ---- recolour: skin brown, dark texels grey, red cloth ivory ------------------------------------------------------------
def recolour(mat):
    nt = mat.node_tree; N, L = nt.nodes, nt.links.new
    bsdf = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    src = bsdf.inputs["Base Color"].links[0].from_socket
    hsv = N.new("ShaderNodeSeparateColor"); hsv.mode = "HSV"; L(src, hsv.inputs[0])
    sk = N.new("ShaderNodeAttribute"); sk.attribute_name = "skin"

    def m(op, a, b, clamp=True):
        n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
        for i, x in enumerate((a, b)):
            (L(x, n.inputs[i]) if hasattr(x, "is_linked") else n.inputs[i].__setattr__("default_value", x))
        return n.outputs[0]

    def mixc(fac, a, b):
        n = N.new("ShaderNodeMix"); n.data_type = "RGBA"; L(fac, n.inputs[0])
        for sock, x in ((n.inputs[6], a), (n.inputs[7], b)):
            (L(x, sock) if hasattr(x, "is_linked") else sock.__setattr__("default_value", x))
        return n.outputs[2]

    def tint(rgb, gain):                                                # value of the texture times a flat colour
        c = N.new("ShaderNodeCombineColor"); c.mode = "RGB"
        for i in range(3):
            L(m("MULTIPLY", hsv.outputs[2], rgb[i] * gain), c.inputs[i])
        return c.outputs[0]

    notskin = m("SUBTRACT", 1.0, sk.outputs["Fac"])
    H, S, V = hsv.outputs[0], hsv.outputs[1], hsv.outputs[2]
    red = m("MULTIPLY", m("GREATER_THAN", S, 0.42), m("MAXIMUM", m("LESS_THAN", H, 0.035), m("GREATER_THAN", H, 0.93)))
    dark = m("MULTIPLY", m("LESS_THAN", V, 0.06), m("LESS_THAN", S, 0.6))
    grey = N.new("ShaderNodeCombineColor"); grey.mode = "HSV"; grey.inputs[1].default_value = 0.04
    L(m("ADD", m("MULTIPLY", V, 1.8), 0.22), grey.inputs[2])
    c = mixc(m("MULTIPLY", red, notskin), src, tint((0.86, 0.80, 0.68), 1.45))     # ivory dhoti and sash
    c = mixc(m("MULTIPLY", sk.outputs["Fac"], m("GREATER_THAN", V, 0.06)), c, tint((0.62, 0.38, 0.24), 1.25))   # warm brown skin
    c = mixc(dark, c, grey.outputs[0])                                            # iron-grey hair (even where the mask calls it skin)
    L(c, bsdf.inputs["Base Color"])


for o in (body, head):
    for mt in o.data.materials:
        if mt and mt.name.endswith("_detail"):
            recolour(mt)


# ---- turban and beard, on the head bone ---------------------------------------------------------------------------------
def material(name, rgb, rough=0.8, sheen=0.3, bump=0.0, scale=60.0):
    mt = bpy.data.materials.new(name); nt = mt.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Sheen Weight"].default_value = sheen
    if bump:
        nz = nt.nodes.new("ShaderNodeTexWave"); nz.inputs["Scale"].default_value = scale; nz.inputs["Distortion"].default_value = 6
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return mt


def on_head(o):
    o.parent = rig; o.parent_type = "BONE"; o.parent_bone = "head"
    o.matrix_parent_inverse = (rig.matrix_world @ rig.data.bones["head"].matrix_local @
                               __import__("mathutils").Matrix.Translation((0, rig.data.bones["head"].length, 0))).inverted()


hw = co[(co[:, 2] > brow - 0.02) & (co[:, 2] < brow + 0.03)]
cx, cyy = float(chin[0]), float(np.median(hw[:, 1]))
rx = float(np.percentile(np.abs(hw[:, 0] - cx), 90)) + 0.01
ry = float(np.percentile(np.abs(hw[:, 1] - cyy), 90)) + 0.01
cloth = material("SHALYA_turban", (0.82, 0.76, 0.64), bump=0.25, scale=40.0)
gold = material("SHALYA_turban_band", (0.78, 0.55, 0.16), rough=0.3, sheen=0.0); gold.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.85
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1, location=(cx, cyy + 0.01, brow + 0.028))
tb = bpy.context.object; tb.name = "SHALYA_turban"; tb.scale = (rx + 0.022, ry + 0.022, 0.09)
bpy.ops.object.transform_apply(scale=True)
for v in tb.data.vertices:                                              # flat-ish underside, a fuller crown wrapped to one side
    if v.co.z < -0.03: v.co.z = -0.03 + (v.co.z + 0.03) * (0.35 if v.co.y < 0 else 0.9)   # lower at the back, over the nape
    v.co.z += 0.012 * math.sin(math.atan2(v.co.y, v.co.x) * 3 + v.co.z * 40) * (v.co.z > 0)
tb.data.materials.append(cloth); bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.04, location=(cx, cyy + 0.01, brow + 0.002))
band = bpy.context.object; band.name = "SHALYA_turban_band"; band.scale = (rx + 0.022, ry + 0.022, 0.25)
bpy.ops.object.transform_apply(scale=True); band.data.materials.append(gold); bpy.ops.object.shade_smooth()
hair = material("SHALYA_beard", (0.42, 0.41, 0.39), rough=0.9, sheen=0.6, bump=0.6, scale=120.0)
bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=(chin[0], chin[1] + 0.03, chin[2] - 0.03))
bd = bpy.context.object; bd.name = "SHALYA_beard"; bd.scale = (0.05, 0.035, 0.06)
bpy.ops.object.transform_apply(scale=True)
for v in bd.data.vertices:                                              # tapers to a point below the chin
    if v.co.z < 0: v.co.x *= 1 + v.co.z * 6; v.co.z *= 1.35
bd.data.materials.append(hair); bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.25, location=(chin[0], chin[1] + 0.002, chin[2] + 0.055))
mo = bpy.context.object; mo.name = "SHALYA_moustache"; mo.scale = (0.03, 0.012, 0.01); mo.rotation_euler = (math.radians(90), 0, 0)
bpy.ops.object.transform_apply(scale=True, rotation=True); mo.data.materials.append(hair); bpy.ops.object.shade_smooth()
for o in (tb, band, bd, mo):
    on_head(o)

OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), compress=True)
vis = IN.with_name("krishna_hero_v1.visemes.json")
if vis.exists():
    shutil.copy(vis, OUT.with_name("shalya_hero_v1.visemes.json"))
print("saved", OUT, flush=True)

# ---- check render -------------------------------------------------------------------------------------------------------
sc.render.engine = "BLENDER_EEVEE"; sc.eevee.taa_render_samples = 16
sc.render.resolution_x, sc.render.resolution_y = 600, 800
cam = bpy.data.cameras.new("chk"); cobj = bpy.data.objects.new("chk", cam); sc.collection.objects.link(cobj); sc.camera = cobj
sun = bpy.data.lights.new("chk_sun", "SUN"); sun.energy = 4; so = bpy.data.objects.new("chk_sun", sun); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), 0, math.radians(30))
sc.world = bpy.data.worlds.new("chk"); sc.world.color = (0.3, 0.3, 0.35)
c = Vector((cx, cyy, (brow + chin[2]) / 2 + 0.02)); shots = []
for name, off, lens in (("front", (0, -1.2, 0), 60), ("side", (1.2, 0, 0), 60), ("back", (0, 1.2, 0), 60), ("full", (0, -4.5, -0.75), 50)):
    cobj.location = c + Vector(off); d = (c + Vector((0, 0, off[2]))) - cobj.location
    cobj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler(); cam.lens = lens
    p = OUT.with_name(f"_chk_{name}.png"); sc.render.filepath = str(p); bpy.ops.render.render(write_still=True); shots.append(p)
from PIL import Image
ims = [Image.open(p).convert("RGB") for p in shots]
sheet = Image.new("RGB", (sum(i.width for i in ims), 800)); x = 0
for i in ims:
    sheet.paste(i, (x, 0)); x += i.width
sheet.save(OUT.with_name(OUT.stem + "_checks.jpg"), quality=88)
for p in shots:
    p.unlink()
print("checks", OUT.with_name(OUT.stem + "_checks.jpg"))

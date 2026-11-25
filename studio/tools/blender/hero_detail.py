"""Detail pass for a rigged series hero: real metal, engraving relief, living skin, cloth sheen. Free, cloud Blender.

The heroes are TRELLIS meshes with one baked 4K colour texture each (body, head), so the detail comes from that texture:
  gold    texels of gold hue and saturation become metal, a little brighter, with a thin clear coat
  steel   (--steel, Arjuna) low-saturation bright texels outside the skin and face become silver-steel
  relief  the texture's own light and dark (painted engraving, rope, embroidery) is raised as bump on metal and cloth
  edges   convex edges of the metal are polished brighter (Cycles pointiness), like worn armour
  skin    subsurface light (warm red scatter), softer gloss, fine pore bump; --skin-sat boosts its colour (Krishna's blue)
  cloth   sheen and a fine weave
Skin and the steel zone are found per vertex from the texture (a colour test) and stored as mesh attributes the shader
reads, so the masks follow the mesh when it bends.

  python hero_detail.py <hero> <in.blend> <out.blend> [--steel] [--skin-sat 1.2] [--blue-skin] [--gold-lo 0.045]
Check render next to <out>: _detail_checks.jpg (before on top, after below: face, torso, full figure).
"""
import math, pathlib, sys
import bpy
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
HERO, IN, OUT = args[:3]
TAG = HERO.upper()
STEEL = "--steel" in args
BLUE = "--blue-skin" in args
GOLD_LO = float(args[args.index("--gold-lo") + 1]) if "--gold-lo" in args else 0.07   # lowest gold hue (Krishna's crown is copper)
SKIN_SAT = float(args[args.index("--skin-sat") + 1]) if "--skin-sat" in args else 1.0
if pathlib.Path(OUT).exists():
    sys.exit(f"exists, not overwriting (folder law 1): {OUT}")
out = pathlib.Path(OUT).resolve()
bpy.ops.wm.open_mainfile(filepath=str(pathlib.Path(IN).resolve()))
bpy.ops.preferences.addon_enable(module="rigify")
scene = bpy.context.scene
for o in list(scene.objects):
    if o.type in ("CAMERA", "LIGHT"):
        bpy.data.objects.remove(o)


def is_skin(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = np.where(mx > 1e-4, (mx - mn) / np.maximum(mx, 1e-4), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    if BLUE:                                                           # Krishna: lavender blue, b at least near r, r over g
        return (b >= r * 0.85) & (r >= g * 0.95) & (sat > 0.06) & (sat < 0.5) & (mx > 0.08) & (mx < 0.9)
    hue = np.where(mx - mn > 1e-4, ((g - b) / np.maximum(mx - mn, 1e-4)) / 6.0, 0)   # red is max for skin: hue 0..1/6
    return (r >= g) & (g >= b * 0.9) & (sat > 0.25) & (mx > 0.02) & (mx < 0.85) & (r - b > 0.03) & (hue < 0.075)


def base_tex(mat):
    return next(n for n in mat.node_tree.nodes
                if n.type == "TEX_IMAGE" and any(l.to_socket.name == "Base Color" for l in n.outputs[0].links))


def masks(obj, is_head):
    """per-vertex skin (0..1) and steel-zone (0/1) attributes from the colour texture at each loop"""
    me = obj.data
    img = base_tex(obj.active_material).image
    IW, IH = img.size
    px = np.empty(IW * IH * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(IH, IW, 4)
    luv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get("uv", luv); luv = luv.reshape(-1, 2)
    lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", lv)
    rgb = px[np.clip((luv[:, 1] * IH).astype(int), 0, IH - 1), np.clip((luv[:, 0] * IW).astype(int), 0, IW - 1), :3]
    sk = is_skin(rgb).astype(np.float32)
    nv = len(me.vertices)
    acc = np.bincount(lv, sk, nv); cnt = np.maximum(np.bincount(lv, None, nv), 1)
    skin = acc / cnt
    co = np.empty(nv * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    M = np.array(obj.matrix_world); co = co @ M[:3, :3].T + M[:3, 3]
    steel = np.ones(nv, np.float32) if STEEL else np.zeros(nv, np.float32)
    if STEEL and is_head:                                              # keep eyes and teeth out: steel only above the forehead
        S = co[skin > 0.5]                                             # or out at the sides (ear guards)
        front = S[S[:, 1] < np.median(S[:, 1])]
        z_top = np.percentile(front[:, 2], 97); half = np.percentile(np.abs(front[:, 0]), 90)
        steel = ((co[:, 2] > z_top - 0.005) | (np.abs(co[:, 0]) > half * 1.05)).astype(np.float32)
    del px, rgb
    for name, val in (("skin", skin), ("steel_zone", steel)):
        if name in me.attributes:
            me.attributes.remove(me.attributes[name])
        a = me.attributes.new(name, "FLOAT", "POINT"); a.data.foreach_set("value", val.astype(np.float32))
    print(obj.name, "skin verts", int((skin > 0.5).sum()), "steel zone", int(steel.sum()), "of", nv, flush=True)


def smooth(obj):
    """one level of subdivision after the armature: the TRELLIS facets on the muscles round off"""
    for p in obj.data.polygons:
        p.use_smooth = True
    if "detail_subd" not in obj.modifiers:
        m = obj.modifiers.new("detail_subd", "SUBSURF"); m.levels = 0; m.render_levels = 1; m.quality = 2
        m.uv_smooth = "PRESERVE_BOUNDARIES"


def detail_material(obj):
    mat = obj.active_material.copy(); mat.name = obj.active_material.name + "_detail"; obj.active_material = mat
    nt = mat.node_tree; N = nt.nodes; L = nt.links.new
    bsdf = N["Principled BSDF"]; tn = base_tex(mat)
    for l in list(nt.links):                                           # TRELLIS metal/rough map is unreliable: replaced
        if l.to_node == bsdf and l.to_socket.name in ("Metallic", "Roughness", "Base Color"):
            nt.links.remove(l)
    x = [0]

    def node(t, **kw):
        n = N.new(t); x[0] += 1; n.location = (-200 + 180 * (x[0] % 8), -400 - 160 * (x[0] // 8))
        for k, v in kw.items():
            setattr(n, k, v)
        return n

    def math_(op, a, b=None, clamp=False):
        n = node("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs[0]

    def ramp(v, a, b):                                                 # smoothstep from a to b (b < a falls)
        n = node("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", clamp=True)
        L(v, n.inputs["Value"])
        n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = (a, b) if a < b else (b, a)
        n.inputs["To Min"].default_value, n.inputs["To Max"].default_value = (0, 1) if a < b else (1, 0)
        return n.outputs["Result"]

    def attr(name):
        n = node("ShaderNodeAttribute", attribute_name=name); return n.outputs["Fac"]

    col = tn.outputs["Color"]
    hsv = node("ShaderNodeSeparateColor", mode="HSV"); L(col, hsv.inputs["Color"])
    H, S, V = hsv.outputs[0], hsv.outputs[1], hsv.outputs[2]
    skin = attr("skin"); notskin = math_("SUBTRACT", 1.0, skin, True)
    gold = math_("MULTIPLY", math_("MULTIPLY", ramp(H, GOLD_LO - 0.015, GOLD_LO + 0.015), ramp(H, 0.2, 0.165)),
                 math_("MULTIPLY", ramp(S, 0.33, 0.5), ramp(V, 0.18, 0.32)))
    gold = math_("MULTIPLY", gold, notskin)
    steel = math_("MULTIPLY", math_("MULTIPLY", ramp(S, 0.24, 0.12), ramp(V, 0.28, 0.45)), math_("MULTIPLY", attr("steel_zone"), notskin))
    metal = math_("MAXIMUM", gold, steel)
    cloth = math_("MULTIPLY", math_("SUBTRACT", 1.0, metal, True), notskin)
    geo = node("ShaderNodeNewGeometry")
    edge = math_("MULTIPLY", ramp(geo.outputs["Pointiness"], 0.52, 0.58), metal)

    # colour: metals brighter (a metal's albedo is its reflectance), worn edges brighter still; skin saturation
    bright = node("ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY"); bright.inputs["Factor"].default_value = 1
    L(col, bright.inputs["A"]); bright.inputs["B"].default_value = (1.45, 1.4, 1.3, 1)
    c1 = node("ShaderNodeMix", data_type="RGBA"); L(metal, c1.inputs["Factor"]); L(col, c1.inputs["A"]); L(bright.outputs["Result"], c1.inputs["B"])
    hue = node("ShaderNodeHueSaturation"); hue.inputs["Saturation"].default_value = SKIN_SAT; L(c1.outputs["Result"], hue.inputs["Color"])
    L(skin, hue.inputs["Fac"])
    worn = node("ShaderNodeMix", data_type="RGBA", blend_type="SCREEN"); L(math_("MULTIPLY", edge, 0.35), worn.inputs["Factor"])
    L(hue.outputs["Color"], worn.inputs["A"]); worn.inputs["B"].default_value = (1.0, 0.88, 0.6, 1)
    L(worn.outputs["Result"], bsdf.inputs["Base Color"])
    L(math_("MULTIPLY", metal, 0.95), bsdf.inputs["Metallic"])
    rough = math_("ADD", math_("ADD", math_("MULTIPLY", cloth, 0.72), math_("MULTIPLY", skin, 0.6)),
                  math_("MULTIPLY", metal, math_("SUBTRACT", 0.32, math_("MULTIPLY", edge, 0.14))))
    L(rough, bsdf.inputs["Roughness"])
    L(math_("MULTIPLY", skin, 0.3), bsdf.inputs["Subsurface Weight"])
    L(math_("SUBTRACT", 0.5, math_("MULTIPLY", skin, 0.22)), bsdf.inputs["Specular IOR Level"])
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.25)
    bsdf.inputs["Subsurface Scale"].default_value = 0.012
    L(math_("MULTIPLY", cloth, math_("MULTIPLY", V, 0.6)), bsdf.inputs["Sheen Weight"]); bsdf.inputs["Sheen Roughness"].default_value = 0.4
    L(math_("MULTIPLY", gold, 0.25), bsdf.inputs["Coat Weight"]); bsdf.inputs["Coat Roughness"].default_value = 0.12

    # relief: the painted light and dark as height on metal and cloth, pores on skin, weave on cloth
    uv = node("ShaderNodeTexCoord").outputs["UV"]
    pores = node("ShaderNodeTexNoise"); pores.inputs["Scale"].default_value = 2600; pores.inputs["Detail"].default_value = 2
    L(uv, pores.inputs["Vector"])
    weave = node("ShaderNodeTexWave", wave_type="BANDS", bands_direction="DIAGONAL"); weave.inputs["Scale"].default_value = 1800
    L(uv, weave.inputs["Vector"])
    h = math_("ADD", math_("ADD", math_("MULTIPLY", V, math_("ADD", math_("MULTIPLY", metal, 0.9), math_("MULTIPLY", cloth, 0.25))),
                                  math_("MULTIPLY", pores.outputs["Fac"], math_("MULTIPLY", skin, 0.25))),
              math_("MULTIPLY", weave.outputs["Fac"], math_("MULTIPLY", cloth, 0.12)))
    bump = node("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.45; bump.inputs["Distance"].default_value = 0.0015
    L(h, bump.inputs["Height"]); L(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


# ---- check renders: before, then after ------------------------------------------------------------------------------------------
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = 32; scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.resolution_x, scene.render.resolution_y = 560, 700
cam = bpy.data.cameras.new("chk"); camo = bpy.data.objects.new("chk", cam); scene.collection.objects.link(camo); scene.camera = camo
for e, rot, col in ((4.0, (50, 0, -35), (1, 0.93, 0.82)), (2.5, (70, 0, 150), (0.75, 0.85, 1.0))):    # warm key, cool rim
    l = bpy.data.lights.new("k", "SUN"); l.energy = e; l.color = col; l.angle = math.radians(3)
    lo = bpy.data.objects.new("k", l); scene.collection.objects.link(lo); lo.rotation_euler = [math.radians(a) for a in rot]
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.16, 0.15, 0.17, 1); bg.inputs["Strength"].default_value = 1
body, head = bpy.data.objects[f"{TAG}_body"], bpy.data.objects[f"{TAG}_head"]
bpy.context.view_layer.update()
pts = np.array([body.matrix_world @ Vector(c) for c in body.bound_box] + [head.matrix_world @ Vector(c) for c in head.bound_box])
ztop = float(pts[:, 2].max())
rig = bpy.data.objects[f"{TAG}_rig"]
zh = (rig.matrix_world @ rig.pose.bones["DEF-spine.006"].head).z
VIEWS = [("face", Vector((0, 0, zh + 0.1)), 0.42, 28), ("torso", Vector((0, 0, zh - 0.32)), 0.95, 35), ("full", Vector((0, 0, ztop / 2)), ztop * 1.08, 30)]


def shoot(tag):
    paths = []
    cam.type = "ORTHO"
    for name, aim, size, az in VIEWS:
        cam.ortho_scale = size
        a = math.radians(az); d = Vector((math.sin(a), -math.cos(a), 0.12)).normalized()
        camo.location = aim + d * 4; camo.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        p = out.with_name(f"{out.stem}_{tag}_{name}.png"); scene.render.filepath = str(p)
        bpy.ops.render.render(write_still=True); paths.append(p)
    return paths


before = shoot("before")
for o in (body, head):
    masks(o, o is head)
    detail_material(o)
    if o is body:                                                      # the head is already dense (and memory is 16 GB)
        smooth(o)
after = shoot("after")
from PIL import Image
ims = [Image.open(p) for p in before + after]
W, Hh = ims[0].size
sheet = Image.new("RGB", (W * 3, Hh * 2))
for i, im in enumerate(ims):
    sheet.paste(im.convert("RGB"), ((i % 3) * W, (i // 3) * Hh))
sheet.save(out.with_name(out.stem + "_detail_checks.jpg"), quality=88)
for p in before + after:
    p.unlink()
for o in list(scene.objects):
    if o.type in ("CAMERA", "LIGHT"):
        bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
print("saved", OUT, flush=True)

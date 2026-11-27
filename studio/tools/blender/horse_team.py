"""Chariot teams from the Hastinapur TRELLIS white horse (studio/assets/hastinapur/hst_white_horse.glb).

    import horse_team
    team = horse_team.make(chariot_obj, coat="dun")     # Karna (passport: dun horses so the teams read apart)
    team = horse_team.make(chariot_obj, coat="white")   # the horse as painted

Four horses abreast, heads toward the chariot's front (-Y), sharing one mesh, so a team costs one horse of memory.
Placed for the kit chariot krk_rank_chariot (pole tip at y -4.84). The horse is a static statue: fine for standing
and rolling shots (A02, A16); A05's gallop needs a rig. The coat recolour only touches pale, unsaturated texels,
so the gold bridle, bells, green plume and brocade saddle-cloth keep their paint.
"""
import pathlib
import bpy

GLB = pathlib.Path(__file__).resolve().parents[2] / "assets/hastinapur/hst_white_horse.glb"
COATS = {"white": None, "dun": (0.62, 0.40, 0.17), "bay": (0.45, 0.22, 0.10), "black": (0.12, 0.11, 0.11)}
X = (-1.27, -0.45, 0.45, 1.27)     # the pole runs between the two middle horses
Y = -4.3                          # horse centre in chariot space: rumps just ahead of the car, noses past the pole tip

_mesh_cache = {}


def _horse_mesh(coat):
    if coat in _mesh_cache:
        return _mesh_cache[coat]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(GLB))
    src = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
    me = src.data; me.name = f"hst_horse_{coat}"
    for o in set(bpy.data.objects) - before:
        bpy.data.objects.remove(o)
    if COATS[coat]:
        me.materials[0] = _recoat(me.materials[0], coat)
    _mesh_cache[coat] = me
    return me


def _recoat(mat, coat):
    m = mat.copy(); m.name = f"M_hst_horse_{coat}"
    nt = m.node_tree; N, L = nt.nodes, nt.links
    bsdf = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    tex_out = bsdf.inputs["Base Color"].links[0].from_socket
    sep = N.new("ShaderNodeSeparateColor"); sep.mode = "HSV"; L.new(tex_out, sep.inputs[0])
    low_sat = N.new("ShaderNodeMapRange"); L.new(sep.outputs[1], low_sat.inputs[0])
    low_sat.inputs[1].default_value, low_sat.inputs[2].default_value = 0.42, 0.22    # shader values are linear: sat 0.42 -> 0, 0.22 -> 1
    bright = N.new("ShaderNodeMapRange"); L.new(sep.outputs[2], bright.inputs[0])
    bright.inputs[1].default_value, bright.inputs[2].default_value = 0.10, 0.25    # linear value (about sRGB 0.35 to 0.54)
    mask = N.new("ShaderNodeMath"); mask.operation = "MULTIPLY"
    L.new(low_sat.outputs[0], mask.inputs[0]); L.new(bright.outputs[0], mask.inputs[1])
    tint = N.new("ShaderNodeMix"); tint.data_type = "RGBA"; tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    L.new(tex_out, tint.inputs["A"]); tint.inputs["B"].default_value = (*COATS[coat], 1)
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"
    L.new(mask.outputs[0], mix.inputs["Factor"]); L.new(tex_out, mix.inputs["A"]); L.new(tint.outputs["Result"], mix.inputs["B"])
    L.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    return m


def make(chariot, coat="dun", name="team"):
    """Four horses parented to `chariot`; returns the empty that holds them."""
    me = _horse_mesh(coat)
    root = bpy.data.objects.new(f"{name}_{coat}", None); bpy.context.scene.collection.objects.link(root)
    root.parent = chariot
    for i, x in enumerate(X):
        o = bpy.data.objects.new(f"{name}_{coat}_{i}", me); bpy.context.scene.collection.objects.link(o)
        o.parent = root; o.location = (x, Y + (0.06 if i % 2 else -0.04), 0)   # a little stagger so they don't read as clones
        o.rotation_euler = (0, 0, (-1) ** i * 0.03)
    return root

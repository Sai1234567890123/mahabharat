"""Assemble L_Kurukshetra in Unreal 5.8 (run inside the editor's Python).

Follows world/ASSEMBLY_METHOD.md steps 5 to 7 for the Kurukshetra kit:
  1. imports every FBX listed in <kit>/manifest.json into /Game/Kurukshetra/Proc,
     Nanite on, material slots mapped to master materials by slot name;
  2. finds the already-imported TRELLIS meshes (hst_* and krk_*) anywhere under /Game;
  3. places crowds and props from layout.json as one actor per group with an
     InstancedStaticMeshComponent (cheap on a 7.5 GB PC), heroes as single actors;
  4. adds the sun, sky, height fog and the three check cameras.

Re-running replaces only actors whose label starts with KRKP_ or KRK3D_ or KRK_CAM_.

Hero battle models (hero/build_hero.py: chariots, soldiers, war tents, banner, drum cart) are
imported from <hero_dir>/manifest.json into /Game/Kurukshetra/Hero when that folder exists. Their
MAT_* slots get flat master materials M_KRKH_* built from the palette stored in that manifest.
A hero model wins over a TRELLIS mesh of the same name. Add --reimport to import the FBXs again.

In the editor:  py "<path>/ue_assemble_kurukshetra.py" "<kit_dir>" "<layout.json>" ["<hero_dir>"] [--reimport]
"""
import json
import math
import os
import sys

import unreal

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
REIMPORT = "--reimport" in sys.argv
HERE = os.path.dirname(__file__)
KIT_DIR, LAYOUT = (ARGS[0:2] if len(ARGS) >= 2 else (os.path.join(HERE, "kit"), os.path.join(HERE, "layout.json")))
HERO_DIR = ARGS[2] if len(ARGS) >= 3 else os.path.join(HERE, "hero_out")
DEST = "/Game/Kurukshetra/Proc"
HERO_DEST = "/Game/Kurukshetra/Hero"
MAT_DIR = "/Game/Kurukshetra/Materials"
# Master materials made by the Hastinapur assemble_proc.py are reused if they exist there.
HST_MAT_DIRS = ["/Game/Hastinapur/Proc/Materials", "/Game/Hastinapur/Materials"]
SLOT_COLOURS = {
    "MAT_Marble": (0.94, 0.90, 0.82), "MAT_Sandstone": (0.71, 0.54, 0.35), "MAT_Gold": (0.85, 0.65, 0.20),
    "MAT_Malachite": (0.18, 0.42, 0.25), "MAT_Saffron": (0.91, 0.53, 0.12), "MAT_Red": (0.48, 0.10, 0.07),
    "MAT_Wood": (0.36, 0.24, 0.14), "MAT_Bronze": (0.55, 0.36, 0.18), "MAT_Water": (0.20, 0.45, 0.50),
}
TINTS = {"Red": (0.48, 0.10, 0.07), "Saffron": (0.91, 0.53, 0.12)}

eal = unreal.EditorAssetLibrary
ell = unreal.EditorLevelLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(msg):
    unreal.log(f"[KRK] {msg}")


# ------------------------------------------------------------ materials
def make_material(name, rgb_linear, metallic, roughness, existing=None):
    """Flat master material: constant base colour, metallic and roughness. Rebuilds `existing` in place."""
    mel = unreal.MaterialEditingLibrary
    if existing is not None:
        mat = existing
        mel.delete_all_material_expressions(mat)
    else:
        mat = asset_tools.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
    r, g, b = rgb_linear
    col.set_editor_property("constant", unreal.LinearColor(r, g, b, 1))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    metal = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 200)
    metal.set_editor_property("r", metallic)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    rough = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 300)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)
    return mat


def master_material(slot):
    for d in HST_MAT_DIRS + [MAT_DIR]:
        for name in (f"M_{slot}", slot):
            p = f"{d}/{name}"
            if eal.does_asset_exist(p):
                return eal.load_asset(p)
    metal = slot in ("MAT_Gold", "MAT_Bronze")
    return make_material(f"M_{slot}", SLOT_COLOURS[slot], 1.0 if metal else 0.0, 0.3 if metal else 0.8)


HERO_METALLIC_MAX = 0.7
_HERO_MATS_DONE = set()  # rebuilt once per --reimport run


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hero_material(slot, spec):
    """Master for one hero palette slot. The manifest stores sRGB; Unreal wants linear."""
    name = f"M_KRKH_{slot[4:]}"
    p = f"{MAT_DIR}/{name}"
    old = eal.load_asset(p) if eal.does_asset_exist(p) else None
    if old is not None and (not REIMPORT or name in _HERO_MATS_DONE):
        return old
    _HERO_MATS_DONE.add(name)
    # Full metal with a flat colour goes black wherever it reflects shadow, so hero metals are eased to 0.7
    # and kept a little rough; the skylight then still tints them.
    metallic = min(spec["metallic"], HERO_METALLIC_MAX)
    rough = max(spec["roughness"], 0.38) if spec["metallic"] > 0.5 else spec["roughness"]
    return make_material(name, [srgb_to_linear(c) for c in spec["srgb"]], metallic, rough, existing=old)


def tinted_instance(base_mat, tint):
    """Material instance for the Kaurava/Pandava elephant caparison tint.

    Only changes the look if the parent material exposes a vector parameter
    named "Tint"; the baked TRELLIS material does not yet, so for now this is
    a hook for the recolour pass, not a finished recolour.
    """
    path = f"{MAT_DIR}/MI_Elephant_{tint}"
    if eal.does_asset_exist(path):
        return eal.load_asset(path)
    mi = asset_tools.create_asset(f"MI_Elephant_{tint}", MAT_DIR, unreal.MaterialInstanceConstant,
                                  unreal.MaterialInstanceConstantFactoryNew())
    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, base_mat)
    r, g, b = TINTS[tint]
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(r, g, b, 1))
    eal.save_loaded_asset(mi)
    return mi


# ------------------------------------------------------------ import
def import_set(src_dir, dest, material_for, what):
    """Import every FBX in <src_dir>/manifest.json to <dest>; Nanite on; slots mapped by material_for(slot name)."""
    man = json.load(open(os.path.join(src_dir, "manifest.json")))
    meshes = {}
    tasks = []
    for a in man["assets"]:
        sm_path = f"{dest}/SM_{a['name']}"
        if eal.does_asset_exist(sm_path) and not REIMPORT:
            meshes[a["name"]] = eal.load_asset(sm_path)
            continue
        t = unreal.AssetImportTask()
        t.filename = os.path.join(src_dir, a["file"])
        t.destination_path = dest
        t.automated = True
        t.replace_existing = True
        t.save = True
        opts = unreal.FbxImportUI()
        opts.import_mesh = True
        opts.import_materials = False
        opts.import_textures = False
        opts.import_as_skeletal = False
        opts.static_mesh_import_data.combine_meshes = True
        opts.static_mesh_import_data.generate_lightmap_u_vs = False
        opts.static_mesh_import_data.auto_generate_collision = a["category"] != "crowd"
        t.options = opts
        tasks.append((a["name"], t))
    if tasks:
        asset_tools.import_asset_tasks([t for _, t in tasks])
    for name, _ in tasks:
        meshes[name] = eal.load_asset(f"{dest}/SM_{name}")
    for name, sm in list(meshes.items()):
        if sm is None:
            unreal.log_warning(f"[KRK] import failed: {name}")
            del meshes[name]
            continue
        ns = sm.get_editor_property("nanite_settings")
        if not ns.enabled:
            ns.enabled = True
            sm.set_editor_property("nanite_settings", ns)
        for i, slot in enumerate(sm.static_materials):
            mat = material_for(str(slot.material_slot_name), man)
            if mat is not None:
                sm.set_material(i, mat)
        eal.save_loaded_asset(sm)
    log(f"{what} ready: {len(meshes)} meshes")
    return meshes


def kit_slot(sname, man):
    key = next((k for k in SLOT_COLOURS if sname.startswith(k)), None)
    return master_material(key) if key else None


def hero_slot(sname, man):
    pal = man.get("materials", {})
    # longest name first, so MAT_GoldDark is not taken for MAT_Gold
    key = next((k for k in sorted(pal, key=len, reverse=True) if sname.startswith(k)), None)
    return hero_material(key, pal[key]) if key else None


def import_kit():
    return import_set(KIT_DIR, DEST, kit_slot, "kit")


def import_hero():
    if not os.path.exists(os.path.join(HERO_DIR, "manifest.json")):
        unreal.log_warning(f"[KRK] no hero models at {HERO_DIR}; using TRELLIS meshes and proxies only")
        return {}
    return import_set(HERO_DIR, HERO_DEST, hero_slot, "hero models")


def find_trellis_meshes(names):
    """Locate already-imported TRELLIS meshes by name, anywhere under /Game."""
    found = {}
    if not names:  # since hero batch 2 every mesh in the layout is a Blender model
        return found
    want = {n.lower(): n for n in names}
    for path in eal.list_assets("/Game", recursive=True, include_folder=False):
        base = path.split("/")[-1].split(".")[0].lower()
        for key, orig in want.items():
            if orig in found:
                continue
            if base in (key, f"sm_{key}") or base.endswith(key):
                a = eal.load_asset(path)
                if isinstance(a, unreal.StaticMesh):
                    found[orig] = a
    missing = sorted(set(names) - set(found))
    if missing:
        unreal.log_warning(f"[KRK] not imported yet, skipped: {', '.join(missing)}")
    return found


# ------------------------------------------------------------ placement
def clear_previous():
    n = 0
    for a in actor_sub.get_all_level_actors():
        if a.get_actor_label().startswith(("KRKP_", "KRK3D_", "KRK_CAM_", "KRK_ENV_")):
            actor_sub.destroy_actor(a)
            n += 1
    log(f"removed {n} old actors")


def to_transform(t):
    x, y, z, yaw, s = t
    return unreal.Transform(unreal.Vector(x, y, z), unreal.Rotator(0, 0, yaw), unreal.Vector(s, s, s))


def spawn_instanced(label, folder, mesh, transforms, material=None):
    actor = actor_sub.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0))
    actor.set_actor_label(label)
    actor.set_folder_path(folder)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    root = sds.k2_gather_subobject_data_for_instance(actor)[0]
    params = unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.InstancedStaticMeshComponent,
                                          blueprint_context=None)
    handle, fail = sds.add_new_subobject(params)
    if not fail.is_empty():
        raise RuntimeError(f"could not add ISM component for {label}: {fail}")
    bfl = unreal.SubobjectDataBlueprintFunctionLibrary
    comp = bfl.get_object(bfl.get_data(handle))
    comp.set_static_mesh(mesh)
    if material is not None:
        for i in range(mesh.get_num_sections(0) if hasattr(mesh, "get_num_sections") else 1):
            comp.set_material(i, material)
    comp.add_instances([to_transform(t) for t in transforms], False)
    return actor


def spawn_single(label, folder, mesh, t):
    tr = to_transform(t)
    a = actor_sub.spawn_actor_from_object(mesh, tr.translation, tr.rotation.rotator())
    a.set_actor_scale3d(tr.scale3d)
    a.set_actor_label(label)
    a.set_folder_path(folder)
    return a


def ground_material():
    """v3: dusty ground with large patches and fine mottling instead of one flat colour."""
    path = f"{MAT_DIR}/M_KRK_Ground"
    if eal.does_asset_exist(path):
        return eal.load_asset(path)
    mel = unreal.MaterialEditingLibrary
    mat = asset_tools.create_asset("M_KRK_Ground", MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())

    def const3(rgb, x, y):
        e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, x, y)
        e.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1))
        return e

    def noise(scale, x, y):
        e = mel.create_material_expression(mat, unreal.MaterialExpressionNoise, x, y)
        e.set_editor_property("scale", scale)
        e.set_editor_property("output_min", 0.0)
        e.set_editor_property("output_max", 1.0)
        return e

    light, dust, dark = const3((0.62, 0.48, 0.32), -900, 0), const3((0.45, 0.33, 0.21), -900, 150), \
        const3((0.23, 0.17, 0.11), -900, 300)
    big, fine = noise(0.0004, -900, 450), noise(0.03, -900, 600)
    l1 = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -500, 100)
    mel.connect_material_expressions(light, "", l1, "A")
    mel.connect_material_expressions(dust, "", l1, "B")
    mel.connect_material_expressions(big, "", l1, "Alpha")
    k = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -700, 700)
    k.set_editor_property("r", 0.35)
    m = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -500, 600)
    mel.connect_material_expressions(fine, "", m, "A")
    mel.connect_material_expressions(k, "", m, "B")
    l2 = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -250, 200)
    mel.connect_material_expressions(l1, "", l2, "A")
    mel.connect_material_expressions(dark, "", l2, "B")
    mel.connect_material_expressions(m, "", l2, "Alpha")
    mel.connect_material_property(l2, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -250, 400)
    rough.set_editor_property("r", 0.95)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)
    return mat


def environment(L):
    sun_cfg = L["sun"]
    sun = actor_sub.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 50000),
                                           unreal.Rotator(0, sun_cfg["pitch"], sun_cfg["yaw"]))
    sun.set_actor_label("KRK_ENV_Sun")
    sun.set_folder_path("KRK/Env")
    lc = sun.get_component_by_class(unreal.DirectionalLightComponent)
    lc.set_editor_property("intensity", sun_cfg.get("intensity", 9.0))
    lc.set_light_color(unreal.LinearColor(1.0, 0.76, 0.48, 1))
    lc.set_editor_property("atmosphere_sun_light", True)
    env = [(unreal.SkyAtmosphere, "KRK_ENV_Sky"), (unreal.SkyLight, "KRK_ENV_SkyLight")]
    if sun_cfg.get("clouds") and hasattr(unreal, "VolumetricCloud"):
        env.append((unreal.VolumetricCloud, "KRK_ENV_Clouds"))  # v2: dramatic sky
    for cls, label in env:
        a = actor_sub.spawn_actor_from_class(cls, unreal.Vector(0, 0, 0))
        a.set_actor_label(label)
        a.set_folder_path("KRK/Env")
        if cls is unreal.SkyLight:
            sk = a.get_component_by_class(unreal.SkyLightComponent)
            sk.set_editor_property("real_time_capture", True)
            sk.set_editor_property("intensity", sun_cfg.get("sky_intensity", 1.0))   # fill, so shadow sides read
            sk.set_editor_property("lower_hemisphere_is_black", False)
    fog = actor_sub.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0))
    fog.set_actor_label("KRK_ENV_DustFog")
    fog.set_folder_path("KRK/Env")
    fc = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    fc.set_editor_property("fog_density", sun_cfg["fog_density"])
    fc.set_editor_property("fog_height_falloff", 0.12)
    fc.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(0.71, 0.54, 0.35, 1))
    fc.set_editor_property("enable_volumetric_fog", True)
    fc.set_editor_property("volumetric_fog_albedo", unreal.Color(220, 180, 130, 255))


def cameras(L):
    for c in L["cameras"]:
        cam = actor_sub.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(*c["loc"]),
                                               unreal.Rotator(0, c["rot"][0], c["rot"][1]))
        cam.set_actor_label(c["label"])
        cam.set_folder_path("KRK/Cameras")
        cc = cam.get_cine_camera_component()
        # horizontal FOV -> focal length on the default 36 mm filmback
        cc.set_editor_property("current_focal_length", 18.0 / math.tan(math.radians(c["fov"]) / 2))


def main():
    L = json.load(open(LAYOUT))
    kit = import_kit()
    hero = import_hero()
    trellis_names = sorted(({k.split("@")[0] for k in L["groups"] if not k.startswith("KRK_")} |
                            {h["mesh"] for h in L["heroes"]}) - set(hero))
    trellis = find_trellis_meshes(trellis_names)
    trellis.update(hero)  # a hero model wins over a TRELLIS mesh of the same name
    clear_previous()

    if L["terrain"] in kit:
        ter = spawn_single("KRKP_Terrain", "KRK/Terrain", kit[L["terrain"]], [0, 0, 0, 0, 1])
        ter.static_mesh_component.set_material(0, ground_material())

    with unreal.ScopedSlowTask(len(L["groups"]), "Placing Kurukshetra") as task:
        task.make_dialog(True)
        for key, g in L["groups"].items():
            task.enter_progress_frame(1, key)
            base, _, tint = key.partition("@")
            mesh = kit.get(base) or trellis.get(base)
            if mesh is None:
                continue
            mat = None
            if tint and mesh.static_materials:
                mat = tinted_instance(mesh.static_materials[0].material_interface, tint)
            prefix = "KRKP_" if base.startswith("KRK_") else "KRK3D_"
            spawn_instanced(f"{prefix}{key.replace('@', '_')}", g["folder"], mesh, g["instances"], mat)
            log(f"{key}: {len(g['instances'])} instances")

    for h in L["heroes"]:
        mesh = trellis.get(h["mesh"])
        if mesh is not None:
            spawn_single(h["label"], h["folder"], mesh, h["t"])

    environment(L)
    cameras(L)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("done; check views: " + ", ".join(c["label"] for c in L["cameras"]))


main()

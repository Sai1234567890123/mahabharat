"""Assemble L_Kurukshetra in Unreal 5.8 (run inside the editor's Python).

Follows world/ASSEMBLY_METHOD.md steps 5 to 7 for the Kurukshetra kit:
  1. imports every FBX listed in <kit>/manifest.json into /Game/Kurukshetra/Proc,
     Nanite on, material slots mapped to master materials by slot name;
  2. finds the already-imported TRELLIS meshes (hst_* and krk_*) anywhere under /Game;
  3. places crowds and props from layout.json as one actor per group with an
     InstancedStaticMeshComponent (cheap on a 7.5 GB PC), heroes as single actors;
  4. adds the sun, sky, height fog and the three check cameras.

Re-running replaces only actors whose label starts with KRKP_ or KRK3D_ or KRK_CAM_.

In the editor:  py "<path>/ue_assemble_kurukshetra.py" "<kit_dir>" "<layout.json>"
"""
import json
import math
import os
import sys

import unreal

KIT_DIR, LAYOUT = (sys.argv[1:3] if len(sys.argv) >= 3 else
                   (os.path.join(os.path.dirname(__file__), "kit"), os.path.join(os.path.dirname(__file__), "layout.json")))
DEST = "/Game/Kurukshetra/Proc"
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
def master_material(slot):
    for d in HST_MAT_DIRS + [MAT_DIR]:
        for name in (f"M_{slot}", slot):
            p = f"{d}/{name}"
            if eal.does_asset_exist(p):
                return eal.load_asset(p)
    # create a simple master: constant base colour, metallic for gold and bronze
    mat = asset_tools.create_asset(f"M_{slot}", MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    col = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
    r, g, b = SLOT_COLOURS[slot]
    col.set_editor_property("constant", unreal.LinearColor(r, g, b, 1))
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    metal = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 200)
    metal.set_editor_property("r", 1.0 if slot in ("MAT_Gold", "MAT_Bronze") else 0.0)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    rough = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 300)
    rough.set_editor_property("r", 0.3 if slot in ("MAT_Gold", "MAT_Bronze") else 0.8)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)
    return mat


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
def import_kit():
    man = json.load(open(os.path.join(KIT_DIR, "manifest.json")))
    meshes = {}
    tasks = []
    for a in man["assets"]:
        sm_path = f"{DEST}/SM_{a['name']}"
        if eal.does_asset_exist(sm_path):
            meshes[a["name"]] = eal.load_asset(sm_path)
            continue
        t = unreal.AssetImportTask()
        t.filename = os.path.join(KIT_DIR, a["file"])
        t.destination_path = DEST
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
        meshes[name] = eal.load_asset(f"{DEST}/SM_{name}")
    for name, sm in meshes.items():
        if sm is None:
            unreal.log_warning(f"[KRK] import failed: {name}")
            continue
        ns = sm.get_editor_property("nanite_settings")
        if not ns.enabled:
            ns.enabled = True
            sm.set_editor_property("nanite_settings", ns)
        for i, slot in enumerate(sm.static_materials):
            sname = str(slot.material_slot_name)
            key = next((k for k in SLOT_COLOURS if sname.startswith(k)), None)
            if key:
                sm.set_material(i, master_material(key))
        eal.save_loaded_asset(sm)
    log(f"kit ready: {len(meshes)} meshes")
    return meshes


def find_trellis_meshes(names):
    """Locate already-imported TRELLIS meshes by name, anywhere under /Game."""
    found = {}
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


def environment(L):
    sun_cfg = L["sun"]
    sun = actor_sub.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 50000),
                                           unreal.Rotator(0, sun_cfg["pitch"], sun_cfg["yaw"]))
    sun.set_actor_label("KRK_ENV_Sun")
    sun.set_folder_path("KRK/Env")
    lc = sun.get_component_by_class(unreal.DirectionalLightComponent)
    lc.set_editor_property("intensity", 9.0)
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
            a.get_component_by_class(unreal.SkyLightComponent).set_editor_property("real_time_capture", True)
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
    trellis_names = sorted({k.split("@")[0] for k in L["groups"] if not k.startswith("KRK_")} |
                           {h["mesh"] for h in L["heroes"]})
    trellis = find_trellis_meshes(trellis_names)
    clear_previous()

    if L["terrain"] in kit:
        spawn_single("KRKP_Terrain", "KRK/Terrain", kit[L["terrain"]], [0, 0, 0, 0, 1])

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

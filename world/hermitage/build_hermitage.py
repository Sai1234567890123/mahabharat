#!/usr/bin/env python3
"""Build the S1E01 sc01 Vedic Forest Hermitage set in Blender 5.2 (EEVEE).

Matches all 12 shots in studio/episodes/s1e01_the_scribe/sc01/shots.json and the
Vedic period checklist in studio/episodes/s1e01_the_scribe/canon_check.md:
  - Riverbank ashram at dawn beside misty Malini river with grazing spotted deer (S01)
  - Layered kusa-grass thatched open-porch earthen hut (no stone temple)
  - Stepped earthen Homa fire altar (Kunda) with sculpted Agni flames & smooth rising smoke
  - Ancient banyan with CC0 buttress root clusters, wide multi-limb umbrella canopy &
    gnarled hanging aerial roots — keeping center sky completely open above altar for Brahma's lotus seat
  - Vyasa left & Ganesha right woven kusa mats, incised palm-leaf (Talapatra) bundles,
    curled birch-bark (Bhurja-patra) sheets, cast bronze stylus & open brass/clay diya (zero glass!)
  - Clay terracotta & hammered brass vessels (strictly CC0 Poly Haven assets, zero glass/idols/paper books)
  - Lit with studio/bible.md palette: warm gold key (#FFC27A) + cool blue dawn shadow (#3E5A86)
  - Exports compact self-contained world/hermitage/hermitage_set.blend (<40 MB) + 12 1280x720 EEVEE stills.
"""
import argparse
import math
import pathlib
import random
import shutil
import sys
import tempfile

import bmesh
import bpy
from mathutils import Euler, Vector

DEFAULT_ASSETS = pathlib.Path(r"C:\Users\dharm\OneDrive\Desktop\claude projects\MAHABHARATA_STUDIO\02_BLENDER")
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
HERMITAGE_DIR = REPO_ROOT / "world" / "hermitage"


def reset_scene():
    """Initialize a clean metric Blender scene."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    return scene


def make_collection(name: str, parent=None):
    """Create and link a named collection cleanly."""
    col = bpy.data.collections.new(name)
    if parent is None:
        bpy.context.scene.collection.children.link(col)
    else:
        parent.children.link(col)
    return col


def link_to_col(obj, col):
    """Link object exclusively to col."""
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    return obj


def set_smooth_shade(obj):
    """Enable smooth shading across all faces of a mesh object."""
    if obj and obj.type == "MESH" and obj.data:
        for poly in obj.data.polygons:
            poly.use_smooth = True


class CC0AssetCache:
    """Load each external CC0 collection once and instance duplicates cleanly to avoid duplicate texture bloat."""

    def __init__(self):
        self._templates = {}

    def _load_template(self, blend_path: pathlib.Path, col_name: str, decimate_ratio=None, override_mat=None):
        key = (str(blend_path), col_name, decimate_ratio, override_mat.name if override_mat else None)
        if key in self._templates:
            return self._templates[key]
        if not blend_path.exists():
            raise FileNotFoundError(f"Missing CC0 blend asset: {blend_path}")

        with bpy.data.libraries.load(str(blend_path), link=False) as (df, dt):
            if col_name not in df.collections:
                raise ValueError(f"Collection '{col_name}' missing in {blend_path.name}; found={list(df.collections)}")
            dt.collections = [col_name]

        src_col = dt.collections[0]
        # Keep only primary root meshes (avoid duplicate hidden proxies if present)
        objs = [o for o in src_col.all_objects if o.type == "MESH"]
        if not objs:
            objs = list(src_col.all_objects)

        for obj in objs:
            if obj.type != "MESH":
                continue
            if decimate_ratio is not None and 0.05 < decimate_ratio < 0.99 and len(obj.data.polygons) > 10000:
                bpy.context.scene.collection.objects.link(obj)
                mod = obj.modifiers.new(name="SetDecimate", type="DECIMATE")
                mod.ratio = decimate_ratio
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.modifier_apply(modifier=mod.name)
                bpy.context.scene.collection.objects.unlink(obj)
            if override_mat is not None:
                obj.data.materials.clear()
                obj.data.materials.append(override_mat)
            for m in obj.data.materials:
                if m and "glass" in m.name.lower():
                    raise RuntimeError(f"Disallowed glass material '{m.name}' inside {blend_path.name}")

        min_z = 0.0
        zs = [b[2] for o in objs if o.type == "MESH" for b in o.bound_box]
        if zs:
            min_z = min(zs)

        self._templates[key] = (objs, min_z)
        bpy.data.collections.remove(src_col)
        return self._templates[key]

    def place(
        self,
        blend_path: pathlib.Path,
        col_name: str,
        target_col,
        loc=(0.0, 0.0, 0.0),
        rot=(0.0, 0.0, 0.0),
        scale=(1.0, 1.0, 1.0),
        name_prefix="Prop",
        decimate_ratio=None,
        override_mat=None,
        ground_align=False,
    ):
        """Instantiate an already-cached CC0 mesh group sharing mesh & material datablocks."""
        objs, min_z = self._load_template(blend_path, col_name, decimate_ratio, override_mat)
        z_off = (-min_z * scale[2]) if ground_align else 0.0
        placed = []
        for idx, tmpl in enumerate(objs):
            inst = bpy.data.objects.new(f"{name_prefix}_{idx}" if len(objs) > 1 else name_prefix, tmpl.data)
            target_col.objects.link(inst)
            inst.location = (loc[0] + tmpl.location[0] * scale[0], loc[1] + tmpl.location[1] * scale[1], loc[2] + z_off + tmpl.location[2] * scale[2])
            inst.rotation_euler = Euler((math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2])), "XYZ")
            inst.scale = (tmpl.scale[0] * scale[0], tmpl.scale[1] * scale[1], tmpl.scale[2] * scale[2])
            set_smooth_shade(inst)
            placed.append(inst)
        return placed


def append_material(blend_path: pathlib.Path, mat_name: str):
    """Append a CC0 PBR material cleanly by exact name."""
    if not blend_path.exists():
        raise FileNotFoundError(f"Missing texture blend: {blend_path}")
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]
    with bpy.data.libraries.load(str(blend_path), link=False) as (df, dt):
        if mat_name in df.materials:
            dt.materials = [mat_name]
    return dt.materials[0] if dt.materials else None


def configure_box_mapping(mat, scale_val=1.0):
    """Rewire material images to Object-space Box projection so trunks & terrain never stretch UVs."""
    if not mat or not mat.node_tree:
        return
    nt = mat.node_tree
    tcoord = next((n for n in nt.nodes if n.type == "TEX_COORD"), None) or nt.nodes.new("ShaderNodeTexCoord")
    mapping = next((n for n in nt.nodes if n.type == "MAPPING"), None) or nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (scale_val, scale_val, scale_val)
    nt.links.new(tcoord.outputs["Object"], mapping.inputs["Vector"])
    for n in nt.nodes:
        if n.type == "TEX_IMAGE":
            n.projection = "BOX"
            n.projection_blend = 0.25
            nt.links.new(mapping.outputs["Vector"], n.inputs["Vector"])


def make_painterly_mat(
    name: str,
    base_color,
    roughness=0.78,
    spec=0.25,
    metallic=0.0,
    emission=None,
    emission_strength=0.0,
    noise_scale=28.0,
    noise_amp=0.10,
    bump_strength=0.12,
):
    """Create a rich textured Principled material matching studio/bible.md."""
    mat = bpy.data.materials.new(name=name)
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = spec

    if noise_amp > 0 or bump_strength > 0:
        tcoord = nt.nodes.new("ShaderNodeTexCoord")
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = noise_scale
        tex.inputs["Detail"].default_value = 6.0
        tex.inputs["Roughness"].default_value = 0.65
        nt.links.new(tcoord.outputs["Object"], tex.inputs["Vector"])

        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        c_dark = tuple(max(0.0, c * (1.0 - noise_amp)) for c in base_color[:3]) + (1.0,)
        c_lit = tuple(min(1.0, c * (1.0 + noise_amp)) for c in base_color[:3]) + (1.0,)
        mix.inputs[6].default_value = c_dark
        mix.inputs[7].default_value = c_lit
        nt.links.new(tex.outputs["Fac"], mix.inputs["Factor"])
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])

        if bump_strength > 0:
            bump = nt.nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = bump_strength
            bump.inputs["Distance"].default_value = 0.015
            nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
            nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    else:
        bsdf.inputs["Base Color"].default_value = (*base_color[:3], 1.0)

    if emission and emission_strength > 0:
        bsdf.inputs["Emission Color"].default_value = (*emission[:3], 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def clamp_loaded_materials():
    """Soften raw glossiness on imported PBR mats while keeping water/metals crisp."""
    for mat in bpy.data.materials:
        nt = getattr(mat, "node_tree", None)
        if not nt:
            continue
        bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if not bsdf:
            continue
        m_name = mat.name.lower()
        if any(k in m_name for k in ("water", "flame", "smoke", "mist", "brass", "bronze", "ghee", "diya")):
            continue
        r_inp = bsdf.inputs.get("Roughness")
        if r_inp and not r_inp.is_linked and r_inp.default_value < 0.55:
            r_inp.default_value = 0.68
        s_inp = bsdf.inputs.get("Specular IOR Level")
        if s_inp and not s_inp.is_linked:
            s_inp.default_value = min(s_inp.default_value, 0.25)


def terrain_height_at(x: float, y: float) -> float:
    """Dead-flat sacred clearing r<=3.6m, gentle forest bank swells, sloping smoothly into Malini river & far hills."""
    dist_clear = math.hypot(x, y)
    t_hill = max(0.0, min(1.0, (dist_clear - 3.6) / 2.8))
    t_hill = t_hill * t_hill * (3.0 - 2.0 * t_hill)
    undulation = t_hill * (0.14 * math.sin(x * 0.22) * math.cos(y * 0.20) + 0.08 * math.sin(x * 0.48 + y * 0.28))

    bank_y = 4.65 + 0.70 * math.sin(x * 0.16)
    river_drop = -max(0.0, min(1.15, (y - bank_y) * 0.25))

    # Opposite wooded Malini river shore rises gently from Y > 21m so horizon never shows floating plane edge!
    far_rise = max(0.0, (y - 21.0) * 0.22) + (0.65 * math.sin(x * 0.11 + 1.0) if y > 22.0 else 0.0)
    return undulation + river_drop + far_rise


def build_terrain_and_river(col, ph_tex_dir: pathlib.Path):
    """Build lush Vedic forest loam bank, pebble shore, wide endless misty Malini river, and dawn mist ribbons."""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=80, y_subdivisions=80, size=110.0, location=(0.0, 14.0, 0.0))
    ground = link_to_col(bpy.context.active_object, col)
    ground.name = "Terrain_HermitageBank"
    for v in ground.data.vertices:
        wx, wy = v.co.x, v.co.y + 14.0
        v.co.z = terrain_height_at(wx, wy)
    ground.data.update()
    set_smooth_shade(ground)

    # Rich warm loam + mossy riverside forest green blend built over CC0 dry_ground_01 diffuse
    ground_mat = append_material(ph_tex_dir / "dry_ground_01" / "dry_ground_01_2k.blend", "dry_ground_01")
    if ground_mat and ground_mat.node_tree:
        gnt = ground_mat.node_tree
        configure_box_mapping(ground_mat, 0.55)
        bsdf = next(n for n in gnt.nodes if n.type == "BSDF_PRINCIPLED")
        diff_src = bsdf.inputs["Base Color"].links[0].from_socket if bsdf.inputs["Base Color"].is_linked else None
        if diff_src:
            # Tint bright grey clay toward rich damp ochre earth & blend mossy green patches in clearing margins
            earth_tint = gnt.nodes.new("ShaderNodeMix")
            earth_tint.data_type = "RGBA"
            earth_tint.blend_type = "MULTIPLY"
            earth_tint.inputs["Factor"].default_value = 0.85
            earth_tint.inputs[7].default_value = (0.36, 0.24, 0.14, 1.0)
            gnt.links.new(diff_src, earth_tint.inputs[6])

            moss_noise = gnt.nodes.new("ShaderNodeTexNoise")
            moss_noise.inputs["Scale"].default_value = 0.35
            moss_noise.inputs["Detail"].default_value = 4.0
            moss_ramp = gnt.nodes.new("ShaderNodeValToRGB")
            moss_ramp.color_ramp.elements[0].position = 0.42
            moss_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
            moss_ramp.color_ramp.elements[1].position = 0.62
            moss_ramp.color_ramp.elements[1].color = (0.58, 0.58, 0.58, 1.0)
            tcoord = next((n for n in gnt.nodes if n.type == "TEX_COORD"), None) or gnt.nodes.new("ShaderNodeTexCoord")
            gnt.links.new(tcoord.outputs["Object"], moss_noise.inputs["Vector"])
            gnt.links.new(moss_noise.outputs["Fac"], moss_ramp.inputs["Fac"])

            moss_mix = gnt.nodes.new("ShaderNodeMix")
            moss_mix.data_type = "RGBA"
            moss_mix.inputs[7].default_value = (0.14, 0.22, 0.09, 1.0)  # lush Vedic bank moss
            gnt.links.new(moss_ramp.outputs["Color"], moss_mix.inputs["Factor"])
            gnt.links.new(earth_tint.outputs[2], moss_mix.inputs[6])
            gnt.links.new(moss_mix.outputs[2], bsdf.inputs["Base Color"])
    ground.data.materials.append(ground_mat)

    # Curving riverbank pebbles conform strip along shore
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=48, y_subdivisions=10, size=60.0, location=(0.0, 5.75, 0.0))
    pebble_strip = link_to_col(bpy.context.active_object, col)
    pebble_strip.name = "Malini_ShorePebbles"
    pebble_strip.scale = (1.0, 0.055, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for v in pebble_strip.data.vertices:
        wx = v.co.x
        v.co.y += 0.70 * math.sin(wx * 0.16)
        wy = v.co.y + 5.75
        v.co.z = terrain_height_at(wx, wy) + 0.015
    pebble_strip.data.update()
    set_smooth_shade(pebble_strip)
    pebble_mat = append_material(ph_tex_dir / "ganges_river_pebbles" / "ganges_river_pebbles_2k.blend", "ganges_river_pebbles")
    configure_box_mapping(pebble_mat, 0.85)
    pebble_strip.data.materials.append(pebble_mat)

    # Wide endless Malini river water spanning full camera horizon (-60m..+60m)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=36, y_subdivisions=18, size=120.0, location=(0.0, 14.5, -0.32))
    water = link_to_col(bpy.context.active_object, col)
    water.name = "Malini_River_Water"
    water.scale = (1.0, 0.18, 1.0)
    set_smooth_shade(water)

    water_mat = bpy.data.materials.new("Malini_River_Water")
    wnt = water_mat.node_tree
    wbsdf = next(n for n in wnt.nodes if n.type == "BSDF_PRINCIPLED")
    wbsdf.inputs["Base Color"].default_value = (0.035, 0.075, 0.135, 1.0)  # deep twilight blue river
    wbsdf.inputs["Roughness"].default_value = 0.09
    wbsdf.inputs["Specular IOR Level"].default_value = 0.75
    wtex = wnt.nodes.new("ShaderNodeTexNoise")
    wtex.inputs["Scale"].default_value = 55.0
    wtex.inputs["Detail"].default_value = 5.0
    wbump = wnt.nodes.new("ShaderNodeBump")
    wbump.inputs["Strength"].default_value = 0.07
    wbump.inputs["Distance"].default_value = 0.01
    wnt.links.new(wtex.outputs["Fac"], wbump.inputs["Height"])
    wnt.links.new(wbump.outputs["Normal"], wbsdf.inputs["Normal"])
    water.data.materials.append(water_mat)

    # Smooth BLENDED morning mist layers floating over Malini river (zero dither stippling!)
    mist_mat = bpy.data.materials.new("Malini_SmoothMorningMist")
    mist_mat.surface_render_method = "BLENDED"
    mnt = mist_mat.node_tree
    mbsdf = next(n for n in mnt.nodes if n.type == "BSDF_PRINCIPLED")
    mbsdf.inputs["Base Color"].default_value = (0.64, 0.75, 0.90, 1.0)
    mbsdf.inputs["Roughness"].default_value = 1.0
    mbsdf.inputs["Emission Color"].default_value = (0.68, 0.78, 0.94, 1.0)
    mbsdf.inputs["Emission Strength"].default_value = 0.35

    tcoord = mnt.nodes.new("ShaderNodeTexCoord")
    grad = mnt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "QUADRATIC_SPHERE"
    map_g = mnt.nodes.new("ShaderNodeMapping")
    map_g.inputs["Location"].default_value = (-1.0, -1.0, 0.0)
    map_g.inputs["Scale"].default_value = (2.0, 2.0, 2.0)
    noise = mnt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.6
    noise.inputs["Detail"].default_value = 3.0
    mult1 = mnt.nodes.new("ShaderNodeMath")
    mult1.operation = "MULTIPLY"
    mult2 = mnt.nodes.new("ShaderNodeMath")
    mult2.operation = "MULTIPLY"
    mult2.inputs[1].default_value = 0.24
    mnt.links.new(tcoord.outputs["UV"], map_g.inputs["Vector"])
    mnt.links.new(map_g.outputs["Vector"], grad.inputs["Vector"])
    mnt.links.new(grad.outputs["Fac"], mult1.inputs[0])
    mnt.links.new(noise.outputs["Fac"], mult1.inputs[1])
    mnt.links.new(mult1.outputs["Value"], mult2.inputs[0])
    mnt.links.new(mult2.outputs["Value"], mbsdf.inputs["Alpha"])

    for idx, (mx, my, mz, sx, sy, rx) in enumerate([
        (-4.5, 9.2, 0.05, 14.0, 3.8, 4),
        (5.5, 11.0, 0.16, 16.0, 4.2, -3),
        (-0.5, 14.8, 0.42, 24.0, 5.5, 5),
        (-12.0, 12.2, 0.22, 14.0, 4.0, 2),
        (14.0, 12.6, 0.25, 14.0, 4.2, 3),
    ]):
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(mx, my, mz))
        mc = link_to_col(bpy.context.active_object, col)
        mc.name = f"Malini_MistLayer_{idx+1}"
        mc.scale = (sx, sy, 1.0)
        mc.rotation_euler = (math.radians(rx), 0.0, 0.0)
        mc.data.materials.append(mist_mat)


def build_kusa_hut(col, loc=(-4.9, -2.0, 0.0), rot_deg=-35.0):
    """Build a rustic 1000 BCE Vedic thatched kusa-grass hut with overlapping shingled straw eaves."""
    parent = bpy.data.objects.new("Ashram_KusaHut_Root", None)
    parent.location = loc
    parent.rotation_euler = (0.0, 0.0, math.radians(rot_deg))
    col.objects.link(parent)

    mud_mat = make_painterly_mat("Hut_EarthenMud", (0.31, 0.19, 0.11), roughness=0.92, spec=0.12, noise_scale=16.0, noise_amp=0.18, bump_strength=0.22)
    wood_mat = make_painterly_mat("Hut_SalTimber", (0.18, 0.11, 0.06), roughness=0.86, spec=0.16, noise_scale=32.0, noise_amp=0.16, bump_strength=0.18)
    thatch_mat = make_painterly_mat("Hut_KusaThatch", (0.39, 0.28, 0.12), roughness=0.96, spec=0.08, noise_scale=80.0, noise_amp=0.26, bump_strength=0.45)
    thatch_dark = make_painterly_mat("Hut_KusaUnderEave", (0.24, 0.17, 0.08), roughness=0.96, spec=0.06, noise_scale=70.0, noise_amp=0.20, bump_strength=0.35)
    rope_mat = make_painterly_mat("Hut_HempCord", (0.28, 0.18, 0.09), roughness=0.92, spec=0.08)

    def add_child(obj, name, mat):
        link_to_col(obj, col)
        obj.parent = parent
        obj.name = name
        obj.data.materials.append(mat)
        return obj

    # Raised earthen mud plinth
    bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=2.30, depth=0.22, location=(0, 0, 0.11))
    add_child(bpy.context.active_object, "Hut_EarthenPlinth_Base", mud_mat)
    bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=1.92, depth=0.12, location=(0, 0, 0.24))
    add_child(bpy.context.active_object, "Hut_EarthenPlinth_Step", mud_mat)

    # Curved mud-wattle wall leaving wide open doorway (-34°..+34°)
    bm = bmesh.new()
    segs = 28
    ang_start, ang_end = math.radians(34.0), math.radians(326.0)
    r_in, r_out, z0, z1 = 1.56, 1.72, 0.28, 1.98
    rings = []
    for i in range(segs + 1):
        a = ang_start + (ang_end - ang_start) * (i / segs)
        ca, sa = math.cos(a), math.sin(a)
        rings.append((bm.verts.new((r_in * ca, r_in * sa, z0)), bm.verts.new((r_in * ca, r_in * sa, z1)),
                      bm.verts.new((r_out * ca, r_out * sa, z0)), bm.verts.new((r_out * ca, r_out * sa, z1))))
    for i in range(segs):
        a, b = rings[i], rings[i + 1]
        bm.faces.new((a[2], b[2], b[3], a[3]))
        bm.faces.new((b[0], a[0], a[1], b[1]))
        bm.faces.new((a[3], b[3], b[1], a[1]))
    bm.faces.new((rings[0][0], rings[0][1], rings[0][3], rings[0][2]))
    bm.faces.new((rings[-1][2], rings[-1][3], rings[-1][1], rings[-1][0]))
    wm = bpy.data.meshes.new("Hut_CurvedMudWall")
    bm.to_mesh(wm)
    bm.free()
    wobj = bpy.data.objects.new("Hut_CurvedMudWall", wm)
    add_child(wobj, "Hut_CurvedMudWall", mud_mat)
    set_smooth_shade(wobj)

    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=1.54, depth=0.04, location=(0, 0, 0.29))
    add_child(bpy.context.active_object, "Hut_DarkFloor", make_painterly_mat("Hut_InteriorSoil", (0.12, 0.08, 0.05), roughness=0.95))

    for side, ang_d in [("L", 34.0), ("R", -34.0)]:
        ar = math.radians(ang_d)
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.062, depth=1.90, location=(1.64 * math.cos(ar), 1.64 * math.sin(ar), 1.15))
        add_child(bpy.context.active_object, f"Hut_DoorPost_{side}", wood_mat)
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.062, depth=2.0, location=(1.46, 0.0, 1.94), rotation=(math.radians(90), 0, 0))
    add_child(bpy.context.active_object, "Hut_DoorLintel", wood_mat)

    for i in range(11):
        ar = math.radians(38.0 + (284.0 * i / 10.0))
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.045, depth=1.86, location=(2.02 * math.cos(ar), 2.02 * math.sin(ar), 1.06))
        add_child(bpy.context.active_object, f"Hut_VerandahPole_{i:02d}", wood_mat)

    # 5 Corrugated layered bell-skirt kusa thatch tiers (flush overlapping bundled straw ribs!)
    rng = random.Random(101)
    for tier_idx, (r_bot, r_top, z_bot, z_top, mat) in enumerate([
        (2.86, 2.25, 1.72, 2.28, thatch_dark),
        (2.48, 1.78, 2.18, 2.74, thatch_mat),
        (1.94, 1.24, 2.66, 3.22, thatch_dark),
        (1.38, 0.65, 3.12, 3.66, thatch_mat),
        (0.76, 0.14, 3.58, 4.08, thatch_mat),
    ]):
        bm = bmesh.new()
        n_rad = 64
        n_v = 5
        rings = []
        for iv in range(n_v):
            f = iv / (n_v - 1)
            r_cur = r_bot + (r_top - r_bot) * (f ** 0.88)
            z_cur = z_bot + (z_top - z_bot) * f
            row = []
            for ir in range(n_rad):
                a = (2 * math.pi * ir) / n_rad
                # Radial straw bundle ribbing & slight ragged eave hem at f==0
                rib = 0.045 * math.sin(ir * 2.0 + tier_idx) * (1.0 - 0.5 * f)
                edge_fray = (-0.065 * abs(math.sin(ir * 3.5 + tier_idx))) if iv == 0 else 0.0
                rr = r_cur + rib
                row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z_cur + edge_fray)))
            rings.append(row)
        for iv in range(n_v - 1):
            for ir in range(n_rad):
                nir = (ir + 1) % n_rad
                bm.faces.new((rings[iv][ir], rings[iv][nir], rings[iv + 1][nir], rings[iv + 1][ir]))
        tm = bpy.data.meshes.new(f"Hut_ThatchTier_{tier_idx+1}")
        bm.to_mesh(tm)
        bm.free()
        tobj = bpy.data.objects.new(f"Hut_ThatchTier_{tier_idx+1}", tm)
        add_child(tobj, f"Hut_ThatchTier_{tier_idx+1}", mat)
        set_smooth_shade(tobj)

    # Top bound kusa finial sheaf & hemp rope collar
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.22, radius2=0.06, depth=0.45, location=(0, 0, 4.18))
    add_child(bpy.context.active_object, "Hut_KusaApexSheaf", thatch_mat)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.032, location=(0, 0, 3.98))
    add_child(bpy.context.active_object, "Hut_ApexCord", rope_mat)


def build_fire_altar_and_smoke(col, cache: CC0AssetCache, ph_props_dir: pathlib.Path):
    """Build stepped earthen Homa Kunda, CC0 fire pit hearth, sculpted Agni tongues & smooth BLENDED rising smoke."""
    altar_mud = make_painterly_mat("Homa_EarthenMud", (0.38, 0.21, 0.13), roughness=0.90, spec=0.12, noise_scale=22.0, noise_amp=0.14, bump_strength=0.18)
    altar_ash = make_painterly_mat("Homa_SandAshBed", (0.48, 0.37, 0.24), roughness=0.94, spec=0.08, noise_scale=30.0, noise_amp=0.10, bump_strength=0.12)

    for sname, sx, sy, sz, zp, mat in [
        ("Homa_AltarStep1", 1.54, 1.54, 0.10, 0.05, altar_mud),
        ("Homa_AltarStep2", 1.20, 1.20, 0.10, 0.135, altar_ash),
    ]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.35, zp))
        st = link_to_col(bpy.context.active_object, col)
        st.name = sname
        st.scale = (sx, sy, sz)
        st.data.materials.append(mat)

    cache.place(
        ph_props_dir / "stone_fire_pit" / "stone_fire_pit_2k.blend",
        "stone_fire_pit", col, loc=(0.0, 0.35, 0.18), rot=(0, 0, 18), scale=(0.52, 0.52, 0.52), name_prefix="Homa_FirePit_CC0", ground_align=True
    )

    ember_mat = make_painterly_mat("Homa_EmberGlow", (0.42, 0.09, 0.01), roughness=0.6, emission=(1.0, 0.38, 0.04), emission_strength=4.0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=18, radius=0.25, depth=0.05, location=(0.0, 0.35, 0.23))
    eb = link_to_col(bpy.context.active_object, col)
    eb.name = "Homa_EmberBed"
    eb.data.materials.append(ember_mat)

    # Sculpted curved flame ribbons (soft yellow-gold base fading to saffron-orange tip — no blunt white cones!)
    flame_mat = bpy.data.materials.new("Agni_FlameGradient")
    flame_mat.surface_render_method = "BLENDED"
    fnt = flame_mat.node_tree
    fbsdf = next(n for n in fnt.nodes if n.type == "BSDF_PRINCIPLED")
    fbsdf.inputs["Roughness"].default_value = 0.2
    tc = fnt.nodes.new("ShaderNodeTexCoord")
    sep = fnt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = fnt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (1.0, 0.90, 0.50, 1.0)
    mid = ramp.color_ramp.elements.new(0.45)
    mid.color = (1.0, 0.45, 0.05, 1.0)
    ramp.color_ramp.elements[2].position = 0.95
    ramp.color_ramp.elements[2].color = (0.75, 0.12, 0.01, 1.0)
    aramp = fnt.nodes.new("ShaderNodeValToRGB")
    aramp.color_ramp.elements[0].position = 0.0
    aramp.color_ramp.elements[0].color = (0.95, 0.95, 0.95, 1.0)
    aramp.color_ramp.elements[1].position = 0.98
    aramp.color_ramp.elements[1].color = (0.05, 0.05, 0.05, 1.0)
    fbsdf.inputs["Emission Strength"].default_value = 11.0
    fnt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    fnt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    fnt.links.new(sep.outputs["Z"], aramp.inputs["Fac"])
    fnt.links.new(ramp.outputs["Color"], fbsdf.inputs["Base Color"])
    fnt.links.new(ramp.outputs["Color"], fbsdf.inputs["Emission Color"])
    fnt.links.new(aramp.outputs["Color"], fbsdf.inputs["Alpha"])

    for k in range(7):
        ang = k * (2 * math.pi / 7.0)
        rad = 0.085 if k > 0 else 0.0
        h = 0.40 if k == 0 else (0.24 + 0.06 * (k % 2))
        pts = [
            (rad * math.cos(ang), 0.35 + rad * math.sin(ang), 0.23, 0.085 if k == 0 else 0.048),
            (rad * math.cos(ang) * 0.7 + 0.02 * math.sin(k), 0.35 + rad * math.sin(ang) * 0.7, 0.23 + h * 0.45, 0.055 if k == 0 else 0.032),
            (rad * math.cos(ang) * 0.3 - 0.03 * math.cos(k), 0.35 + rad * math.sin(ang) * 0.3, 0.23 + h, 0.004),
        ]
        create_curve_branch(f"Homa_AgniTongue_{k}", pts, flame_mat, col, bevel_res=3)

    # Smooth translucent curling smoke wisps (BLENDED = zero dither noise!) drifting diagonally left-back
    smoke_mat = bpy.data.materials.new("Homa_SmoothSmoke")
    smoke_mat.surface_render_method = "BLENDED"
    snt = smoke_mat.node_tree
    sbsdf = next(n for n in snt.nodes if n.type == "BSDF_PRINCIPLED")
    sbsdf.inputs["Base Color"].default_value = (0.78, 0.75, 0.72, 1.0)
    sbsdf.inputs["Roughness"].default_value = 1.0
    sbsdf.inputs["Emission Color"].default_value = (0.75, 0.68, 0.60, 1.0)
    sbsdf.inputs["Emission Strength"].default_value = 0.22
    stc = snt.nodes.new("ShaderNodeTexCoord")
    ssep = snt.nodes.new("ShaderNodeSeparateXYZ")
    slw = snt.nodes.new("ShaderNodeLayerWeight")
    slw.inputs["Blend"].default_value = 0.55
    sinv = snt.nodes.new("ShaderNodeMath")
    sinv.operation = "SUBTRACT"
    sinv.inputs[0].default_value = 1.0
    # Fade smoothly near top and bottom of spline
    zramp = snt.nodes.new("ShaderNodeValToRGB")
    zramp.color_ramp.elements[0].position = 0.02
    zramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    midz = zramp.color_ramp.elements.new(0.28)
    midz.color = (1.0, 1.0, 1.0, 1.0)
    zramp.color_ramp.elements[2].position = 0.96
    zramp.color_ramp.elements[2].color = (0.0, 0.0, 0.0, 1.0)
    sm1 = snt.nodes.new("ShaderNodeMath")
    sm1.operation = "MULTIPLY"
    sm2 = snt.nodes.new("ShaderNodeMath")
    sm2.operation = "MULTIPLY"
    sm2.inputs[1].default_value = 0.22
    snt.links.new(stc.outputs["Generated"], ssep.inputs["Vector"])
    snt.links.new(ssep.outputs["Z"], zramp.inputs["Fac"])
    snt.links.new(slw.outputs["Facing"], sinv.inputs[1])
    snt.links.new(sinv.outputs["Value"], sm1.inputs[0])
    snt.links.new(zramp.outputs["Color"], sm1.inputs[1])
    snt.links.new(sm1.outputs["Value"], sm2.inputs[0])
    snt.links.new(sm2.outputs["Value"], sbsdf.inputs["Alpha"])

    smoke_ribbons = [
        [(0.0, 0.35, 0.45, 0.045), (-0.16, 0.38, 1.05, 0.11), (-0.06, 0.44, 1.75, 0.16), (-0.36, 0.52, 2.55, 0.22), (-0.58, 0.62, 3.60, 0.28), (-0.82, 0.72, 4.65, 0.32)],
        [(-0.04, 0.37, 0.50, 0.038), (0.08, 0.35, 0.98, 0.09), (-0.18, 0.42, 1.62, 0.14), (-0.04, 0.50, 2.38, 0.19), (-0.38, 0.58, 3.35, 0.25), (-0.64, 0.68, 4.35, 0.30)],
        [(0.03, 0.33, 0.48, 0.038), (-0.22, 0.32, 1.15, 0.10), (-0.34, 0.40, 1.95, 0.15), (-0.18, 0.48, 2.75, 0.20), (-0.48, 0.56, 3.70, 0.25), (-0.78, 0.66, 4.70, 0.30)],
    ]
    for idx, pts in enumerate(smoke_ribbons):
        create_curve_branch(f"Homa_SmokeRibbon_{idx+1}", pts, smoke_mat, col, bevel_res=3)


def build_open_diya(col, loc=(0.48, -0.68, 0.0)):
    """Build a glass-free brass & terracotta Vedic oil diya with tapered golden flame for S11/S12."""
    parent = bpy.data.objects.new("Sacred_Open_Diya_Root", None)
    parent.location = loc
    col.objects.link(parent)

    stand_mat = make_painterly_mat("Diya_TerracottaStand", (0.45, 0.20, 0.12), roughness=0.88, spec=0.16)
    brass_mat = make_painterly_mat("Diya_HammeredBrass", (0.78, 0.54, 0.19), roughness=0.36, spec=0.65, metallic=0.85, noise_scale=48.0, noise_amp=0.10, bump_strength=0.06)
    ghee_mat = make_painterly_mat("Diya_WarmGhee", (0.46, 0.25, 0.04), roughness=0.15, spec=0.65)
    wick_mat = make_painterly_mat("Diya_CottonWick", (0.65, 0.55, 0.40), roughness=0.92)

    flame_out = bpy.data.materials.new("Diya_FlameTeardrop")
    flame_out.surface_render_method = "BLENDED"
    fnt = flame_out.node_tree
    fbsdf = next(n for n in fnt.nodes if n.type == "BSDF_PRINCIPLED")
    ftc = fnt.nodes.new("ShaderNodeTexCoord")
    fsep = fnt.nodes.new("ShaderNodeSeparateXYZ")
    framp = fnt.nodes.new("ShaderNodeValToRGB")
    framp.color_ramp.elements[0].position = 0.0
    framp.color_ramp.elements[0].color = (1.0, 0.72, 0.18, 1.0)
    framp.color_ramp.elements[1].position = 0.85
    framp.color_ramp.elements[1].color = (0.95, 0.24, 0.02, 1.0)
    fbsdf.inputs["Emission Strength"].default_value = 4.2
    fbsdf.inputs["Alpha"].default_value = 0.85
    fnt.links.new(ftc.outputs["Generated"], fsep.inputs["Vector"])
    fnt.links.new(fsep.outputs["Z"], framp.inputs["Fac"])
    fnt.links.new(framp.outputs["Color"], fbsdf.inputs["Base Color"])
    fnt.links.new(framp.outputs["Color"], fbsdf.inputs["Emission Color"])

    flame_core = make_painterly_mat("Diya_Flame_Core", (1.0, 0.88, 0.45), roughness=0.2, emission=(1.0, 0.84, 0.38), emission_strength=7.5, noise_amp=0.0, bump_strength=0.0)

    def add_p(obj, name, mat):
        link_to_col(obj, col)
        obj.parent = parent
        obj.name = name
        obj.data.materials.append(mat)
        set_smooth_shade(obj)
        return obj

    bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=0.135, depth=0.034, location=(0, 0, 0.017))
    add_p(bpy.context.active_object, "Diya_ClayStand", stand_mat)

    bpy.ops.mesh.primitive_cone_add(vertices=28, radius1=0.080, radius2=0.030, depth=0.044, location=(0, 0, 0.055))
    add_p(bpy.context.active_object, "Diya_BrassStem", brass_mat)

    bm = bmesh.new()
    segs = 32
    prof = [(0.022, 0.070), (0.070, 0.077), (0.098, 0.100), (0.108, 0.120), (0.096, 0.122), (0.062, 0.098), (0.015, 0.084)]
    rings = []
    for i in range(segs):
        a = (2 * math.pi * i) / segs
        spout = max(0.0, math.cos(a + math.radians(65))) ** 6
        ring = []
        for r, z in prof:
            r_mod = r * (1.0 + 0.42 * spout)
            z_mod = z + (0.010 * spout if z > 0.11 else 0.0)
            ring.append(bm.verts.new((r_mod * math.cos(a), r_mod * math.sin(a), z_mod)))
        rings.append(ring)
    for i in range(segs):
        ni = (i + 1) % segs
        for j in range(len(prof) - 1):
            bm.faces.new((rings[i][j], rings[ni][j], rings[ni][j + 1], rings[i][j + 1]))
    dm = bpy.data.meshes.new("Diya_BrassBowl")
    bm.to_mesh(dm)
    bm.free()
    add_p(bpy.data.objects.new("Diya_BrassBowl", dm), "Diya_BrassBowl", brass_mat)

    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.072, depth=0.008, location=(0, 0, 0.102))
    add_p(bpy.context.active_object, "Diya_GheePool", ghee_mat)

    wick_a = math.radians(-65)
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.0045, depth=0.068, location=(0.088 * math.cos(wick_a), 0.088 * math.sin(wick_a), 0.118))
    wk = add_p(bpy.context.active_object, "Diya_CottonWick", wick_mat)
    wk.rotation_euler = (math.radians(78), 0.0, wick_a + math.radians(90))

    # Graceful pointed teardrop flame built via spline radius curve (never a giant white egg!)
    fx, fy, fz = 0.114 * math.cos(wick_a), 0.114 * math.sin(wick_a), 0.126
    fo = create_curve_branch("Diya_Flame_Outer", [
        (fx, fy, fz, 0.011), (fx, fy, fz + 0.014, 0.015), (fx, fy, fz + 0.032, 0.009), (fx, fy, fz + 0.050, 0.001)
    ], flame_out, col, bevel_res=3)
    fo.parent = parent
    fi = create_curve_branch("Diya_Flame_Core", [
        (fx, fy, fz + 0.002, 0.006), (fx, fy, fz + 0.013, 0.0075), (fx, fy, fz + 0.026, 0.002)
    ], flame_core, col, bevel_res=2)
    fi.parent = parent


def make_palm_leaf_strip(name, width, length, thickness, camber, mat, col, loc, rot_deg):
    """Create a realistic cambered incised palm-leaf manuscript strip (Talapatra)."""
    bm = bmesh.new()
    nx, ny = 8, 2
    verts = []
    for ix in range(nx + 1):
        u = (ix / nx) - 0.5
        row = []
        for iy in range(ny + 1):
            v = (iy / ny) - 0.5
            z = camber * (1.0 - 4.0 * u * u) + (0.0015 if iy == 1 else 0.0)
            row.append(bm.verts.new((u * length, v * width, z)))
        verts.append(row)
    for ix in range(nx):
        for iy in range(ny):
            bm.faces.new((verts[ix][iy], verts[ix + 1][iy], verts[ix + 1][iy + 1], verts[ix][iy + 1]))
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thickness)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = Euler((math.radians(rot_deg[0]), math.radians(rot_deg[1]), math.radians(rot_deg[2])), "XYZ")
    link_to_col(obj, col)
    obj.data.materials.append(mat)
    set_smooth_shade(obj)
    return obj


def make_birch_bark_sheet(name, width, length, curl_z, mat, col, loc, rot_deg):
    """Create a curled birch-bark manuscript sheet (Bhurja-patra) — no paper books."""
    bm = bmesh.new()
    nx, ny = 8, 6
    verts = []
    for ix in range(nx + 1):
        u = (ix / nx) - 0.5
        row = []
        for iy in range(ny + 1):
            v = (iy / ny) - 0.5
            edge_curl = curl_z * ((u * u * 3.0) + (v * v * 1.4))
            ripple = 0.002 * math.sin(u * 9.0 + v * 5.0)
            row.append(bm.verts.new((u * length, v * width, edge_curl + ripple)))
        verts.append(row)
    for ix in range(nx):
        for iy in range(ny):
            bm.faces.new((verts[ix][iy], verts[ix + 1][iy], verts[ix + 1][iy + 1], verts[ix][iy + 1]))
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.0020)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = Euler((math.radians(rot_deg[0]), math.radians(rot_deg[1]), math.radians(rot_deg[2])), "XYZ")
    link_to_col(obj, col)
    obj.data.materials.append(mat)
    set_smooth_shade(obj)
    return obj


def build_scribe_mats_and_vessels(col, cache: CC0AssetCache, ph_props_dir: pathlib.Path):
    """Build Vyasa & Ganesha mats, inscribed palm-leaf strips, birch-bark sheets, bronze stylus & clay/brass pots."""
    mat_kusa = make_painterly_mat("Mat_KusaWeave", (0.46, 0.36, 0.18), roughness=0.92, spec=0.12, noise_scale=75.0, noise_amp=0.22, bump_strength=0.25)
    mat_border = make_painterly_mat("Mat_OchreTrim", (0.44, 0.16, 0.08), roughness=0.88, spec=0.14)
    cord_mat = make_painterly_mat("Talapatra_RedCord", (0.62, 0.12, 0.08), roughness=0.80)
    wood_mat = make_painterly_mat("Scribe_DarkWood", (0.18, 0.10, 0.06), roughness=0.72, spec=0.24)
    stylus_mat = make_painterly_mat("Ganesha_BronzeStylus", (0.80, 0.56, 0.20), roughness=0.34, spec=0.70, metallic=0.88)
    clay_mat = make_painterly_mat("Vedic_RedTerracottaClay", (0.46, 0.21, 0.12), roughness=0.88, spec=0.16, noise_scale=30.0, noise_amp=0.12, bump_strength=0.14)

    # Procedural incised-script Palm Leaf material (faint horizontal incised grooves/characters along X)
    palm_mat = bpy.data.materials.new("Talapatra_InscribedPalmLeaf")
    pnt = palm_mat.node_tree
    pbsdf = next(n for n in pnt.nodes if n.type == "BSDF_PRINCIPLED")
    pbsdf.inputs["Roughness"].default_value = 0.78
    ptc = pnt.nodes.new("ShaderNodeTexCoord")
    wave = pnt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Y"
    wave.inputs["Scale"].default_value = 38.0
    wave.inputs["Distortion"].default_value = 4.2
    wave.inputs["Detail"].default_value = 5.0
    pramp = pnt.nodes.new("ShaderNodeValToRGB")
    pramp.color_ramp.elements[0].position = 0.25
    pramp.color_ramp.elements[0].color = (0.28, 0.21, 0.11, 1.0)  # incised carbon-ash line stroke
    pramp.color_ramp.elements[1].position = 0.52
    pramp.color_ramp.elements[1].color = (0.58, 0.49, 0.29, 1.0)  # seasoned palm-leaf golden tan
    pbump = pnt.nodes.new("ShaderNodeBump")
    pbump.inputs["Strength"].default_value = 0.14
    pnt.links.new(ptc.outputs["Object"], wave.inputs["Vector"])
    pnt.links.new(wave.outputs["Fac"], pramp.inputs["Fac"])
    pnt.links.new(pramp.outputs["Color"], pbsdf.inputs["Base Color"])
    pnt.links.new(wave.outputs["Fac"], pbump.inputs["Height"])
    pnt.links.new(pbump.outputs["Normal"], pbsdf.inputs["Normal"])

    # Horizontal lenticel Birch Bark material (creamy pale Bhurja-patra)
    birch_mat = bpy.data.materials.new("BhurjaPatra_LenticelBark")
    bnt = birch_mat.node_tree
    bbsdf = next(n for n in bnt.nodes if n.type == "BSDF_PRINCIPLED")
    bbsdf.inputs["Roughness"].default_value = 0.85
    btc = bnt.nodes.new("ShaderNodeTexCoord")
    bmap = bnt.nodes.new("ShaderNodeMapping")
    bmap.inputs["Scale"].default_value = (1.5, 16.0, 1.0)
    bnoise = bnt.nodes.new("ShaderNodeTexNoise")
    bnoise.inputs["Scale"].default_value = 18.0
    bramp = bnt.nodes.new("ShaderNodeValToRGB")
    bramp.color_ramp.elements[0].position = 0.36
    bramp.color_ramp.elements[0].color = (0.52, 0.38, 0.24, 1.0)
    bramp.color_ramp.elements[1].position = 0.56
    bramp.color_ramp.elements[1].color = (0.76, 0.65, 0.47, 1.0)
    bnt.links.new(btc.outputs["Object"], bmap.inputs["Vector"])
    bnt.links.new(bmap.outputs["Vector"], bnoise.inputs["Vector"])
    bnt.links.new(bnoise.outputs["Fac"], bramp.inputs["Fac"])
    bnt.links.new(bramp.outputs["Color"], bbsdf.inputs["Base Color"])

    for side, mx in [("Vyasa", -1.45), ("Ganesha", +1.45)]:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mx, 0.08, 0.015))
        pm = link_to_col(bpy.context.active_object, col)
        pm.name = f"Mat_Kusa_{side}"
        pm.scale = (0.98, 0.78, 0.030)
        pm.data.materials.append(mat_kusa)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(mx, 0.08, 0.008))
        br = link_to_col(bpy.context.active_object, col)
        br.name = f"Mat_Border_{side}"
        br.scale = (1.03, 0.83, 0.016)
        br.data.materials.append(mat_border)

    # Vyasa left-side tied palm-leaf bundles + birch-bark sheet stack
    for k, (px, py, pz, rz) in enumerate([(-0.92, -0.18, 0.036, 22), (-0.90, -0.17, 0.056, 19), (-1.92, -0.22, 0.036, -15)]):
        make_palm_leaf_strip(f"PalmLeaf_Vyasa_{k+1}", 0.075, 0.36, 0.012, 0.006, palm_mat, col, (px, py, pz), (0, 0, rz))
        bpy.ops.mesh.primitive_torus_add(major_radius=0.040, minor_radius=0.005, location=(px, py, pz))
        cr = link_to_col(bpy.context.active_object, col)
        cr.name = f"PalmCord_Vyasa_{k+1}"
        cr.rotation_euler = (math.radians(90), 0, math.radians(rz))
        cr.data.materials.append(cord_mat)

    make_birch_bark_sheet("BirchBark_Vyasa_01", 0.16, 0.22, 0.014, birch_mat, col, (-0.82, 0.26, 0.018), (0, 0, 12))
    make_birch_bark_sheet("BirchBark_Vyasa_02", 0.15, 0.21, 0.018, birch_mat, col, (-0.80, 0.27, 0.026), (0, 0, 19))

    # Ganesha RIGHT scribe station: wooden low writing plank at (+0.96, -0.24, 0.0)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.96, -0.24, 0.032))
    board = link_to_col(bpy.context.active_object, col)
    board.name = "Ganesha_ScribeBoard"
    board.scale = (0.58, 0.42, 0.018)
    board.rotation_euler = (0.0, 0.0, math.radians(-18))
    board.data.materials.append(wood_mat)
    for bx_s in (-0.22, +0.22):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.96 + bx_s * 0.9, -0.24 - bx_s * 0.3, 0.012))
        ft = link_to_col(bpy.context.active_object, col)
        ft.name = f"Ganesha_ScribeFoot_{bx_s:+.2f}"
        ft.scale = (0.042, 0.38, 0.024)
        ft.rotation_euler = (0.0, 0.0, math.radians(-18))
        ft.data.materials.append(wood_mat)

    # Inscribed palm leaves (front active leaf + back tied stack) + curled birch-bark sheets side-by-side (zero overlap!)
    make_palm_leaf_strip("PalmLeaf_Hero_Active", 0.095, 0.42, 0.008, 0.005, palm_mat, col, (0.98, -0.20, 0.052), (0, 0, -16))
    make_palm_leaf_strip("PalmLeaf_Hero_Finished1", 0.082, 0.38, 0.013, 0.004, palm_mat, col, (1.07, -0.06, 0.052), (0, 0, -24))
    make_palm_leaf_strip("PalmLeaf_Hero_Finished2", 0.082, 0.38, 0.013, 0.004, palm_mat, col, (1.08, -0.05, 0.068), (0, 0, -20))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.044, minor_radius=0.005, location=(1.075, -0.055, 0.062))
    hcord = link_to_col(bpy.context.active_object, col)
    hcord.name = "PalmCord_HeroStack"
    hcord.rotation_euler = (math.radians(90), 0, math.radians(-22))
    hcord.data.materials.append(cord_mat)

    # Curled Bhurja-patra birch-bark sheets placed cleanly beside the active palm leaf
    make_birch_bark_sheet("BirchBark_Hero_01", 0.16, 0.22, 0.012, birch_mat, col, (0.84, -0.34, 0.045), (0, 0, -8))
    make_birch_bark_sheet("BirchBark_Hero_02", 0.15, 0.21, 0.015, birch_mat, col, (0.85, -0.33, 0.053), (0, 0, -3))
    make_birch_bark_sheet("BirchBark_Ganesha_Side", 0.18, 0.24, 0.016, birch_mat, col, (1.28, -0.38, 0.016), (0, 0, 26))

    # Cast Bronze Stylus resting flush ON TOP of PalmLeaf_Hero_Active without piercing any birch bark!
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.007, radius2=0.0012, depth=0.22, location=(1.00, -0.21, 0.070))
    st = link_to_col(bpy.context.active_object, col)
    st.name = "Vedic_Bronze_Stylus"
    st.rotation_euler = (math.radians(90), 0.0, math.radians(-52))
    set_smooth_shade(st)
    st.data.materials.append(stylus_mat)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.010, location=(0.914, -0.278, 0.071))
    sk = link_to_col(bpy.context.active_object, col)
    sk.name = "Vedic_Bronze_StylusKnob"
    set_smooth_shade(sk)
    sk.data.materials.append(stylus_mat)

    # Poly Haven CC0 vessels (instanced cleanly via CC0AssetCache)
    cache.place(ph_props_dir / "wooden_bowl_01" / "wooden_bowl_01_2k.blend", "wooden_bowl_01", col, loc=(-1.02, 0.42, 0.0), rot=(0, 0, 15), scale=(0.85, 0.85, 0.85), name_prefix="Wooden_Bowl_Vyasa_CC0", ground_align=True)
    cache.place(ph_props_dir / "brass_pot_01" / "brass_pot_01_2k.blend", "brass_pot_01", col, loc=(-1.98, 0.55, 0.0), rot=(0, 0, -25), scale=(0.88, 0.88, 0.88), name_prefix="Brass_Kamandalu_Vyasa_CC0", ground_align=True)
    cache.place(ph_props_dir / "brass_pot_02" / "brass_pot_02_2k.blend", "brass_pot_02", col, loc=(1.35, -0.48, 0.0), rot=(0, 0, 35), scale=(0.75, 0.75, 0.75), name_prefix="Brass_InkWater_Ganesha_CC0", ground_align=True)

    for pidx, (px, py, rotz, sc) in enumerate([
        (-2.95, -1.25, 10, 1.35), (-2.68, -1.48, -50, 1.05), (2.05, -0.52, 70, 1.15), (-3.25, -2.55, 130, 1.25), (-2.85, -0.75, -35, 1.12)
    ]):
        cache.place(ph_props_dir / "planter_pot_clay" / "planter_pot_clay_2k.blend", "planter_pot_clay", col, loc=(px, py, terrain_height_at(px, py)), rot=(0, 0, rotz), scale=(sc, sc, sc * 1.18), name_prefix=f"Vedic_ClayPot_{pidx+1}_CC0", override_mat=clay_mat, ground_align=True)


def create_curve_branch(name: str, pts_with_radii, mat, col, bevel_res=3):
    """Build an organic tapered branch, flame ribbon, aerial root, or limb spline mesh."""
    curve_data = bpy.data.curves.new(name=name, type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 8
    curve_data.bevel_depth = 1.0
    curve_data.bevel_resolution = bevel_res
    curve_data.use_fill_caps = True

    spline = curve_data.splines.new("NURBS")
    spline.points.add(len(pts_with_radii) - 1)
    for i, (x, y, z, r) in enumerate(pts_with_radii):
        spline.points[i].co = (x, y, z, 1.0)
        spline.points[i].radius = r
    spline.use_endpoint_u = True
    spline.order_u = min(4, len(pts_with_radii))

    obj = bpy.data.objects.new(name, curve_data)
    link_to_col(obj, col)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    obj.select_set(False)
    obj.data.materials.append(mat)
    set_smooth_shade(obj)
    return obj


def make_leaf_cluster(col, name: str, loc, radii, seed: int, mat):
    """Create a finely sculpted non-faceted organic leaf crown sub-cluster."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=loc)
    lf = link_to_col(bpy.context.active_object, col)
    lf.name = name
    rng = random.Random(seed)
    for v in lf.data.vertices:
        # Organic multi-lobe botanical silhouette with slightly flat banyan crown bottom
        ang = math.atan2(v.co.y, v.co.x)
        lobe = 0.85 + 0.24 * math.sin(ang * 5.0 + seed) + 0.14 * math.cos(v.co.z * 6.0 + seed)
        j = 1.0 + rng.uniform(-0.14, 0.16)
        z_squash = 0.65 if v.co.z < 0 else 1.0
        v.co.x *= radii[0] * lobe * j
        v.co.y *= radii[1] * lobe * j
        v.co.z *= radii[2] * z_squash * j
    lf.data.update()
    lf.data.materials.append(mat)
    set_smooth_shade(lf)
    return lf


def build_sacred_banyan_and_forest(col, cache: CC0AssetCache, ph_env_dir: pathlib.Path, ph_tex_dir: pathlib.Path):
    """Build towering wide-canopy ancient banyan & gnarled aerial roots while keeping center sky open above altar."""
    bark_mat = append_material(ph_tex_dir / "bark_brown_01" / "bark_brown_01_2k.blend", "bark_brown_01")
    configure_box_mapping(bark_mat, 0.75)

    leaf_deep = make_painterly_mat("Banyan_DeepCanopy", (0.08, 0.16, 0.06), roughness=0.84, spec=0.12, noise_scale=14.0, noise_amp=0.25, bump_strength=0.35)
    leaf_mid = make_painterly_mat("Banyan_EmeraldCrown", (0.13, 0.24, 0.09), roughness=0.80, spec=0.14, noise_scale=18.0, noise_amp=0.25, bump_strength=0.35)
    leaf_lit = make_painterly_mat("Banyan_DawnSunCrown", (0.20, 0.30, 0.11), roughness=0.76, spec=0.16, noise_scale=20.0, noise_amp=0.22, bump_strength=0.30)

    # 1. Pull ancient banyan back-left to (-5.2, 5.2) so S02 close-up of Vyasa has crystal clear sightlines!
    bx, by = -5.2, 5.2
    bz0 = terrain_height_at(bx, by) - 0.15

    cache.place(ph_env_dir / "root_cluster_01" / "root_cluster_01_2k.blend", "root_cluster_01", col, loc=(bx + 0.1, by - 0.2, bz0 + 0.05), rot=(0, 0, -25), scale=(1.35, 1.35, 1.25), name_prefix="Banyan_Roots1_CC0", decimate_ratio=0.30, override_mat=bark_mat)
    cache.place(ph_env_dir / "root_cluster_02" / "root_cluster_02_2k.blend", "root_cluster_02", col, loc=(bx + 1.0, by - 0.8, bz0 + 0.04), rot=(0, 0, 75), scale=(1.15, 1.15, 1.25), name_prefix="Banyan_Roots2_CC0", decimate_ratio=0.28, override_mat=bark_mat)

    # Multi-stem fluted banyan trunk
    create_curve_branch("Banyan_MainTrunk", [(bx, by, bz0, 0.88), (bx + 0.1, by - 0.1, 1.4, 0.66), (bx + 0.15, by + 0.1, 3.0, 0.56), (bx + 0.25, by + 0.2, 4.5, 0.44)], bark_mat, col, bevel_res=4)
    for si, (dx, dy, r0, r1) in enumerate([(-0.48, -0.35, 0.38, 0.22), (0.45, -0.32, 0.35, 0.20), (-0.30, 0.48, 0.38, 0.24)]):
        create_curve_branch(f"Banyan_Stem_{si+1}", [(bx + dx * 1.3, by + dy * 1.3, bz0, r0), (bx + dx * 0.8, by + dy * 0.8, 1.7, r0 * 0.78), (bx + dx * 0.3, by + dy * 0.3, 3.6, r1)], bark_mat, col, bevel_res=3)

    # Wide horizontal boughs spanning canopy LEFT & HIGH OVERHEAD (strictly leaving X in [-2.3,+2.3], Z<4.6m CLEAR!)
    boughs = [
        [(bx, by, 3.8, 0.40), (-7.0, 4.0, 4.5, 0.30), (-9.2, 2.8, 4.9, 0.18), (-11.2, 1.8, 5.2, 0.08)],
        [(bx, by, 4.1, 0.36), (-7.4, 6.8, 4.8, 0.24), (-9.8, 8.2, 5.2, 0.15)],
        [(bx, by, 4.3, 0.34), (-3.6, 5.0, 5.1, 0.26), (-1.2, 5.4, 5.7, 0.16), (+1.2, 5.4, 5.8, 0.09)],
        [(bx, by, 3.7, 0.34), (-6.8, 2.2, 4.4, 0.23), (-8.4, 0.2, 4.7, 0.14), (-9.2, -1.4, 4.9, 0.06)],
    ]
    for bi, pts in enumerate(boughs):
        create_curve_branch(f"Banyan_PrimaryBough_{bi+1}", pts, bark_mat, col, bevel_res=3)

    # Curved gnarled hanging aerial prop-roots (strictly outside center clearing!)
    rng = random.Random(2027)
    aerials = [
        (-6.8, 3.8, 4.5, 0.055, True), (-8.2, 3.0, 4.8, 0.045, True), (-9.6, 2.3, 5.0, 0.038, True),
        (-3.9, 4.7, 4.7, 0.052, True), (-6.3, 2.3, 4.3, 0.040, True), (-7.6, 1.0, 4.5, 0.036, True),
        (-7.0, 6.2, 4.7, 0.048, True), (-8.6, 7.2, 5.0, 0.040, True),
        (-6.0, 3.1, 4.5, 0.025, False), (-7.3, 3.5, 4.7, 0.022, False), (-8.8, 2.5, 4.8, 0.024, False),
        (-4.5, 4.2, 4.8, 0.024, False), (-5.8, 4.8, 4.7, 0.022, False),
    ]
    for ai, (ax, ay, ztop, rad, grounded) in enumerate(aerials):
        zb = (terrain_height_at(ax, ay) - 0.05) if grounded else (terrain_height_at(ax, ay) + rng.uniform(1.2, 2.4))
        w1 = (ax + rng.uniform(-0.18, 0.18), ay + rng.uniform(-0.18, 0.18), ztop * 0.65 + zb * 0.35, rad * 0.85)
        w2 = (ax + rng.uniform(-0.15, 0.15), ay + rng.uniform(-0.15, 0.15), ztop * 0.30 + zb * 0.70, rad * (0.95 if grounded else 0.55))
        create_curve_branch(f"Banyan_AerialRoot_{ai+1:02d}", [(ax, ay, ztop, rad * 1.15), w1, w2, (ax, ay, zb, rad * (1.28 if grounded else 0.30))], bark_mat, col, bevel_res=2)

    # Right flanking riverbank banyan framing wide shots (also keeps center clear!)
    rx, ry = 6.2, 5.4
    rz0 = terrain_height_at(rx, ry) - 0.12
    create_curve_branch("RightBanyan_Trunk", [(rx, ry, rz0, 0.62), (rx - 0.2, ry - 0.1, 2.3, 0.44), (rx - 0.5, ry + 0.1, 4.4, 0.28)], bark_mat, col, bevel_res=3)
    create_curve_branch("RightBanyan_LimbL", [(rx - 0.4, ry, 4.0, 0.25), (4.4, 5.1, 4.9, 0.18), (2.8, 5.2, 5.5, 0.09)], bark_mat, col, bevel_res=2)
    create_curve_branch("RightBanyan_LimbR", [(rx - 0.1, ry + 0.1, 4.1, 0.24), (8.2, 6.0, 4.8, 0.16), (9.8, 6.5, 5.1, 0.08)], bark_mat, col, bevel_res=2)
    for ri, (arx, ary, zt) in enumerate([(4.6, 5.0, 4.8), (7.2, 5.6, 4.7), (5.4, 5.9, 4.6)]):
        create_curve_branch(f"RightBanyan_AerialRoot_{ri+1}", [(arx, ary, zt, 0.036), (arx + 0.08, ary - 0.06, 2.1, 0.028), (arx, ary, terrain_height_at(arx, ary) - 0.05, 0.044)], bark_mat, col, bevel_res=2)

    # Dense cohesive umbrella banyan foliage made from 42 tightly overlapping sculpted leaf-crown clusters!
    # Crucially keeps Z < 4.5m across X in [-2.3, +2.3] unobstructed so Brahma's lotus seat frames cleanly against misty river dawn!
    crown_specs = [
        # Main left banyan umbrella crown
        (-5.2, 5.2, 5.4, (2.4, 2.2, 1.05)), (-7.0, 4.2, 5.3, (2.2, 2.1, 1.0)), (-8.8, 3.0, 5.4, (2.1, 1.9, 0.95)),
        (-10.5, 1.9, 5.5, (1.8, 1.7, 0.90)), (-4.0, 4.8, 5.7, (2.0, 1.9, 0.95)), (-6.8, 6.6, 5.5, (2.2, 2.0, 1.0)),
        (-8.6, 7.8, 5.6, (2.0, 1.9, 0.95)), (-6.6, 2.4, 5.0, (2.1, 1.9, 0.95)), (-8.1, 0.5, 5.1, (1.9, 1.8, 0.90)),
        (-9.0, -1.0, 5.2, (1.7, 1.6, 0.85)), (-5.6, 4.0, 6.2, (2.5, 2.3, 1.0)), (-7.5, 5.2, 6.1, (2.4, 2.2, 1.0)),
        # High arched bridging crown over river horizon (Z=5.9..6.4m so underside frames upper edge without dropping into center!)
        (-2.2, 5.4, 6.1, (1.9, 1.8, 0.85)), (-0.4, 5.7, 6.3, (2.0, 1.8, 0.85)), (+1.5, 5.5, 6.1, (1.9, 1.7, 0.85)),
        # Right flanking banyan crown
        (6.0, 5.4, 5.2, (2.4, 2.2, 1.05)), (4.2, 5.1, 5.4, (2.0, 1.8, 0.92)), (7.9, 6.0, 5.3, (2.1, 1.9, 0.95)),
        (5.6, 6.8, 5.5, (2.0, 1.9, 0.95)), (6.8, 4.3, 5.6, (2.1, 2.0, 0.95)), (9.4, 6.4, 5.4, (1.8, 1.7, 0.88)),
    ]
    mats = [leaf_deep, leaf_mid, leaf_lit]
    for ci, (cx, cy, cz, rads) in enumerate(crown_specs):
        make_leaf_cluster(col, f"Banyan_Crown_{ci+1:02d}", (cx, cy, cz), rads, 500 + ci, mats[ci % 3])
        # Secondary smaller outer sprig cluster for organic jagged leaf edge
        make_leaf_cluster(col, f"Banyan_Sprig_{ci+1:02d}", (cx + 0.7 * ((ci % 2) * 2 - 1), cy - 0.5, cz - 0.35), (rads[0] * 0.58, rads[1] * 0.58, rads[2] * 0.62), 900 + ci, mats[(ci + 1) % 3])

    # Distant forested far riverbank silhouette ridge (sunk cleanly into far bank so there is zero gap above water!)
    for fi, fx in enumerate(range(-38, 42, 5)):
        fy = 22.8 + (fi % 3) * 1.4
        fz = terrain_height_at(fx, fy) + 0.55
        make_leaf_cluster(col, f"FarShore_Forest_{fi+1:02d}", (fx, fy, fz), (4.2, 3.2, 3.2), 1200 + fi, leaf_deep)

    # Riverbank CC0 boulders, mossy rocks, ferns & kusa grass clumps (all cached/instanced cleanly!)
    cache.place(ph_env_dir / "boulder_01" / "boulder_01_2k.blend", "boulder_01_LOD3", col, loc=(4.8, 4.3, terrain_height_at(4.8, 4.3) - 0.14), rot=(0, 0, 38), scale=(0.95, 0.95, 0.78), name_prefix="River_Boulder_Right_CC0")
    cache.place(ph_env_dir / "boulder_01" / "boulder_01_2k.blend", "boulder_01_LOD3", col, loc=(-6.5, 5.8, terrain_height_at(-6.5, 5.8) - 0.16), rot=(0, 0, 145), scale=(1.15, 1.15, 0.92), name_prefix="River_Boulder_Left_CC0")
    cache.place(ph_env_dir / "rock_moss_set_01" / "rock_moss_set_01_2k.blend", "rock_moss_set_01", col, loc=(-2.7, 4.8, terrain_height_at(-2.7, 4.8) - 0.10), rot=(0, 0, 14), scale=(0.78, 0.78, 0.78), name_prefix="Mossy_BankRocks_CC0", decimate_ratio=0.45)

    for fi, (fx, fy, rotz, sc) in enumerate([
        (-2.9, -3.5, 15, 1.1), (2.7, -3.3, -40, 1.05), (-3.8, 1.4, 85, 1.0),
        (3.4, 2.2, 130, 1.1), (-1.4, 4.1, 25, 0.9), (1.7, 4.0, -70, 0.95),
        (5.5, 3.0, 50, 1.0), (-4.2, -0.4, -15, 1.0),
    ]):
        cache.place(ph_env_dir / "fern_02" / "fern_02_2k.blend", "fern_02", col, loc=(fx, fy, terrain_height_at(fx, fy) - 0.02), rot=(0, 0, rotz), scale=(sc, sc, sc), name_prefix=f"Hermitage_Fern_{fi+1}_CC0")

    for gi, (gx, gy, rotz, sc) in enumerate([
        (-2.8, 2.2, 10, 1.2), (2.6, 2.8, 65, 1.3), (3.8, 3.8, 120, 1.4),
        (2.4, 4.4, 30, 1.3), (-3.4, 3.2, -45, 1.35), (4.5, 5.1, 180, 1.2),
        (-2.5, -2.5, 45, 1.1), (2.9, -2.1, -20, 1.15), (-5.4, 0.4, 75, 1.4),
        (1.9, 3.6, 15, 1.1), (-0.8, 4.3, 95, 1.0), (5.2, 2.7, -80, 1.3),
        (3.1, 4.7, 40, 1.25), (3.9, 4.9, 100, 1.2),
    ]):
        cache.place(ph_env_dir / "grass_medium_02" / "grass_medium_02_2k.blend", "grass_medium_02_static", col, loc=(gx, gy, terrain_height_at(gx, gy) - 0.02), rot=(0, 0, rotz), scale=(sc, sc, sc), name_prefix=f"Kusa_Tuft_{gi+1}_CC0")


def make_spotted_deer(col, name: str, loc, yaw_deg: float, grazing=True, has_antlers=False):
    """Build an organic smooth-subdivided spotted chital deer silhouette for S01 riverbank."""
    parent = bpy.data.objects.new(f"{name}_Root", None)
    parent.location = (loc[0], loc[1], terrain_height_at(loc[0], loc[1]))
    parent.rotation_euler = (0.0, 0.0, math.radians(yaw_deg))
    col.objects.link(parent)

    coat_mat = bpy.data.materials.new(f"{name}_ChitalCoat")
    cnt = coat_mat.node_tree
    bsdf = next(n for n in cnt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.80
    bsdf.inputs["Specular IOR Level"].default_value = 0.16
    vor = cnt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 26.0
    ramp = cnt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.10
    ramp.color_ramp.elements[0].color = (0.88, 0.78, 0.62, 1.0)
    ramp.color_ramp.elements[1].position = 0.20
    ramp.color_ramp.elements[1].color = (0.45, 0.22, 0.09, 1.0)
    cnt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    cnt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    horn_mat = make_painterly_mat("Deer_AntlerBone", (0.62, 0.54, 0.40), roughness=0.72)

    # Organic Subsurf Body + Neck + Head cage via BMesh skin-like metaball/capsule blend
    def metabody_part(pname, pts, mat=coat_mat):
        obj = create_curve_branch(pname, pts, mat, col, bevel_res=3)
        obj.parent = parent
        return obj

    # Seamless torso tapering nicely to chest & rump
    metabody_part(f"{name}_Torso", [
        (-0.36, 0.0, 0.64, 0.06), (-0.28, 0.0, 0.66, 0.155), (0.0, 0.0, 0.62, 0.185),
        (+0.26, 0.0, 0.65, 0.165), (+0.36, 0.0, 0.68, 0.08),
    ])
    for ln, lx, ly, kx in [("FL", 0.24, 0.08, 0.22), ("FR", 0.24, -0.08, 0.22), ("BL", -0.25, 0.09, -0.31), ("BR", -0.25, -0.09, -0.31)]:
        metabody_part(f"{name}_Leg_{ln}", [(lx, ly, 0.62, 0.065), (kx, ly, 0.34, 0.030), (lx + 0.01, ly, 0.0, 0.020)])

    if grazing:
        metabody_part(f"{name}_Neck", [(0.26, 0.0, 0.67, 0.125), (0.46, 0.0, 0.44, 0.082), (0.65, 0.0, 0.15, 0.058)])
        metabody_part(f"{name}_Head", [(0.62, 0.0, 0.16, 0.064), (0.71, 0.0, 0.08, 0.052), (0.79, 0.0, 0.01, 0.022)])
        ear_z, ear_x = 0.21, 0.62
    else:
        metabody_part(f"{name}_Neck", [(0.26, 0.0, 0.68, 0.128), (0.35, 0.0, 0.90, 0.082), (0.42, 0.0, 1.07, 0.062)])
        metabody_part(f"{name}_Head", [(0.39, 0.0, 1.08, 0.068), (0.49, 0.0, 1.08, 0.054), (0.59, 0.0, 1.05, 0.022)])
        ear_z, ear_x = 1.15, 0.39

    for side, sy in [("L", +0.055), ("R", -0.055)]:
        bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=0.024, radius2=0.004, depth=0.10, location=(ear_x, sy, ear_z))
        er = link_to_col(bpy.context.active_object, col)
        er.parent = parent
        er.name = f"{name}_Ear_{side}"
        er.rotation_euler = (math.radians(32 if sy > 0 else -32), math.radians(-26), 0)
        er.data.materials.append(coat_mat)
        set_smooth_shade(er)

    if has_antlers and not grazing:
        for side, sy in [("L", +0.032), ("R", -0.032)]:
            metabody_part(f"{name}_Antler_{side}", [(0.42, sy, 1.14, 0.014), (0.40, sy * 2.1, 1.32, 0.010), (0.46, sy * 2.5, 1.46, 0.004)], horn_mat)
            metabody_part(f"{name}_AntlerTine_{side}", [(0.41, sy * 1.6, 1.24, 0.009), (0.50, sy * 1.8, 1.33, 0.003)], horn_mat)

    metabody_part(f"{name}_Tail", [(-0.33, 0.0, 0.67, 0.028), (-0.42, 0.0, 0.60, 0.010)])


def setup_world_and_lighting(col, hdri_path: pathlib.Path):
    """Apply studio/bible.md gold key (#FFC27A) + blue dawn shadow (#3E5A86)."""
    scene = bpy.context.scene
    world = bpy.data.worlds.new("Hermitage_Dawn_World")
    scene.world = world
    nt = world.node_tree
    nt.nodes.clear()

    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.56
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    if not hdri_path.exists():
        raise FileNotFoundError(f"Missing CC0 dawn HDRI: {hdri_path}")
    env_tex = nt.nodes.new("ShaderNodeTexEnvironment")
    env_tex.image = bpy.data.images.load(str(hdri_path))
    hue_mix = nt.nodes.new("ShaderNodeMix")
    hue_mix.data_type = "RGBA"
    hue_mix.blend_type = "MULTIPLY"
    hue_mix.inputs["Factor"].default_value = 0.68
    hue_mix.inputs[7].default_value = (0.34, 0.52, 0.92, 1.0)  # Blue shadow atmosphere (#3E5A86)
    nt.links.new(env_tex.outputs["Color"], hue_mix.inputs[6])
    nt.links.new(hue_mix.outputs[2], bg.inputs["Color"])

    # Warm golden horizon sun key (#FFC27A)
    sun_data = bpy.data.lights.new("Sun_DawnGoldRim", type="SUN")
    sun_data.energy = 2.6
    sun_data.color = (1.0, 0.76, 0.48)
    sun_data.angle = math.radians(4.5)
    sun = bpy.data.objects.new("Sun_DawnGoldRim", sun_data)
    sun.rotation_euler = (math.radians(74), math.radians(-12), math.radians(150))
    col.objects.link(sun)

    # Warm altar fire key (#FFC27A) illuminating Vyasa left & Ganesha right
    fire_data = bpy.data.lights.new("Key_HomaFire", type="POINT")
    fire_data.energy = 240.0
    fire_data.color = (1.0, 0.72, 0.42)
    fire_data.shadow_soft_size = 0.25
    fire = bpy.data.objects.new("Key_HomaFire", fire_data)
    fire.location = (0.0, 0.35, 0.62)
    col.objects.link(fire)

    # Cool blue dawn overhead sky bounce (#3E5A86)
    sky_data = bpy.data.lights.new("Fill_BlueDawnSky", type="AREA")
    sky_data.energy = 165.0
    sky_data.color = (0.24, 0.35, 0.56)
    sky_data.size = 10.0
    sky = bpy.data.objects.new("Fill_BlueDawnSky", sky_data)
    sky.location = (0.0, -3.5, 5.2)
    sky.rotation_euler = (math.radians(30), 0.0, 0.0)
    col.objects.link(sky)

    # Close golden diya lamp warm bounce for S12 & Ganesha writing corner
    diya_data = bpy.data.lights.new("Key_DiyaFlame", type="POINT")
    diya_data.energy = 22.0
    diya_data.color = (1.0, 0.66, 0.30)
    diya_data.shadow_soft_size = 0.04
    diya = bpy.data.objects.new("Key_DiyaFlame", diya_data)
    diya.location = (0.53, -0.78, 0.22)
    col.objects.link(diya)


def setup_eevee_and_compositor(scene):
    """Set 1280x720 EEVEE render, AgX lookdev, and Blender 5.2 Fog Glow + gentle Kuwahara paint cohesion."""
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 24
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"

    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0.05

    ng = bpy.data.node_groups.new("S1E01_HermitageLookdev", "CompositorNodeTree")
    ng.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    scene.compositing_node_group = ng

    rl = ng.nodes.new("CompositorNodeRLayers")
    rl.location = (-360, 0)
    kuw = ng.nodes.new("CompositorNodeKuwahara")
    kuw.location = (-100, 0)
    kuw.inputs["Size"].default_value = 1.35

    glare = ng.nodes.new("CompositorNodeGlare")
    glare.location = (160, 0)
    glare.inputs["Type"].default_value = "Fog Glow"
    glare.inputs["Threshold"].default_value = 1.20
    glare.inputs["Size"].default_value = 6.0
    glare.inputs["Strength"].default_value = 0.42

    out = ng.nodes.new("NodeGroupOutput")
    out.location = (420, 0)
    ng.links.new(rl.outputs["Image"], kuw.inputs["Image"])
    ng.links.new(kuw.outputs["Image"], glare.inputs["Image"])
    ng.links.new(glare.outputs["Image"], out.inputs["Image"])


def add_shot_camera(col, shot_id: str, panel: str, loc, target, lens_mm: float):
    """Create a named TrackTo camera aligned to one shot in sc01/shots.json."""
    cam_name = f"CAM_{shot_id}_{panel}"
    cam_data = bpy.data.cameras.new(cam_name)
    cam_data.lens = lens_mm
    cam_data.sensor_width = 36.0
    cam = bpy.data.objects.new(cam_name, cam_data)
    cam.location = loc
    col.objects.link(cam)

    tgt = bpy.data.objects.new(f"{cam_name}_Target", None)
    tgt.location = target
    col.objects.link(tgt)

    track = cam.constraints.new(type="TRACK_TO")
    track.target = tgt
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    return shot_id, panel, cam


def compact_and_pack_textures(max_px=512):
    """Deduplicate/downscale images to compressed PNG/JPG & purge unused displacement maps so blend stays compact (~25 MB)."""
    # Unlink unused heavy displacement images so EEVEE set carries only diffuse/normal/rough/alpha/HDRI
    for mat in bpy.data.materials:
        nt = getattr(mat, "node_tree", None)
        if not nt:
            continue
        for node in list(nt.nodes):
            if node.type == "TEX_IMAGE" and node.image and "disp" in node.image.name.lower():
                nt.nodes.remove(node)

    bpy.ops.outliner.orphans_purge(do_recursive=True)

    tmp_dir = pathlib.Path(tempfile.mkdtemp(prefix="hermitage_tex_"))
    try:
        for idx, img in enumerate(bpy.data.images):
            if img.source != "FILE" or img.name in ("Render Result", "Viewer Node"):
                continue
            w, h = img.size[0], img.size[1]
            if w == 0 or h == 0:
                continue
            is_hdri = img.filepath.lower().endswith(".exr") and ("aarfontein" in img.name.lower() or w == 2 * h)
            cap = 768 if is_hdri else max_px
            if w > cap or h > cap:
                if w >= h:
                    nw, nh = cap, max(64, int(round(h * (cap / float(w)))))
                else:
                    nh, nw = cap, max(64, int(round(w * (cap / float(h)))))
                img.scale(nw, nh)
            # Save scaled pixels cleanly as compressed format on disk & reload before packing
            if is_hdri:
                ext = "exr"
                fmt = "OPEN_EXR"
            elif "diff" in img.name.lower() and not ("alpha" in img.name.lower() or "leaf" in img.name.lower() or "fern" in img.name.lower() or "grass" in img.name.lower()):
                ext = "jpg"
                fmt = "JPEG"
            else:
                ext = "png"
                fmt = "PNG"

            fp = tmp_dir / f"tex_{idx:03d}.{ext}"
            img.file_format = fmt
            img.filepath_raw = str(fp)
            img.save()
            img.filepath = str(fp)
            img.reload()
            img.pack()

        bpy.context.scene.render.image_settings.file_format = "PNG"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets-dir", default=str(DEFAULT_ASSETS))
    ap.add_argument("--out-dir", default=str(HERMITAGE_DIR))
    ap.add_argument("--no-render", action="store_true")
    args = ap.parse_args(argv)

    assets = pathlib.Path(args.assets_dir)
    ph_props = assets / "Props" / "PolyHaven_CC0"
    ph_env = assets / "Environments" / "PolyHaven_CC0"
    ph_tex = assets / "Environments" / "PolyHaven_Textures"
    hdri = assets / "Environments" / "PolyHaven_HDRIs" / "aarfontein_dawn_2k.exr"

    out_dir = pathlib.Path(args.out_dir)
    checks_dir = out_dir / "checks"
    checks_dir.mkdir(parents=True, exist_ok=True)
    out_blend = out_dir / "hermitage_set.blend"

    scene = reset_scene()
    cache = CC0AssetCache()

    c_env = make_collection("01_Terrain_MaliniRiver")
    c_props = make_collection("02_VedicHut_Props")
    c_trees = make_collection("03_SacredBanyan_Forest")
    c_deer = make_collection("04_Hermitage_Deer")
    c_light = make_collection("05_BibleLighting_Cameras")

    build_terrain_and_river(c_env, ph_tex)
    build_kusa_hut(c_props)
    build_fire_altar_and_smoke(c_props, cache, ph_props)
    build_open_diya(c_props)
    build_scribe_mats_and_vessels(c_props, cache, ph_props)
    build_sacred_banyan_and_forest(c_trees, cache, ph_env, ph_tex)
    make_spotted_deer(c_deer, "Deer_01_Grazing", (3.0, 4.7, 0.0), yaw_deg=-130.0, grazing=True, has_antlers=False)
    make_spotted_deer(c_deer, "Deer_02_Alert", (4.0, 5.4, 0.0), yaw_deg=-155.0, grazing=False, has_antlers=True)

    clamp_loaded_materials()
    setup_world_and_lighting(c_light, hdri)
    setup_eevee_and_compositor(scene)

    # All 12 shot cameras calibrated strictly to sc01/shots.json
    shot_specs = [
        ("S01", "hermitage_dawn",  (-1.5, -7.8, 2.35), (0.6, 2.5, 0.85),   24.0),
        ("S02", "vyasa_cu",        (-0.58, -1.95, 0.66),(-1.42, 0.08, 0.36), 46.0),
        ("S03", "brahma_appears",  (0.0, -5.2, 1.35),   (0.0, 1.8, 1.58),   35.0),
        ("S04", "cosmos_montage",  (-1.95, -2.35, 0.90),(0.30, 1.4, 1.25),  35.0),
        ("S05", "think_of_ganesa", (0.0, -4.3, 1.28),   (0.0, 1.5, 1.48),   40.0),
        ("S06", "ganesha_arrives", (0.0, -5.4, 1.36),   (0.0, 0.4, 0.86),   35.0),
        ("S07", "the_condition",   (-1.95, -1.85, 0.96),(1.10, -0.05, 0.42),45.0),
        ("S08", "writing_speed",   (0.66, -0.72, 0.42), (0.98, -0.22, 0.055),85.0),
        ("S09", "broken_tusk",     (1.42, -3.15, 0.86), (1.30, -0.08, 0.36),42.0),
        ("S10", "the_knots",       (0.0, -3.95, 1.12),  (0.0, 0.15, 0.50),  48.0),
        ("S11", "the_lamp",        (1.42, -1.28, 0.34), (-0.15, 0.65, 1.15),30.0),
        ("S12", "title_lamp",      (0.28, -1.32, 0.25), (0.50, -0.74, 0.145),90.0),
    ]
    cameras = [add_shot_camera(c_light, sid, pnl, loc, tgt, lens) for sid, pnl, loc, tgt, lens in shot_specs]
    scene.camera = cameras[0][2]

    compact_and_pack_textures(max_px=512)
    bpy.ops.wm.save_as_mainfile(filepath=str(out_blend), compress=True)
    print(f"SAVED_BLEND:{out_blend} SIZE_MB:{out_blend.stat().st_size / 1e6:.2f}")

    if not args.no_render:
        for sid, pnl, cam in cameras:
            scene.camera = cam
            out_png = checks_dir / f"{sid}_{pnl}.png"
            scene.render.filepath = str(out_png)
            bpy.ops.render.render(write_still=True)
            print(f"RENDERED:{out_png}")


if __name__ == "__main__":
    main()

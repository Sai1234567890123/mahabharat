#!/usr/bin/env python3
"""Build the unified Mahabharata Production SQLite DB, populate 04_shots.csv & 05_assets.csv,
write ASSET_AND_FAB_MATRIX.md, and export anonymized JSON/CSV bundles for external planning.

Zero credentials, zero screenshots, zero personal creator metadata included in sanitized exports.

Usage:
    python studio/refs/library/build_prod_db.py
    python studio/refs/library/build_prod_db.py --studio-dir "C:\\Users\\dharm\\OneDrive\\Desktop\\claude projects\\MAHABHARATA_STUDIO"
"""
import argparse
import csv
import json
import pathlib
import re
import shutil
import sqlite3
from collections import Counter, defaultdict

STUDIO = pathlib.Path(__file__).resolve().parent.parent.parent
LIB_DIR = pathlib.Path(__file__).resolve().parent
DEFAULT_LOCAL_STUDIO = pathlib.Path(
    r"C:\Users\dharm\OneDrive\Desktop\claude projects\MAHABHARATA_STUDIO"
)

SHOTS_HEADER = [
    "shot_id", "episode", "sequence", "scene", "duration_seconds", "shot_description",
    "character_ids", "environment_id", "concept_ids", "camera_plan", "animation_status",
    "lighting_status", "vfx_status", "render_status", "edit_status", "priority", "notes",
]

ASSETS_HEADER = [
    "asset_id", "asset_name", "asset_type", "blender_file", "unreal_asset_path", "version",
    "dependencies", "rig_status", "material_status", "optimization_status", "reuse_scope",
    "source_or_license", "status", "notes",
]

# Canonical catalog of studio & pipeline reusable assets.
# Paths reflect verified files in studio/ and mahabharat/work/.
CANONICAL_ASSETS = [
    # --- HERO CHARACTERS (EXISTING RIGS) ---
    {
        "asset_id": "AST-0001", "asset_name": "Arjuna Hero (Armored)", "asset_type": "CHARACTER",
        "blender_file": "studio/cast/arjuna/model/rig/arjuna_hero_v4.blend",
        "unreal_asset_path": "", "version": "v4", "dependencies": "studio/cast/arjuna/passport_web.md",
        "rig_status": "RIGGED_NEEDS_HAND_FACE_FIX", "material_status": "NEEDS_2K_PAINTERLY_REPAINT",
        "optimization_status": "LOD_PENDING", "reuse_scope": "SERIES",
        "source_or_license": "CUSTOM_BLENDER (Original + TRELLIS base)",
        "status": "IN_PROGRESS",
        "notes": "Char tag @arjuna. Web look locked (close_v4, full_v4). Fix finger skin stretch, barefoot option, red tilak, inverted-hull outline.",
        "char_tags": ["@arjuna"], "keywords": ["arjuna"],
    },
    {
        "asset_id": "AST-0002", "asset_name": "Arjuna Hero (Bare-Headed / Crownless)", "asset_type": "CHARACTER",
        "blender_file": "studio/cast/arjuna_bare/model/rig/arjuna_bare_hero_v1.blend",
        "unreal_asset_path": "", "version": "v1", "dependencies": "AST-0001",
        "rig_status": "RIGGED", "material_status": "NEEDS_2K_PAINTERLY_REPAINT",
        "optimization_status": "LOD_PENDING", "reuse_scope": "EP01_S6",
        "source_or_license": "CUSTOM_BLENDER",
        "status": "IN_PROGRESS",
        "notes": "Char tag @arjuna_bare. Used after snake arrow knocks crown off in EP01 A14-A22.",
        "char_tags": ["@arjuna_bare"], "keywords": ["arjuna_bare", "crownless"],
    },
    {
        "asset_id": "AST-0003", "asset_name": "Karna Hero (Sun Armor & Kavacha)", "asset_type": "CHARACTER",
        "blender_file": "studio/cast/karna/model/rig/karna_hero_v4.blend",
        "unreal_asset_path": "", "version": "v4", "dependencies": "studio/cast/karna/passport.md",
        "rig_status": "RIGGED_WITH_VISEMES", "material_status": "NEEDS_SUN_CUIRASS_EMISSIVE",
        "optimization_status": "LOD_PENDING", "reuse_scope": "SERIES",
        "source_or_license": "CUSTOM_BLENDER (Original + TRELLIS base)",
        "status": "IN_PROGRESS",
        "notes": "Char tag @karna. Gold & saffron; sun-face cuirass ignites first in Astra shots. Keep v1/v2 retired.",
        "char_tags": ["@karna"], "keywords": ["karna", "maharathi"],
    },
    {
        "asset_id": "AST-0004", "asset_name": "Krishna Hero (Charioteer / Sovereign)", "asset_type": "CHARACTER",
        "blender_file": "studio/cast/krishna/model/rig/krishna_hero_v3.blend",
        "unreal_asset_path": "", "version": "v3 (local v27 face)", "dependencies": "studio/cast/krishna/passport.md",
        "rig_status": "RIGGED_404_RIGIFY_TONGUE_TEETH", "material_status": "NEEDS_2K_PAINTERLY_REPAINT",
        "optimization_status": "VERIFIED_LOCAL_V27", "reuse_scope": "SERIES",
        "source_or_license": "CUSTOM_BLENDER (Original)",
        "status": "IN_PROGRESS",
        "notes": "Char tag @krishna. Local work/agent1_v26/krishna_v27_clean.blend adds separated dental arches & tongue driven by KRISHNA_expr_jaw_open.",
        "char_tags": ["@krishna"], "keywords": ["krishna"],
    },
    {
        "asset_id": "AST-0005", "asset_name": "Shalya Hero (Madraka King / Charioteer)", "asset_type": "CHARACTER",
        "blender_file": "studio/cast/shalya/model/rig/shalya_hero_v1.blend",
        "unreal_asset_path": "", "version": "v1", "dependencies": "studio/cast/shalya/passport.md",
        "rig_status": "RIGGED", "material_status": "NEEDS_2K_PAINTERLY_REPAINT",
        "optimization_status": "LOD_PENDING", "reuse_scope": "EP01_S5_S6",
        "source_or_license": "CUSTOM_BLENDER (shalya_build.py)",
        "status": "IN_PROGRESS",
        "notes": "Char tag @shalya. Grey-bearded charioteer for Karna in EP01 Scene 01 & A03/A11/A21.",
        "char_tags": ["@shalya"], "keywords": ["shalya"],
    },
    # --- S1E01 NEW CHARACTERS (PASSPORTS ONLY) ---
    {
        "asset_id": "AST-0006", "asset_name": "Rishi Vyasa", "asset_type": "CHARACTER",
        "blender_file": "", "unreal_asset_path": "", "version": "v0", "dependencies": "studio/cast/vyasa/passport.md",
        "rig_status": "NOT_STARTED", "material_status": "NOT_STARTED", "optimization_status": "NOT_STARTED",
        "reuse_scope": "SERIES", "source_or_license": "CUSTOM_BLENDER (Original sculpt + Rigify)",
        "status": "PLANNED",
        "notes": "Char tag @vyasa. S1E01 sc01 & sc03 closing match-cut + future narration beats.",
        "char_tags": ["@vyasa"], "keywords": ["vyasa"],
    },
    {
        "asset_id": "AST-0007", "asset_name": "Lord Ganesha (Scribe)", "asset_type": "CHARACTER",
        "blender_file": "", "unreal_asset_path": "", "version": "v0", "dependencies": "studio/cast/ganesha/passport.md",
        "rig_status": "NOT_STARTED", "material_status": "NOT_STARTED", "optimization_status": "NOT_STARTED",
        "reuse_scope": "S1E01", "source_or_license": "CUSTOM_BLENDER (Special anatomy: trunk + 4 arms + snap tusk)",
        "status": "PLANNED",
        "notes": "Char tag @ganesha. Needs detaching right-tusk tip prop/shape key for S09 added beat.",
        "char_tags": ["@ganesha"], "keywords": ["ganesha"],
    },
    {
        "asset_id": "AST-0008", "asset_name": "Lord Brahma (Four-Faced)", "asset_type": "CHARACTER",
        "blender_file": "", "unreal_asset_path": "", "version": "v0", "dependencies": "studio/cast/brahma/passport.md",
        "rig_status": "NOT_STARTED", "material_status": "NOT_STARTED", "optimization_status": "NOT_STARTED",
        "reuse_scope": "SERIES_DIVINE", "source_or_license": "CUSTOM_BLENDER + LOTUS_SEAT_TRELLIS2",
        "status": "PLANNED",
        "notes": "Char tag @brahma. S1E01 sc01 (S03-S05); stationary sacred stillness, glows on lotus seat.",
        "char_tags": ["@brahma"], "keywords": ["brahma"],
    },
    {
        "asset_id": "AST-0009", "asset_name": "King Dushmanta (Forest & Court Variants)", "asset_type": "CHARACTER",
        "blender_file": "", "unreal_asset_path": "", "version": "v0", "dependencies": "studio/cast/dushmanta/passport.md",
        "rig_status": "NOT_STARTED", "material_status": "NOT_STARTED", "optimization_status": "NOT_STARTED",
        "reuse_scope": "S1E01", "source_or_license": "CUSTOM_BLENDER (TRELLIS2 copper armor accents)",
        "status": "PLANNED",
        "notes": "Char tag @dushmanta. Vedic 1000 BCE copper plate guard + court red dhoti + plain copper circlet.",
        "char_tags": ["@dushmanta"], "keywords": ["dushmanta"],
    },
    {
        "asset_id": "AST-0010", "asset_name": "Shakuntala (Hermitage & Infant Variant)", "asset_type": "CHARACTER",
        "blender_file": "", "unreal_asset_path": "", "version": "v0", "dependencies": "studio/cast/shakuntala/passport.md",
        "rig_status": "NOT_STARTED", "material_status": "NOT_STARTED", "optimization_status": "NOT_STARTED",
        "reuse_scope": "S1E01", "source_or_license": "CUSTOM_BLENDER (Bark-cloth + cotton, NO ring/crown)",
        "status": "PLANNED",
        "notes": "Char tag @shakuntala. Strict Ganguli canon: no Kalidasa ring prop.",
        "char_tags": ["@shakuntala"], "keywords": ["shakuntala"],
    },
    {
        "asset_id": "AST-0011", "asset_name": "Sage Kanwa", "asset_type": "CHARACTER",
        "blender_file": "", "unreal_asset_path": "", "version": "v0", "dependencies": "studio/cast/kanwa/passport.md",
        "rig_status": "NOT_STARTED", "material_status": "NOT_STARTED", "optimization_status": "NOT_STARTED",
        "reuse_scope": "S1E01_RECURRING_SAGE_BASE", "source_or_license": "CUSTOM_BLENDER (Modular sage base rig)",
        "status": "PLANNED",
        "notes": "Char tag @kanwa. Base elderly forest-sage body can be reused across background rishis.",
        "char_tags": ["@kanwa"], "keywords": ["kanwa", "sage"],
    },
    {
        "asset_id": "AST-0012", "asset_name": "Young Bharata (Sarvadamana, age 6)", "asset_type": "CHARACTER",
        "blender_file": "", "unreal_asset_path": "", "version": "v0", "dependencies": "studio/cast/bharata_boy/passport.md",
        "rig_status": "NOT_STARTED", "material_status": "NOT_STARTED", "optimization_status": "NOT_STARTED",
        "reuse_scope": "S1E01_CHILD_BASE", "source_or_license": "CUSTOM_BLENDER",
        "status": "PLANNED",
        "notes": "Char tag @bharata_boy. Compact 6yo rig; reusable child proportions for young Pandavas/Abhimanyu insert.",
        "char_tags": ["@bharata_boy"], "keywords": ["sarvadamana", "bharata_boy", "young child"],
    },
    # --- ANIMALS & CREATURES (FAB + BLENDER) ---
    {
        "asset_id": "AST-0013", "asset_name": "Vedic Chariot Horses (White & Dun Teams)", "asset_type": "ANIMAL_CREATURE",
        "blender_file": "",
        "unreal_asset_path": "/Game/Kurukshetra/Hero/SM_krk_horse_white; /Game/Kurukshetra/Hero/SM_krk_horse_team; /Game/Hastinapur/Trellis/hst_white_horse/SM_hst_white_horse",
        "version": "v1", "dependencies": "",
        "rig_status": "NEEDED_GALLOP_KNEEL", "material_status": "NEEDS_PAINTERLY_COAT",
        "optimization_status": "UNREAL_STATIC_PRESENT_NEED_RIG", "reuse_scope": "SERIES",
        "source_or_license": "MahabharataWorld UE + FAB_TARGET (Rigged Horse + Gallop/Kneel anim) -> strip stirrups",
        "status": "IN_PROGRESS",
        "notes": "Static meshes exist in MahabharataWorld/Kurukshetra & Hastinapur; add rigged/animated Fab horse pack for A05/A13 kneeling beat.",
        "char_tags": [], "keywords": ["horse", "horses", "steed", "steeds", "hooves"],
    },
    {
        "asset_id": "AST-0014", "asset_name": "Hermitage Animals (Lion, Tiger, Deer)", "asset_type": "ANIMAL_CREATURE",
        "blender_file": "", "unreal_asset_path": "", "version": "v1", "dependencies": "",
        "rig_status": "NEEDED_LION_RIDE", "material_status": "NEEDS_PAINTERLY_FUR",
        "optimization_status": "NOT_STARTED", "reuse_scope": "S1E01_S4_VANA",
        "source_or_license": "FAB_TARGET (Big cat / deer rigged packs) -> Blender stylized fur",
        "status": "ACQUISITION_TARGET",
        "notes": "Used in S1E01 H02 (deer flee), V08 (Bharata rides lion / holds tiger jaw).",
        "char_tags": [], "keywords": ["lion", "tiger", "tigers", "deer", "elephant", "elephants"],
    },
    {
        "asset_id": "AST-0015", "asset_name": "Noble Shakunta Vulture Pack (SSS Feather Kit)", "asset_type": "ANIMAL_CREATURE",
        "blender_file": "", "unreal_asset_path": "", "version": "v1", "dependencies": "",
        "rig_status": "FLAP_CYCLE_OR_BOIDS", "material_status": "FEATHER_SSS_SHADER (CON-0030)",
        "optimization_status": "INSTANCED_BOIDS", "reuse_scope": "S1E01_S6_OMENS",
        "source_or_license": "FAB_TARGET (Raptor bird rig) + Blender Boids + CON-0030 SSS Feather Kit",
        "status": "ACQUISITION_TARGET",
        "notes": "Directly applies REF-0010 (Garuda/flock feather SSS). Painted noble/protective in V01-V02.",
        "char_tags": [], "keywords": ["vulture", "vultures", "bird", "birds", "flock", "feather", "garuda", "shakunta"],
    },
    # --- VEHICLES, WEAPONS & PROPS (BLENDER + TRELLIS.2) ---
    {
        "asset_id": "AST-0016", "asset_name": "Vedic Gold War Chariots (Arjuna Ape-Banner / Karna Elephant-Rope / Dushmanta)", "asset_type": "VEHICLE",
        "blender_file": "studio/tools/blender/shalya_chariot_check.py",
        "unreal_asset_path": "/Game/Kurukshetra/Hero/SM_krk_arjuna_chariot; /Game/Kurukshetra/Hero/SM_krk_ape_banner; /Game/Hastinapur/Trellis/hst_arjuna_chariot/SM_hst_arjuna_chariot",
        "version": "v1", "dependencies": "studio/tools/blender/banners.py",
        "rig_status": "RIGGED_WHEEL_SINK_VARIANT", "material_status": "CARVED_GOLD_BLACK_ENAMEL",
        "optimization_status": "SUB_100K_TRIS", "reuse_scope": "SERIES",
        "source_or_license": "CUSTOM_BLENDER + MahabharataWorld UE + TRELLIS2_CARVED_TRIM",
        "status": "IN_PROGRESS",
        "notes": "No canopy, no horned saddle/stirrups. Needs detachable left wheel + banner pole break rigid-joint for A16/A18.",
        "char_tags": [], "keywords": ["chariot", "chariots", "wheel", "banner", "kapi-dhvaja"],
    },
    {
        "asset_id": "AST-0017", "asset_name": "Divine Bows & Hero Arrows (Gandiva, Vijaya, Snake Arrow, Anjalika)", "asset_type": "PROP_WEAPON",
        "blender_file": "studio/tools/blender/bows.py",
        "unreal_asset_path": "/Game/Kurukshetra/Hero/SM_krk_great_bow; /Game/Kurukshetra/Hero/SM_krk_arrow_cluster; /Game/Kurukshetra/Hero/SM_krk_gada",
        "version": "v1", "dependencies": "studio/cast/karna/model/trellis_out/karna_bow_1536.glb",
        "rig_status": "BOW_FLEX_RIG_EYELID_SNAKE", "material_status": "CARVED_GOLD_AND_WOOD",
        "optimization_status": "HERO_MACRO_READY", "reuse_scope": "SERIES",
        "source_or_license": "TRELLIS2_PROP (karna_bow_1536.glb) + CUSTOM_BLENDER bows.py + MahabharataWorld UE",
        "status": "IN_PROGRESS",
        "notes": "Snake arrowhead needs eyelid shape key for EP01 A10 macro; Anjalika has large crescent blade head (A19).",
        "char_tags": [], "keywords": ["bow", "arrow", "arrows", "arrowhead", "arrowheads", "gandiva", "vijaya", "quiver", "anjalika", "serpent", "spear", "sword", "gada"],
    },
    {
        "asset_id": "AST-0018", "asset_name": "Hermitage & Vedic Props (Palm-Leaf Manuscripts, Brass Stylus, Fire Altar, Diya, Kalash)", "asset_type": "PROP",
        "blender_file": "MAHABHARATA_STUDIO/02_BLENDER/Props/PolyHaven_CC0/brass_diya_lantern/brass_diya_lantern_2k.blend",
        "unreal_asset_path": "/Game/Hastinapur/Trellis/hst_lamp_pillar/SM_hst_lamp_pillar; /Game/Kurukshetra/Hero/SM_krk_conch",
        "version": "v1", "dependencies": "NVIDIA_SimReady + PolyHaven_CC0 (11 Vedic-adaptable .blend props)",
        "rig_status": "NOT_APPLICABLE", "material_status": "PAINTERLY_REPAINT_NEEDED",
        "optimization_status": "2K_LOW_VRAM_SAFE", "reuse_scope": "SERIES",
        "source_or_license": "PolyHaven CC0 (brass_diya_lantern, brass_pot_01/02, brass_vase_01/03, stone_fire_pit) + NVIDIA SimReady OpenUSD + TRELLIS.2",
        "status": "ACQUIRED_NEEDS_PAINTERLY_REPAINT",
        "notes": "Downloaded CC0 brass diya, pots, stone fire pit, clay pots & carved wood plates + OpenUSD clay/copper props. Strictly NO paper books.",
        "char_tags": [], "keywords": ["palm leaf", "palm leaves", "palm-leaf", "stylus", "altar", "diya", "lamp", "kalash", "lotus", "torch", "mashal", "bolster", "water pot", "tusk", "water jar"],
    },
    {
        "asset_id": "AST-0019", "asset_name": "Hero Crowns, Ornaments & Armour Trims (Kiritamukuta, Keyura, Mekhala)", "asset_type": "PROP_COSTUME",
        "blender_file": "studio/tools/blender/hero_crown.py",
        "unreal_asset_path": "", "version": "v1", "dependencies": "studio/tools/blender/hero_detail.py",
        "rig_status": "RIGGED_DETACH_CROWN", "material_status": "HAMMERED_GOLD_VERDIGRIS_CON0050",
        "optimization_status": "SHARED_LIBRARY", "reuse_scope": "SERIES",
        "source_or_license": "TRELLIS2_PROP (high-detail reliefs) + BLENDER shader CON-0050 (REF-0017 patina)",
        "status": "IN_PROGRESS",
        "notes": "Detaching crown on Arjuna needed for EP01 A14. Apply REF-0017 verdigris/copper shader language.",
        "char_tags": [], "keywords": ["crown", "diadem", "armour", "armor", "jewelry", "jewellery", "ornament", "harness"],
    },
    # --- ENVIRONMENTS (BLENDER + FAB + UNREAL PLATES) ---
    {
        "asset_id": "AST-0020", "asset_name": "Kurukshetra Battlefield & 14k Instanced Army", "asset_type": "ENVIRONMENT",
        "blender_file": "studio/tools/blender/battlefield.py",
        "unreal_asset_path": "/Game/Kurukshetra/L_Kurukshetra; /Game/Kurukshetra/Proc/SM_KRK_Terrain", "version": "v1",
        "dependencies": "CON-0001, CON-0009, CON-0051, PolyHaven aarfontein_dusk_2k.exr",
        "rig_status": "GEOMETRY_NODES_13977_INSTANCES", "material_status": "TRAMPLED_RED_EARTH_PAINTERLY",
        "optimization_status": "LOW_VRAM_4GB_READY", "reuse_scope": "SERIES_SEASONS_5_6",
        "source_or_license": "CUSTOM_BLENDER_GN + MahabharataWorld UE (L_Kurukshetra) + PolyHaven CC0 dry_ground_01 & dusk HDRI",
        "status": "IN_PROGRESS",
        "notes": "73 Unreal assets already in MahabharataWorld/Kurukshetra! Keep UE strictly for parallax sky/terrain plates on 4 GB GTX 1650.",
        "char_tags": [], "keywords": ["kurukshetra", "battlefield", "armies", "camp", "tent", "red earth"],
    },
    {
        "asset_id": "AST-0021", "asset_name": "Kanwa / Vyasa Vedic Hermitage & Malini Riverbank", "asset_type": "ENVIRONMENT",
        "blender_file": "studio/tools/blender/scene01_3d.py",
        "unreal_asset_path": "/Game/Cities/Vrindavan/L_Vrindavan; /Game/Cities/Vrindavan/Kit/SM_Vrindavan_banyan; /Game/Cities/Vrindavan/Kit/SM_Vrindavan_banks",
        "version": "v1",
        "dependencies": "CON-0025, CON-0040, CON-0058, CON-0060, PolyHaven CC0 (root_cluster_01/02, ganges_river_pebbles, tree_small_02, fern_02)",
        "rig_status": "MODULAR_THATCH_HUT_BANYAN", "material_status": "PAINTERLY_FOLIAGE_RIVER",
        "optimization_status": "2K_MULTIPLANE_4GB_SAFE", "reuse_scope": "SERIES_ALL_ASHRAM_SCENES",
        "source_or_license": "MahabharataWorld UE (Vrindavan banyan/banks) + PolyHaven CC0 nature/ganges_river_pebbles + FAB_TARGET (Ancient Trees/River)",
        "status": "IN_PROGRESS_CC0_ACQUIRED",
        "notes": "Downloaded 9 CC0 2K nature .blends + 5 river/bark PBRs + dawn/sunrise HDRIs + Vrindavan banyan/bank UE meshes! Add Fab foliage next.",
        "char_tags": [], "keywords": ["hermitage", "forest", "malini", "banyan", "ashram", "grove", "waterfall", "yamuna", "riverbank", "thatched"],
    },
    {
        "asset_id": "AST-0022", "asset_name": "Vedic Royal Court Hall (Hastinapur / Puru Sabha Kit)", "asset_type": "ENVIRONMENT",
        "blender_file": "",
        "unreal_asset_path": "/Game/Hastinapur/L_Hastinapur; /Game/Hastinapur/Proc/palace/SM_throne_hall; /Game/Hastinapur/Trellis/hst_sabha_column_bay/SM_hst_sabha_column_bay",
        "version": "v1",
        "dependencies": "CON-0010, CON-0013, CON-0019, CON-0020, CON-0021, CON-0055",
        "rig_status": "MODULAR_WOOD_SANDSTONE_PILLARS", "material_status": "WARM_GOLD_SANDSTONE_PAINTERLY",
        "optimization_status": "MODULAR_KIT_4GB_SAFE", "reuse_scope": "SERIES",
        "source_or_license": "MahabharataWorld UE (170 Hastinapur assets!) + FAB_TARGET (Courtyard/Wooden pillars for 1000 BCE S1E01 court)",
        "status": "IN_PROGRESS",
        "notes": "MahabharataWorld has Hastinapur Sabha/Throne/Torana assets; for S1E01 sc03 Puru court simplify to Vedic wooden pillars + oil lamps.",
        "char_tags": [], "keywords": ["court", "palace", "sabha", "pillars", "throne", "rampart", "parapet", "temple", "citadel", "balcony"],
    },
    # --- LOOKDEV, SHADERS & 2D/3D FX LIBRARY ---
    {
        "asset_id": "AST-0023", "asset_name": "2D Grease Pencil Astra & Combat FX Library", "asset_type": "VFX_LIBRARY",
        "blender_file": "studio/tools/fx_a06_release.py",
        "unreal_asset_path": "/Game/VFX/Niagara_Plates", "version": "v1",
        "dependencies": "CON-0011, CON-0022, CON-0023, CON-0031, CON-0032, CON-0041, CON-0048",
        "rig_status": "GP_V3_CYCLES", "material_status": "TWO_TONE_ASTRA_EMISSIVE",
        "optimization_status": "NEAR_ZERO_RENDER_COST", "reuse_scope": "SERIES",
        "source_or_license": "CUSTOM_BLENDER_GP_V3 + FAB_TARGET (Optional Niagara sparks/dust for UE plates)",
        "status": "IN_PROGRESS",
        "notes": "Karna: #FFF1C2/#FF8A1E sun-gold; Arjuna: #F2FAFF/#3FA9FF white-blue. Includes impact frames, starbursts, dust bursts, shockwave rings.",
        "char_tags": [], "keywords": ["lightning", "sun-fire", "sparks", "spark", "shockwave", "impact frame", "impact frames", "negative flash", "astra", "static", "meteors", "starburst", "embers", "selective color"],
    },
    {
        "asset_id": "AST-0024", "asset_name": "Arcane-Family Painterly Compositor & Kuwahara Grade", "asset_type": "SHADER_LOOKDEV",
        "blender_file": "studio/setup/eevee_test.py",
        "unreal_asset_path": "", "version": "v1", "dependencies": "studio/bible.md, CON-0042, CON-0057, CON-0063",
        "rig_status": "EEVEE_COMPOSITOR_PRESET", "material_status": "GOLD_KEY_BLUE_SHADOW_KUWAHARA",
        "optimization_status": "SHEEPIT_UNDER_2GB_PACKABLE", "reuse_scope": "SERIES",
        "source_or_license": "CUSTOM_BLENDER_COMPOSITOR",
        "status": "IN_PROGRESS",
        "notes": "Enforces #FFC27A key / #3E5A86 blue shadow, downscale Kuwahara brush breakup, glow/light-wrap, edge chromatic offset.",
        "char_tags": [], "keywords": ["shader", "template", "compositor", "lighting", "preset", "hdr", "mist", "fog"],
    },
]

# High-value Fab Marketplace search & collection targets matched to real pipeline needs
FAB_SHOPPING_TARGETS = [
    ("FAB-01", "AST-0021", "Forest, Ancient Banyan Trees, River Rocks & Tropical/Monsoon Foliage",
     "Fantasy forest / Ancient trees / River stones / Waterfall (Fab Free + Megascans)",
     "S1E01 sc01-sc03 (Vyasa/Shakuntala hermitage) + Season 4 Exile", "Standard / FAB Standard",
     "Decimate to <50k tris per cluster; replace photoreal bark/leaf textures with painted Krita brush albedo + #3E5A86 shadow fill."),
    ("FAB-02", "AST-0022", "Ancient Courtyard, Modular Columns, Torchholders & Hall Architecture",
     "Ancient palace / Temple pillars / Sandstone hall / Wooden rafters",
     "S1E01 sc03 Dushmanta court + Season 3 Hastinapur Sabha", "Standard / CC-BY (credit if required)",
     "For S1E01 strip ornate late-medieval stone idols/domes (Vedic 1000 BCE uses wooden pillars + oil lamps). Re-grade to warm sandstone/wood."),
    ("FAB-03", "AST-0013", "Rigged Horse + Gallop/Rear/Idle Animation Pack",
     "Horse / Horse rig / Animal animation",
     "EP01 Teaser (A02, A05, A13 kneeling beat!) + S1E01 H01-H03", "Standard (commercial safe)",
     "Check skeleton compatibility for Blender FBX import; remove all modern saddles/stirrups; add golden Vedic breastplate geometry."),
    ("FAB-04", "AST-0014", "Rigged Lion, Tiger & Forest Deer Pack",
     "Lion rig / Tiger / Deer",
     "S1E01 H02 (fleeing deer), V08 (Bharata riding lion & opening tiger jaws)", "Standard",
     "Paint stylised mane cards; apply simplified broad value shading so animals match @bharata_boy."),
    ("FAB-05", "AST-0015", "Rigged Eagle / Vulture Bird Flock",
     "Vulture / Eagle flight loop",
     "S1E01 V01-V02 (Shakunta protectors) + EP01 sky omens (CON-0029)", "Standard / CC-BY",
     "Apply thin-sheet SSS wing feather shader from REF-0010 (CON-0030) for rose-gold dawn translucency."),
    ("FAB-06", "AST-0020", "Dry Red Earth, Dust Storms & Modular Battlefield Props",
     "Cracked red earth material / Niagara dust / Broken wood / Spears",
     "EP01 Kurukshetra ring & UE 5.8 background plates", "Standard / Megascans free tier",
     "Use ONLY for UE 5.8 background plates & terrain depth; keep heavy meshes out of 4 GB GTX 1650 hero scene."),
]


def init_schema(conn: sqlite3.Connection):
    """Create the 8-table + extension production schema cleanly."""
    conn.executescript("""
    PRAGMA foreign_keys = ON;

    DROP TABLE IF EXISTS shot_assets;
    DROP TABLE IF EXISTS asset_concepts;
    DROP TABLE IF EXISTS shots;
    DROP TABLE IF EXISTS assets;
    DROP TABLE IF EXISTS concept_references;
    DROP TABLE IF EXISTS concepts;
    DROP TABLE IF EXISTS reference_techniques;
    DROP TABLE IF EXISTS techniques;
    DROP TABLE IF EXISTS "references";

    CREATE TABLE "references" (
        reference_id TEXT PRIMARY KEY,
        source_url TEXT,
        saved_collection TEXT,
        access_status TEXT,
        primary_category TEXT,
        secondary_tags TEXT,
        subject TEXT,
        analysis_status TEXT DEFAULT 'PENDING',
        priority_score REAL,
        mahabharata_scene_idea TEXT,
        originality_cautions TEXT,
        research_json TEXT
    );

    CREATE TABLE techniques (
        technique_id TEXT PRIMARY KEY,
        category TEXT,
        technique_name TEXT,
        description TEXT,
        blender_notes TEXT,
        unreal_notes TEXT
    );

    CREATE TABLE reference_techniques (
        reference_id TEXT,
        technique_id TEXT,
        relevance_score REAL,
        FOREIGN KEY(reference_id) REFERENCES "references"(reference_id),
        FOREIGN KEY(technique_id) REFERENCES techniques(technique_id),
        PRIMARY KEY(reference_id, technique_id)
    );

    CREATE TABLE concepts (
        concept_id TEXT PRIMARY KEY,
        title TEXT,
        episode_id TEXT,
        scene TEXT,
        scene_description TEXT,
        camera_plan TEXT,
        lighting_plan TEXT,
        vfx_requirements TEXT,
        required_assets_raw TEXT,
        originality_status TEXT DEFAULT 'APPROVED_PRINCIPLES_ONLY',
        approval_status TEXT DEFAULT 'DRAFT'
    );

    CREATE TABLE concept_references (
        concept_id TEXT,
        reference_id TEXT,
        FOREIGN KEY(concept_id) REFERENCES concepts(concept_id),
        FOREIGN KEY(reference_id) REFERENCES "references"(reference_id),
        PRIMARY KEY(concept_id, reference_id)
    );

    CREATE TABLE assets (
        asset_id TEXT PRIMARY KEY,
        asset_name TEXT,
        asset_type TEXT,
        source_type TEXT,
        blender_path TEXT,
        unreal_path TEXT,
        version TEXT,
        rig_status TEXT,
        material_status TEXT,
        optimization_status TEXT,
        reuse_scope TEXT,
        status TEXT,
        notes TEXT
    );

    CREATE TABLE asset_concepts (
        asset_id TEXT,
        concept_id TEXT,
        FOREIGN KEY(asset_id) REFERENCES assets(asset_id),
        FOREIGN KEY(concept_id) REFERENCES concepts(concept_id),
        PRIMARY KEY(asset_id, concept_id)
    );

    CREATE TABLE shots (
        shot_id TEXT PRIMARY KEY,
        episode_id TEXT,
        sequence_id TEXT,
        scene_name TEXT,
        duration_seconds REAL,
        grade TEXT,
        beat TEXT,
        description TEXT,
        camera_plan TEXT,
        animation_status TEXT,
        lighting_status TEXT,
        vfx_status TEXT,
        render_status TEXT,
        edit_status TEXT,
        priority TEXT,
        canon_notes TEXT
    );

    CREATE TABLE shot_assets (
        shot_id TEXT,
        asset_id TEXT,
        role_in_shot TEXT,
        FOREIGN KEY(shot_id) REFERENCES shots(shot_id),
        FOREIGN KEY(asset_id) REFERENCES assets(asset_id),
        PRIMARY KEY(shot_id, asset_id)
    );
    """)


def match_assets_for_text(text: str, char_tags=None, default_env=None, is_shot=False):
    """Map shot/concept text & character tags to canonical AST-* IDs deterministically."""
    char_tags = set(char_tags or [])
    lower = text.lower()
    matched = []
    for ast in CANONICAL_ASSETS:
        aid = ast["asset_id"]
        if char_tags and any(tag in char_tags for tag in ast["char_tags"]):
            matched.append((aid, "CHARACTER"))
            continue
        # For storyboarded shots with explicit @char lists, avoid false CHARACTER links from dialogue mentions
        if is_shot and ast["asset_type"] == "CHARACTER":
            # Exception: Shalya is un-tagged in EP01 A03/A11/A21 frames but physically visible
            if aid == "AST-0005" and re.search(r"\bshalya\b", lower):
                matched.append((aid, "CHARACTER"))
            continue
        if any(re.search(r"\b" + re.escape(kw) + r"\b", lower) for kw in ast["keywords"]):
            matched.append((aid, ast["asset_type"]))

    # Ensure deterministic primary environment when caller specifies scene context
    if default_env:
        env_list = default_env if isinstance(default_env, list) else [default_env]
        for eid in env_list:
            matched.append((eid, "ENVIRONMENT"))

    # Always include base painterly compositor preset
    matched.append(("AST-0024", "PIPELINE_GRADE"))

    seen = set()
    out = []
    for aid, role in matched:
        if aid not in seen:
            seen.add(aid)
            out.append((aid, role))
    return out


def infer_default_env(ep_id: str, seq_id: str, raw_id: str):
    """Assign primary environment accurately per shot (prevents multi-scene header bleed)."""
    if ep_id == "EP01":
        return "AST-0020"
    if seq_id in ("SC01", "SC02"):
        return "AST-0021"
    if seq_id == "SC03":
        num = int(re.sub(r"\D", "", raw_id) or 0)
        if num == 18:
            return ["AST-0022", "AST-0021"]  # Match cut: court -> hermitage
        if 11 <= num <= 17:
            return "AST-0022"
        return "AST-0021"
    return None


def parse_episode_shots():
    """Read all committed storyboard shots from EP01 Teaser and S1E01 sc01..sc03."""
    sources = [
        ("EP01", "TEASER", "Karna vs Arjuna", STUDIO / "episodes" / "ep01_arjuna_vs_karna" / "shots.json"),
        ("S1E01", "SC01", "Vyasa, Brahma & Ganesha", STUDIO / "episodes" / "s1e01_the_scribe" / "sc01" / "shots.json"),
        ("S1E01", "SC02", "The Hunter King & Shakuntala", STUDIO / "episodes" / "s1e01_the_scribe" / "sc02" / "shots.json"),
        ("S1E01", "SC03", "The Promise, Boy & Voice", STUDIO / "episodes" / "s1e01_the_scribe" / "sc03" / "shots.json"),
    ]
    all_shots = []
    for ep_id, seq_id, scene_label, json_path in sources:
        if not json_path.exists():
            continue
        data = json.loads(json_path.read_text(encoding="utf-8"))
        for sh in data.get("shots", []):
            raw_id = sh["id"]
            full_id = f"{ep_id}_{seq_id}_{raw_id}"
            grade = sh.get("grade", "B")
            prio = "CRITICAL" if grade == "S" else ("HIGH" if grade == "A" else "MEDIUM")
            canon = sh.get("canon", {})
            canon_str = f"Lines {canon.get('lines', '')} ({canon.get('verdict', '')})".strip()
            # Match ONLY on this specific shot's own action, frame, motion & panel
            combined_txt = " ".join([
                sh.get("action", ""), sh.get("frame", ""), " ".join(sh.get("motion", [])),
                str(sh.get("panel", "")),
            ])
            all_shots.append({
                "shot_id": full_id,
                "episode_id": ep_id,
                "sequence_id": seq_id,
                "scene_name": f"{scene_label} [{sh.get('panel', raw_id)}]",
                "duration_seconds": float(sh.get("dur", 5)),
                "grade": grade,
                "beat": sh.get("beat", ""),
                "description": sh.get("action", ""),
                "camera_plan": sh.get("camera", ""),
                "chars": sh.get("chars", []),
                "combined_text": combined_txt,
                "default_env": infer_default_env(ep_id, seq_id, raw_id),
                "canon_notes": canon_str,
                "priority": prio,
                "ref_file": sh.get("ref", ""),
            })
    return all_shots


def load_csv(path: pathlib.Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build():
    ap = argparse.ArgumentParser()
    ap.add_argument("--studio-dir", default=str(DEFAULT_LOCAL_STUDIO))
    args = ap.parse_args()
    local_studio = pathlib.Path(args.studio_dir)

    refs = load_csv(LIB_DIR / "01_references.csv")
    cards = {c["reference_id"]: c for c in load_csv(LIB_DIR / "02_analysis_cards.csv")}
    concepts = load_csv(LIB_DIR / "03_concepts.csv")
    shots = parse_episode_shots()

    # Connect to SQLite in local MAHABHARATA_STUDIO (never committed raw binary)
    db_path = local_studio / "00_REFERENCE_LIBRARY" / "mahabharat_prod.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    init_schema(conn)
    cur = conn.cursor()

    # 1. Insert sanitized references (strip creator_username out of DB & exports per sharing hygiene, keep internal IDs)
    for r in refs:
        rid = r["reference_id"]
        card = cards.get(rid, {})
        payload = {
            "subject": r.get("subject", ""),
            "collection": r.get("saved_collection", ""),
            "timestamps_reviewed": r.get("timestamps_reviewed", ""),
            "visible_action": card.get("visible_action", ""),
            "composition": card.get("composition", ""),
            "lighting": card.get("lighting", ""),
            "palette": card.get("palette", ""),
            "emotional_effect": card.get("emotional_effect", ""),
        }
        prio = float(r["priority_score"]) if (r.get("priority_score") or "").strip() else None
        cur.execute(
            'INSERT INTO "references" VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
            (
                rid, r.get("instagram_url", ""), r.get("saved_collection", ""),
                r.get("access_status", ""), r.get("primary_category", ""),
                r.get("secondary_tags", ""), r.get("subject", ""),
                r.get("analysis_status", "PENDING"), prio,
                r.get("mahabharata_scene_idea", ""),
                card.get("originality_cautions", "") or r.get("rights_notes", ""),
                json.dumps(payload, ensure_ascii=False),
            ),
        )

    # 2. Extract reusable techniques from the 21 completed analysis cards
    tech_count = 0
    for rid, card in sorted(cards.items()):
        if not (card.get("visible_action") or "").strip():
            continue
        tech_count += 1
        tid = f"TECH-{tech_count:04d}"
        ref_row = next((x for x in refs if x["reference_id"] == rid), {})
        cat = ref_row.get("primary_category", "CINEMATOGRAPHY")
        name = (ref_row.get("subject", "") or tid)[:80]
        desc = f"Camera: {card.get('camera_angle','')} | Move: {card.get('camera_movement','')} | Light: {card.get('lighting','')}"
        cur.execute(
            "INSERT INTO techniques VALUES (?,?,?,?,?,?)",
            (tid, cat, name, desc, card.get("blender_tasks", ""), card.get("unreal_tasks", "")),
        )
        prio = float(ref_row["priority_score"]) if (ref_row.get("priority_score") or "").strip() else 3.0
        cur.execute("INSERT INTO reference_techniques VALUES (?,?,?)", (rid, tid, prio))

    # 3. Insert canonical assets
    for ast in CANONICAL_ASSETS:
        cur.execute(
            "INSERT INTO assets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                ast["asset_id"], ast["asset_name"], ast["asset_type"], ast["source_or_license"],
                ast["blender_file"], ast["unreal_asset_path"], ast["version"],
                ast["rig_status"], ast["material_status"], ast["optimization_status"],
                ast["reuse_scope"], ast["status"], ast["notes"],
            ),
        )

    # 4. Insert concepts & link both references and required assets
    concept_to_assets = defaultdict(list)
    for c in concepts:
        cid = c["concept_id"]
        cur.execute(
            "INSERT INTO concepts VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                cid, c.get("concept_title", ""), c.get("episode", ""), c.get("scene", ""),
                c.get("original_shot_description", ""), c.get("camera_plan", ""),
                c.get("lighting_plan", ""), c.get("vfx_requirements", ""),
                c.get("required_assets", ""), c.get("originality_review", "PENDING"),
                c.get("approval_status", "DRAFT"),
            ),
        )
        for ref_part in (c.get("source_reference_ids") or "").split(","):
            rp = ref_part.strip()
            if rp:
                cur.execute("INSERT OR IGNORE INTO concept_references VALUES (?,?)", (cid, rp))

        c_txt = " ".join([
            c.get("concept_title", ""), c.get("original_shot_description", ""),
            c.get("required_assets", ""), c.get("lighting_plan", ""), c.get("vfx_requirements", ""),
        ])
        for aid, _ in match_assets_for_text(c_txt):
            cur.execute("INSERT OR IGNORE INTO asset_concepts VALUES (?,?)", (aid, cid))
            concept_to_assets[aid].append(cid)

    # 5. Insert all 62 scripted shots & link assets
    shots_csv_rows = [SHOTS_HEADER]
    shot_asset_hits = Counter()
    for sh in shots:
        sid = sh["shot_id"]
        matches = match_assets_for_text(sh["combined_text"], sh["chars"], sh["default_env"], is_shot=True)
        env_ids = sh["default_env"] if isinstance(sh["default_env"], list) else ([sh["default_env"]] if sh["default_env"] else [])
        env_str = ",".join(env_ids)

        # Auto-match relevant concepts for EP01 / S1E01
        rel_concepts = []
        for aid, _ in matches:
            rel_concepts.extend(concept_to_assets.get(aid, [])[:1])
        rel_concepts_str = ",".join(dict.fromkeys(rel_concepts))[:80]

        cur.execute(
            "INSERT INTO shots VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                sid, sh["episode_id"], sh["sequence_id"], sh["scene_name"], sh["duration_seconds"],
                sh["grade"], sh["beat"], sh["description"], sh["camera_plan"],
                "BLOCKED_MOVES" if sh["episode_id"] == "EP01" else "NOT_STARTED",
                "LAYOUT_ONLY" if sh["episode_id"] == "EP01" else "NOT_STARTED",
                "PROOF_A06" if sid == "EP01_TEASER_A06" else "NOT_STARTED",
                "DRAFT_ONLY" if sh["episode_id"] == "EP01" else "NOT_STARTED",
                "ANIMATIC_BUILT" if sh["episode_id"] == "EP01" else "NOT_STARTED",
                sh["priority"], f"Grade {sh['grade']} | {sh['canon_notes']}",
            ),
        )
        for aid, role in matches:
            cur.execute("INSERT OR IGNORE INTO shot_assets VALUES (?,?,?)", (sid, aid, role))
            shot_asset_hits[aid] += 1

        shots_csv_rows.append([
            sid, sh["episode_id"], sh["sequence_id"], sh["scene_name"], str(int(sh["duration_seconds"])),
            sh["description"], ",".join(sh["chars"]), env_str, rel_concepts_str, sh["camera_plan"],
            "BLOCKED_MOVES" if sh["episode_id"] == "EP01" else "NOT_STARTED",
            "NOT_STARTED", "NOT_STARTED", "NOT_STARTED",
            "ANIMATIC_BUILT" if sh["episode_id"] == "EP01" else "NOT_STARTED",
            sh["priority"], f"Grade {sh['grade']} ({sh['beat']}) | {sh['canon_notes']}",
        ])

    conn.commit()

    # 6. Write updated 04_shots.csv & 05_assets.csv back to repo (and mirror to local MAHABHARATA_STUDIO)
    assets_csv_rows = [ASSETS_HEADER]
    for ast in CANONICAL_ASSETS:
        aid = ast["asset_id"]
        hit_note = f"Linked to {shot_asset_hits[aid]} shots & {len(concept_to_assets[aid])} concepts. "
        assets_csv_rows.append([
            aid, ast["asset_name"], ast["asset_type"], ast["blender_file"], ast["unreal_asset_path"],
            ast["version"], ast["dependencies"], ast["rig_status"], ast["material_status"],
            ast["optimization_status"], ast["reuse_scope"], ast["source_or_license"], ast["status"],
            hit_note + ast["notes"],
        ])

    for name, rows in [("04_shots.csv", shots_csv_rows), ("05_assets.csv", assets_csv_rows)]:
        repo_csv = LIB_DIR / name
        with repo_csv.open("w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerows(rows)
        local_reg = local_studio / "00_REFERENCE_LIBRARY" / "01_URL_REGISTER" / name
        if local_reg.parent.exists():
            shutil.copy2(repo_csv, local_reg)

    # 7. Export sanitized planning JSON & CSV (zero creator usernames, zero screenshots, safe to share)
    export_dir = local_studio / "00_REFERENCE_LIBRARY" / "05_ORIGINAL_CONCEPTS" / "export_for_planning"
    export_dir.mkdir(parents=True, exist_ok=True)

    sanitized_refs_csv = export_dir / "mahabharat_sanitized_refs.csv"
    with sanitized_refs_csv.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["reference_id", "primary_category", "secondary_tags", "subject", "analysis_status", "priority_score", "mahabharata_scene_idea"])
        for r in refs:
            w.writerow([
                r["reference_id"], r.get("primary_category", ""), r.get("secondary_tags", ""),
                r.get("subject", ""), r.get("analysis_status", ""), r.get("priority_score", ""),
                r.get("mahabharata_scene_idea", ""),
            ])

    # ChatGPT-requested 9-field conversion mapping CSV for all concepts + analysed refs
    mapping_csv = export_dir / "mahabharat_chatgpt_mapping_export.csv"
    ref_lookup = {r["reference_id"]: r for r in refs}
    with mapping_csv.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow([
            "reference_id", "visual_category", "shot_concept", "required_asset",
            "asset_source", "asset_status", "blender_task", "unreal_task", "episode_id",
        ])
        for c in concepts:
            cid = c["concept_id"]
            first_ref = (c.get("source_reference_ids") or "").split(",")[0].strip()
            rinfo = ref_lookup.get(first_ref, {})
            card = cards.get(first_ref, {})
            linked_aids = [aid for aid, cids in concept_to_assets.items() if cid in cids]
            src_summary = "; ".join(
                next((a["source_or_license"] for a in CANONICAL_ASSETS if a["asset_id"] == aid), aid)
                for aid in linked_aids[:3]
            )
            status_summary = "; ".join(
                next((a["status"] for a in CANONICAL_ASSETS if a["asset_id"] == aid), "PLANNED")
                for aid in linked_aids[:3]
            )
            w.writerow([
                c.get("source_reference_ids", ""),
                rinfo.get("primary_category", "SCENE_DIRECTION"),
                f"{cid}: {c.get('concept_title','')} — {c.get('original_shot_description','')}",
                ", ".join(linked_aids) + f" | {c.get('required_assets','')}",
                src_summary,
                status_summary,
                card.get("blender_tasks", c.get("animation_requirements", "")),
                card.get("unreal_tasks", c.get("lighting_plan", "")),
                c.get("episode", ""),
            ])

    # Inspect downloaded manifests & existing MahabharataWorld Unreal project
    ph_manifest_path = local_studio / "02_BLENDER" / "polyhaven_cc0_manifest.json"
    nv_manifest_path = local_studio / "02_BLENDER" / "Props" / "nvidia_downloaded_manifest.json"
    mw_content = pathlib.Path.home() / "Documents" / "Unreal Projects" / "MahabharataWorld" / "Content"

    ph_manifest = json.loads(ph_manifest_path.read_text(encoding="utf-8")) if ph_manifest_path.exists() else {}
    nv_manifest = json.loads(nv_manifest_path.read_text(encoding="utf-8")) if nv_manifest_path.exists() else {}
    mw_counts = {}
    if mw_content.exists():
        for folder in ("Hastinapur", "Kurukshetra", "Cities"):
            fp = mw_content / folder
            if fp.exists():
                mw_counts[folder] = sum(1 for x in fp.rglob("*") if x.is_file())

    export_bundle = {
        "project": "Mahabharat Painterly 3D Animated Web Series",
        "visual_direction": "Arcane-family Painted 3D (gold key #FFC27A, blue shadow #3E5A86) + Grease Pencil 2D FX",
        "hardware_constraint": "GTX 1650 (4 GB VRAM) local; Blender EEVEE hero lead; UE 5.8 background plates only; TRELLIS.2 props on approved L4",
        "summary_counts": {
            "total_catalogued_refs": len(refs),
            "analysed_refs": sum(1 for r in refs if r["analysis_status"] == "ANALYSED"),
            "pending_refs": sum(1 for r in refs if r["analysis_status"] == "PENDING"),
            "extracted_techniques": tech_count,
            "concepts": len(concepts),
            "canonical_assets": len(CANONICAL_ASSETS),
            "scripted_shots": len(shots),
            "polyhaven_cc0_models": len(ph_manifest.get("models", [])),
            "polyhaven_cc0_textures": len(ph_manifest.get("textures", [])),
            "polyhaven_cc0_hdris": len(ph_manifest.get("hdris", [])),
            "nvidia_simready_props": len(nv_manifest.get("simready", [])),
            "nvidia_omniverse_sample_files": len(nv_manifest.get("omniverse_github", [])),
            "mahabharata_world_ue_files": sum(mw_counts.values()),
        },
        "existing_unreal_mahabharata_world": mw_counts,
        "downloaded_polyhaven_cc0": ph_manifest,
        "downloaded_nvidia_simready_and_openusd": nv_manifest,
        "refs_by_category": dict(Counter(r.get("primary_category", "") for r in refs)),
        "assets": [
            {k: v for k, v in a.items() if k not in ("char_tags", "keywords")}
            | {"linked_shots": shot_asset_hits[a["asset_id"]], "linked_concepts": len(concept_to_assets[a["asset_id"]])}
            for a in CANONICAL_ASSETS
        ],
        "fab_acquisition_targets": [
            dict(zip(["target_id", "asset_id", "target", "search_terms", "episodes_served", "license_rule", "adaptation_notes"], row))
            for row in FAB_SHOPPING_TARGETS
        ],
        "concepts_sample_top15": concepts[:15],
        "shots_summary": [
            {k: s[k] for k in ("shot_id", "episode_id", "sequence_id", "duration_seconds", "grade", "beat", "description")}
            for s in shots
        ],
    }
    bundle_json = export_dir / "mahabharat_production_bundle_sanitized.json"
    bundle_json.write_text(json.dumps(export_bundle, indent=2, ensure_ascii=False), encoding="utf-8")

    # 8. Write markdown matrix doc inside studio/refs/library/
    matrix_lines = [
        "# Mahabharata Production Asset Matrix & Fab / TRELLIS.2 / Reference Linker",
        "",
        "Generated directly from `studio/refs/library/` CSVs, `studio/episodes/`, `studio/cast/`, and `studio/tools/blender/`.",
        "",
        "## 1. Current Verified Counts",
        f"- **Catalogued Instagram References (`01_references.csv`):** `{len(refs)}` (`{export_bundle['summary_counts']['analysed_refs']}` deeply frame-analysed, `{export_bundle['summary_counts']['pending_refs']}` pending with category/subject tags already populated)",
        f"- **Extracted Visual Techniques:** `{tech_count}` (from `REF-0001`–`REF-0021`)",
        f"- **Original Scene Concepts (`03_concepts.csv`):** `{len(concepts)}`",
        f"- **Canonical Reusable Assets (`05_assets.csv`):** `{len(CANONICAL_ASSETS)}`",
        f"- **Scripted Shots Linked (`04_shots.csv`):** `{len(shots)}` (`22` EP01 Teaser + `40` S1E01 sc01–sc03)",
        "",
        "## 2. Reusable Asset Priority Table (Sorted by Shot Reuse)",
        "",
        "| Asset ID | Name | Type | Status | Linked Shots | Linked Concepts | Strategy / Source |",
        "|---|---|---|---|---:|---:|---|",
    ]
    sorted_assets = sorted(CANONICAL_ASSETS, key=lambda a: (shot_asset_hits[a["asset_id"]], len(concept_to_assets[a["asset_id"]])), reverse=True)
    for a in sorted_assets:
        aid = a["asset_id"]
        matrix_lines.append(
            f"| `{aid}` | {a['asset_name']} | `{a['asset_type']}` | `{a['status']}` | {shot_asset_hits[aid]} | {len(concept_to_assets[aid])} | {a['source_or_license']} |"
        )

    matrix_lines += [
        "",
        "## 3. Targeted Epic Fab Marketplace Checklist (Painterly Adaptation Required)",
        "",
        "> **Rule (`epic_film_pipelines.md` & `bible.md`):** On a **GTX 1650 (4 GB VRAM)**, keep Unreal Engine 5.8 + Fab for **background plates and modular kitbash parts**. Never ship raw photoreal marketplace materials — repaint/re-grade all Fab downloads to warm key `#FFC27A` + cool blue shadow `#3E5A86` and Vedic 1000 BCE period rules (no stirrups, no horned saddles, no medieval stone palaces).",
        "",
        "| Target | Linked Asset | Fab Search Terms | Serves Episodes | Period & Style Adaptation Rule |",
        "|---|---|---|---|---|",
    ]
    for tid, aid, tgt, search, eps, lic, adapt in FAB_SHOPPING_TARGETS:
        matrix_lines.append(f"| `{tid}` | `{aid}` | {search} | {eps} | {adapt} |")

    matrix_lines += [
        "",
        "## 4. Shifted Reel Workflow (Targeted Instead of Blind Grinding)",
        "",
        "After closing **Batch 1 (`REF-0022`–`REF-0031`)** once browser quota resets, stop blind sequential inspection of remaining `PENDING` Reels and query SQLite (`mahabharat_prod.db`) strictly for open production gaps:",
        "- `ENVIRONMENT` (`34` catalogued) -> Vedic forest/riverbank/court composition only for `AST-0021` & `AST-0022`",
        "- `COMBAT_ANIMATION` (`40` catalogued) -> Archery draw/volley timing only for `EP01` S/A shots",
        "- `VFX` (`42` catalogued) -> Grease Pencil impact & astral trail study for `AST-0023`",
        "- `FACIAL_ANIMATION` (`10` catalogued) -> Subtle close-up blinks/speech restraint for `A09`, `A22`, `S1E01 V12`",
        "",
        "## 5. Acquired & Existing Local 3D Assets (Ready on Disk)",
        f"- **MahabharataWorld Unreal Project (`Documents/Unreal Projects/MahabharataWorld/Content`):** `{sum(mw_counts.values())}` files (`Hastinapur`: {mw_counts.get('Hastinapur',0)}, `Kurukshetra`: {mw_counts.get('Kurukshetra',0)}, `Cities`: {mw_counts.get('Cities',0)})",
        f"- **Poly Haven CC0 (`MAHABHARATA_STUDIO/02_BLENDER/`):** `{len(ph_manifest.get('models', []))}` 2K `.blend` props & nature kits + `{len(ph_manifest.get('textures', []))}` 2K PBR texture blends + `{len(ph_manifest.get('hdris', []))}` 2K dawn/dusk/storm HDRIs (`CC0 1.0`, commercially safe)",
        f"- **NVIDIA SimReady Central (`MAHABHARATA_STUDIO/02_BLENDER/Props/NVIDIA_SimReady/`):** `{len(nv_manifest.get('simready', []))}` curated OpenUSD clay/copper/decor/stool props (`CC BY 4.0` per `.metadata/LICENSE.txt` — attribute NVIDIA SimReady), compiled into `nvidia_simready_vedic_props.blend` via `import_usd_prop.py`",
        f"- **NVIDIA Omniverse OpenUSD GitHub Samples (`03_UNREAL/NVIDIA_OpenUSD_Samples/`):** `{len(nv_manifest.get('omniverse_github', []))}` OpenUSD sample scene/material files",
        "- **Epic Fab Marketplace (`fab.com` / `VaultCache/FabLibrary`):** Currently `0` downloaded listings (`listings_v1.db` empty) — requires interactive sign-in & EULA claim inside Epic account / UE 5.8 (`Window -> Fab`) for `FAB-01`..`FAB-06`.",
        "",
        "## 6. Local Non-Committed Database & Shareable Export Paths",
        f"- **SQLite DB:** `{db_path}`",
        f"- **Sanitized CSV (safe to share externally):** `{sanitized_refs_csv}`",
        f"- **ChatGPT 9-Field Concept->Asset CSV:** `{mapping_csv}`",
        f"- **Sanitized Production JSON Bundle:** `{bundle_json}`",
    ]
    (LIB_DIR / "ASSET_AND_FAB_MATRIX.md").write_text("\n".join(matrix_lines) + "\n", encoding="utf-8")

    # Quick DB sanity verify
    counts = {}
    for tbl in ('"references"', "techniques", "concepts", "assets", "shots", "shot_assets", "asset_concepts"):
        counts[tbl.strip('"')] = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    conn.close()

    print("=== BUILD_PROD_DB COMPLETE ===")
    print("SQLite DB:", db_path)
    print("Table counts:", counts)
    print("CSV written:", LIB_DIR / "04_shots.csv", f"({len(shots_csv_rows)-1} rows)")
    print("CSV written:", LIB_DIR / "05_assets.csv", f"({len(assets_csv_rows)-1} rows)")
    print("Matrix written:", LIB_DIR / "ASSET_AND_FAB_MATRIX.md")
    print("Sanitized export:", bundle_json)


if __name__ == "__main__":
    build()

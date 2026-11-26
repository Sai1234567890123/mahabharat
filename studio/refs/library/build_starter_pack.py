#!/usr/bin/env python3
"""Generate the 6 Mahabharata Reference Library CSV templates and optional local MAHABHARATA_STUDIO starter pack ZIP."""
import argparse
import csv
import pathlib
import shutil
import zipfile

HERE = pathlib.Path(__file__).resolve().parent

DATASETS = {
    "01_references.csv": [
        ["reference_id", "instagram_url", "creator_username", "saved_collection", "date_added", "access_status",
         "primary_category", "secondary_tags", "subject", "timestamps_reviewed", "analysis_status",
         "priority_score", "mahabharata_scene_idea", "notes", "rights_notes"],
        ["REF-0001", "", "", "", "", "NEEDS_REVIEW", "", "", "", "", "PENDING", "", "", "", ""],
    ],
    "02_analysis_cards.csv": [
        ["reference_id", "visible_action", "shot_scale", "camera_angle", "camera_movement", "composition",
         "lighting", "palette", "atmosphere", "subject_motion", "emotional_effect", "blender_tasks",
         "unreal_tasks", "three_original_scene_uses", "difficulty_1_to_5", "reusability_1_to_5",
         "feasibility_1_to_5", "originality_cautions", "reviewer", "review_date"],
        ["REF-0001", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ],
    "03_concepts.csv": [
        ["concept_id", "source_reference_ids", "concept_title", "episode", "scene", "original_shot_description",
         "story_purpose", "camera_plan", "animation_requirements", "lighting_plan", "vfx_requirements",
         "required_assets", "originality_review", "approval_status"],
        ["CON-0001", "REF-0001", "", "EP001", "", "", "", "", "", "", "", "", "PENDING", "DRAFT"],
    ],
    "04_shots.csv": [
        ["shot_id", "episode", "sequence", "scene", "duration_seconds", "shot_description", "character_ids",
         "environment_id", "concept_ids", "camera_plan", "animation_status", "lighting_status", "vfx_status",
         "render_status", "edit_status", "priority", "notes"],
        ["EP001_SEQ001_SH001", "EP001", "SEQ001", "", "5", "", "", "", "CON-0001", "",
         "NOT_STARTED", "NOT_STARTED", "NOT_STARTED", "NOT_STARTED", "NOT_STARTED", "HIGH", ""],
    ],
    "05_assets.csv": [
        ["asset_id", "asset_name", "asset_type", "blender_file", "unreal_asset_path", "version", "dependencies",
         "rig_status", "material_status", "optimization_status", "reuse_scope", "source_or_license", "status", "notes"],
        ["AST-0001", "", "CHARACTER", "", "", "v001", "", "NOT_APPLICABLE", "NOT_STARTED", "NOT_STARTED",
         "SERIES", "", "PLANNED", ""],
    ],
    "06_tag_dictionary.csv": [
        ["tag_group", "tag", "meaning"],
        ["PRIMARY_CATEGORY", "CHARACTER_DESIGN", "Faces, anatomy, costume, armour, silhouette"],
        ["PRIMARY_CATEGORY", "ENVIRONMENT", "Palaces, forests, cities, temples, battlefields"],
        ["PRIMARY_CATEGORY", "COMBAT_ANIMATION", "Attacks, dodges, impacts, weapon movement"],
        ["PRIMARY_CATEGORY", "LIGHTING", "Rim light, backlight, firelight, moonlight"],
        ["PRIMARY_CATEGORY", "VFX", "Particles, energy, fire, dust, lightning"],
        ["PRIMARY_CATEGORY", "CINEMATOGRAPHY", "Framing, angles, tracking, orbit, crane"],
        ["PRIMARY_CATEGORY", "FACIAL_ANIMATION", "Expressions, eyes, lip sync"],
        ["PRIMARY_CATEGORY", "CROWD_ARMIES", "Crowds, formations, marching, cavalry"],
        ["PRIMARY_CATEGORY", "VEHICLES_ANIMALS", "Chariots, horses, elephants"],
        ["PRIMARY_CATEGORY", "ART_DIRECTION", "Materials, painterly look, colour language"],
        ["PRIMARY_CATEGORY", "SCENE_DIRECTION", "Reveals, tension, entrances, emotional beats"],
        ["PRIMARY_CATEGORY", "EDITING_TRANSITIONS", "Cuts, match cuts, montage, pacing"],
        ["CAMERA_MOVEMENT", "STATIC", "Camera remains fixed"],
        ["CAMERA_MOVEMENT", "DOLLY_IN", "Camera moves toward subject"],
        ["CAMERA_MOVEMENT", "ORBIT", "Camera moves around subject"],
        ["CAMERA_MOVEMENT", "TRACKING", "Camera follows subject"],
        ["CAMERA_MOVEMENT", "CRANE_OR_AERIAL", "Vertical or elevated camera move"],
        ["ACCESS_STATUS", "ACCESSIBLE", "Opens through normal permitted access"],
        ["ACCESS_STATUS", "LOGIN_REQUIRED", "Requires login; do not bypass"],
        ["ACCESS_STATUS", "UNAVAILABLE", "Private, deleted, restricted or inaccessible"],
        ["ANALYSIS_STATUS", "PENDING", "Not yet reviewed"],
        ["ANALYSIS_STATUS", "NEEDS_VISUAL_INPUT", "URL alone was insufficient"],
        ["ANALYSIS_STATUS", "ANALYSED", "Analysis card completed"],
        ["ANALYSIS_STATUS", "APPROVED", "Human reviewed and accepted"],
    ],
}

STUDIO_FOLDERS = [
    "00_REFERENCE_LIBRARY/01_URL_REGISTER",
    "00_REFERENCE_LIBRARY/02_PERMITTED_SCREENSHOTS",
    "00_REFERENCE_LIBRARY/03_ANALYSIS_CARDS",
    "00_REFERENCE_LIBRARY/04_REFERENCE_BOARDS",
    "00_REFERENCE_LIBRARY/05_ORIGINAL_CONCEPTS",
    "01_VISUAL_BIBLE/Character_Design",
    "01_VISUAL_BIBLE/Costume_Design",
    "01_VISUAL_BIBLE/Architecture",
    "01_VISUAL_BIBLE/Weapons",
    "01_VISUAL_BIBLE/Lighting",
    "01_VISUAL_BIBLE/Colour_Palettes",
    "02_BLENDER/Characters",
    "02_BLENDER/Environments",
    "02_BLENDER/Props",
    "02_BLENDER/Rigging",
    "02_BLENDER/Animation",
    "03_UNREAL/Materials",
    "03_UNREAL/VFX",
    "03_UNREAL/Sequencer",
    "03_UNREAL/Lighting",
    "04_EPISODES/EP001",
    "04_EPISODES/EP002",
    "04_EPISODES/EP003",
    "05_AUDIO",
    "06_RENDERS",
    "07_BACKUPS",
]


def write_csvs(target_dir: pathlib.Path):
    target_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in DATASETS.items():
        with (target_dir / name).open("w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--studio-dir", help="Optional local MAHABHARATA_STUDIO root to scaffold and zip")
    args = ap.parse_args()

    write_csvs(HERE)
    print(f"Wrote 6 CSV templates into {HERE}")

    if args.studio_dir:
        root = pathlib.Path(args.studio_dir)
        for rel in STUDIO_FOLDERS:
            (root / rel).mkdir(parents=True, exist_ok=True)
        reg = root / "00_REFERENCE_LIBRARY" / "01_URL_REGISTER"
        write_csvs(reg)
        for doc in ("README_START_HERE.md", "ANALYSIS_CARD_TEMPLATE.md", "ingest_instagram_saved.py"):
            src = HERE / doc
            if src.exists():
                dst = (root / "00_REFERENCE_LIBRARY" / "03_ANALYSIS_CARDS" / doc) if doc == "ANALYSIS_CARD_TEMPLATE.md" else (reg / doc)
                shutil.copy2(src, dst)
                if doc == "README_START_HERE.md":
                    shutil.copy2(src, root / doc)
        zip_path = root / "mahabharat_reference_starter_pack.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for name in list(DATASETS.keys()) + ["README_START_HERE.md", "ANALYSIS_CARD_TEMPLATE.md", "ingest_instagram_saved.py"]:
                z.write(HERE / name, arcname=f"mahabharata_reference_starter/{name}")
        print(f"Scaffolded {root} and created {zip_path}")


if __name__ == "__main__":
    main()

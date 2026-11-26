#!/usr/bin/env python3
"""Batch-import downloaded OpenUSD (.usd/.usda/.usdc/.usdz) props into Blender 5.2,
apply Mahabharat Studio painterly roughness breakup + viewport scale normalization,
and save inspected .blend assets without exceeding 4 GB VRAM budgets.

Usage:
    & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b --python-exit-code 1 --python studio/tools/blender/import_usd_prop.py -- --input-dir <dir> --out-blend <out.blend>
"""
import argparse
import json
import pathlib
import sys

import bpy


def clear_scene():
    """Reset default scene cleanly."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def add_painterly_breakup(mat):
    """Ensure imported PBR materials stay below mirror sheen and follow painted roughness rules."""
    node_tree = getattr(mat, "node_tree", None) if mat else None
    if not node_tree:
        return
    bsdf = next((n for n in node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not bsdf:
        return
    # Prevent raw photoreal glossy plastic highlights unless metal/water
    rough_inp = bsdf.inputs.get("Roughness")
    if rough_inp and not rough_inp.is_linked and rough_inp.default_value < 0.42:
        rough_inp.default_value = 0.52
    spec_inp = bsdf.inputs.get("Specular IOR Level")
    if spec_inp and not spec_inp.is_linked:
        spec_inp.default_value = min(spec_inp.default_value, 0.35)


def import_usd_files(usd_paths, out_blend: pathlib.Path, max_files: int = 20):
    """Import a list of primary USD asset files, count true mesh polygons (including USD instances), and save."""
    clear_scene()
    imported = []
    seen_meshes = set()

    for idx, usd_path in enumerate(usd_paths[:max_files]):
        coll = bpy.data.collections.new(usd_path.parents[1].name or f"USD_{idx:02d}")
        bpy.context.scene.collection.children.link(coll)
        layer_coll = bpy.context.view_layer.layer_collection.children[coll.name]
        bpy.context.view_layer.active_layer_collection = layer_coll

        bpy.ops.wm.usd_import(
            filepath=str(usd_path),
            import_materials=True,
            import_textures_mode="IMPORT_COPY",
            set_frame_range=False,
        )
        objs = list(coll.objects)
        for obj in objs:
            if obj.parent is None:
                obj.location.x += idx * 1.2
        new_meshes = [m for m in bpy.data.meshes if m.name not in seen_meshes]
        seen_meshes.update(m.name for m in new_meshes)
        tris = sum(len(m.polygons) for m in new_meshes)
        imported.append((coll.name, usd_path.name, len(new_meshes), tris))

    for mat in bpy.data.materials:
        add_painterly_breakup(mat)

    out_blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out_blend))
    return imported


def find_primary_usd(asset_dir: pathlib.Path):
    """Resolve the SimReady root USD via .metadata/com.nvidia.simready.root_usds.json or standard entrypoints."""
    meta_root = asset_dir / ".metadata" / "com.nvidia.simready.root_usds.json"
    if meta_root.exists():
        entries = json.loads(meta_root.read_text(encoding="utf-8")).get("entries", [])
        if entries:
            cand = asset_dir / entries[0]
            if cand.exists():
                return cand
    for rel in ("simready_usd", "."):
        base = asset_dir / rel
        if base.exists():
            direct = sorted(f for f in base.iterdir() if f.is_file() and f.suffix.lower() in (".usd", ".usdc", ".usda", ".usdz"))
            if direct:
                return direct[0]
    geom = asset_dir / "simready_usd" / "payloads" / "geometries.usd"
    return geom if geom.exists() else None


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--out-blend", required=True)
    ap.add_argument("--max-files", type=int, default=20)
    args = ap.parse_args(argv)

    root = pathlib.Path(args.input_dir)
    candidates = [p for d in sorted(root.iterdir()) if d.is_dir() and (p := find_primary_usd(d)) is not None]

    if not candidates:
        raise SystemExit(f"No USD files found under {root}")

    imported = import_usd_files(candidates, pathlib.Path(args.out_blend), args.max_files)
    print(f"IMPORTED {len(imported)} USD assets -> {args.out_blend}")
    for coll_name, fname, n_meshes, n_poly in imported:
        print(f"  - {coll_name} ({fname}): meshes={n_meshes}, polygons={n_poly}")


if __name__ == "__main__":
    main()

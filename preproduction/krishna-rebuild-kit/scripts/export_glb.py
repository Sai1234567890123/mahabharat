"""Export the Krishna model (body, head, feather, cloth, rig) to a single GLB (headless Blender).

Usage:
  blender -b --python scripts/export_glb.py -- IN.blend OUT.glb
"""

import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1 :]
in_blend, out_glb = argv[0], argv[1]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
keep = {"KRISHNA_rig", "KRISHNA_body", "KRISHNA_head", "KRISHNA_feather", "KRISHNA_cloth_dhoti", "KRISHNA_cloth_shawl", "KRISHNA_mouth_cavity", "KRISHNA_teeth_upper", "KRISHNA_teeth_lower", "KRISHNA_tongue"}
bpy.ops.object.select_all(action="DESELECT")
for o in bpy.data.objects:
    if o.name in keep:
        o.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects["KRISHNA_rig"]
bpy.ops.export_scene.gltf(
    filepath=os.path.abspath(out_glb),
    export_format="GLB",
    use_selection=True,
    export_apply=False,
    export_skins=True,
    export_morph=True,
    export_image_format="JPEG",
    export_jpeg_quality=85,
)
print("GLB", os.path.abspath(out_glb), os.path.getsize(out_glb), flush=True)

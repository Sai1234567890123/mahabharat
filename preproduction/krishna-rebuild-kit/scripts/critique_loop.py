"""One round of the visual critique loop for the Krishna model (headless Blender + Python).

Usage (Blender renders, then Python scores):
  blender -b --python scripts/critique_loop.py -- MODEL.blend OUT_DIR
  python scripts/critique_loop.py --score OUT_DIR

Render: front and side, neutral pose, Workbench, fixed camera. Score: silhouette IoU of the front render
against the approved close-up's subject mask, plus a crude colour check (gold and skin shares). Writes
OUT_DIR/critique.md with the numbers, so each round records what changed.
"""

import math
import os
import sys

if "--score" in sys.argv:
    import numpy as np
    from PIL import Image

    out = sys.argv[sys.argv.index("--score") + 1]
    ref = np.asarray(Image.open(os.path.join(os.path.dirname(__file__), "..", "art", "krishna", "krishna_closeup_approved.png")).convert("RGB").resize((400, 400))).astype(float)
    dark = ref.sum(2) < 120
    subj_ref = ~dark  # the approved close-up has a near-black background
    front = np.asarray(Image.open(os.path.join(out, "front.png")).convert("RGB").resize((400, 400))).astype(float)
    grey = np.abs(front - front[0, 0]).sum(2) > 40
    iou = (subj_ref & grey).sum() / max((subj_ref | grey).sum(), 1)
    gold = ((front[..., 0] > 150) & (front[..., 1] > 110) & (front[..., 2] < 110)).mean()
    skin = ((front[..., 0] > 120) & (front[..., 1] > 80) & (front[..., 2] > 60) & (front[..., 0] > front[..., 2] + 20)).mean()
    with open(os.path.join(out, "critique.md"), "w", encoding="utf-8") as f:
        f.write("# Critique round\n\n")
        f.write("- Silhouette IoU vs approved close-up: %.2f\n" % iou)
        f.write("- Gold share of front render: %.2f\n" % gold)
        f.write("- Skin share of front render: %.2f\n" % skin)
    print("IoU %.2f gold %.2f skin %.2f" % (iou, gold, skin))
    sys.exit(0)

import bpy

argv = sys.argv[sys.argv.index("--") + 1 :]
model, out = argv[0], argv[1]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(model))
scn = bpy.context.scene
for o in scn.objects:
    if o.type == "ARMATURE":
        o.hide_render = True
scn.render.engine = "BLENDER_WORKBENCH"
sh = scn.display.shading
sh.light = "FLAT"
sh.color_type = "TEXTURE"
scn.render.resolution_x = 400
scn.render.resolution_y = 400
scn.world = scn.world or bpy.data.worlds.new("w")
scn.world.color = (0.6, 0.6, 0.6)
cd = bpy.data.cameras.new("cam")
cd.type = "ORTHO"
cd.ortho_scale = 2.4
cam = bpy.data.objects.new("cam", cd)
scn.collection.objects.link(cam)
scn.camera = cam
cam.location = (0, -6, 0.95)
cam.rotation_euler = (math.radians(90), 0, 0)
scn.render.filepath = os.path.join(out, "front.png")
bpy.ops.render.render(write_still=True)
cam.location = (6, 0, 0.95)
cam.rotation_euler = (math.radians(90), 0, math.radians(90))
scn.render.filepath = os.path.join(out, "side.png")
bpy.ops.render.render(write_still=True)
print("RENDERED", out, flush=True)

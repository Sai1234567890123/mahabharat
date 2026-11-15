"""Check render of Arjuna's chariot with its team of four, as in concept image 42 (not an export).

  python render_combo.py <out.png> [style] [az]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy

import chariot as C
import creatures as CR
import hero_lib as H
import render_check as RC

out = os.path.abspath(sys.argv[1])
style = sys.argv[2] if len(sys.argv) > 2 else "arjuna"
az = float(sys.argv[3]) if len(sys.argv) > 3 else -84
H.reset()
car = C.build(style)
team = CR.horse_team(*{"arjuna": ("MAT_White", "MAT_Gold", "MAT_Red"),
                       "bhishma": ("MAT_White", "MAT_Silver", "MAT_Cream"),
                       "duryodhana": ("MAT_Bay", "MAT_Bronze", "MAT_Crimson")}.get(style, ("MAT_White", "MAT_Gold", "MAT_Red")))
for o in bpy.context.scene.objects:
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
bpy.ops.object.shade_smooth_by_angle(angle=0.7)
RC.render(out, res=(1800, 1050), samples=48, az=az, el=5, dist_mul=1.22, lens=60)

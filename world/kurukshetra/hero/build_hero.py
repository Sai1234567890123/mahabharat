"""Build every hero battle asset, export FBX + .blend, and render a check image of each.

  blender -b -P build_hero.py -- <out_dir> [asset names...]      (or: python build_hero.py <out_dir> ...)

Output: <out_dir>/SM_<name>.fbx, SM_<name>.blend, manifest.json and checks/<name>.png
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy

import assets as A
import chariot as C
import creatures as CR
import hero_lib as H
import render_check as RC

# name: (builder, category, render kwargs)
ASSETS = {
    "krk_arjuna_chariot": (lambda: C.build("arjuna"), "hero", dict(az=-72, el=8, res=(1400, 1050))),
    "krk_bhishma_chariot": (lambda: C.build("bhishma"), "hero", dict(az=-72, el=8, res=(1400, 1050))),
    "krk_duryodhana_chariot": (lambda: C.build("duryodhana"), "hero", dict(az=-72, el=8, res=(1400, 1050))),
    "krk_rank_chariot": (A.rank_chariot, "army", dict(az=-72, el=8, res=(1400, 1050))),
    "krk_rank_chariot_red": (lambda: A.rank_chariot(style="rank_kaurava"), "army", dict(az=-72, el=8, res=(1400, 1050))),
    "krk_ape_banner": (A.ape_banner, "hero", dict(az=-25, el=4, res=(800, 1400), dist_mul=0.9)),
    "krk_kaurava_soldier": (lambda: A.soldier("kaurava", "attention"), "crowd", dict(az=-30, el=6, res=(800, 1100))),
    "krk_kaurava_soldier_b": (lambda: A.soldier("kaurava", "advance"), "crowd", dict(az=-50, el=6, res=(1000, 1000))),
    "krk_pandava_archer": (lambda: A.soldier("pandava", "attention"), "crowd", dict(az=-30, el=6, res=(800, 1100))),
    "krk_pandava_archer_b": (lambda: A.soldier("pandava", "advance"), "crowd", dict(az=-50, el=6, res=(1000, 1000))),
    "krk_war_tent": (A.war_tent, "camp", dict(az=-32, el=14, res=(1300, 1000))),
    "krk_war_tent_red": (lambda: A.war_tent("MAT_Crimson", "MAT_Bronze"), "camp", dict(az=-32, el=14, res=(1300, 1000))),
    "krk_war_drum_cart": (A.drum_cart, "hero", dict(az=-55, el=12, res=(1300, 1000))),
    "krk_chariot_wreck": (A.chariot_wreck, "battle", dict(az=-50, el=20, res=(1300, 1000))),
    # batch 2 (13 Nov): animals, crews and battle props after concept images 24, 33, 34, 40 and 42
    "krk_war_elephant": (lambda: CR.elephant("pandava", "walk"), "army", dict(az=-55, el=6, res=(1300, 1100))),
    "krk_war_elephant_red": (lambda: CR.elephant("kaurava", "charge"), "army", dict(az=-55, el=6, res=(1300, 1100))),
    "krk_horse_white": (lambda: CR.horse("MAT_White", "MAT_Gold", "MAT_Red"), "army", dict(az=-65, el=6, res=(1200, 1000))),
    "krk_horse_team": (lambda: CR.horse_team("MAT_White", "MAT_Gold", "MAT_Red"), "hero", dict(az=-55, el=10, res=(1400, 1000))),
    "krk_horse_team_dark": (lambda: CR.horse_team("MAT_Bay", "MAT_Bronze", "MAT_Crimson"), "army",
                            dict(az=-55, el=10, res=(1400, 1000))),
    "krk_kaurava_cavalry": (lambda: A.cavalry("kaurava"), "crowd", dict(az=-60, el=6, res=(1200, 1000))),
    "krk_pandava_cavalry": (lambda: A.cavalry("pandava"), "crowd", dict(az=-60, el=6, res=(1200, 1000))),
    "krk_conch": (A.conch, "prop", dict(az=-78, el=22, res=(1000, 800))),
    "krk_gada": (A.gada, "prop", dict(az=-40, el=22, res=(1200, 800))),
    "krk_great_bow": (A.great_bow, "prop", dict(az=-40, el=28, res=(1200, 800))),
    "krk_arrow_cluster": (A.arrow_cluster, "battle", dict(az=-40, el=14, res=(1000, 800))),
}


# Chariots keep the origin midway between the axles (yoke at Blender y = -4.7, i.e. 4.7 m ahead in Unreal),
# so the layout can stand the horses under the yoke and a rider on the seat.
KEEP_ORIGIN = {"krk_arjuna_chariot", "krk_bhishma_chariot", "krk_duryodhana_chariot", "krk_rank_chariot",
               "krk_rank_chariot_red", "krk_horse_team", "krk_horse_team_dark"}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    out_dir = os.path.abspath(argv[0] if argv else "hero_out")
    only = [a for a in argv[1:] if not a.startswith("--")]
    do_render = "--no-render" not in argv
    os.makedirs(os.path.join(out_dir, "checks"), exist_ok=True)
    mpath = os.path.join(out_dir, "manifest.json")
    manifest = json.load(open(mpath))["assets"] if os.path.exists(mpath) else []
    for name, (fn, cat, rk) in ASSETS.items():
        if only and name not in only:
            continue
        t = time.time()
        H.reset()
        o = fn()
        for stray in [x for x in bpy.context.scene.objects if x is not o]:      # nothing but the asset is exported
            bpy.data.objects.remove(stray)
        H.ground_and_centre(o, centre_xy=name not in KEEP_ORIGIN)
        manifest = [m for m in manifest if m["name"] != name]
        H.export(o, name, out_dir, cat, manifest)
        if do_render:
            RC.render(os.path.join(out_dir, "checks", f"{name}.png"), samples=40, lens=60, **rk)
        print(f"DONE {name} in {time.time() - t:.0f}s")
        with open(mpath, "w") as f:
            json.dump({"kit": "KurukshetraHero", "units": "m", "front": "-Y",
                       "materials": {k: {"srgb": list(v[0]), "metallic": v[1], "roughness": v[2]}
                                     for k, v in H.PAL.items()},
                       "assets": manifest}, f, indent=2)


if __name__ == "__main__":
    main()

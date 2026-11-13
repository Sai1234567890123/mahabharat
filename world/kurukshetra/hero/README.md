# Kurukshetra hero battle models (Blender only, no cloud)

Built on 13 Nov 2026 after the GCP credits ran out. Every model is made by a Python script with Blender
(`pip install bpy`, or `blender -b -P`), from sai's concept paintings (images 6, 42 and 46 for the chariot,
35 for Bhishma's silver car, 34 and 40 for the battle). No TRELLIS, no image model, no spend.

```
python build_hero.py <out_dir>                     # all 25 models, FBX + .blend + check render each
python build_hero.py <out_dir> krk_arjuna_chariot  # one model
python build_hero.py <out_dir> --no-render         # skip the Cycles check renders
```

| Model | Triangles | Notes |
|---|---|---|
| `krk_arjuna_chariot` | 397k | gold, four wheels, lion-flanked box, white parasol, green ape flag, ape on the finial |
| `krk_bhishma_chariot` | 383k | silver and white, gold panels, palmyra standard on a mast |
| `krk_duryodhana_chariot` | 385k | bronze and crimson, serpent standard |
| `krk_rank_chariot`, `krk_rank_chariot_red` | 36k | lighter cars for the army lines (Pandava gold, Kaurava bronze), with a driver and a bowman |
| `krk_ape_banner` | 34k | 10.6 m free-standing ape standard with hanging banner |
| `krk_pandava_archer`, `_b` | 2.9k | at rest, and bow drawn (front ranks) |
| `krk_kaurava_soldier`, `_b` | 2.9k | spear upright, and spear levelled (front ranks) |
| `krk_war_tent`, `krk_war_tent_red` | 15k | 7.2 m striped command pavilion |
| `krk_war_drum_cart` | 31k | kettle drum and two great horns on a cart |
| `krk_chariot_wreck` | 155k | overturned rank chariot with arrows, for battle shots |
| `krk_war_elephant`, `krk_war_elephant_red` | 60k | batch 2: armoured war elephant, caparison, bell collar, archers' tower with two bowmen (Kaurava one has the trunk raised) |
| `krk_horse_white` | 18k | batch 2: chariot horse with gold harness |
| `krk_horse_team`, `krk_horse_team_dark` | 60k | batch 2: four horses abreast with traces and reins; shares the chariot's origin, so it is placed with the chariot's transform |
| `krk_kaurava_cavalry`, `krk_pandava_cavalry` | 15k | batch 2: lancer on a bay, horse archer on a dun |
| `krk_conch`, `krk_gada`, `krk_great_bow`, `krk_arrow_cluster` | 1k to 3k | batch 2: Panchajanya, Bhima's mace, Gandiva, arrows stuck in the ground |

Conventions (same as `world/ASSEMBLY_METHOD.md`): metres, Z up, base on Z=0, front toward -Y in Blender
(+Y in Unreal), one mesh per `SM_<name>.fbx`. Chariots and horse teams keep their origin midway between the
chariot's axles, so a team placed with its chariot's transform stands under the yoke (4.7 m ahead, collars at
x = ±0.375 and ±1.125 m, yoke 1.66 m high for 1.55 m horses). Everything else is centred.

Materials are 20 flat slots (`MAT_Gold`, `MAT_Silver`, `MAT_Crimson`, ...). Their colour, metallic and
roughness are written into `manifest.json`, and `ue_assemble_kurukshetra.py` builds matching `M_KRKH_*`
master materials from it. There are no textures or UV maps yet: carved relief, cloth weave and dirt are the
next pass (Unreal materials or a texture bake).

| File | What it holds |
|---|---|
| `hero_lib.py` | palette, mesh helpers (lathe, tube, extrude, scroll), `blob()` for sculpted forms, export |
| `parts.py` | lion, ape, serpent, wheel, parasol, flag with emblem, bells and garlands |
| `chariot.py` | the war chariot and its five styles |
| `assets.py` | banner, soldiers, war tent, drum cart, wreck, cavalry, conch, mace, bow, arrows |
| `creatures.py` | horse, team of four, war elephant and its tower |
| `render_combo.py` | check render of a hero chariot with its team |
| `render_check.py` | Cycles CPU check render |
| `checks/` | the check renders and the contact sheet next to the paintings |

Known weak points: the soldiers are simple figures meant for crowd distance only, and the lions and ape are
smooth sculpted forms without fur or carved detail.

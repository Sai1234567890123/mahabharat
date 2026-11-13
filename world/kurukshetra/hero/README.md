# Kurukshetra hero battle models (Blender only, no cloud)

Built on 13 Nov 2026 after the GCP credits ran out. Every model is made by a Python script with Blender
(`pip install bpy`, or `blender -b -P`), from sai's concept paintings (images 6, 42 and 46 for the chariot,
35 for Bhishma's silver car, 34 and 40 for the battle). No TRELLIS, no image model, no spend.

```
python build_hero.py <out_dir>                     # all 14 models, FBX + .blend + check render each
python build_hero.py <out_dir> krk_arjuna_chariot  # one model
python build_hero.py <out_dir> --no-render         # skip the Cycles check renders
```

| Model | Triangles | Notes |
|---|---|---|
| `krk_arjuna_chariot` | 397k | gold, four wheels, lion-flanked box, white parasol, green ape flag, ape on the finial |
| `krk_bhishma_chariot` | 383k | silver and white, gold panels, palmyra standard on a mast |
| `krk_duryodhana_chariot` | 385k | bronze and crimson, serpent standard |
| `krk_rank_chariot`, `krk_rank_chariot_red` | 30k | lighter cars for the army lines (Pandava gold, Kaurava bronze) |
| `krk_ape_banner` | 34k | 10.6 m free-standing ape standard with hanging banner |
| `krk_pandava_archer`, `_b` | 2.9k | at rest, and bow drawn (front ranks) |
| `krk_kaurava_soldier`, `_b` | 2.9k | spear upright, and spear levelled (front ranks) |
| `krk_war_tent`, `krk_war_tent_red` | 15k | 7.2 m striped command pavilion |
| `krk_war_drum_cart` | 31k | kettle drum and two great horns on a cart |
| `krk_chariot_wreck` | 155k | overturned rank chariot with arrows, for battle shots |

Conventions (same as `world/ASSEMBLY_METHOD.md`): metres, Z up, base on Z=0, front toward -Y in Blender
(+Y in Unreal), one mesh per `SM_<name>.fbx`. Chariots keep their origin midway between the axles, so the
yoke is 4.7 m ahead and the four collars sit at x = ±0.375 and ±1.125 m. Everything else is centred.

Materials are 16 flat slots (`MAT_Gold`, `MAT_Silver`, `MAT_Crimson`, ...). Their colour, metallic and
roughness are written into `manifest.json`, and `ue_assemble_kurukshetra.py` builds matching `M_KRKH_*`
master materials from it. There are no textures or UV maps yet: carved relief, cloth weave and dirt are the
next pass (Unreal materials or a texture bake).

| File | What it holds |
|---|---|
| `hero_lib.py` | palette, mesh helpers (lathe, tube, extrude, scroll), `blob()` for sculpted forms, export |
| `parts.py` | lion, ape, serpent, wheel, parasol, flag with emblem, bells and garlands |
| `chariot.py` | the war chariot and its five styles |
| `assets.py` | banner, soldiers, war tent, drum cart, wreck |
| `render_check.py` | Cycles CPU check render |
| `checks/` | the check renders and the contact sheet next to the paintings |

Known weak points: the soldiers are simple figures meant for crowd distance only, and the lions and ape are
smooth sculpted forms without fur or carved detail.

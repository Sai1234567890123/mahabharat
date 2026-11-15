# Kurukshetra world plan (world 1 in the bible)

Hastinapur is done. Kurukshetra is next because the bible ranks it first (the action hub) and the pilot "The First Conch" happens there. The old Blender blockout was deleted, so this starts clean. The method is the same as Hastinapur (`world/ASSEMBLY_METHOD.md`): concept image per asset, score 80+, build the model (TRELLIS.2 or procedural Blender), assemble in Unreal, score the view against a picked painting, fix the biggest gap, repeat.

## 1. What the field must show (from the bible and the pilot canon)

- An endless pale-ochre dusty plain with trampled grass and chariot ruts, dust always moving low.
- Two hosts facing each other across an empty middle strip. Pandava on screen left, saffron and gold, upright standards. Kaurava on screen right, deep red and bronze, denser and darker.
- Arjuna's ape banner is the tallest standard on the field.
- Formations 1 to 2 km wide with banner lines and gaps for chariot lanes.
- Low sun at 8 to 15 degrees, god rays through dust, smoke from fires on the horizon.
- Palette: dust #B48A5A, sun #FFC37A, shadow #3B2A1E, blood red #7A1A12.
- Reference paintings: bible images 6, 24, 25, 33, 34, 35, 36, 37, 40, 42, 46, plus the expansion paintings in `world/concepts/expansion` (exp_24 is the only one at 80+ so far).

## 2. Assets

### Already built, reuse (no GPU needed)

| GLB | Use |
|---|---|
| hst_arjuna_chariot | Hero car (Krishna and Arjuna), centre strip |
| hst_war_elephant | Both armies; Kaurava copies get a red and bronze material swap in Unreal |
| hst_white_horse | Four per chariot, plus cavalry |
| hst_royal_chariot | Generic Pandava chariots in the ranks |

### New TRELLIS.2 models (carved or organic), in build order

| # | Asset | Why it is needed |
|---|---|---|
| K01 | Ape (Hanuman) banner standard | Tallest standard on the field, pilot SH020 |
| K02 | Bhishma's white chariot with gold palmyra standard | Pilot SH030 and SH040 |
| K03 | Duryodhana's crimson chariot with serpent standard | Kaurava lead car |
| K04 | Kaurava footsoldier (spear, shield, red and bronze) | Crowd instancing, one model |
| K05 | Pandava archer footsoldier (saffron and gold) | Crowd instancing, one model |
| K06 | Royal war tent (shibira pavilion) | Camps behind each host |
| K07 | War drum cart (dundubhi) | Kaurava drums and horns, SH040 |
| K08 | Broken chariot wreck | Later war-day shots |

### Procedural Blender kit (runs on the PC, no GPU queue)

- Terrain plain, 6 km by 4 km, with ruts and a low ridge line on the horizon.
- Banner pole kit: saffron, red, green and white flags, two heights.
- Camp kit: plain tents, palisade, weapon racks, spear and shield stacks.
- Army block helper: places soldier instances in formations with chariot lanes.
- Dust, smoke, god rays and arrow streaks are Unreal effects (Niagara and exponential height fog), not models.

## 3. Unreal

- Level `L_Kurukshetra` in project `MahabharataWorld`, assets under `/Game/Kurukshetra/`.
- Labels `KRKP_` (procedural) and `KRK3D_` (TRELLIS.2), same re-run rule as Hastinapur.
- Army counts start low because the PC has 7.5 GB RAM: about 2,000 instanced soldiers per side, raised only if the editor stays stable.
- Three check cameras: the wide establishing view of both hosts, the hero chariot in the empty strip (low, 1 to 3 m), and Bhishma's car across the field.

## 4. What counts as done

1. Every K asset has a concept image scoring 80+ with gemini-4-argon.
2. Every K asset is a GLB, cleaned, real-world scale, imported with Nanite.
3. `L_Kurukshetra` is built with both hosts, the hero chariots, camps and atmosphere.
4. The wide establishing view scores 60+ against the picked painting (average of two scorings). Hastinapur finished at 58.
5. The three check cameras exist and match the pilot shot framings.

## 5. Cost (needs sai's go before any GPU start)

- TRELLIS.2: 8 models at about 10 minutes each, one job at a time per L4, about 1.5 to 2 hours of L4 time, about $1.50 to $2.00 of credit. The VM is stopped as soon as the batch ends.
- Concept images: 8 assets with about 3 tries each on gemini-3.1-flash-image, a few cents.
- No snapshot restores and no zone scanning, per `10-cost-and-safety-rules.md`.

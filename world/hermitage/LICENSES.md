# S1E01 `sc01` Vedic Hermitage Set — Asset Licenses & Credits

Every external 3D asset, PBR material, and HDRI used inside `world/hermitage/hermitage_set.blend` is strictly **CC0 1.0 Universal (Public Domain)** from **Poly Haven** (`https://polyhaven.com`), plus period-authentic procedural geometry built specifically for S1E01 `sc01`.

**Period & Compliance Audit (`studio/episodes/s1e01_the_scribe/canon_check.md`):**
- **No stone temples / carved stone pillars:** Replaced with earthen compacted plinths, carved mud-brick *Homa* fire altar base, open-porch *kusa*-grass thatched hut, and ancient banyan roots.
- **No idols:** `carved_wooden_elephant` and decorative animal sculptures were deliberately excluded.
- **No glass:** `brass_diya_lantern_2k.blend` (`brass_diya_lantern_glass`) and third-party glass shaders were excluded; the hero lamp is an open hammered brass/terracotta *diya* oil bowl (`Sacred_Open_Diya`).
- **No paper books:** All writing substrates are tied incised palm-leaf strips (`Talapatra`), curled birch-bark sheets (`Bhurja-patra`), and a cast bronze stylus.
- **No paid or CC BY dependencies:** Zero paid marketplace assets and zero attribution-locked third-party USD props are linked into `hermitage_set.blend`.

## Downloaded CC0 1.0 Poly Haven Assets Used in `hermitage_set.blend`

| Asset ID | Name | Author(s) | Source URL | License | Usage in Set |
|---|---|---|---|---|---|
| `stone_fire_pit` | Stone Fire Pit | Sebastian Platen | https://polyhaven.com/a/stone_fire_pit | CC0 1.0 Universal | Central Vedic Homa hearth ring inside stepped earthen altar (`Homa_FirePit_CC0`) |
| `planter_pot_clay` | Planter Pot Clay | Amal Kumar | https://polyhaven.com/a/planter_pot_clay | CC0 1.0 Universal | Terracotta hermitage clay water vessels beside hut entrance & scribe area (overridden matte clay) |
| `brass_pot_01` | Brass Pot 01 | Rico Cilliers | https://polyhaven.com/a/brass_pot_01 | CC0 1.0 Universal | Vyasa's sacred brass *kamandalu* pot beside meditation mat |
| `brass_pot_02` | Brass Pot 02 | Rico Cilliers | https://polyhaven.com/a/brass_pot_02 | CC0 1.0 Universal | Ganesha's brass water/ink vessel beside scribe station |
| `wooden_bowl_01` | Wooden Bowl 01 | Oliver Harries | https://polyhaven.com/a/wooden_bowl_01 | CC0 1.0 Universal | Carved wooden offering bowl beside Vyasa's palm-leaf bundles |
| `root_cluster_01` | Root Cluster 01 | Jenelle van Heerden, Rico Cilliers | https://polyhaven.com/a/root_cluster_01 | CC0 1.0 Universal | Ancient banyan primary buttress roots (decimated cleanly; bark shader unified) |
| `root_cluster_02` | Root Cluster 02 | Jenelle van Heerden | https://polyhaven.com/a/root_cluster_02 | CC0 1.0 Universal | Secondary sprawling banyan buttress roots anchoring riverbank |
| `boulder_01` (`LOD2`) | Boulder 01 | Rico Cilliers | https://polyhaven.com/a/boulder_01 | CC0 1.0 Universal | Natural riverbank boulders along Malini shore (`LOD2`) |
| `rock_moss_set_01` | Rock Moss Set 01 | Kless Gyzen | https://polyhaven.com/a/rock_moss_set_01 | CC0 1.0 Universal | Moss-covered riverbank rocks near left hermitage clearing |
| `fern_02` | Fern 02 | Rob Tuytel, Rico Cilliers | https://polyhaven.com/a/fern_02 | CC0 1.0 Universal | Forest floor fern silhouettes around clearing edge & huts |
| `grass_medium_02` | Grass Medium 02 | Rico Cilliers | https://polyhaven.com/a/grass_medium_02 | CC0 1.0 Universal | Wild hermitage *kusa* grass clumps along clearing border & deer pasture |
| `dry_ground_01` | Dry Ground 01 | Rob Tuytel | https://polyhaven.com/a/dry_ground_01 | CC0 1.0 Universal | Main packed earthen hermitage & riverbank terrain shader |
| `ganges_river_pebbles` | Ganges River Pebbles | Amal Kumar | https://polyhaven.com/a/ganges_river_pebbles | CC0 1.0 Universal | Malini riverbank pebble shoal strip |
| `bark_brown_01` | Bark Brown 01 | Rob Tuytel | https://polyhaven.com/a/bark_brown_01 | CC0 1.0 Universal | Ancient banyan trunk, sweeping canopy boughs, buttress & hanging aerial roots |
| `aarfontein_dawn` | Aarfontein Dawn | Greg Zaal, Jarod Guest | https://polyhaven.com/a/aarfontein_dawn | CC0 1.0 Universal | Dawn world lighting sky IBL tinted to `studio/bible.md` cool blue fill (`#3E5A86`) |

## Procedural Original Project Geometry (`build_hermitage.py`)

- `Ashram_KusaHut_Root`: Open-doorway earthen wattle hut with sal-timber verandah poles and multi-course *kusa*-grass thatched conical roof & eave straw tufts.
- `Homa_AltarStep1/2` & `Homa_Flame_Tongue_*` & `Homa_SmokePuff_*`: Stepped earthen Vedic fire altar base, Agni fire tongues, and rising leftward smoke plumes keeping center sky open for Brahma's lotus seat.
- `Sacred_Open_Diya_Root`: Turned brass/terracotta spouted oil *diya* bowl with cotton wick and dual-layer golden flame (`S11`/`S12`).
- `Mat_Kusa_*`, `PalmLeaf_*`, `BirchBark_*`, `Vedic_Bronze_Stylus`: Symmetrical *kusa* mats, incised cambered palm-leaf bundles with red cords, curled *bhurja-patra* birch-bark sheets, carved scribe board, and cast bronze stylus.
- `Ashram_SacredBanyan` canopy/boughs/aerial prop roots & `Malini_River_Water` / mist ribbons & `Deer_01_Grazing` / `Deer_02_Alert`: Stylized Vedic forest clearing, misty river, and grazing spotted *chital* deer.

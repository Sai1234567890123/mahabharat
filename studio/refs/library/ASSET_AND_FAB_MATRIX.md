# Mahabharata Production Asset Matrix & Fab / TRELLIS.2 / Reference Linker

Generated directly from `studio/refs/library/` CSVs, `studio/episodes/`, `studio/cast/`, and `studio/tools/blender/`.

## 1. Current Verified Counts
- **Catalogued Instagram References (`01_references.csv`):** `266` (`31` deeply frame-analysed, `229` pending with category/subject tags already populated)
- **Extracted Visual Techniques:** `31` (from `REF-0001`–`REF-0021`)
- **Original Scene Concepts (`03_concepts.csv`):** `93`
- **Canonical Reusable Assets (`05_assets.csv`):** `24`
- **Scripted Shots Linked (`04_shots.csv`):** `62` (`22` EP01 Teaser + `40` S1E01 sc01–sc03)

## 2. Reusable Asset Priority Table (Sorted by Shot Reuse)

| Asset ID | Name | Type | Status | Linked Shots | Linked Concepts | Strategy / Source |
|---|---|---|---|---:|---:|---|
| `AST-0024` | Arcane-Family Painterly Compositor & Kuwahara Grade | `SHADER_LOOKDEV` | `IN_PROGRESS` | 62 | 93 | CUSTOM_BLENDER_COMPOSITOR |
| `AST-0021` | Kanwa / Vyasa Vedic Hermitage & Malini Riverbank | `ENVIRONMENT` | `IN_PROGRESS_CC0_ACQUIRED` | 33 | 11 | MahabharataWorld UE (Vrindavan banyan/banks) + PolyHaven CC0 nature/ganges_river_pebbles + FAB_TARGET (Ancient Trees/River) |
| `AST-0020` | Kurukshetra Battlefield & 14k Instanced Army | `ENVIRONMENT` | `IN_PROGRESS` | 23 | 8 | CUSTOM_BLENDER_GN + MahabharataWorld UE (L_Kurukshetra) + PolyHaven CC0 dry_ground_01 & dusk HDRI |
| `AST-0017` | Divine Bows & Hero Arrows (Gandiva, Vijaya, Snake Arrow, Anjalika) | `PROP_WEAPON` | `IN_PROGRESS` | 20 | 18 | TRELLIS2_PROP (karna_bow_1536.glb) + CUSTOM_BLENDER bows.py + MahabharataWorld UE |
| `AST-0018` | Hermitage & Vedic Props (Palm-Leaf Manuscripts, Brass Stylus, Fire Altar, Diya, Kalash) | `PROP` | `ACQUIRED_NEEDS_PAINTERLY_REPAINT` | 18 | 9 | PolyHaven CC0 (brass_diya_lantern, brass_pot_01/02, brass_vase_01/03, stone_fire_pit) + NVIDIA SimReady OpenUSD + TRELLIS.2 |
| `AST-0016` | Vedic Gold War Chariots (Arjuna Ape-Banner / Karna Elephant-Rope / Dushmanta) | `VEHICLE` | `IN_PROGRESS` | 17 | 9 | CUSTOM_BLENDER + MahabharataWorld UE + TRELLIS2_CARVED_TRIM |
| `AST-0009` | King Dushmanta (Forest & Court Variants) | `CHARACTER` | `PLANNED` | 16 | 0 | CUSTOM_BLENDER (TRELLIS2 copper armor accents) |
| `AST-0010` | Shakuntala (Hermitage & Infant Variant) | `CHARACTER` | `PLANNED` | 14 | 1 | CUSTOM_BLENDER (Bark-cloth + cotton, NO ring/crown) |
| `AST-0023` | 2D Grease Pencil Astra & Combat FX Library | `VFX_LIBRARY` | `IN_PROGRESS` | 12 | 19 | CUSTOM_BLENDER_GP_V3 + FAB_TARGET (Optional Niagara sparks/dust for UE plates) |
| `AST-0022` | Vedic Royal Court Hall (Hastinapur / Puru Sabha Kit) | `ENVIRONMENT` | `IN_PROGRESS` | 10 | 19 | MahabharataWorld UE (170 Hastinapur assets!) + FAB_TARGET (Courtyard/Wooden pillars for 1000 BCE S1E01 court) |
| `AST-0006` | Rishi Vyasa | `CHARACTER` | `PLANNED` | 10 | 1 | CUSTOM_BLENDER (Original sculpt + Rigify) |
| `AST-0003` | Karna Hero (Sun Armor & Kavacha) | `CHARACTER` | `IN_PROGRESS` | 9 | 3 | CUSTOM_BLENDER (Original + TRELLIS base) |
| `AST-0012` | Young Bharata (Sarvadamana, age 6) | `CHARACTER` | `PLANNED` | 8 | 0 | CUSTOM_BLENDER |
| `AST-0007` | Lord Ganesha (Scribe) | `CHARACTER` | `PLANNED` | 7 | 0 | CUSTOM_BLENDER (Special anatomy: trunk + 4 arms + snap tusk) |
| `AST-0004` | Krishna Hero (Charioteer / Sovereign) | `CHARACTER` | `IN_PROGRESS` | 6 | 4 | CUSTOM_BLENDER (Original) |
| `AST-0014` | Hermitage Animals (Lion, Tiger, Deer) | `ANIMAL_CREATURE` | `ACQUISITION_TARGET` | 6 | 1 | FAB_TARGET (Big cat / deer rigged packs) -> Blender stylized fur |
| `AST-0001` | Arjuna Hero (Armored) | `CHARACTER` | `IN_PROGRESS` | 5 | 4 | CUSTOM_BLENDER (Original + TRELLIS base) |
| `AST-0015` | Noble Shakunta Vulture Pack (SSS Feather Kit) | `ANIMAL_CREATURE` | `ACQUISITION_TARGET` | 4 | 5 | FAB_TARGET (Raptor bird rig) + Blender Boids + CON-0030 SSS Feather Kit |
| `AST-0013` | Vedic Chariot Horses (White & Dun Teams) | `ANIMAL_CREATURE` | `IN_PROGRESS` | 4 | 1 | MahabharataWorld UE + FAB_TARGET (Rigged Horse + Gallop/Kneel anim) -> strip stirrups |
| `AST-0002` | Arjuna Hero (Bare-Headed / Crownless) | `CHARACTER` | `IN_PROGRESS` | 4 | 0 | CUSTOM_BLENDER |
| `AST-0011` | Sage Kanwa | `CHARACTER` | `PLANNED` | 4 | 0 | CUSTOM_BLENDER (Modular sage base rig) |
| `AST-0019` | Hero Crowns, Ornaments & Armour Trims (Kiritamukuta, Keyura, Mekhala) | `PROP_COSTUME` | `IN_PROGRESS` | 3 | 11 | TRELLIS2_PROP (high-detail reliefs) + BLENDER shader CON-0050 (REF-0017 patina) |
| `AST-0005` | Shalya Hero (Madraka King / Charioteer) | `CHARACTER` | `IN_PROGRESS` | 3 | 0 | CUSTOM_BLENDER (shalya_build.py) |
| `AST-0008` | Lord Brahma (Four-Faced) | `CHARACTER` | `PLANNED` | 3 | 0 | CUSTOM_BLENDER + LOTUS_SEAT_TRELLIS2 |

## 3. Targeted Epic Fab Marketplace Checklist (Painterly Adaptation Required)

> **Rule (`epic_film_pipelines.md` & `bible.md`):** On a **GTX 1650 (4 GB VRAM)**, keep Unreal Engine 5.8 + Fab for **background plates and modular kitbash parts**. Never ship raw photoreal marketplace materials — repaint/re-grade all Fab downloads to warm key `#FFC27A` + cool blue shadow `#3E5A86` and Vedic 1000 BCE period rules (no stirrups, no horned saddles, no medieval stone palaces).

| Target | Linked Asset | Fab Search Terms | Serves Episodes | Period & Style Adaptation Rule |
|---|---|---|---|---|
| `FAB-01` | `AST-0021` | Fantasy forest / Ancient trees / River stones / Waterfall (Fab Free + Megascans) | S1E01 sc01-sc03 (Vyasa/Shakuntala hermitage) + Season 4 Exile | Decimate to <50k tris per cluster; replace photoreal bark/leaf textures with painted Krita brush albedo + #3E5A86 shadow fill. |
| `FAB-02` | `AST-0022` | Ancient palace / Temple pillars / Sandstone hall / Wooden rafters | S1E01 sc03 Dushmanta court + Season 3 Hastinapur Sabha | For S1E01 strip ornate late-medieval stone idols/domes (Vedic 1000 BCE uses wooden pillars + oil lamps). Re-grade to warm sandstone/wood. |
| `FAB-03` | `AST-0013` | Horse / Horse rig / Animal animation | EP01 Teaser (A02, A05, A13 kneeling beat!) + S1E01 H01-H03 | Check skeleton compatibility for Blender FBX import; remove all modern saddles/stirrups; add golden Vedic breastplate geometry. |
| `FAB-04` | `AST-0014` | Lion rig / Tiger / Deer | S1E01 H02 (fleeing deer), V08 (Bharata riding lion & opening tiger jaws) | Paint stylised mane cards; apply simplified broad value shading so animals match @bharata_boy. |
| `FAB-05` | `AST-0015` | Vulture / Eagle flight loop | S1E01 V01-V02 (Shakunta protectors) + EP01 sky omens (CON-0029) | Apply thin-sheet SSS wing feather shader from REF-0010 (CON-0030) for rose-gold dawn translucency. |
| `FAB-06` | `AST-0020` | Cracked red earth material / Niagara dust / Broken wood / Spears | EP01 Kurukshetra ring & UE 5.8 background plates | Use ONLY for UE 5.8 background plates & terrain depth; keep heavy meshes out of 4 GB GTX 1650 hero scene. |

### 3B. Verified $0 Free / Personal-Free Fab Listings (Inspected 2026-11-27 — Ready to Claim After Epic Sign-In)

| Listing | Asset | Price Tier ($0 Only) | License | Formats | URL |
|---|---|---|---|---|---|
| Ancient Temple Jungle Roots | `AST-0021` | Free | Standard License | fbx, glb, gltf, usdz, ZBrush, UEFN | https://www.fab.com/listings/d30849f6-13cd-4e6f-9664-d7db13b5555f |
| FREE Stylized Forest Sample | Stylized Trees & Foliage Pack | `AST-0021` | Free | Standard License | Unreal Engine | https://www.fab.com/listings/3c1a31b6-e523-4a0f-97d0-26b0db69b6bc |
| Free Pack - Rocks Stylized | `AST-0021` | Personal = Free (select Personal $0) | Standard License | Blender, UE, fbx, obj, usd, glb, gltf | https://www.fab.com/listings/a0746c4b-428b-4556-b4c9-98f70c2a30d4 |
| Rock Sandstone | `AST-0020 / AST-0021` | Free | Standard License | fbx, glb, gltf, usdz, ZBrush | https://www.fab.com/listings/66f241e5-43fa-47c0-a475-07b2d1391f7e |
| Ancient Temple Lintel | `AST-0022` | Free | Standard License | fbx, glb, gltf, usdz, ZBrush | https://www.fab.com/listings/8d54fd6b-4d87-4bba-94d6-8078253a9dc7 |
| Ancient Temple Stairs | `AST-0022` | Free | Standard License | fbx, glb, gltf, usdz, ZBrush | https://www.fab.com/listings/3b79f3b7-a1f3-4dfa-b340-d09d75dd4651 |
| Stylized Low Poly Ancient Temple - Game Ready with LODs | `AST-0022` | Free | CC-BY (credit required) | Unity, fbx, glb, obj | https://www.fab.com/listings/fb9e06f5-c921-48c6-baf1-7b83b7edcfda |
| Lion Statue 3D Scan | `AST-0022` | Free | Standard License | fbx | https://www.fab.com/listings/1687bd29-0f25-47a7-90f5-43fb86b29b12 |
| Absorption FX | `AST-0023` | Personal = -100% Free* (ends 2026-12-01 8:29 PM) | Standard License | Unreal Engine, UEFN Source | https://www.fab.com/listings/81550176-a90e-4e07-8817-c8d1a1d3884b |
| Perfect Fire VFX | `AST-0023` | Personal = Free (select Personal $0) | Standard License | Unreal Engine | https://www.fab.com/listings/d2136c01-8d35-403f-a637-146e8173bdb3 |
| The senses -scene Inspired by the Bhagavad Gita- | `AST-0013 / AST-0016` | Free | Standard License | Blender, gltf, glb, usdz | https://www.fab.com/listings/7b6c9949-e849-4c4f-b725-219c6aa180b2 |
| Stylized lowpoly HORSE | `AST-0013` | Free | Standard License | Blender, obj, fbx, glb | https://www.fab.com/listings/f59ac535-4432-4a38-802e-d951d3806456 |
| Leopard Hybrid_A1 | `AST-0014` | Personal = Free (select Personal $0) | Standard License | Blender, fbx | https://www.fab.com/listings/d0e9ce8d-bdb9-412f-9740-6f528f56a2c1 |
| Animals FREE - Low Poly 3D Models Pack | `AST-0014` | Free | Standard License | Blender, UE, fbx, glb, obj | https://www.fab.com/listings/0c8f3917-2461-4775-a853-b995bb93bac5 |
| King_Demon_Vulture | `AST-0015` | Free | Standard License (Note: Gen AI = Yes) | fbx | https://www.fab.com/listings/60141af9-a9ce-48db-ac9c-6044fe47985e |
| Cartoon Yellow Canary: Rigged Stylized Bird | `AST-0015` | Personal = Free (select Personal $0) | Standard License | Unreal Engine, Blender, fbx, obj | https://www.fab.com/listings/6f93aa0a-f450-440f-897a-9389d05c34d5 |

## 4. Shifted Reel Workflow (Targeted Instead of Blind Grinding)

After closing **Batch 1 (`REF-0022`–`REF-0031`)** once browser quota resets, stop blind sequential inspection of remaining `PENDING` Reels and query SQLite (`mahabharat_prod.db`) strictly for open production gaps:
- `ENVIRONMENT` (`34` catalogued) -> Vedic forest/riverbank/court composition only for `AST-0021` & `AST-0022`
- `COMBAT_ANIMATION` (`40` catalogued) -> Archery draw/volley timing only for `EP01` S/A shots
- `VFX` (`42` catalogued) -> Grease Pencil impact & astral trail study for `AST-0023`
- `FACIAL_ANIMATION` (`10` catalogued) -> Subtle close-up blinks/speech restraint for `A09`, `A22`, `S1E01 V12`

## 5. Acquired & Existing Local 3D Assets (Ready on Disk)
- **MahabharataWorld Unreal Project (`Documents/Unreal Projects/MahabharataWorld/Content`):** `315` files (`Hastinapur`: 170, `Kurukshetra`: 73, `Cities`: 72)
- **Poly Haven CC0 (`MAHABHARATA_STUDIO/02_BLENDER/`):** `20` 2K `.blend` props & nature kits + `5` 2K PBR texture blends + `4` 2K dawn/dusk/storm HDRIs (`CC0 1.0`, commercially safe)
- **NVIDIA SimReady Central (`MAHABHARATA_STUDIO/02_BLENDER/Props/NVIDIA_SimReady/`):** `12` curated OpenUSD clay/copper/decor/stool props (`CC BY 4.0` per `.metadata/LICENSE.txt` — attribute NVIDIA SimReady), compiled into `nvidia_simready_vedic_props.blend` via `import_usd_prop.py`
- **NVIDIA Omniverse OpenUSD GitHub Samples (`03_UNREAL/NVIDIA_OpenUSD_Samples/`):** `14` OpenUSD sample scene/material files
- **Epic Fab Marketplace (`fab.com` / `VaultCache/FabLibrary`):** Currently `0` downloaded listings (`listings_v1.db` empty) — requires interactive sign-in & EULA claim inside Epic account / UE 5.8 (`Window -> Fab`) for `FAB-01`..`FAB-06`.

## 6. Local Non-Committed Database & Shareable Export Paths
- **SQLite DB:** `C:\Users\dharm\OneDrive\Desktop\claude projects\MAHABHARATA_STUDIO\00_REFERENCE_LIBRARY\mahabharat_prod.db`
- **Sanitized CSV (safe to share externally):** `C:\Users\dharm\OneDrive\Desktop\claude projects\MAHABHARATA_STUDIO\00_REFERENCE_LIBRARY\05_ORIGINAL_CONCEPTS\export_for_planning\mahabharat_sanitized_refs.csv`
- **ChatGPT 9-Field Concept->Asset CSV:** `C:\Users\dharm\OneDrive\Desktop\claude projects\MAHABHARATA_STUDIO\00_REFERENCE_LIBRARY\05_ORIGINAL_CONCEPTS\export_for_planning\mahabharat_chatgpt_mapping_export.csv`
- **Sanitized Production JSON Bundle:** `C:\Users\dharm\OneDrive\Desktop\claude projects\MAHABHARATA_STUDIO\00_REFERENCE_LIBRARY\05_ORIGINAL_CONCEPTS\export_for_planning\mahabharat_production_bundle_sanitized.json`

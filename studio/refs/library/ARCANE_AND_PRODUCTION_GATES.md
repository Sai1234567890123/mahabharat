# Mahabharata Arcane-Inspired Visual Development & 6-Gate Production System

Connects [`studio/bible.md`](../../bible.md) and [`studio/pipeline.md`](../../pipeline.md) to [`mahabharat_prod.db`](../../../../../../OneDrive/Desktop/claude%20projects/MAHABHARATA_STUDIO/00_REFERENCE_LIBRARY/mahabharat_prod.db), [`04_shots.csv`](04_shots.csv), and [`05_assets.csv`](05_assets.csv).

---

## 1. Seven Arcane-Inspired Visual Rules (Adapted Strictly for Mahabharata)

> **Boundary:** Apply broad painterly-3D visual principles only. Never copy *Arcane* character designs, costumes, or frame compositions, and never feed third-party film/Reel frames into AI generation tools.

1. **Rule 1 — Character Design & Silhouette Readability**
   - Simplified large silhouette shapes carrying fine Vedic craft details (peacock feather, lotus crown, asymmetrical bronze shoulder guard, Kiritamukuta contours).
   - Consistent multi-shot face topology and controlled proportions.
   - **Priority Hero Roster (`05_assets.csv`):**
     - **Built / In-Progress (`EP01` & Teaser):** Arjuna Armored (`AST-0001`), Arjuna Bare (`AST-0002`), Karna (`AST-0003`), Krishna (`AST-0004`), Shalya (`AST-0005`).
     - **S1E01 Passports Complete (`studio/cast/`):** Rishi Vyasa (`AST-0006`), Ganesha (`AST-0007`), Brahma (`AST-0008`), King Dushmanta (`AST-0009`), Shakuntala (`AST-0010`), Sage Kanwa (`AST-0011`), Young Bharata (`AST-0012`).
     - **Next Series Anchor Cast (Future Passports):** Bhishma, Draupadi, Bhima, Yudhishthira, Duryodhana (each requiring front/side/back/3-quarter/expression sheets before blocking).

2. **Rule 2 — Painterly Materials (Krita + Blender Texture Paint)**
   - Break up metallic reflections with brush-stroke roughness maps (`CON-0050`: hammered bronze + oxidized verdigris patina from `REF-0017`).
   - Matte terracotta/warm brown skin tones (`#FFC27A` bounce), subtle canvas/brush grain on silks and bark-cloth, clean crisp silhouette edge + soft internal shading.
   - **Rule:** Never ship raw photoreal marketplace scans (`Fab` / `Megascans` / `Omniverse`); strip/repaint textures to matte-painted 2K maps to protect 4 GB VRAM and preserve style unity.

3. **Rule 3 — Lighting & Colour Vocabulary**

| Situation | Light & Palette Rule | Key Colors |
|---|---|---|
| **Hastinapur / Puru Court** | Warm sandstone & wooden pillar lamp bounce, low-key indigo hall depth | Gold key `#D9A21B` / `#FFC27A`, indigo shadow `#3E5A86` |
| **Gurukul / Hermitage (`S1E01`)** | Dappled diagonal forest canopy sunbeam (`CON-0058`), earthy foliage greens, river mist | Morning warmth + deep mossy shadow |
| **Vedic Forest Exile** | Muted deep emerald/umber, multiplane parallax foliage (`CON-0060`) | Soft cool slate fill, warm foliage rim |
| **Kurukshetra (`EP01`)** | Dusty ochre earth + blazing low western sunset backlight (`bible.md` locked direction) | `#E9CF9A`, `#B8743C`, darkening orange `#E8792E` |
| **Divine / Sacred Beats** | Strictly locked symmetrical frames, luminous center key/halo (`1988 Vishwaroop` + `S03/S06`) | Controlled white-gold `#FFE9A8` core bloom only |
| **Tragic / Aftermath Beats** | Selective color drain (`EP01 A18` / `A20`), cool cobalt night/dusk wash | Desaturated slate + single ember/sun disc |

4. **Rule 4 — Four Reusable Master Environments**
   - **`AST-0021` Hermitage / Riverbank (`S1E01` + Ashram scenes):** Modular thatch hut, fire altar, banyan roots, Malini river stones (`33` linked shots).
   - **`AST-0022` Vedic Court / Sabha (`S1E01` Court -> Hastinapur Sabha):** Wooden pillars/oil lamps (1000 BCE early) expanding into sandstone halls (`10` linked shots, `17` concepts).
   - **`AST-0020` Kurukshetra Battlefield (`EP01` + War):** Red-earth ring, 13,977 GN instanced army, sky plates (`23` linked shots).
   - **Forest & Mountain Terraces (Season 2–4):** Multiplane 2.5D painted forest + `Fab` rock/tree kitbash.

5. **Rule 5 — Reusable Camera Templates**
   - `Hero Entrance` (`REF-0006` / `CON-0016` low-angle match cut)
   - `Low-Angle Wheel/Monumental Scale` (`REF-0001` / `CON-0001` 18mm wheel-height push)
   - `Locked Symmetrical Sacred` (`S03`, `S06`, `S09`, `A20`, `V17`)
   - `Emotional Dialogue Close-Up` (`85mm` shallow DOF warm key, `REF-0021` / `CON-0063`)
   - `Whip-Pan & Arrow Ride` (`EP01 A06`, `A12`, `A14` speed ramp 100->10->100%)
   - `360° Orbital Reveal` (`REF-0005` / `CON-0013`)

6. **Rule 6 — Three Animation Tiers**
   - **Tier 1 (Hero `S`/`A` Shots):** Hand-keyed on **twos**, **ones** on arrow release/impact, 4–8 frame held anticipation, full Rhubarb + shape-key facial performance.
   - **Tier 2 (Secondary / `B`/`C` Shots):** Blocked key poses + `anim_lib.py` / `moves.py` cycles or retargeted movement cleanup; `C` shots = breath + blink + camera drift.
   - **Tier 3 (Background Armies / Flocks):** Geometry Nodes instancing (`battlefield.py`) & Boid bird flocks (`CON-0029`).

7. **Rule 7 — Hybrid VFX System**
   - **Lead (2D Grease Pencil v3 in Blender):** Arrow streaks, Karna sun-gold (`#FFF1C2`/`#FF8A1E`), Arjuna lightning-blue (`#F2FAFF`/`#3FA9FF`), starburst shockwave rings (`CON-0032`), 2-frame graphic impact flashes.
   - **Support (UE 5.8 Niagara Plates only where needed):** Far battlefield dust haze, drifting ember atmospheres, waterfall spray behind 3D foreground.

---

## 2. The 6 Mandatory Shot Production Gates

No shot in `04_shots.csv` moves to final render before passing all 6 gates:

| Gate | Stage | Exit Criteria | Verified By |
|---|---|---|---|
| **1. Research & Canon** | Canon + Reference lock | Ganguli lines cited (`canon_check.md`), originality rule clear (`APPROVED_PRINCIPLES_ONLY`), period checklist passed | `canon_check` + Sai |
| **2. Visual Dev** | Storyboard & Color Script | `shots.json` + grade (`S`/`A`/`B`/`C`) approved, color script palette matches shot mood | Creative Lead + Sai |
| **3. Asset Gate** | Model, Rig, Material Check | Linked `AST-*` meshes decimated for 4 GB GTX 1650 / <2 GB SheepIt limit; textures painted; Vedic rules checked (no stirrups/paper books) | 3D Lead |
| **4. Animation Gate** | Blocking & Timing | Cut directly into `animatic_layout.mp4` (`build_layout_animatic.py`), twos/ones timing locked, lip-sync verified | Production QA |
| **5. Look & FX Gate** | EEVEE + GP v3 + Grade | Lighting matches `#FFC27A`/`#3E5A86` key/fill, 2D FX & Kuwahara compositor pass clean at 960×540 draft | Lookdev Check |
| **6. Final Render & Mix** | 1080p + Vertical 9:16 | Clean 16:9 master + 9:16 safe-zone cut, `-14 LUFS` mix, audio licences logged | Publisher + Sai |

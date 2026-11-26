# Mahabharata Reference Library Starter Pack

Connected directly to `studio/` (`studio/bible.md`, `studio/pipeline.md`, and `studio/refs/study_notes_2026-11-21.md`).

## Safe Ingestion (No Account Credentials Required)

Never share Instagram passwords or scrape restricted pages. Use Instagram's built-in export or paste URLs in batches:

1. **Best for 300+ Reels at once (Instagram Official Export):**
   - In Instagram: **Settings & Activity -> Accounts Center -> Your information and permissions -> Download your information -> Download or transfer information -> Some of your information -> Saved** (format: **JSON**).
   - Run the ingestor on the downloaded `saved_posts.json` / `saved_collections.json`:
     ```bash
     python studio/refs/library/ingest_instagram_saved.py --input path/to/saved_posts.json --csv studio/refs/library/01_references.csv
     ```
2. **Or Paste URLs in Batches of 30 (`urls.txt`):**
   - Save 30 URLs in a text file (one URL per line, optional `# Collection Name` header lines) and run:
     ```bash
     python studio/refs/library/ingest_instagram_saved.py --input urls.txt --collection "Warrior animations" --csv studio/refs/library/01_references.csv
     ```

## Workflow
1. Ingest Instagram Reel URLs into `01_references.csv`, one Reel per row (`REF-0001`, `REF-0002`, ...).
2. Keep the original URL and creator username as provenance. Record `access_status` honestly (`ACCESSIBLE`, `LOGIN_REQUIRED`, `UNAVAILABLE`).
3. Review each Reel manually in Instagram. If inaccessible, mark `NEEDS_VISUAL_INPUT`.
4. Fill `02_analysis_cards.csv` (or a markdown card from `ANALYSIS_CARD_TEMPLATE.md`) using only observable techniques—do not infer unseen software or frame rates.
5. Score priority out of 5 (`P = 0.30V + 0.25R + 0.20M + 0.15F + 0.10C` via `ingest_instagram_saved.py --score V R M F C`).
6. Add original Mahabharata ideas to `03_concepts.csv` (`CON-0001`). A concept can cite multiple `REF-*` IDs.
7. Convert approved concepts into shot rows in `04_shots.csv` (`EP001_SEQ001_SH001`).
8. Track reusable Blender/Unreal assets in `05_assets.csv` (`AST-0001`).
9. Use `06_tag_dictionary.csv` for consistent tags.

## Studio Bible & Copyright Guardrails (Read First)
- **Never feed third-party Reels, screenshots, film frames, or other artists' work into any AI image/video model** (`studio/bible.md`).
- Any permitted local reference screenshots stay strictly on your PC inside gitignored `studio/refs/study_reels/` or `MAHABHARATA_STUDIO/00_REFERENCE_LIBRARY/02_PERMITTED_SCREENSHOTS/` and are never committed to the public GitHub repo.
- Extract general filmmaking principles (camera angle, rim light, pacing, dust, silhouette)—never copy footage, music, character designs, choreography, or exact shot sequences without permission.

## Local Folder Structure (`MAHABHARATA_STUDIO/`)
```
MAHABHARATA_STUDIO/
  00_REFERENCE_LIBRARY/
    01_URL_REGISTER/
    02_PERMITTED_SCREENSHOTS/
    03_ANALYSIS_CARDS/
    04_REFERENCE_BOARDS/
    05_ORIGINAL_CONCEPTS/
  01_VISUAL_BIBLE/
    Character_Design/ Costume_Design/ Architecture/ Weapons/ Lighting/ Colour_Palettes/
  02_BLENDER/
    Characters/ Environments/ Props/ Rigging/ Animation/
  03_UNREAL/
    Materials/ VFX/ Sequencer/ Lighting/
  04_EPISODES/
    EP001/ EP002/ EP003/
  05_AUDIO/
  06_RENDERS/
  07_BACKUPS/
```

## 30-Reel Pilot Plan
- **Reels 1–10:** Cinematography and scene direction
- **Reels 11–20:** Character design and environments
- **Reels 21–30:** Combat, animation, and VFX
Complete analysis cards and originality reviews for the 30-Reel pilot before scaling to all 300+.

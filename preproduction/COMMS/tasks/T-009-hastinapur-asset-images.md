---
id: T-009
owner: antigravity
status: open
created: 2026-10-30
depends_on: []
---
## Goal
Generate 10 single-object asset images for TRELLIS.2, each scoring 80 or above with gemini-4-argon.

## Rules
- Image model: only Nano Banana 2, `gemini-3.1-flash-image`, on Vertex AI, project `aiautomationplatform`, global endpoint, via ADC. Aspect ratio 1:1.
- Scoring: `gemini-4-argon` only, using `trellis_assets/ascore.py`.
- Wait 8 seconds between image calls; the model rate-limits (429).

## Folders
- Base folder (B): `C:/Users/dharm/AppData/Local/Temp/claude/C--Users-dharm-OneDrive-Desktop-claude-projects/94185024-0f53-413d-b4d2-6208b45777d2/scratchpad/trellis_assets`
- Current images: `B/round4/hst_<name>.png`. Attach the current image and the listed concept as references.
- Concepts: `C:/Users/dharm/Downloads/conceptartmahabharat/image (N).jpeg`
- Output: `B/round5/hst_<name>.png`, plus `B/round5/scores.json`.

## Ending for every prompt
Paste this after each prompt:

> Isolated single 3D-asset reference for image-to-3D reconstruction: one object only, entire object fully visible with margin, centred, three-quarter front view from slightly above, plain pure white background, no ground plane, no cast shadow, no people, no text. Ancient Indian Mahabharata style only, nothing Greek, Roman, Mughal or Islamic. White and cream marble, polished gold, green malachite, saffron and red accents, crisp symmetric carved detail, solid forms with no thin wires or strings.

## Prompts

| Name | Concept | Prompt |
|---|---|---|
| arjuna_chariot | 6, 42 | Arjuna's golden war chariot: gold lion-head front, two huge ornate spoked wheels, carved gold body with saffron and red cushions, a bulbous gold umbrella canopy with a kalash finial on four solid supports, a tall flagpole with a green Hanuman banner, a solid front yoke pole, no horses. |
| dice_table | 50, 53 | One royal dice table only: a low draped table in red and gold with a marble and malachite game board set into the top, a clean 8x8 Ashtapada grid, no stools, no loose pieces. |
| ganesha_relief_wall | 11 | One straight section of carved temple wall in dark stone with deep relief panels of Ganesha and deities, framed by square malachite pilasters with gold bands, on a stepped plinth. |
| garden_pavilion | 30, 49 | An open square garden pavilion with exactly 4 corner columns of polished green malachite, a gold dome with a kalash finial, saffron and red garlands solid against the beams, on a lotus-carved marble platform. |
| hill_fort_gate | 12, 4 | A hill fort gateway in cream stone: one ancient Hindu corbelled torana arch between two round towers, polished gold bulb domes, chhatri columns in green malachite, saffron and red accents on the friezes. |
| sabha_column_bay | 30, 49 | One walkable bay of the Maya Sabha colonnade: two identical smooth green malachite columns with ornate gold Indian lotus and kalasha capitals, a carved marble beam with garlands above, separate pedestals with an open floor between them. |
| war_elephant | 24, 36 | One armoured war elephant standing: polished gold head armour matching a gold howdah, green malachite howdah columns, red and gold caparison, tusk blades, solid clean arrow quivers and bells, no riders, correct anatomy. |
| white_horse | 6, 42 | One white war horse standing, correct anatomy, four legs clearly separate, an ancient Indian ornamental saddle cloth (ashva-stara) in saffron, red, gold and malachite, gold harness flush to the body, no modern saddle or stirrups. |
| peacock_throne | 31, 38 | The royal golden throne of Hastinapur on a stepped marble dais: gold sun-disc back, gold lion arms, red cushions, malachite inlay. |
| dwaraka_tower | 8, 41 | A tall white marble temple tower of Dwaraka with stacked gold finials, arched windows and carved tiers on a square plinth. |

## Done when
- All 10 images are in `B/round5/` and each scores 80 or above.
- For anything below 80, use the score's `fix_prompt` and regenerate from scratch. Stop after 3 rounds and keep the best.
- Write `COMMS/reports/R-009-hastinapur-asset-images.md`: a table of name, score, rounds used.

## Do not
- Do not start any GCP VM or run TRELLIS.2. Claude does that.
- Do not touch Unreal or Blender.
- Do not use any other image model.

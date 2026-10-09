# Mahabharat pilot: MVP preproduction and concept art

Preproduction package for a 90-second proof-of-concept sequence, **"The First Conch"** (Bhishma Parva: the conches at Kurukshetra, Arjuna's doubt and the universal form). It turns the research in `../trailer-analysis/` into our own production plan and a first pass of concept art. All designs are original; no frames from any film were used.

## Documents

1. [01-treatment.md](01-treatment.md): why this sequence, logline, 12 story beats with Ganguli line references, tone.
2. [02-style-bible.md](02-style-bible.md): the look, the color script per act, character color and energy codes, shape language, rendering, FX, impact frame and lens rules, and the global AI style prompt.
3. [03-characters.md](03-characters.md): design sheets in words for Krishna, Arjuna, Bhishma, Duryodhana, Bhima and Yudhishthira.
4. [04-locations-props.md](04-locations-props.md): Kurukshetra, the cosmic space, Arjuna's chariot, the ape banner, Bhishma's palmyra standard, the five conches and Gandiva.
5. [05-shot-list.md](05-shot-list.md): 18 shots with lens, camera move, FX, sound and source line.
6. [06-prompt-pack.md](06-prompt-pack.md): keyframe and motion prompts for every shot, ready for Nano Banana, Imagen, Flux, Veo 3.1 or Wan 2.2.
7. [07-pipeline-and-next-steps.md](07-pipeline-and-next-steps.md): how the concept art was made, how to re-run it, and the next steps to reach final quality.

## Concept art (`art/`)

- `concept-SH*.jpg`: eight hero concept frames with captions.
- `frames/SH*.jpg`: a concept frame for every shot; `frames/SH*_impact.jpg`: the impact frames.
- `storyboard-1.jpg`, `storyboard-2.jpg`: the whole pilot on two boards.
- `color-script.jpg`: one panel per beat, grouped by act, with palette swatches.
- `silhouette-lineup.png`: the hero cast in color and as pure silhouettes.
- `fx-sheet.jpg`: the 2D FX vocabulary (five conch rings, god rays, halo, chakra, yantra, lightning, shockwave, impact frame).
- `control/`: depth, line art and ID passes per shot, for the AI paint-over.

## Data and scripts

- `data/shots.json` is the single source of truth: acts, palettes, characters, conches, and every shot's camera, staging, FX and prompts.
- `scripts/make_shots.py` writes `shots.json`; `scripts/blockout.py` builds and renders each shot in Blender; `scripts/compose.py` paints sky, haze, line art, FX and lens; `scripts/sheets.py` builds the boards; `scripts/docs_from_shots.py` writes docs 05 and 06; `scripts/render_all.sh` runs everything.

# How the concept art was made, and what comes next

## What these frames are

The concept frames are **layout and design frames**, the stage the build plan calls "3D layout and animatic" plus "2D FX and compositing". They fix the composition, lens, staging, palette, haze, FX design and the edit rhythm for every shot. They are not final paintings: faces, hands, costume detail, hair and painted textures come from the AI paint-over pass, which uses these frames and their control passes as input. That keeps the AI on our layout instead of inventing its own.

## How they were made

1. `scripts/make_shots.py` defines the pilot as data: four acts with palettes and light directions, six hero characters with color codes, five conches, and 18 shots with camera, staging, FX and prompts. It writes `data/shots.json`.
2. `scripts/blockout.py` (Blender 5.2 Python API, run headless) builds Kurukshetra from that data:
   - a ground plane, two instanced armies of about 100,000 soldiers with standards, and deep painted masses behind them;
   - Arjuna's chariot with gold body, spoked wheels, bells, four white horses and the ape banner; Bhishma's white car with the gold palmyra and five stars; Duryodhana's, Drona's, Bhima's and Yudhishthira's cars; generic cars along both lines;
   - proxy figures built from metaballs, with poses (reins, conch, roar, mace, bow, slump, bow raised, universal form with ten extra arms);
   - a toon shader made of emission (3 value steps, painted breakup of the terminator, colored rim light), so Cycles renders it on a CPU in about a minute per shot at 1920×803;
   - three passes per shot (color, log depth, object IDs) and a JSON of the camera, horizon, sun and named anchor points in pixels.
3. `scripts/compose.py` paints everything that belongs to 2D, following the style bible:
   - a matte-painted sky with posterized cloud banks and a hard-edged sun, or a cosmos with nebula and stars in act C;
   - stepped atmospheric haze from the depth pass;
   - colored line art from depth and ID edges, fading with distance;
   - the FX listed per shot in `shots.json`: conch rings in each conch's color, speed lines, god rays, halo, glow, sparkles, shockwave, dust banks, Sudarshana chakra, the Vishvarupa yantra with rings of eyes, and Arjuna's lightning, all anchored to 3D points so they track the camera;
   - lens effects: bloom, anamorphic flare and ghosts, chromatic fringe, vignette and grain;
   - impact frames in three flat colors (black, white, energy color) with radial speed lines;
   - control passes for the AI stage: depth (near = white), line art (black on white) and IDs.
4. `scripts/sheets.py` builds the storyboard, color script, cast lineup, FX sheet and captioned hero plates.

To re-run everything: `BPY_PYTHON=/path/to/python-with-bpy scripts/render_all.sh 1920 12` (or `pip install bpy` into a Python 3.13 environment). Blender MCP on your PC can drive the same `blockout.py` code when Blender is open with the MCP add-on running.

## Next steps to reach final quality

| Step | What | Tools | Needs |
|---|---|---|---|
| 1 | Approve or change the pilot sequence, palettes and character codes | These docs | Your notes |
| 2 | Character turnarounds: paint over the proxy figures, 3 views each, then an expression sheet | Nano Banana / Imagen on Vertex AI, or Flux in ComfyUI | Gemini or Vertex access |
| 3 | Train one LoRA per hero on 20 to 40 approved images | Flux or Qwen-Image LoRA training on a GCP L4/A100 VM | GCP credits |
| 4 | AI paint-over of the 8 hero frames using `art/control/` depth + line art and `06-prompt-pack.md` | ComfyUI + ControlNet, or Nano Banana with the frame as reference | Steps 2–3 |
| 5 | Gemini QA loop against the style bible checklist | Gemini 2.5 Pro | Gemini key |
| 6 | Animate the Blender layout into an animatic with the timings in the shot list | Blender | Blender on your PC |
| 7 | Motion: Veo 3.1 image-to-video or Wan 2.2 VACE video-to-video over the animatic | Vertex AI Veo, or Wan on a GCP GPU VM | GCP credits |
| 8 | Composite FX on twos and impact frames over the moving shots; edit, sound, music | `compose.py` per frame, Natron or Blender compositor, DaVinci Resolve | |

## What I need from you

- A Gemini API key or Vertex AI access in this project's cloud environment, so the AI paint-over can run here (variable `GEMINI_API_KEY`, or a service account for Vertex).
- Blender open on your PC with the MCP server started, if you want the 3D scene built live in your Blender.
- Your GCP credit amount and whether you have a local GPU, which decide whether training and video run on GCP VMs or at home.

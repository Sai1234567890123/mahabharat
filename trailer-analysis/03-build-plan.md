# Plan: building a Baahubali-Eternal-War-grade look for the Mahabharat series

Goal: reach the painterly 2D/3D hybrid style described in [01-shot-analysis.md](01-shot-analysis.md) with a small team, using open-source tools, Google Cloud AI credits, AI image and video models, and Claude Code as the pipeline engineer.

The core idea: **3D gives control, AI gives paint, 2D gives energy, code gives scale.** The big studios get consistency from hundreds of artists. We get it from a 3D layout that every AI generation is forced to follow, plus a strict style bible and automated quality checks.

## 0. Ground rules

- **Use the Baahubali frames only as reference for analysis.** Never train a model on them, never feed them to an image or video model as a style reference, never trace them. Our style bible must be our own paintings and designs. This keeps the series legally clean and visually original.
- **Mahabharat is public-domain mythology**, so characters, events and iconography are free to use. Do not reproduce any specific actor's face; design original characters (the repo's PROMPTS.md already follows this).
- **Keep the existing work.** The repo already has a 170-shot Veo prompt list, approved manga sketches for shots 1 to 16 (Nano Banana 2.1 / Gemini 3.1 Flash Image) and a Gemini review loop that scores each sketch. That loop is exactly the QA stage this plan needs. The one change: PROMPTS.md asks for "photorealistic"; this style needs "painterly stylized CG" instead (see section 3).

## 1. Translating the trailer's techniques into our toolset

| Trailer technique | How they likely did it | Our version |
|---|---|---|
| 3D sets, characters, cameras | Maya, previs in 3D, feature animation team | **Blender** (open source) for layout, blocking and camera; AI 3D generators for proxy models |
| Hand-painted surfaces | Texture painters in Photoshop | **AI paint-over** of Blender renders (Nano Banana on Vertex; Flux or Qwen-Image with ControlNet in ComfyUI) guided by depth and line passes |
| Painted skies and matte paintings | Matte painters, projected on 3D cards | AI-generated matte paintings projected onto simple Blender geometry for parallax |
| Character animation | Keyframe animators, possibly mocap | Video mocap from our own performance footage (open-source pose estimation) retargeted in Blender, plus AI video models for secondary motion |
| 2D effects on twos | 2D FX animators | **Blender Grease Pencil** and **Krita** for hand-drawn FX; AI-generated FX plates on black; held at 12 fps |
| Line-art mandalas and yantras | Motion graphics | Procedural SVG and Blender geometry-node generators written by Claude Code |
| Impact frames | Illustrators | AI stills generated with a strict 3-color rule, then cleaned in Krita |
| Final painterly motion | Rendering and compositing | **Video-to-video restyle**: Blender animatic in, Wan 2.2 VACE or Veo 3.1 first/last-frame out |
| Lens: flares, fringing, grain | Nuke, After Effects | Blender compositor or Natron, plus ffmpeg/OpenCV scripts |
| Edit, sound | Editorial and sound teams | Kdenlive or DaVinci Resolve (free); temp music and voice from Vertex AI models; final voices recorded |

## 2. The pipeline

```
Story & shot list ─► Style bible ─► Characters & assets ─► 3D layout & animatic (Blender)
       │                                                         │
       │                                         control passes (depth, line, pose, color IDs)
       │                                                         ▼
       │                                  AI keyframe paint-over (start/end frames per shot)
       │                                                         │  Gemini QA loop
       │                                                         ▼
       │                                  AI motion (video-to-video or first/last-frame)
       │                                                         ▼
       └────────────────────────────►  2D FX + impact frames ─► Compositing ─► Edit, sound, grade
```

### Stage 1: Story, shot list and color script
- Start from the existing 170-shot list. Restructure it with the trailer's rhythm: action blocks of 10 to 15 seconds, separated by 2 to 4 second ritual beats that return to one recurring image (for example Krishna's conch at Kurukshetra, or Draupadi before the fire).
- Assign each act a palette (the trailer runs pink-red, violet-black, then storm grey).
- Claude Code: keep the shot list as structured data (`shots.json`: id, act, duration, characters, camera move, lens, palette, FX, impact frames, status) and generate prompts, file names and reports from it.

### Stage 2: Style bible (our own, original)
- 10 to 20 master paintings that define the look: brush texture, edge hardness, rim-light colors, haze, how skin, gold and cloth are painted.
- Per character: skin color, accent color, energy color, silhouette, ornaments, weapon. Example: Arjuna (dark skin, gold, Gandiva arrows in white-gold), Karna (golden armor and earrings, sun-orange energy), Bhima (mace, earth-brown, dust and rock FX), Krishna (blue skin, peacock feather, Sudarshana chakra as a spinning line-art mandala), Duryodhana (mace, deep red and black).
- Generate candidates with Nano Banana Pro or the Gemini image model on Vertex; the team picks and repaints.
- Write the bible as a short prompt block plus negative rules, used by every generation and by the QA reviewer.

### Stage 3: Characters and assets
- **Turnarounds and expression sheets** per character from the bible (Nano Banana with reference images).
- **Character LoRAs** trained on our approved sheets only (20 to 40 images each) for Flux/Qwen-Image (stills) and Wan 2.2 (video). Train with musubi-tuner or diffusion-pipe on a GCP GPU VM.
- **3D proxies**: generate base meshes from the turnarounds with an open-source image-to-3D model (Hunyuan3D or TRELLIS), clean them in Blender, auto-rig with Rigify. They only need to be good enough for silhouette, depth and pose; the paint pass supplies detail.
- **Sets**: blocky Blender geometry for Kurukshetra, Hastinapura, the Lac palace, the floating celestial realms. Matte paintings for skies.

### Stage 4: 3D layout and animatic in Blender
- Claude Code writes `bpy` scripts that read `shots.json` and create a scene per shot: set, characters, camera with lens and move (push-in, orbit, free-fall roll, top-down), frame range.
- Performances: film ourselves doing the action (Kalaripayattu, archery, mace swings, dance) on a phone; extract 3D motion with an open-source video mocap model; retarget to the rigs.
- Render a gray-shaded animatic at low resolution and cut it to temp music. This is where timing and camera are locked; AI is not used to decide composition.

### Stage 5: Control passes
For every shot, Blender renders: depth, normals, Line Art (Grease Pencil Line Art modifier), flat color IDs per character and object, a toon-shaded base (Shader to RGB with 2 to 3 light bands), and OpenPose skeletons. These passes are what keep AI output consistent from shot to shot.

### Stage 6: AI keyframe paint-over
- For each shot, generate the first and last frames (plus a middle frame for long shots) by painting over the toon render with ControlNet depth plus lineart, the character LoRAs and the style bible prompt.
- Run the existing Gemini review loop: score composition match against the Blender frame, character accuracy, style fidelity; regenerate below threshold. Keep human approval for hero shots.

### Stage 7: AI motion
Use the method that fits the shot:

| Shot type | Method |
|---|---|
| Character acting, fights, anything where the pose matters | **Video-to-video**: Blender animatic plus control passes into Wan 2.2 VACE or Wan Animate in ComfyUI with character LoRAs |
| Slow push-ins, landscapes, reveals, atmospheric shots | **Veo 3.1 first-and-last-frame** on Vertex AI with the painted keyframes |
| Quick tests, previz of new ideas | LTX-2.5 or Veo 3.1 Fast / Lite |
| Single dramatic stills (impact frames, comic-panel beats) | Image model only, no video |

Rules: generate at 24 fps, then hold the FX layer on twos; keep clips short (2 to 8 seconds) because trailer shots are short; never let the model decide the camera.

### Stage 8: 2D FX and impact frames
- **Hand-drawn layer**: lightning, sparks, speed lines, energy arcs in Blender Grease Pencil over the 3D camera, or frame-by-frame in Krita. Hard-edged, 2 to 3 tones, on twos.
- **AI FX plates**: fire, smoke puffs, energy blasts generated on black, keyed and composited.
- **Sacred geometry**: Claude Code writes generators for Sri Yantra, mandalas, lotus shields and chakra rings as SVG and as Blender geometry nodes so they can be placed in 3D space and animated (bloom, rotate, shatter).
- **Impact frames**: 1 to 3 per big hit, generated as flat 3-color images (for example black silhouette on red with white accents) from the shot's pose pass.

### Stage 9: Compositing and finishing
- Composite in the Blender compositor or Natron: AI plate + FX + mandalas + matte paintings.
- Lens pass via scripts: anamorphic flare, chromatic aberration, bloom, halation, grain, occasional lens bulge on impacts.
- Upscale with Real-ESRGAN or a video super-resolution model; interpolate only where needed, never on the FX layer.
- Grade per act in DaVinci Resolve (free) or Blender.

### Stage 10: Edit, sound and voice
- Cut in Kdenlive or Resolve against the animatic timing.
- Temp score and sound design: Vertex AI music generation (Lyria) and sound libraries; temp voice with Google text-to-speech. Final voices recorded by people.

## 3. Update to the global style prompt

Replace the "Photorealistic cinematic epic" block in PROMPTS.md with something like:

> Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged shadows, strong colored rim light, atmospheric haze, matte-painted sky, cinematic anamorphic lens, 16:9. Indian epic iconography. No text, no logos, no watermarks. No photorealism, no plastic 3D look.

Plus per-act palette lines and the character color codes from the style bible.

## 4. Google Cloud setup

| Need | GCP service | Notes |
|---|---|---|
| Image generation and editing | Vertex AI: Gemini image models (Nano Banana family), Imagen | Already in use in the repo |
| Video generation | Vertex AI: Veo 3.1, 3.1 Fast, 3.1 Lite | First-and-last-frame supported; 8-second max per clip; Veo runs in us-central1; download results promptly because generated videos are kept only for a short time |
| QA and shot review | Vertex AI: Gemini (multimodal) | Existing review loop |
| Open-source model inference and LoRA training | Compute Engine GPU VMs (L4 for ComfyUI, A100/H100 for Wan 14B and training), ideally Spot | Run ComfyUI headless with its API; shut down when idle |
| Storage | Cloud Storage bucket per stage (`refs/`, `layout/`, `keyframes/`, `clips/`, `fx/`, `comp/`) | Lifecycle rules to delete rejected takes |
| Cost control | Budgets and alerts in Billing | Set an alert at 50%, 75% and 90% of the credits |

**Budget logic** (set real numbers once we know the credit amount; check current Vertex prices before committing):
- Video generation is the biggest cost. Each final second of trailer typically needs several takes, so budget roughly *final seconds × 3 to 5 takes × price per second*. Use the cheap Veo tier or open-source models for all exploration and the top tier only for approved hero shots.
- Open-source video on a rented GPU is cheapest per take but slower; use it for the high-take-count action shots.
- Image generation and Gemini reviews are small by comparison.

## 5. What Claude Code does

- Maintains `shots.json` and generates every prompt, file name and report from it.
- Writes and runs Blender Python: scene setup per shot, camera moves, control-pass rendering, batch renders.
- Drives ComfyUI through its API: queue workflows per shot with the right LoRAs, seeds and control inputs.
- Calls Vertex AI for images, Veo clips and Gemini reviews in batches, with retries and cost logging.
- Runs the QA loop and writes `pipeline_progress.json` (already started in the repo).
- Builds the procedural mandala, yantra and chakra generators and the lens-effects scripts.
- Assembles review reels (ffmpeg) and keeps everything versioned in the GitHub repo.
- Tracks spend against the GCP credits.

People still do: story, the style bible paintings, approving designs, acting out performances, choosing takes, hand-drawn FX polish, final edit and music.

## 6. Roadmap

1. **Pilot sequence first (10 shots, about 20 seconds).** Pick a short Kurukshetra moment with one duel, one ritual beat and one impact frame. Run it through every stage above. This proves the hybrid method before spending most of the credits.
2. **Style bible and character set** for the main cast, with LoRAs trained.
3. **Full animatic** of the trailer in Blender, cut to temp music.
4. **Production in act order**: keyframes, motion, FX, comp; review each act as a reel.
5. **Finishing**: grade, lens pass, sound, voices, titles.

Decision points that change the plan: the size of the GCP credit; whether we have a local GPU (otherwise all open-source work runs on GCP); and whether the team includes anyone who can draw FX by hand (otherwise lean harder on AI FX plates and procedural line art).

## 7. Risks and how to handle them

| Risk | Mitigation |
|---|---|
| Characters drift between shots | LoRAs trained on our sheets, color-ID passes, Gemini QA that checks the character sheet |
| AI motion ignores the planned camera | Use video-to-video from the Blender animatic for anything important |
| The look slides toward generic glossy 3D | Strong negative prompts, painted keyframes as anchors, impact frames and hand-drawn FX to break the AI look |
| Credits run out mid-production | Pilot first, cheap tiers for exploration, budget alerts, Spot GPUs |
| Copyright or likeness problems | Never use the Baahubali frames as model input; original designs only; no real actor faces |
| Model versions change | Keep the pipeline model-agnostic: every model is a step in `shots.json` that can be swapped |

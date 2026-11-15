# Arjuna vs Karna battle trailer: plan v2 (2026-11-15)

Status: plan only. Nothing in this file has been generated or paid for. Every paid stage waits for sai's written approval of its quoted cost (bible.md money gates, $15 a day).

## 1. Why the last attempts were not good

- **Stage 1 v1 images:** the character sheets used the scene style prompt (dust, frame, letterbox) and the older `gemini-2.5-flash-image` model, while the approved SH170 Arjuna frame and the manga sketches were made with Nano Banana 2.1 (`gemini-3.1-flash-image`). The prompts were text only: nothing tied them to the look of the concept art.
- **The pilot trailer (main branch):** Veo clips were made from layout frames without locked characters, so faces, armor and chariots drift from shot to shot, and there was no hand-drawn FX or impact-frame pass. The result reads as separate AI clips, not one battle.
- **Fix:** lock the look and the characters first, make the whole battle in a Blender layout so every shot shares the same space and camera rules, and let AI only paint and animate on top of that layout.

## 2. What the concept art folder says (C:\Users\dharm\Downloads\conceptartmahabharat, 59 images)

Most images are classical oil-painted epic illustration: warm gold sunlight, realistic anatomy, richly ornamented gold armor and chariots, white horses, banners, umbrellas, and dusty battlefields seen from low eye level.

The images that define the battle look:

| Image | Use it for |
|---|---|
| 6, 42 | Arjuna and Krishna's gold chariot, four white horses, ape banner, army in dust |
| 13, 28 | Krishna as charioteer, lion-headed gold chariot front |
| 5, 46 | Karna's silhouette: gold sculpted armor, crown, drawing the bow from the chariot |
| 34 | Arrow storm and chariot charge, umbrella, horses at full gallop |
| 33, 36, 40 | Chariot crashes, elephants, spears, dust trails, scale of the melee |
| 24, 25 | Darker, fire-lit mood for the night/doom beats (sinking wheel, Anjalika) |
| 22, 39 | Divine light and Vishvarupa energy (Krishna's power, the final light column) |
| 37 | Shield and armor detail, extreme low angle |
| hastinapur_assets | White marble and gold props (not needed for the battle; for later episodes) |

## 3. Style decision (sai to choose)

The folder is painted realism; "Arcane style" is stylized painterly 3D with brush textures and hand-drawn FX. They are different looks. Options:

- **A. Concept-art look:** oil-painted realism like images 5, 34, 42. Most faithful to the folder, hardest to keep consistent in motion.
- **B. Arcane-like look:** stylized painterly 3D, graphic shapes, hand-drawn FX. Easiest to keep consistent, furthest from the folder.
- **C. Hybrid (recommended):** the folder's designs, gold light, palette and costume detail, painted with visible brush texture and hard-edged shadows; energy (arrows, lightning, sun-fire) and impact frames drawn in 2D on twos. This is "painted epic" for form and "Arcane-like" only for energy and motion.

The epic war-film grammar we want (wide shots of two armies, tiny heroes against a huge sky, slow-motion hero beats, arrow storms that blot out the sun, chariot charges at wheel height, speed ramps, impact frames, drum score with silence before each release) is in the existing 22-shot list (`shots.md`). We use that grammar with our own designs; no film or TV frame is ever given to a model (bible.md "Never").

## 4. 2D or 3D, and which tools

Both: **3D owns form, space and camera; AI owns paint; 2D owns energy.**

| Tool | Needed? | Role | On this PC |
|---|---|---|---|
| Blender | Yes, core | Kurukshetra ring, two chariots, horses, instanced armies, cameras per shot from `shots.json`, grey animatic, depth and line passes | Blender 5.2 installed, Blender MCP running |
| Nano Banana 2.1 (`gemini-3.1-flash-image`) | Yes | Character sheets, then paint-over of each Blender keyframe with the passports as references | Vertex AI, project cs-project-07zg2j2c (gcloud login works) |
| Google Veo 3.1 | Yes | Image-to-video from first/last keyframes: Fast at 720p for drafts, full model for 8 hero shots | Vertex AI |
| Gemini (text) | Yes | QA reviewer that scores every frame against the passports and bible | Vertex AI |
| 2D FX | Yes | Arrows, Arjuna's blue lightning, Karna's sun-fire, impact frames, on twos; Blender Grease Pencil and `preproduction/scripts/compose.py` | Free |
| ffmpeg + DaVinci Resolve | Yes | Edit, grade, titles, sound, YouTube export (16:9 trailer, 9:16 Short) | ffmpeg installed; Resolve not checked |
| Unreal Engine 5.8 | Not now | Installed, but this PC has a GTX 1650 (4 GB) and 7 GB RAM: crowd battle scenes would be very slow. Blender with a simple toon shader is enough because the AI paints the final look. Revisit with a stronger GPU or a cloud workstation. | Installed |
| Local ComfyUI / Flux / Wan | No | Needs 12+ GB GPU memory | Not installed |

## 5. Stages, costs and gates

| Stage | What | Cost (estimate) | Gate |
|---|---|---|---|
| 0. Look lock (free) | Style board from the images in section 2; bible.md v2 (style prompt rewritten from the concept art); passports v2 for Arjuna, Karna, Krishna, Shalya; character sheet prompt (front/side/back, plain grey, full body, 3:4) | $0 | sai picks A/B/C and approves bible v2 |
| 1. Character lock | Nano Banana 2.1: Karna and Arjuna sheets (front, side, back), Shalya front; up to 4 tries each; Krishna already has an approved close-up | about $1 (price of the 3.1 model to confirm) | sai approves each sheet |
| 2. Blender layout (free) | Battlefield, chariots, horses, armies, 22 cameras, grey animatic at 720p replacing the HTML animatic | $0 | sai approves the timing and cameras |
| 3. Keyframes | Paint-over of each Blender frame, first and last frame per shot, up to 3 tries, Gemini QA | about $3 to $6 | Reviewer pass plus sai approves |
| 4. Motion drafts | Veo 3.1 Fast, 720p, no audio, about 5 s per shot, 2 takes | about $18 | sai approves the draft cut |
| 5. Hero finals | Veo 3.1 full on 8 hero shots (A02, A06, A08, A13, A14, A16, A19, A21) | about $10 | sai approves |
| 6. FX, edit, sound (free) | 2D FX and impact frames, grade, free-licensed drums and drone, titles, 1080p trailer and a 9:16 Short | $0 | sai approves before upload |
| | **Total** | **about $32 to $36, cap $45** | |

## 6. Rights check before YouTube

Many images in the concept folder look like published paintings by other artists. Unless sai made them or has a licence, they are used only as written style notes in this plan: they are not given to any model as image references and nothing in the trailer copies them. If some images are sai's own (for example the hastinapur_assets renders), name them and they can be used as direct references.

## 7. Questions for sai

1. Style A, B or C?
2. Which images in the concept folder are your own (usable as direct references)?
3. Keep the 90 s, 22-shot story in `shots.md`, or change it?
4. Approve stage 0 (free) now?

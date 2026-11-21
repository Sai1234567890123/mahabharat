# Story scene 01: "Suryaputra" (Karna at dawn, the 17th day) · plan v1 · 2026-11-21

Free plan, nothing generated. Web series look (bible), locked hero set (`cast/*/web/`). Route: hybrid (sai, 2026-11-20):
quiet close-ups from key frames by image-to-video, one action per shot; Blender only where the action must be exact.

## Why this scene first

Sai's reference reel that matched best was a slow, emotional scene of one hero, with close-ups of eyes and hands and one
subtitle line per shot. Karna's dawn prayer is canon (he worships Surya at the river every day; Indra came to him there
for the armour and earrings), needs only Karna (Shalya in silhouette), and sets up the duel: the son of the sun goes to
die on the day his father rises. 45 s, 9 shots, 9:16 safe.

## Shots

| # | Sec | Shot | One action | Line (subtitle) | Route |
|---|-----|------|------------|-----------------|-------|
| 1 | 5 | Wide, painted: the river in blue pre-dawn haze, war camp fires on the far bank, one tiny figure waist-deep in the river | water ripples, mist drifts | (none) | key frame + i2v |
| 2 | 5 | Close-up, Karna's cupped hands lift water toward the horizon | water pours from his hands, first light catches it | "Father." | key frame + i2v |
| 3 | 4 | Extreme close-up, his eyes, the sun's rim reflected | he closes his eyes | (none) | key frame + i2v |
| 4 | 5 | Close-up, profile: bare earlobes, faint healed scars, gold light rising on his face | light rises slowly across his face | "I gave away what you gave me." | key frame + i2v |
| 5 | 5 | Medium, low angle, Karna in profile facing frame left: the sun disc clears the horizon ahead of him; the sun-face on his cuirass (on a stone in the foreground) flares | sun rises, the cuirass glints | (none) | key frame + i2v |
| 6 | 5 | Close-up, his hand closes on Vijaya resting on a stone | fingers tighten on the grip | "Today I keep only my word." | key frame + i2v |
| 7 | 4 | Medium, Shalya in silhouette by the chariot, horses stamping; Karna walks up out of the water | Karna walks toward camera | Shalya: "The Pandavas wait, son of a charioteer." | Blender (walk) or i2v |
| 8 | 5 | Close-up, Karna's face, half gold, half blue shadow, a small smile | he smiles | "Let them see the sun." | key frame + i2v |
| 9 | 7 | Wide, painted: the chariot rolls out toward the dust of Kurukshetra, elephant-rope standard against the sunrise | chariot moves away, dust rises | title card (in the edit) | key frame + i2v |

Rules held: no earrings (scars only, bloodless), no tilak, nothing on his back; Karna's horses dun; the elephant-rope
standard on his chariot (canon); Shalya appears only in silhouette until he is designed.

## Key frames (v1 prompts, 2026-11-21)

Script: `tools/gen_scene01_keyframes.py` (group `scene01`, 9 images, about $0.63; `--dry-run` prints every prompt).
Refs: style frame `cast/karna/web/close_v1.png` (face, look) and `full_v2.png` (body, bow) on every Karna shot;
sai's `refs/concept/concept_42.jpeg` for the plain and sky of shot 9 only (its chariot, white horses and green banner are
excluded in the prompt). Costume: shots 1 to 7 at prayer (crown, cuirass, sash and bracers off, wet saffron dhoti only,
earlobe scars pale and bloodless); shot 8 fully armed as in the hero set. The river is left unnamed (Kurukshetra lies
between the Sarasvati and Drishadvati, not on the Ganga). Shot 5 now keeps Karna facing the sun (frame left), so screen
direction matches the duel. Output: `episodes/ep01_arjuna_vs_karna/keyframes/s01_NN_v<take>.png`. Shot 3 (eyes) is the
one frame whose 9:16 cut will crop the outer corners of the eyes.

## Needs before any paid step

- Shalya: silhouette only in this scene, no design needed yet.
- Key frames: 9 images from the locked hero set and sai's concept paintings (river and camp from concept 34/42), about
  $0.07 each, about $0.63. Each needs sai's line.
- Image-to-video: 9 clips of 4 to 7 s. Model and price to confirm before quoting (Veo on sai's project, or another
  provider sai chooses). Quote per clip before any run.
- Edit, subtitles, music bed and the 9:16 cut: free.

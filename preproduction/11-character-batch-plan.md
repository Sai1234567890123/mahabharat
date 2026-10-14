# Character batch plan: the next seven heroes as 3D proxies

Goal: original, canon-faithful character references for seven heroes, then one TRELLIS.2 session to turn them into proxy meshes for Blender layout and control passes. No GPU spend until Sai approves a specific VM and rate.

Cast, in order: Arjuna, Bhishma, Duryodhana, Bhima, Yudhishthira (all in the pilot, see `03-characters.md`), then Karna and Draupadi (listed as "later characters" in `02-style-bible.md`, so their designs below are first drafts).

## Rules for every character

- **Original faces only.** Describe features (face shape, brows, nose, jaw, hair, skin tone, expression). Never name or imitate a real actor, a film character or any person. Every image must say it is not based on a real person.
- **Use the project's own look:** painterly stylized CG per `02-style-bible.md` section 9. The Krishna test image was photographic, which is not the series style. Use the style prompt below instead.
- **One image per character:** full body, front view, A-pose, arms slightly away from the body, feet visible, plain flat background, even light. That gives TRELLIS a clean silhouette. Ask for a separate close-up only after the body mesh is accepted.
- **Face check:** Sai approves each image in his own words before it is used as input.
- **Canon check:** costume and props follow the cited source lines in `03-characters.md` and Ganguli.

## Shared prompt wrapper

Paste this around each character block:

```
Painterly stylized CG character design sheet, single character, full body, front view,
A-pose with arms slightly away from the body, feet visible, plain flat neutral grey
background, even soft lighting, hand-painted textures with visible brushwork, flat value
blocks, simplified readable silhouette, Indian epic iconography. Original face, not based
on any real person or existing character. No text, no logos, no watermarks.
No photorealism, no plastic 3D look, no real actor likeness.
[CHARACTER BLOCK]
```

Negative prompt: photorealistic, photograph, real person, celebrity, text, watermark, extra limbs, extra fingers, blurry, cropped feet, busy background, multiple characters.

## Character blocks

### 1. Arjuna
- **Role:** the archer who doubts, then rises (`03-characters.md`).
- **Build and silhouette:** tall, narrow, upright like an arrow; 8.5 heads tall.
- **Face (original):** young, long face, sharp straight brows, steady eyes, curly dark hair to the neck (Ganguli: "O thou of curly hair", line 4830).
- **Skin:** warm brown `#8A5A3C`.
- **Costume:** white and silver scale armor on the torso, blue sash, wrist guards, simple crown band.
- **Props:** Gandiva bow, held unstrung at his side; two quivers.
- **Energy / accent:** electric blue `#6FC3FF`.
- **Block text:** "Young archer prince, tall and narrow, warm brown skin, long face with sharp straight brows and curly dark hair, white and silver scale armor, blue sash, wrist guards, simple crown band, long dark bow in one hand, two quivers on the back, calm focused expression."

### 2. Bhishma
- **Role:** the grandsire; opens the battle with a roar and a conch (lines 3475 to 3478).
- **Build and silhouette:** very tall and straight, a pillar; 9 heads tall.
- **Face (original):** old, long and lean, deep-set eyes, strong straight nose, white beard to the chest, white hair tied back, grave and calm.
- **Skin:** pale tan.
- **Costume:** white and silver armor, white dhoti, plain with a gold band on the brow.
- **Props:** large conch, held low; bow at his side.
- **Energy / accent:** silver-white with river aqua `#CDEFF2`.
- **Block text:** "Elderly warrior patriarch, very tall and straight, pale tan skin, lean face with deep-set eyes, long white beard and white hair tied back, white and silver armor, plain white dhoti, thin gold band on the brow, large white conch held low, grave calm expression."

### 3. Duryodhana
- **Role:** Kaurava prince watching with fierce joy.
- **Build and silhouette:** broad shoulders, heavy wedge; mace on his shoulder.
- **Face (original):** square jaw, thick brows, strong nose, short dark beard, proud half-smile, dark hair in a topknot.
- **Skin:** olive-brown `#7A5A3A`.
- **Costume:** crimson `#9E1B2F` and black with heavy gold ornament.
- **Props:** mace over one shoulder.
- **Energy / accent:** blood red `#D0213F`.
- **Block text:** "Proud royal warrior prince, broad shoulders and heavy build, olive-brown skin, square jaw with thick brows and short dark beard, crimson and black armor with heavy gold ornament, dark hair in a topknot, large mace resting on one shoulder, confident fierce expression."

### 4. Bhima
- **Role:** blows the huge conch Paundra (line 3482).
- **Build and silhouette:** wide boulder mass, thick neck; 8 heads tall, 1.5x shoulder width.
- **Face (original):** broad round face, thick neck, heavy brows, short curly dark hair, full mustache, fierce open expression.
- **Skin:** dark umber `#5A3A28`.
- **Costume:** saffron `#E07A1F` and iron, minimal upper armor, bare arms.
- **Props:** heavy mace, large dark conch at his belt.
- **Energy / accent:** wind green-cyan `#9FE3C1`.
- **Block text:** "Giant warrior, very wide shoulders and thick neck, dark umber skin, broad round face with heavy brows and full mustache, short curly dark hair, saffron cloth and iron arm guards, bare muscular arms, large mace in one hand, big conch at the belt, fierce open expression."

### 5. Yudhishthira
- **Role:** the eldest; blows Anantavijaya (line 3483).
- **Build and silhouette:** upright, square, still; a parasol behind him signals kingship.
- **Face (original):** oval face, level brows, gentle eyes, neat short beard, calm and composed.
- **Skin:** warm brown `#7E5A40`.
- **Costume:** cream and royal blue `#2C4A8C`, modest crown.
- **Props:** conch at his side; no weapon drawn.
- **Energy / accent:** steady pale gold `#F3DCA0`.
- **Block text:** "Calm royal elder brother, upright square posture, warm brown skin, oval face with level brows and gentle eyes, neat short beard, cream and royal blue royal garments, modest gold crown, conch held at the side, composed gentle expression."

### 6. Karna (first draft, verify against Ganguli)
- **Role:** the warrior born with armor and earrings; solar lineage.
- **Build and silhouette:** tall, broad-chested, sunburst shape.
- **Face (original):** strong jaw, high brow, intense steady eyes, long dark hair, serious, proud and slightly sad.
- **Skin:** warm bronze.
- **Costume:** sun gold armor `#E8B92F` with large circular gold earrings, deep red cloth.
- **Props:** long bow; no standard.
- **Energy / accent:** solar orange `#FF7A2E`.
- **Block text:** "Proud warrior hero, tall and broad-chested, warm bronze skin, strong jaw and high brow with intense steady eyes, long dark hair, gold chest armor, large round gold earrings, deep red cloth, long bow in one hand, serious proud expression."
- **Check before use:** cite the Ganguli lines that describe the armor and earrings. Not yet cited in the repo.

### 7. Draupadi (first draft, verify against Ganguli)
- **Role:** the princess of Panchala, born of the sacrificial fire; central to the Pandavas.
- **Build and silhouette:** tall, slender, flame shape; long loose hair.
- **Face (original):** oval face, large long eyes, arched brows, full lips, dark, very long unbound hair, dignified and fiery.
- **Skin:** deep warm brown.
- **Costume:** red and gold sari with a gold waist chain and simple jewelry.
- **Props:** none, or a plain garland.
- **Energy / accent:** flame orange `#E8862A`.
- **Block text:** "Dignified royal woman, tall and slender, deep warm brown skin, oval face with large long eyes and arched brows, very long loose dark hair to the waist, red and gold sari, gold waist chain, simple gold jewelry, composed fiery expression."
- **Check before use:** cite the Ganguli lines for her birth and appearance. Not yet cited in the repo.

## Workflow and cost per batch

| Step | Who | Cost |
|---|---|---|
| 1. Generate one image per character with the wrapper above | Sai in Nano Banana | Vertex credits, per-image rate to confirm in the console |
| 2. Face and canon check for each image | Sai approves in words; Claude reviews against the source lines | none |
| 3. Mesh run: start the existing `trellis-l4-1024` VM in its own zone once, run 7 meshes at 1024 cascade | Claude, after Sai's go that names the GPU and rate | about 10 min each, about $0.15 each, about $1 for the batch (estimate) |
| 4. Stop the VM, confirm the stop and list resources | Claude | none |
| 5. Blender cleanup: scale, pivot, normals, naming, export | Claude | none |
| 6. Review in Blender against the silhouette lineup | Sai | none |

Fallbacks: if the L4 is not available in its own zone, the plan stops and asks. It does not search other zones. If a mesh runs out of memory, drop that character to 512.

## Notes

- A mesh only needs to be good enough for silhouette, depth and pose (see `trailer-analysis/03-build-plan.md`). 512 may be enough for most characters, with 1024 for hero close-ups.
- Run characters in order so the Pandava and Kaurava shape language stays consistent (vertical against heavy horizontals, see `02-style-bible.md` section 4).
- Voice and likeness: no cloned voices and no real-person likeness for any of these characters.

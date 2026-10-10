# Prompt pack (pilot)

Ready-to-run prompts for each shot, generated from `data/shots.json`. Use them with the control passes in `art/control/` (depth, line art, IDs) so the AI paint-over keeps the Blender layout. Never add a reference image from another film or a real actor.

## How to use

1. **Keyframe (image).** Nano Banana (Gemini 2.5 Flash Image) or Imagen on Vertex AI for quick passes; Flux or Qwen-Image with ControlNet depth + line art in ComfyUI for layout-locked passes. Prompt = global style + act line + cast lines + shot prompt. Feed `SHxxx_depth.png` and `SHxxx_lineart.png` as control images at strength 0.5 to 0.7, and the concept frame `art/frames/SHxxx.jpg` as the color reference.
2. **QA.** Ask Gemini to score the keyframe against the style bible checklist (palette, rim light, silhouette, no photorealism, character codes) and regenerate below 8/10.
3. **Motion.** Veo 3.1 image-to-video (first frame = approved keyframe; for shots with a big change, first and last frame) or Wan 2.2 VACE video-to-video over the Blender animatic. Use the motion prompt.
4. **2D FX and impact frames** are composited afterwards (`scripts/compose.py`), not generated, so they stay on model and on twos.

## Global style (every prompt)

> Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.

Negative prompt (models that take one): `photorealistic, live action, plastic CGI, video game render, text, watermark, logo, extra fingers, deformed hands, modern objects, western fantasy armor, real celebrity face`

## Act lines

- **Act A, Dawn of war:** Act A palette: apricot dawn, dusty gold haze, warm violet-brown shadows, saffron accents.
- **Act B, Stillness:** Act B palette: desaturated blue-grey, hidden sun, cold slate shadows; the only warm color is a thin gold rim on Krishna.
- **Act C, Vishvarupa:** Act C palette: black-violet cosmos, white-gold core light, teal, magenta and gold sacred geometry.
- **Act D, War dawn:** Act D palette: hot orange sun, red dust, burnt umber shadows, electric blue energy on Arjuna.

## Cast lines

- **Krishna:** Krishna: deep indigo-blue skin, calm almond eyes, faint smile, yellow silk dhoti and upper cloth, low gold crown with a single peacock feather, gold necklaces and armlets, white-gold divine energy with teal edge.
- **Arjuna:** Arjuna: young archer, warm brown skin, sharp brows, curly black hair, white and silver scale armor, blue sash, very tall dark horn-and-gold bow (Gandiva), electric blue lightning energy.
- **Bhishma:** Bhishma: towering elderly warrior, long white beard and hair, white and silver armor, plain brow band, silver-white energy with river-aqua edge.
- **Duryodhana:** Duryodhana: broad heavy-shouldered prince, crimson and black armor with heavy gold ornament, mace on shoulder, blood-red energy.
- **Bhima:** Bhima: massive warrior, dark umber skin, bare powerful arms, saffron dhoti, iron bands, huge mace, wind green-cyan energy.
- **Yudhishthira:** Yudhishthira: calm upright king, cream dhoti with royal blue upper cloth, modest crown, white royal parasol, steady pale gold energy.

## Shots

### SH010 The field at dawn (act A, 7s)

Control passes: `art/control/SH010_depth.png`, `art/control/SH010_lineart.png`. Color reference: `art/frames/SH010.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act A palette: apricot dawn, dusty gold haze, warm violet-brown shadows, saffron accents.
Arjuna: young archer, warm brown skin, sharp brows, curly black hair, white and silver scale armor, blue sash, very tall dark horn-and-gold bow (Gandiva), electric blue lightning energy.
wide long-lens shot from behind an ancient Indian army at dawn, two vast armies facing each other across a bare dusty plain, thousands of banners, low sun behind the far army, golden dust haze, one giant ape-emblem banner rising above all others, tiny figures, epic scale. 45mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
slow crane down and push in over the army toward the empty ground, banners rippling, dust drifting low, 7 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

### SH020 The ape banner (act A, 4s)

Control passes: `art/control/SH020_depth.png`, `art/control/SH020_lineart.png`. Color reference: `art/frames/SH020.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act A palette: apricot dawn, dusty gold haze, warm violet-brown shadows, saffron accents.
Arjuna: young archer, warm brown skin, sharp brows, curly black hair, white and silver scale armor, blue sash, very tall dark horn-and-gold bow (Gandiva), electric blue lightning energy.
low angle long lens shot of a tall chariot standard topped by a crouching golden ape emblem, saffron banner snapping in wind, silhouetted against a low dawn sun, lens flare. 70mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
banner snaps and ripples, sun flare breathes, very slight upward drift, 4 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

### SH030 The grandsire's roar (act A, 4s)

Control passes: `art/control/SH030_depth.png`, `art/control/SH030_lineart.png`. Color reference: `art/frames/SH030.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act A palette: apricot dawn, dusty gold haze, warm violet-brown shadows, saffron accents.
Bhishma: towering elderly warrior, long white beard and hair, white and silver armor, plain brow band, silver-white energy with river-aqua edge.
Duryodhana: broad heavy-shouldered prince, crimson and black armor with heavy gold ornament, mace on shoulder, blood-red energy.
low angle medium shot of a towering elderly warrior with long white beard on a white chariot, head thrown back in a lion's roar, holding a white conch high, white and silver armor, tall palmyra standard behind, army banners and dust. 28mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
warrior throws head back and roars, raises the conch, beard and cloth whip in wind, slow push in, 4 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

### SH040 Bhishma's conch (act A, 3s)

Control passes: `art/control/SH040_depth.png`, `art/control/SH040_lineart.png`. Color reference: `art/frames/SH040.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act A palette: apricot dawn, dusty gold haze, warm violet-brown shadows, saffron accents.
Bhishma: towering elderly warrior, long white beard and hair, white and silver armor, plain brow band, silver-white energy with river-aqua edge.
side view of a white-bearded warrior blowing a large white conch, concentric silver-aqua sound rings bursting outward as hand-drawn 2D effects, army erupting behind. 50mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
conch blast, sound rings expand outward on twos, camera shake, 3 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

### SH050 Like a thousand suns (act A, 5s)

Control passes: `art/control/SH050_depth.png`, `art/control/SH050_lineart.png`. Color reference: `art/frames/SH050.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act A palette: apricot dawn, dusty gold haze, warm violet-brown shadows, saffron accents.
Krishna: deep indigo-blue skin, calm almond eyes, faint smile, yellow silk dhoti and upper cloth, low gold crown with a single peacock feather, gold necklaces and armlets, white-gold divine energy with teal edge.
Arjuna: young archer, warm brown skin, sharp brows, curly black hair, white and silver scale armor, blue sash, very tall dark horn-and-gold bow (Gandiva), electric blue lightning energy.
heroic low angle three-quarter shot of an ornate golden Indian war chariot with two large spoked wheels and a hundred small bells, four white horses, a tall ape-emblem banner, blue-skinned charioteer in yellow silk holding the reins, young archer in white and silver armor holding a very tall bow, blazing in direct sunlight, gold glints. 35mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
low tracking arc around the chariot, horses stamp and toss their heads, bells shiver, gold glints, 5 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

### SH060 Panchajanya and Devadatta (act A, 3s)

Control passes: `art/control/SH060_depth.png`, `art/control/SH060_lineart.png`. Color reference: `art/frames/SH060.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act A palette: apricot dawn, dusty gold haze, warm violet-brown shadows, saffron accents.
Krishna: deep indigo-blue skin, calm almond eyes, faint smile, yellow silk dhoti and upper cloth, low gold crown with a single peacock feather, gold necklaces and armlets, white-gold divine energy with teal edge.
Arjuna: young archer, warm brown skin, sharp brows, curly black hair, white and silver scale armor, blue sash, very tall dark horn-and-gold bow (Gandiva), electric blue lightning energy.
symmetrical front two-shot on a golden chariot, blue-skinned divine charioteer in yellow silk and a young archer in silver armor each lifting a white conch shell, faint golden halo behind the charioteer. 50mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
both lift their conches to their lips in unison, locked camera, 3 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

### SH070 They blow together (act A, 4s)

Control passes: `art/control/SH070_depth.png`, `art/control/SH070_lineart.png`. Color reference: `art/frames/SH070.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act A palette: apricot dawn, dusty gold haze, warm violet-brown shadows, saffron accents.
Krishna: deep indigo-blue skin, calm almond eyes, faint smile, yellow silk dhoti and upper cloth, low gold crown with a single peacock feather, gold necklaces and armlets, white-gold divine energy with teal edge.
Arjuna: young archer, warm brown skin, sharp brows, curly black hair, white and silver scale armor, blue sash, very tall dark horn-and-gold bow (Gandiva), electric blue lightning energy.
low three-quarter shot of a blue-skinned divine charioteer and a young archer blowing white conch shells on a golden chariot, interlocking white-gold and electric-blue concentric sound rings exploding outward as hand-drawn 2D effects. 30mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
conch blast, two sets of sound rings expand and interlock on twos, cloth and hair blown back, 4 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

### SH080 Paundra and Anantavijaya (act A, 5s)

Control passes: `art/control/SH080_depth.png`, `art/control/SH080_lineart.png`. Color reference: `art/frames/SH080.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act A palette: apricot dawn, dusty gold haze, warm violet-brown shadows, saffron accents.
Bhima: massive warrior, dark umber skin, bare powerful arms, saffron dhoti, iron bands, huge mace, wind green-cyan energy.
Yudhishthira: calm upright king, cream dhoti with royal blue upper cloth, modest crown, white royal parasol, steady pale gold energy.
massive warrior with dark skin and saffron dhoti blowing a huge ribbed conch, green-cyan wind rings tearing up dust; behind him a calm king under a white parasol blowing a gold-banded conch with pale gold rings. 35mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
whip pan from the massive warrior's blast to the king under the parasol, rings expand on twos, 5 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

### SH090 The blare (act A, 5s)

Control passes: `art/control/SH090_depth.png`, `art/control/SH090_lineart.png`. Color reference: `art/frames/SH090.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act A palette: apricot dawn, dusty gold haze, warm violet-brown shadows, saffron accents.
ultra wide shot from behind a crowd of soldiers in dark armor, across a dusty plain a wall of white-gold and blue concentric sound rings rolling across the sky toward camera, ground dust lifting in a shockwave. 20mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
sound wave rolls toward camera, soldiers in foreground recoil, violent handheld shake, 5 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

### SH100 Between the two armies (act B, 5s)

Control passes: `art/control/SH100_depth.png`, `art/control/SH100_lineart.png`. Color reference: `art/frames/SH100.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act B palette: desaturated blue-grey, hidden sun, cold slate shadows; the only warm color is a thin gold rim on Krishna.
Krishna: deep indigo-blue skin, calm almond eyes, faint smile, yellow silk dhoti and upper cloth, low gold crown with a single peacock feather, gold necklaces and armlets, white-gold divine energy with teal edge.
Arjuna: young archer, warm brown skin, sharp brows, curly black hair, white and silver scale armor, blue sash, very tall dark horn-and-gold bow (Gandiva), electric blue lightning energy.
from behind a golden chariot, a young archer in silver armor turning to speak to the blue-skinned charioteer, grey overcast light, two armies ahead, muted cold colors. 35mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
slow push in, archer turns his head toward the charioteer, banners still, 5 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

Dialogue: Arjuna: "Place my car between the two armies, so that I may observe these that stand here." (B06 lines 3498-3499)

### SH110 The empty ground (act B, 6s)

Control passes: `art/control/SH110_depth.png`, `art/control/SH110_lineart.png`. Color reference: `art/frames/SH110.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act B palette: desaturated blue-grey, hidden sun, cold slate shadows; the only warm color is a thin gold rim on Krishna.
high angle wide view looking down at a single small chariot with four white horses on a bare stripe of earth between two vast armies, grey overcast light, cold desaturated colors. 16mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
locked high angle, the chariot rolls slowly into the center and stops, dust trails behind, 6 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

### SH120 Faces of kin (act B, 5s)

Control passes: `art/control/SH120_depth.png`, `art/control/SH120_lineart.png`. Color reference: `art/frames/SH120.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act B palette: desaturated blue-grey, hidden sun, cold slate shadows; the only warm color is a thin gold rim on Krishna.
Arjuna: young archer, warm brown skin, sharp brows, curly black hair, white and silver scale armor, blue sash, very tall dark horn-and-gold bow (Gandiva), electric blue lightning energy.
Bhishma: towering elderly warrior, long white beard and hair, white and silver armor, plain brow band, silver-white energy with river-aqua edge.
over-the-shoulder long lens shot past a young archer's silver shoulder toward an enemy front line where an elderly white-bearded warrior and other noble warriors stand on chariots, compressed perspective, cold grey light. 85mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
slow rack focus from the archer's shoulder to the distant elders, 5 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

### SH130 Gandiva slips (act B, 5s)

Control passes: `art/control/SH130_depth.png`, `art/control/SH130_lineart.png`. Color reference: `art/frames/SH130.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act B palette: desaturated blue-grey, hidden sun, cold slate shadows; the only warm color is a thin gold rim on Krishna.
Krishna: deep indigo-blue skin, calm almond eyes, faint smile, yellow silk dhoti and upper cloth, low gold crown with a single peacock feather, gold necklaces and armlets, white-gold divine energy with teal edge.
Arjuna: young archer, warm brown skin, sharp brows, curly black hair, white and silver scale armor, blue sash, very tall dark horn-and-gold bow (Gandiva), electric blue lightning energy.
side profile of a golden chariot between two armies under grey sky, a young archer in silver armor sinking to the floor, a very tall bow slipping from his hand, the blue-skinned charioteer standing still at the front. 50mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
archer sinks down, bow slides and falls, charioteer does not move, 5 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

Dialogue: Arjuna: "My body trembles, and my hair stands on end. Gandiva slips from my hand." (B06 lines 3519-3521)

### SH140 Krishna turns (act B, 4s)

Control passes: `art/control/SH140_depth.png`, `art/control/SH140_lineart.png`. Color reference: `art/frames/SH140.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act B palette: desaturated blue-grey, hidden sun, cold slate shadows; the only warm color is a thin gold rim on Krishna.
Krishna: deep indigo-blue skin, calm almond eyes, faint smile, yellow silk dhoti and upper cloth, low gold crown with a single peacock feather, gold necklaces and armlets, white-gold divine energy with teal edge.
symmetrical close-up of a blue-skinned divine figure with a low gold crown and single peacock feather, back-lit with a thin gold rim light, a fine golden mandala ring forming behind his head, grey overcast background. 85mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
locked, he turns his face slowly toward camera, the halo ring draws itself on, 4 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

### SH150 The universal form (act C, 6s)

Control passes: `art/control/SH150_depth.png`, `art/control/SH150_lineart.png`. Color reference: `art/frames/SH150.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act C palette: black-violet cosmos, white-gold core light, teal, magenta and gold sacred geometry.
extreme wide low angle, a tiny chariot on a thin dark horizon beneath a colossal radiant multi-armed divine figure filling the night sky, crowned, holding a mace and a spinning discus, surrounded by rotating concentric mandala rings filled with countless faces and eyes, white-gold core light, teal and magenta sacred geometry, splendour of a thousand suns. 12mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
slow tilt up from the tiny chariot to the colossal form, Adishesha's hoods sway, streams of tiny warriors pour into the flaming mouths, fire flickers, the light pulses like a thousand suns, 6 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

### SH160 Arjuna beholds (act C, 4s)

Control passes: `art/control/SH160_depth.png`, `art/control/SH160_lineart.png`. Color reference: `art/frames/SH160.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act C palette: black-violet cosmos, white-gold core light, teal, magenta and gold sacred geometry.
Arjuna: young archer, warm brown skin, sharp brows, curly black hair, white and silver scale armor, blue sash, very tall dark horn-and-gold bow (Gandiva), electric blue lightning energy.
over-the-shoulder shot of a young archer in silver armor looking up at a colossal radiant cosmic figure and rotating mandala rings of faces and eyes, white-gold light on his face and armor, deep violet cosmos. 18mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
slow push in past the archer's shoulder, rings turning overhead, light flickers across his armor, 4 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

### SH170 Arjuna rises (act D, 5s)

Control passes: `art/control/SH170_depth.png`, `art/control/SH170_lineart.png`. Color reference: `art/frames/SH170.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act D palette: hot orange sun, red dust, burnt umber shadows, electric blue energy on Arjuna.
Krishna: deep indigo-blue skin, calm almond eyes, faint smile, yellow silk dhoti and upper cloth, low gold crown with a single peacock feather, gold necklaces and armlets, white-gold divine energy with teal edge.
Arjuna: young archer, warm brown skin, sharp brows, curly black hair, white and silver scale armor, blue sash, very tall dark horn-and-gold bow (Gandiva), electric blue lightning energy.
low angle heroic shot of a young archer in silver armor rising on a golden chariot and lifting a very tall bow high, crackling electric-blue lightning along the bow, hot orange sun and red dust behind him. 24mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
archer rises and raises the bow, lightning crawls along it on twos, camera cranes up with him, 5 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```

Dialogue: Arjuna: "My delusion hath been destroyed." (B06 line 5773)

### SH180 The banner, then black (act D, 4s)

Control passes: `art/control/SH180_depth.png`, `art/control/SH180_lineart.png`. Color reference: `art/frames/SH180.jpg`.

**Keyframe prompt**

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.
Act D palette: hot orange sun, red dust, burnt umber shadows, electric blue energy on Arjuna.
long lens low angle of a golden ape-emblem standard and saffron banner snapping in the wind against a huge red-orange sun, red dust, silhouette. 85mm lens, 2.39:1 widescreen.
```

**Motion prompt (Veo 3.1 / Wan 2.2)**

```
banner snaps three times in slow motion, then hard cut to black, 4 seconds. Painterly stylized animation, keep the art style of the first frame, no photorealism.
```


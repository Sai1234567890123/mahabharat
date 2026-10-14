# Krishna design lock: detailed prompts (skin choice B, approved close-up face)

Stage 1 of `13-krishna-end-to-end-pipeline.md`. These cost no GPU time. You generate the images in Nano Banana, check each one, and send them back.

## Decision recorded

- **Skin: B, natural warm brown.** The style bible row for Krishna was updated on 2026-10-13: skin is now warm medium brown `#B07856` instead of indigo-blue `#2E3F78`. That value comes from sampling the approved close-up: shadow areas about `#8B5939`, mid-tones about `#B07856`, lit areas about `#DAA484`.
- **Face: the approved close-up, unchanged.** Every image must read as the same person.

## Requirement: same face on every image

1. Attach the approved close-up to **every** generation as the reference image. Use the original file, not a screenshot.
2. Say "same character as the reference image, same face" in the prompt.
3. Generate the **front full-body first**, check the face, and only then generate the other views. If the front drifts, regenerate before going on.
4. Never attach a photo of a real person or a frame from any film.
5. After each result, run the face-match checklist below. Reject anything that fails.

### Face-match checklist (you tick each one against the close-up)

- Face shape: long oval, same jaw and chin
- Brows: level, dark, same thickness
- Eyes: almond-shaped, brown, same spacing
- Nose: straight, same width
- Mouth: closed, gentle faint smile
- Hair: dark, wavy, shoulder length, parted
- Tilak: white U-shape with a red center line on the forehead
- Earrings: round gold
- Age: young adult, same as the close-up
- Overall impression: calm, still, same person

## Character facts to include in every prompt

| Item | Detail |
|---|---|
| Role | Charioteer, then the cosmic form (`03-characters.md`) |
| Proportion | 8.5 heads tall, slim, relaxed contrapposto |
| Skin | Warm medium brown, hex `#B07856` |
| Hair | Dark, wavy, shoulder length, loose |
| Crown | Gold, simple, tall, a single peacock feather rising from the front |
| Upper garment | Yellow silk upper cloth, hex `#E8B92F`, draped over one shoulder and trailing |
| Lower garment | Yellow silk dhoti, hex `#E8B92F`, with gold border, tied at the waist, hanging to the ankles |
| Jewelry | Pearl and gold necklaces, armlets (Angada), bracelets, round gold earrings, one bright chest jewel (Kaustubha style) |
| Feet | Barefoot |
| Props | None in the sheet. The conch (Panchajanya, white with gold tips) is added later in Blender |
| Palette accents | Peacock feather teal `#1E8C8C`, gold, yellow |

## Shared wrapper (paste around every sheet block)

```
Painterly stylized CG character design sheet, single character, same character as the
reference image, same face, original face, not based on any real person or existing
character. Hand-painted textures with visible brushwork, flat value blocks, hard-edged
tinted shadows, simplified readable silhouette, Indian epic iconography, simplified hair
and cloth in painted clumps. Plain flat neutral grey background, even soft lighting, no
cast shadow on the background. Ultra clean silhouette, no text, no logos, no watermarks.
No photorealism, no plastic 3D look, no real actor likeness.
[SHEET BLOCK]
```

**Negative prompt (use for every sheet):** photorealistic, photograph, real person, celebrity, text, watermark, signature, extra limbs, extra fingers, fused fingers, cropped feet, cropped head, busy background, multiple characters, different face, weapon in hand, motion blur, heavy shadows on the background.

## Output settings for every generation

- Resolution: the highest the tool allows, at least 1536 px on the long side.
- Aspect ratio: 3:4 portrait for full-body sheets. Use 1:1 for the expression grid.
- Number of images: 4 per prompt, then choose the best.
- Keep the same seed if the tool lets you.

## Sheet blocks

### 1. Front full body (this is the TRELLIS input)

```
Full body, exact front view, camera at chest height, orthographic feel, no perspective
distortion. He stands upright in a relaxed A-pose: arms slightly away from the body,
hands open with fingers relaxed and separated, palms facing his thighs. Weight even on
both feet, feet shoulder-width apart, both bare feet fully visible. Slim body, 8.5 heads
tall. Warm medium brown skin (#B07856). Tall simple gold crown with a single teal peacock
feather rising from the front. Dark wavy shoulder-length hair. Yellow silk upper cloth
(#E8B92F) draped over the left shoulder and hanging down in front, yellow silk dhoti
(#E8B92F) with a gold border, tied at the waist, hanging to the ankles. Pearl and gold
necklaces, gold armlets on both upper arms, gold bracelets on both wrists, round gold
earrings, one bright chest jewel. Calm faint smile. No props.
```

### 2. Left side view

```
Full body, exact left side view, same character and same A-pose, same proportions and
costume, feet visible, bare feet. Show the profile of the crown and peacock feather, the
drape of the upper cloth, and the fall of the dhoti. Camera at chest height, no perspective
distortion.
```

### 3. Back view

```
Full body, exact back view, same character and same A-pose, same proportions and
costume, feet visible. Show the back of the crown, the dark wavy hair, how the upper
cloth drapes across the back, and the back of the dhoti. Camera at chest height, no
perspective distortion.
```

### 4. Expression sheet (6 faces)

```
Head and neck only, six expressions in a 3 by 2 grid on a plain flat neutral grey
background, same character and same crown, hair, earrings and tilak in every cell,
front view, even soft lighting. Row 1: calm neutral, gentle faint smile, stern with
slightly lowered brows. Row 2: eyes closed in meditation, speaking with the mouth
slightly open, wide-eyed awe. Face and head size identical in all six cells.
```

### 5. Three-quarter turn (optional, useful for the mesh check)

```
Full body, three-quarter front view from the left, same A-pose and costume, feet visible,
bare feet, no perspective distortion.
```

### 6. Hands and feet detail (optional, helps the cleanup stage)

```
Close views on a plain flat neutral grey background: both open hands palm-forward with
fingers separated, and both bare feet from the front, same warm medium brown skin
(#B07856), same gold bracelets and armlets.
```

## What to send back

1. Front full-body image (highest resolution).
2. Side view, back view, expression sheet, and any optional views.
3. Your confirmation in words: "face checked, not a real person, same as approved close-up".

## What happens next

- I review each image against the checklist and the style bible.
- I then quote the TRELLIS.2 run: which VM, the hourly rate, and the expected total, and wait for your go.
- The side and back views are for your cleanup and rigging reference, not TRELLIS input.

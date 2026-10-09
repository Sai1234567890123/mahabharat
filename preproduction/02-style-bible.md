# Style bible (v0.1, pilot)

Our own look for the Mahabharat series. It follows the ten style rules in `trailer-analysis/01-shot-analysis.md` section 9, but every design, color and motif here is original to this project. Never feed trailer frames to a model or use them as a style reference.

## 1. The look in one paragraph

Painterly stylized CG. 3D owns form, space and camera. Surfaces are painted, with visible brush texture and flat value blocks. Shadows are hard-edged and tinted, never grey. Every character has a colored rim light from the act's key color. Energy, fire, sound and divinity are drawn in 2D, animated on twos, and laid over the 3D. Big hits get 1 to 3 graphic impact frames. Sacred geometry is both magic and transition. The lens is imperfect: flares, chromatic fringe, bloom, grain.

## 2. Color script (pilot)

| Act | Beats | Mood | Sky / key | Shadow | Accent | Hex (key, shadow, accent) |
|---|---|---|---|---|---|---|
| A. Dawn of war | 1–5 | Awe, pride, noise | Apricot dawn, dusty gold haze | Warm violet-brown | Saffron banners, white steeds | `#F2B36B` `#4A2F45` `#E8862A` |
| B. Stillness | 6–9 | Doubt, grief | Desaturated blue-grey, sun hidden | Cold slate | Single gold rim on Krishna | `#9AA7B4` `#2A3340` `#E8C15A` |
| C. Vishvarupa | 10 | Terror, wonder | Black-violet cosmos with white-gold core | Deep indigo | Teal, magenta and gold geometry | `#FFF2C4` `#120B2E` `#2FD3C6` |
| D. War dawn | 11–12 | Resolve | Hot orange sun, red dust | Burnt umber | Ape banner, blue Arjuna energy | `#FF7A2E` `#3A1A12` `#6FC3FF` |

The color script strip is in `art/color-script.jpg`.

## 3. Character color and energy codes

Each hero character has a skin, a costume accent and an energy color. The energy color is used for their FX, their impact frames and their rim light in close-ups. Keep them consistent in every shot.

| Character | Skin | Accent | Energy | Shape language |
|---|---|---|---|---|
| Krishna | Deep indigo-blue `#2E3F78` | Yellow silk `#E8B92F`, peacock teal `#1E8C8C` | White-gold with teal edge `#FFE9A8` | Circles: halo, chakra, peacock feather |
| Arjuna | Warm brown `#8A5A3C` | White and silver armor, blue sash | Electric blue `#6FC3FF` (son of Indra: lightning) | Tall arrow: vertical, narrow, taut |
| Bhishma | Pale tan, white beard and hair | White and silver, gold palmyra standard | Silver-white with river aqua `#CDEFF2` (son of Ganga) | Pillar: tall rectangle, unmoving |
| Duryodhana | Olive-brown `#7A5A3A` | Crimson and black gold `#9E1B2F` | Blood red `#D0213F` | Heavy wedge: broad shoulders, down-pointing |
| Bhima | Dark umber `#5A3A28` | Saffron `#E07A1F`, iron | Wind green-cyan `#9FE3C1` (son of Vayu) | Boulder: wide, round mass |
| Yudhishthira | Warm brown `#7E5A40` | Cream and royal blue `#2C4A8C` | Steady pale gold `#F3DCA0` (son of Dharma) | Upright square: calm, balanced |

Later characters: Karna (sun gold, energy solar orange, sunburst shape), Draupadi (red and fire, energy flame-orange, flame shape), Drona (ash grey and saffron, energy brahmastra white).

Silhouettes must read as solid black shapes. See `art/silhouette-lineup.png`.

## 4. Shape and world language

- **Pandava side:** vertical lines, upright triangles, banners that rise, open clear skies behind them.
- **Kaurava side:** heavy horizontals, downward wedges, crowded standards, dust and shadow.
- **Divine:** circles and concentric rings (chakra, halo, mandala). Anything circular and glowing means the divine is present.
- **Scale:** humans are tiny against the sky. Use 5–10% frame height for figures in wide shots.
- **Architecture and props:** gold leaf, carved wood and bronze, sculpted with Indian temple ornament but simplified to big readable shapes. No fantasy armor clichés from the West.

## 5. Rendering rules

1. Toon base: 3 values per material (light, mid, shadow) plus a painted texture overlay.
2. Shadows are tinted with the act's shadow color, never neutral grey.
3. Rim light in the act's key color on every character, 2–4 px at 1080p.
4. Atmospheric depth: 3–5 layers of haze with flat color gradients; distant armies become silhouettes.
5. Outlines: thin, colored (not black), only on the silhouette and major folds. Blender Line Art or Freestyle.
6. Hair and cloth: simplified clumps with painted highlights; no strand detail.
7. Skies are matte paintings on a dome, not simulated.

## 6. 2D FX rules

- Animated on twos (12 fps) over 24 fps animation.
- **Conch sound:** concentric rings in the blower's energy color, with drawn speed lines and a dust ring at ground level. Each conch has its own color: Panchajanya white-gold, Devadatta electric blue, Paundra wind green, Anantavijaya pale gold, Sughosa and Manipushpaka silver and rose.
- **Divine light:** god rays as flat, hard-edged wedges, not volumetric blur.
- **Sudarshana chakra:** a spinning ring of 8–12 blades, gold with teal flame edge.
- **Universal form:** concentric yantra rings filled with repeated faces, eyes and arms, rotating in opposite directions.
- **Lightning (Arjuna):** branching blue lines with a white core.
- **Dust and debris:** painted shapes, not particles.

See `art/fx-sheet.jpg`.

## 7. Impact frames

- 1 to 3 frames on each big hit: the conch blast, the Gandiva drop, the universal form reveal.
- Three flat colors only: black, white, and the energy color of the character who causes it.
- Composition is graphic: heavy black shapes, radial speed lines, the hero as a white silhouette.

## 8. Lens and finishing

- Anamorphic flares (horizontal streaks) on suns and divine light.
- Chromatic aberration at frame edges, 1–3 px.
- Bloom on energy FX only.
- Film grain on everything, stronger in act B.
- Aspect ratio 2.39:1 for the pilot, letterboxed in 16:9.

## 9. Global AI style prompt

Use this in place of the old "Photorealistic cinematic epic" block in `PROMPTS.md`:

> Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.

Add the act line from section 2 and each character's codes from section 3 to every prompt.

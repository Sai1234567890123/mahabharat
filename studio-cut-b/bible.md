# Studio bible: Mahabharat battle shorts

## The two folder laws (read these first, every session)

1. **A reference image is never renamed and never regenerated.** Once a file in `cast/` or `frames/` is approved it is locked. If motion looks wrong later, fix the motion prompt, not the reference.
2. **Every generation is logged in `log.md`.** Model, prompt version, cost and verdict, one line per attempt. An unlogged good shot is a shot we cannot make again.

Money rule that sits above both: nothing is generated until the price is quoted and sai says go in his own words (`10-cost-and-safety-rules.md`). Drafts before finals. One billed step at a time.

## Logline

On the seventeenth day of the war, the two greatest archers alive, Arjuna and Karna, finally face each other across the dust of Kurukshetra, and the earth itself chooses the ending.

## World

- **One location:** the plain of Kurukshetra, the empty strip between the two hosts. Tag `@kurukshetra_d17`.
- **Light:** late afternoon, a low hot sun behind the Kaurava side. Long shadows. Red dust always moving low.
- **Colors:** dust ochre, burnt umber shadow, hot orange sky. Each hero carries one energy color and nothing else on screen may use it.
- **Location descriptor (paste verbatim):**

```
Vast flat dusty plain of Kurukshetra in late afternoon, low hot sun in a burnt-orange sky #FF7A2E, red dust haze drifting low, pale ochre ground #B48A5A with chariot ruts and broken arrows, burnt umber hard-edged shadows #3A1A12, two distant armies as flat silhouette bands with spears and banners far behind, layered atmospheric haze, matte-painted sky.
```

## Engine

Every episode is one duel. Two warriors who are equals meet, and skill cannot settle it. Something older than the fight (a vow, a curse, a boon, a debt) decides it. It can never be solved because the Mahabharata keeps supplying duels where both sides are right about something: Bhima and Duryodhana, Bhishma and Arjuna, Drona and Dhrishtadyumna, Abhimanyu in the wheel, Ghatotkacha and Karna.

## Tone

- Painterly stylized CG with hand-drawn 2D energy, in the direction of our own style bible (`preproduction/02-style-bible.md`). The targets sai named are the feel of the *Baahubali: The Eternal War* teaser and the action staging of *Arcane*: expressive cameras, speed ramps, held poses, 1 to 3 frame graphic impact frames on every big hit.
- No dialogue. Sound carries it: bowstrings, wheels, conches, wind, one music bed.
- Pacing: 90 seconds, 24 shots, four movements (challenge, arrow storm, the turn, the wheel). Fast cuts in the middle, long holds at the start and the end.
- Format: 16:9 frame with a 2.39:1 letterbox, as in the pilot. A 9:16 recut for shorts is a later pass.

## Global style line (paste at the start of every image prompt)

```
Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes.
```

## Palette (60 : 30 : 10)

| Share | Role | Color |
|---|---|---|
| 60 | Dominant: dust and sky | Ochre `#B48A5A`, orange `#FF7A2E`, pale sun `#FFC37A` |
| 30 | Secondary: shadow and metal | Burnt umber `#3A1A12`, bronze `#C9962B`, bone white `#F4EFE6` |
| 10 | Accent: energy only | Arjuna electric blue `#6FC3FF`, Karna solar orange `#FF8A1F`, Krishna white-gold `#FFE9A8` |

Impact frames use three flat colors only: black, white and the energy color of whoever lands the hit.

## Never

- No real person's face or likeness. Every face is original. The TV-serial frames in `shots/` and the Baahubali teaser frames are **never** model input and never a style reference. They may be read only to understand which story beat is meant.
- No text, logos or watermarks inside any frame.
- No gore. Karna's death is shown as light, not as a wound.
- No crowds in the foreground, no mirrors, no hands picking up or tying small objects (video models break on these). Armies stay as distant silhouette bands.
- No character, costume or shot copied from another film or show. Only formats and techniques are borrowed.
- No energy color on the wrong character.

## Canon anchors (Karna Parva, day 17)

- Arjuna's charioteer is Krishna; his standard is the ape banner; his bow is Gandiva; his steeds are white.
- Karna's charioteer is Shalya, king of Madra; his standard shows an elephant's girth-rope; his bow is Vijaya. He no longer has his natural armor and earrings: he gave them to Indra before the war.
- Beats used: the exchange of celestial weapons (fire answered by rain), the cut bowstring, the serpent arrow that Krishna dodges by pressing the chariot into the earth so it takes Arjuna's diadem instead of his head, Karna's wheel sinking, the Anjalika arrow, and the light that leaves Karna and enters the sun.
- Design choices that are ours, not canon: Karna's bay horses (the text gives him white steeds; ours are dark so the two cars read apart at a glance), his short beard, and Arjuna's eyebrow scar.

## Episode ideas (one line each)

1. **Arjuna and Karna:** two archers, one sinking wheel. (this episode)
2. **Bhima and Duryodhana:** the mace duel by the lake, and the blow below the belt.
3. **Bhishma falls:** the grandsire who cannot be killed lies down on a bed of arrows.
4. **Abhimanyu in the wheel:** a boy who knows the way in and not the way out.
5. **Ghatotkacha at night:** the giant who makes Karna spend the one weapon he was saving.

## Folder map

```
studio-cut-b/
  bible.md      this file
  cast/         one passport per character (text + locked reference images)
  episodes/     one folder per episode: script, shot cards, prompts, animatic
  frames/       approved still frames only
  renders/      raw video attempts, nobody else looks here
  selects/      accepted takes only, the edit sees nothing else
  log.md        every generation: model, prompt version, cost, verdict
```

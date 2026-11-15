# Studio bible: Mahabharat battle shorts

## The two folder laws (read first, every session)

1. **A reference image is never renamed or regenerated.** Files in `cast/*/ref_*` and `cast/*/hero.png`, `turnaround.png` are locked once approved. If motion looks wrong, fix the motion prompt, never the reference.
2. **Every generation is logged in `log.md`** (model, prompt version, cost, verdict). An unlogged good shot is a shot we cannot make again.

Folder roles: `cast/` passports and references. `episodes/` scripts, shot cards, prompts, animatics. `frames/` approved still frames only. `renders/` raw video attempts. `selects/` accepted takes only; the edit sees nothing else.

Money gates: nothing is generated until sai approves a quoted cost. Drafts are rendered at 480p/720p; a final is rendered only after sai approves the draft. Daily budget: **USD 15** unless sai changes it.

## Logline

On the seventeenth afternoon of Kurukshetra, the two greatest archers alive, brothers who do not know it, meet in a duel that the gods stop to watch.

## World

- **Location:** Kurukshetra, a cleared ring of trampled red earth inside two halted armies. Afternoon sun low in the west, behind Karna.
- **Light:** warm gold key from a low afternoon sun, soft warm-brown shadows, pale gold dust in soft layers; the sky turns orange only in act IV.
- **Screen direction (locked):** Arjuna and Krishna on the LEFT facing right. Karna and Shalya on the RIGHT facing left. The sun sits behind Karna. Never cross the line.

## Engine

Two equal masters, each with one fatal debt the other cannot see: Karna is bound by curses (the sinking wheel, the forgotten weapon), Arjuna is bound by Krishna's hard dharma. Every exchange is a draw until fate, not skill, breaks it.

## Tone

Oil-painted realism from sai's concept art for every surface, with hand-drawn 2D energy FX on twos, graphic impact frames, speed ramps and smash cuts from the Eternal War analysis. Mythic and tragic, not gleeful. No dialogue except one optional line from Karna ("Partha, wait"). Music: war drums and a low drone, silence before each big release.

## Palette (60:30:10)

- 60% dominant: pale gold dust and warm earth `#E9CF9A` / `#B8743C` (paintings 34, 42), deepening to sunset orange `#E8792E` in act IV
- 30% secondary: carved gold `#D9A21B` with black enamel `#14110E`, cream-and-blue sky `#F4E6C8` / `#A9C4DD`
- 10% accent: Arjuna deep green silk `#1F5A3C` and electric blue energy `#6FC3FF`; Karna saffron `#E9982A` and solar gold energy `#FFB02E`; Krishna blue skin `#8C96C8` and white-gold light `#FFE9A8`

## Global style prompt (paste at the start of every image prompt)

> Classical academic oil painting of an Indian epic battle, richly detailed realist canvas, realistic anatomy and faces, visible oil brushwork and canvas weave, warm gold sunlight from a low sun, luminous sky of cream, peach and soft blue, pale gold battlefield dust in soft layers, deeply carved gold armour and chariots with black enamel inlay, saturated silk cloth, warm brown soft-edged shadows, cinematic wide lens, 2.39:1 framing inside 16:9. Original characters. No text, no logos, no watermarks, no captions. No flat cartoon, no cel shading, no vector look, no plastic 3D look, no real actor likeness.

Look source (2026-11-15, sai): the paintings in `refs/concept/` (sai's own AI-generated concept art). Surfaces, costume and colour come from them. Camera, cutting, drawn energy FX and impact frames come from the Eternal War rules below. The older flat "painterly stylized CG" prompt and the v1 passports are retired.

## Trailer rules applied (from trailer-analysis/01-shot-analysis.md, section 9)

- 3D owns form, space and camera; 2D owns energy, texture and emotion. Energy (lightning, arrows, sun-fire) is drawn in 2D.
- Every impact gets 1 to 3 flat-color frames (black, white, the energy color). Applied: A07, A14, A20.
- Negative-flash cut into the chariot press (A13). Selective color drain on the banner cut (A18).
- Locked, symmetrical frames for the sacred (Krishna's foot, the light column, the final hold). Free, tumbling cameras only in the arrow storm.
- Tiny figures against colossal sky and armies for scale (A02, A08).
- Rhythm: the arrow-storm block should cut faster than the rest (next pass: split A06 to A12 into sub-second shots).

## Never

- No real faces or actor likeness. Never attach a film or TV frame to a model; the trailer frames in `shots/` and `trailer-analysis/` are for timing study only.
- No text on screen inside generated frames (titles are added in the edit).
- No gore. Karna's death is shown by the sun, a silhouette and the rising light, never a wound or a head.
- No crowds in close shots, no mirrors, no small objects picked up by hands in close-up.
- No Western fantasy armor.

## Episode ideas (same engine)

1. Arjuna vs Karna: the Anjalika (this episode, 90 s).
2. Bhishma on the bed of arrows.
3. Abhimanyu and the broken wheel inside the Chakravyuha.
4. Bhima and Duryodhana at the lake, the mace to the thigh.
5. Drona lays down his weapons at a lie.

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

## Web series look (2026-11-20, from sai's three reference reels)

sai: "i want this type of style in our web series". The reels are for study only (Never rules below apply): no frame, character or shot is copied, and nothing from them goes into a model.

- **Painted 3D.** Figures stay 3D-rigged with real anatomy (no flat cartoon, no cel shading), but their surfaces read as painted: soft broad value shapes, a slight brush texture on cloth and skin, edges kept crisp on the silhouette and soft inside it.
- **Painted backgrounds.** Skies and far fields are painted matte plates with visible brushwork (sai's own paintings in `refs/concept/` are the source), not photoreal skies. Mid ground is 3D, far ground is paint.
- **Gold key, blue shadow.** Warm low-sun key (`#FFC27A`) against cool blue shadow and fill (`#3E5A86`, ambient `#7F93B8`). Shadows lean blue, not brown. This replaces "warm brown shadows" for the web series; the oil-painting stills keep their own palette.
- **Series hero set: LOCKED by sai 2026-11-21** ("yes"). Never regenerate, rename or re-prompt these; new shots and key frames use them as references. Style frame `cast/karna/web/close_v1.png`; Karna `cast/karna/web/close_v1.png`, `full_v2.png`; Arjuna `cast/arjuna/web/close_v4.png`, `full_v4.png` (passport_web.md); Krishna `cast/krishna/web/close_v2.png`. Earlier takes (Karna full_v1, Arjuna full_v1, close_v2, close_v3, Krishna full_v1) are retired. Open small points: Arjuna is barefoot in full_v4 (old sheet had gold sandals) and wears a small red tilak dot.
- **Series armour colours** (sai, 2026-11-21): Arjuna silver-steel armour with gold trim over a deep blue dhoti (green sash kept), `cast/arjuna/passport_web.md`; Karna keeps his gold and saffron, with the sun-face glowing in his astra shots. Krishna stays blue.
- **Two-colour astra glow.** Divine weapons glow in two colours: Karna sun-gold core with orange rim (`#FFF1C2` / `#FF8A1E`), Arjuna white core with lightning-blue rim (`#F2FAFF` / `#3FA9FF`). Glow and bloom only on energy, sun and fire, never on skin or armour.
- **Astra moments** (2026-11-21, `refs/study_notes_2026-11-21.md`): the hero is lit by his own energy against a dark, smoky ground; energy wraps the body as ribbons and strands, embers or sparks fly, hair and cloth whip in the energy wind; one point is brightest (Karna's sun-face on the cuirass ignites first; Arjuna's arrowhead, with a halo-ring glow behind his crown).
- **Painted worlds** (Hastinapur and beyond): a framed foreground (flowers, carvings), a city stacked on terraces in the mid ground, far layers fading into pastel haze, a tiny figure against colossal statues or towers for scale.
- **Energetic camera.** Fast push-ins, whip pans, rides alongside arrows, speed ramps into impacts. Locked frames stay for the sacred moments (rules above).
- **Story close-ups.** Each episode needs quiet close-ups with dialogue (subtitled in the edit, never baked into frames) between the action beats.
- **Formats.** Episodes 60 to 90 s. Every shot is framed for 16:9 with a 9:16 safe area (the subject stays inside the centre 9:16 band), and a vertical cut is made for Reels and Shorts.

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

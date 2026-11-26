# Studio pipeline: twelve steps per episode

This is how every episode is made, from canon to release. It comes from the research in
`research/epic_film_pipelines.md`, which looked at how Baahubali: The Eternal War, Arcane, Ne Zha 2, Flow, Spider-Verse,
the 1988 Mahabharat, Netflix's Kurukshetra and AI-made series were made. Every step builds on what already exists in `studio/`.

House rules apply to every step:

- Nothing paid happens without sai's own go, naming the command, the folder and the cost.
- Never feed film or TV frames, or other artists' work, to any model.
- No real-actor likeness and no gore.
- Locked looks are never regenerated.

**Who does it:** "Claude" means the crew agents in `.claude/agents/`, driven by scripts. "sai" means sai's own hands and eyes. All costs are in US dollars and are $0 unless noted.

## The steps

| # | Step | What happens | Output in the repo | Who | Cost |
|---|---|---|---|---|---|
| 1 | **Canon lock** | Check every shot against the Ganguli lines. Mark each one canon, dramatised, added or changed. Run the period-accuracy checklist. | `episodes/<ep>/canon_check.md`; `canon` field in `shots.json` | Claude drafts, sai signs off | $0 |
| 2 | **Animatic lock** | Add temp sound (the code-made conch, drone and hooves) to the HTML and Blender animatics. Fix every shot's length. Freeze the edit. | `animatic.mp4`, `animatic_layout.mp4`, `layout/` | Claude builds, sai approves timing | $0 |
| 3 | **Style bible and colour script** | Paint 4 to 6 key frames over layout grabs, plus a 6 to 8 frame colour script (dawn gold, battle haze, darkening sun, cold aftermath). Write down the rules: gold key, blue shadow, astra colours, outline weight. | `bible.md`, `episodes/<ep>/colour_script/` (new) | sai paints in Krita, Claude writes the rules | $0 |
| 4 | **Shot grading** | Grade every shot S, A, B or C. Only S and A shots get bespoke 2D drawing or hand polish. | `grade` field in `shots.json` | Claude proposes, sai approves | $0 |
| 5 | **Asset repair and repaint** | Fix hands, faces and finger skin stretch on the hero rigs. Repaint the textures toward the painted look at 2K. Add inverted-hull outlines. Make new props only when a shot needs one. | `cast/`, the rig `.blend` files | sai paints, Claude scripts fixes | $0. New meshes: TRELLIS.2 on a rented GPU (about $0.69/hr, RunPod L4) or Meshy free (credit Meshy) |
| 6 | **Environments** | Far ground is painted mattes projected onto blockout geometry. Mid ground is Geometry Nodes armies. Use an Unreal plate only where the camera needs real parallax. Light each shot to its plate's sun. | `world/`, plates per shot | Claude sets up, sai renders Unreal plates | $0 |
| 7 | **Voice** | Record the one line, the breaths and the effort sounds against the locked animatic. Drive the mouth shapes with Rhubarb. | `episodes/<ep>/audio/` | sai records, Claude syncs | $0 |
| 8 | **Animation** | Block on twos with `anim_lib.py` and `moves.py`. Releases and impacts go on ones. Hold anticipation 4 to 8 frames. Hand-polish only S and A shots. Use phone video of sai's own bow draw as reference. | the shot `.blend` files | Claude blocks, sai polishes S and A | $0 |
| 9 | **2D FX library, then bespoke FX** | Build the library once: arrow streak, gold sun-fire, blue lightning, shockwave ring, dust burst, sacred-geometry ring, and two-tone impact frames (gold and black for Karna, white-blue and black for Arjuna). Draw bespoke FX only on S shots. | `fx/` (new) | Claude builds the library, sai draws S-shot FX | $0 |
| 10 | **Look and render** | Render EEVEE in passes (character, FX, plate, light masks). Benchmark A06 on the GTX 1650 first. Keep cloud CPU Cycles for 960x540 drafts. Send finals to SheepIt, or to a rented GPU if SheepIt stalls. | `renders/` | renderer agent, sai approves any spend | $0 to about $6 per episode |
| 11 | **Photography and grade** | Add glow, light wrap, a light Kuwahara paint filter, paper grain and a slight colour offset at the edges. Match everything to the step 3 key frames. | `selects/` | Claude composites, sai reviews | $0 |
| 12 | **Sound, mix, deliver, release** | Use code-made beds plus licensed sounds (Sonniss GDC, CC0 Freesound), and log every licence. Mix to about -14 LUFS. Export 1080p H.264 and a 9:16 cut from a second camera. Release a teaser animatic first. | final cut, `log.md` | editor and publisher agents, sai gives final approval | $0 |

## Shot grades (step 4)

The grade decides where hand work goes. It is an idea from Ne Zha 2's VFX vendor, which graded every shot S to D.

| Grade | Treatment | EP01 shots |
|---|---|---|
| S | Bespoke hand-drawn FX, impact frames, polish on ones where it counts | A01, A06, A12, A14, A19 |
| A | Hand polish of the key poses; FX from the library with small drawn touches | A04, A07, A10, A11, A13, A16, A20, A21 |
| B | Blocked animation, library FX only | A02, A05, A08, A15, A17, A18 |
| C | Held pose, breath and camera move only | A03, A09, A22 |

If time runs short, A07 and A13 drop to B before anything else is cut.

## Where each episode stands

Story order and episode numbers are in `series_plan.md`. The duel below was built first; it is released as the teaser and returns as episode 43.

| Step | Teaser / ep 43 "The Anjalika" |
|---|---|
| 1 Canon lock | Draft done (`episodes/ep01_arjuna_vs_karna/canon_check.md`), waiting for sai's sign-off |
| 2 Animatic lock | HTML and Blender layout animatics exist; temp sound and timing freeze still to do |
| 3 Style bible and colour script | Bible exists; key frames and colour script still to do |
| 4 Shot grading | Proposed in `shots.json`, waiting for sai's approval |
| 5 Asset repair | Hero rigs Arjuna v3, Krishna v2 and Karna v3 exist; hands, faces and repaint still to do; no Shalya asset yet |
| 6 Environments | Kurukshetra battlefield in Blender; Unreal duel set in progress on sai's PC |
| 7 Voice | Not started |
| 8 Animation | Moves library and a moves demo exist; shots not started |
| 9 FX | A06 volley proof only |
| 10 Render | Story scene 01 rendered in Cycles on CPU; EEVEE not yet tested |
| 11 Photography | Not started |
| 12 Sound and release | Code-made sound for scene 01 only |

Update this table when a step changes state.

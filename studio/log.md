# Generation log

One line per generation: date, shot, model, prompt version, cost, verdict. Free steps are logged too.

| Date | Item | Model / tool | Prompt version | Cost | Verdict |
|---|---|---|---|---|---|
| 2026-11-15 | ep01 shot cards, frame and motion prompts | Claude (text) | shots.json v1 | $0 | drafted, waiting for sai |
| 2026-11-15 | ep01 animatic.mp4 (90 s, 30 fps) | Playwright + ffmpeg, HTML/SVG | animatic v1 | $0 | drafted, waiting for sai |
| 2026-11-15 | cast/karna/hero.png | gemini-2.5-flash-image | stage1 v1 | tokens out 1290 (about $0.039) | FAIL: gold earrings, no chest scars, framed dusty background, too flat. Design direction good |
| 2026-11-15 | cast/arjuna/turnaround_front.png | gemini-2.5-flash-image | stage1 v1 | tokens out 1290 (about $0.039) | FAIL: cropped at knees, no diadem, two gold earrings. Face, hair, armor, Gandiva match SH170 |
| 2026-11-15 | cast/karna/sheet.png | gemini-3.1-flash-image | sheets v1 (concept-art look) | tokens in 2567 out 1120 | pending review |
| 2026-11-15 | cast/arjuna/sheet.png | gemini-3.1-flash-image | sheets v1 (concept-art look) | tokens in 2541 out 1120 | pending review |
| 2026-11-15 | cast/krishna/sheet.png | gemini-3.1-flash-image | sheets v1 (concept-art look) | tokens in 2501 out 1120 | pending review |
| 2026-11-15 | cast/karna, cast/arjuna, cast/krishna sheet.png | gemini-3.1-flash-image | sheets v1 | 3 images, about $0.10 est. (billing not yet checked) | APPROVED by sai 2026-11-15 ("good ... approve it"). Sai also asked to compare against web reference images; not used as model input (see note) |

Note 2026-11-15: web and Pinterest references are not model inputs. Their likeness and rights are unknown; only sai's own concept paintings are attached (folder law: approved refs are locked).
- 2026-11-15 · no generation · sai sent 15 Karna reference pictures (Pinterest). Compared by eye with cast/karna/sheet.png; wording-only draft written to cast/karna/passport_v3_draft.md and job karna_v3 added to gen_sheets.py (dry-run only, $0). Reference pictures are not in the repo and not model inputs. Locked v2 passport and sheet unchanged; waiting on sai's choice.
- 2026-11-15 · no generation · sai chose "Update Karna, no earrings": passport v3 wording accepted (cast/karna/passport_v3_draft.md). sheet_v3.png waits for sai's go on the cost (1 image).
| 2026-11-15 | cast/karna/sheet_v3.png | gemini-3.1-flash-image | Karna v3 wording (passport_v3_draft.md) | tokens in 2656 out 1120, about $0.07 est. | NOT USED: sai, 2026-11-15, "keep old one". v2 sheet.png stays the locked Karna |
| 2026-11-15 | cast/arjuna_bare/sheet.png | gemini-3.1-flash-image | sheets v1 (concept-art look) | tokens in 2512 out 1120 | pending review |
- 2026-11-15 · no generation, $0 · 3D layout of all 22 shots built with tools/layout_blender.py (bpy 5.3, Cycles CPU, in the cloud): episodes/ep01_arjuna_vs_karna/layout/A01..A22.jpg + cameras.json + contact_sheet.jpg. Hero chariots are shown without parasol and banner so the crew reads; banners are props. Mannequins are colour-coded stand-ins, not the look. animatic_layout.mp4 (90 s) cut from them with tools/build_layout_animatic.py. Full-size PNG stills and layout.blend are in /mnt/project-files/arjuna-karna/layout/.
- 2026-11-15 · no generation, $0 · A06 layout restaged to the card's first frame (Karna at full draw, seven-arrow fan, sun behind). tools/gen_frames.py added for the paint-over step (recipes for A16 and A06 only); dry-run checked, nothing sent.
| 2026-11-15 | episodes/ep01_arjuna_vs_karna/frames/A16_v1.png | gemini-3.1-flash-image | frame over layout, 4 refs | tokens in 5156 out 1120 | FAIL: loose wheel instead of the chariot's own, side view, no tilt |
| 2026-11-15 | episodes/ep01_arjuna_vs_karna/frames/A06_v1.png | gemini-3.1-flash-image | frame over layout, 4 refs | tokens in 5125 out 1120 | FAIL: earring, parasol added, arrows parallel |
| 2026-11-16 | cast/arjuna_bare/sheet_v2.png | gemini-3.1-flash-image | sheets v1 (concept-art look) | tokens in 2575 out 1120 | pending review |
| 2026-11-16 | episodes/ep01_arjuna_vs_karna/frames/A06_v2.png | gemini-3.1-flash-image | frame over layout, 4 refs | tokens in 5196 out 1120 | pending review |
| 2026-11-16 | episodes/ep01_arjuna_vs_karna/frames/A16_v2.png | gemini-3.1-flash-image | frame over layout, 4 refs | tokens in 5253 out 1120 | pending review |
| 2026-11-16 | cast/arjuna_bare/sheet_v3.png | gemini-3.1-flash-image | sheets v1 (concept-art look) | tokens in 2585 out 1120 | pending review |
- 2026-11-16 · review · A16_v2 FAIL (mirrored against the layout, no crown, no cuirass, city and second chariot added, wheel not sunk). A06_v2 close: fan, sun and no parasol are right; a small earring and an extra hooded figure remain; waits for sai. arjuna_bare sheet_v3 matches the passport; waits for sai. arjuna_bare sheet_v2 ran on the PC before sai's approval line was given (1 image); recorded here as a process miss.
- 2026-11-16 · no generation, $0 · A16 layout restaged close behind Karna (painting 37 angle), wheel sunk deeper; A17 to A22 re-rendered to match; A16 frame recipe rewritten (no mirroring, crown and cuirass kept, empty field).
- 2026-11-16 · no generation, $0 · sai: "remove hair band of arjuna". @arjuna_bare passport v3: bare head, loose hair, no cloth band, no earrings, no tilak, no shield. A15 card rewritten (he pushes his hair back and lifts the bow). Layouts A14, A15, A17, A19, A21, A22 re-rendered; sheet job arjuna_bare_v4 added (dry-run only). sheet.png, sheet_v2.png and sheet_v3.png of arjuna_bare are not used.

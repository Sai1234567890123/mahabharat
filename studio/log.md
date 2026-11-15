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

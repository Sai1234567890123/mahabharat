# Vision plan: from the pilot to the full Mahabharat series

**The vision (Sai's):** an animated Mahabharat series in a painterly 2D/3D hybrid style, faithful to the original epic, made with open-source tools, GCP AI credits, AI image and video models, Claude Code and Antigravity.

**The answer to "trailer or whole series?":** both, in order. The pilot "The First Conch" (18 shots, about 84 seconds, Bhishma Parva) proves the method. Its finished shots become the trailer. Then the same pipeline runs episode by episode. We do not start the series until the pilot passes canon and style review, because every mistake in the method would repeat across hundreds of episodes' worth of shots.

## Where we are (estimates, 2026-10-10)

| Stage | What exists | Progress |
|---|---|---|
| 1. Research | Trailer style analysis and production research (`trailer-analysis/`) | Done |
| 2. Source and bible | All 18 books of the Ganguli translation as text (`mahabharat-site/source/`), the series bible and database (`mahabharat-site/BIBLE.md`, `data.json`) | Done, needs a canon index per scene |
| 3. Pilot preproduction | Treatment, style bible, characters, locations, 18-shot list, prompt pack (docs 01-07), `shots.json` | Done |
| 4. 3D layout | Blender blockouts of all 18 shots; Unreal level with 18 cameras and an 84-second Level Sequence; placeholder sets | About 60%: sets are boxes, no animation yet |
| 5. Painted keyframes | 18 shots painted, 8 hero shots at v02-v03 | First pass only. **0 of 8 hero shots pass canon** (R-003) |
| 6. Canon QA | `data/canon_checks.json` for the 8 hero shots | Started; wiring into QA is T-004 |
| 7. Motion | Nothing yet | 0% |
| 8. 2D FX and compositing | `compose.py` for stills | About 20% |
| 9. Edit, sound, voice | Nothing yet | 0% |
| 10. Trailer | Waits on stages 5-9 for the hero shots | 0% |
| 11. Series | Episode 1 scope question is open (`01-treatment.md`) | 0% |

Overall, the pilot is roughly a quarter of the way to a finished, canon-correct 84 seconds. The series has not started, which is right at this stage.

## Next steps, in order

| # | Step | Owner | Task |
|---|---|---|---|
| 1 | Add the canon check to QA | Antigravity | T-004 |
| 2 | Redo and fix the 8 hero shots until they pass canon | Antigravity | T-003 |
| 3 | Review the new hero shots and approve or reject | Sai | |
| 4 | Canon checklists for the other 10 shots | Claude | T-005 (next) |
| 5 | Real set geometry in Unreal (chariots, armies, banner) from the Blender proxies | Claude | |
| 6 | Camera moves and blocking animation in the Unreal sequence | Claude | |
| 7 | Motion tests on 2 approved hero shots (Veo first-and-last frame, or Wan video-to-video) | Claude and Antigravity | |
| 8 | 2D FX, compositing, temp sound, first cut of the pilot | Claude and Antigravity | |
| 9 | Cut the trailer from the approved pilot shots | Claude | |
| 10 | Decide Episode 1's opening (Kurukshetra or Adi Parva) and break it into scenes from the source text | Sai, then Claude | |

## How the loop works for every shot

1. **Source:** each shot cites its lines in the Ganguli text.
2. **Checklist:** those lines and the character bible become a `must` and `must_not` list in `canon_checks.json`.
3. **Paint:** the paint prompt includes the checklist.
4. **QA:** the reviewer reads the epic passage and the checklist and rejects any frame that breaks canon, whatever its style score.
5. **Human review:** Sai approves hero shots. Rejections go back as a new task with the reason.

No model training is needed for this. The reviewer gets the right passage from the epic at check time, which keeps it tied to the real text and costs nothing to update.

# EP01 "Arjuna vs Karna": 3D models and animation plan

sai, 2026-11-25: build all three heroes out with epic detail and make every animation the project needs. Free, cloud
Blender (Cycles CPU). Paid steps (L4 GPU, TRELLIS rebuilds, AI video) only on sai's own typed go.

## Motions EP01 needs, from shots.json (22 shots)

| Hero | Shot | Motion | Library move |
|---|---|---|---|
| Karna | A03 | touches the bow to his forehead, eyes closed; eyes open and lift | `bow_salute` |
| Karna | A06 | full draw, looses a fan of seven arrows | `bow_draw` + `fan_release` |
| Karna, Arjuna | A09 | exhausted: breathing, slow blink, sweat | `exhausted` |
| Karna | A10 | draws one arrow from the golden quiver over his shoulder | `quiver_draw` |
| Karna | A11 | draws the snake arrow to his ear | `bow_draw(ear=True)` |
| Karna | A16 | wheel sinks, he leaps down and heaves it | `leap_down`, `heave` |
| Karna | A17 | raises a palm: "wait" | `palm_wait` |
| Karna | A20 | stands still against the sun | `stand_tall` |
| Arjuna | A04 | raises and draws Gandiva to the cheek, eyes narrow | `bow_draw` |
| Arjuna | A07 | rapid shots, one after another | `rapid_fire` |
| Arjuna | A14 | crown struck off, head snaps | `head_hit` |
| Arjuna bare | A15 | rises from a crouch, pushes his hair back, lifts Gandiva | `rise_hair_push` |
| Arjuna bare | A19 | draws the Anjalika | `bow_draw` |
| Arjuna bare | A22 | lowers Gandiva, no celebration | `bow_lower` |
| Krishna | A02, A04 | charioteer stance, reins in both hands | `charioteer` |
| Krishna | A05 | flicks the reins | `reins_flick` |
| Krishna | A13 | presses his foot down, the chariot sinks | `foot_press` |
| Krishna | A17, A22 | the look: turns his head, calm, watches the light | `calm_look` |

Already in moves.py: `bow_draw`, `bow_release`, `block`, `dodge`, `run`. Bows and arrows: bows.py.

## What the models need for "epic detail"

- All three are single TRELLIS meshes with one baked 4K colour texture: no metal, no relief, flat skin.
- Detail pass (hero_detail.py): metal from the texture's gold and steel colours, engraving relief from the texture,
  skin with subsurface light and pores, cloth sheen and weave, worn bright edges on the armour.
- Arjuna bare-headed variant (passport arjuna_bare, LOCKED): crown off, loose black wavy hair to the nape, A14 on.
- Known limits kept for now: finger skin stretch in tight poses; Krishna's lips rest a little parted.

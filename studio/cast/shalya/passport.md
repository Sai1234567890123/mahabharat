# Shalya: passport (v1, 2026-11-26)

Shalya, king of Madra, is Karna's charioteer on the 17th day. He agreed to drive only under pressure, and taunts Karna as he drives.

- **Canon:** Ganguli, Karna Parva, B08 lines 11683-11688. He tells Karna to aim the serpent arrow again, and Karna refuses.
- **Approved:** sai approved this build on 2026-11-26 for the teaser's wide shots: A02, A06 and A16.

## Descriptor

Shalya, Karna's charioteer, an older Indian king with warm brown skin, an iron-grey beard and grey hair to the shoulders, a plain ivory turban with a thin gold band, a gold cuirass and collar, gold bracers, and an ivory dhoti, standing at the front of Karna's chariot with the reins in both hands.

## Use

- **Distance:** mid-ground and from behind only, as the Karna passport already says ("grey-bearded, mid-ground only"). He is not built for close-ups.
- **Rig:** `model/rig/shalya_hero_v1.blend`. It is the Krishna hero rig, re-dressed by `tools/blender/shalya_build.py`: the crown and peacock feather are cut, the skin is brown, the hair and beard grey, and the dhoti ivory. It loads with `Hero.load(path, "SHALYA")` and poses with `moves_ep01.charioteer()`.
- **Check:** `model/rig/shalya_on_karna_chariot_check.jpg` (made by `tools/blender/shalya_chariot_check.py`) shows him on Karna's chariot with the dun team and the elephant's-rope standard.
- **Known limits of v1:**
  - The turban and beard are simple shapes.
  - The face is Krishna's face shape, which is why he stays out of close-ups.
  - The kit chariot's old driver, his bow and the two lion figureheads in front of him are cut out; no leftover bits.

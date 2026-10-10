# Locations and props (pilot)

## Kurukshetra, the field

- **Shape:** a flat, endless plain with a low horizon at 1/3 frame height. Sky gets 2/3 of the frame in wide shots.
- **Ground:** pale ochre dust, trampled grass, chariot ruts. Shallow dust always moving low across the ground.
- **The armies:** two masses facing each other across an empty strip. The Pandava host on screen left with upright standards; the Kaurava host on the right, denser and darker. Arjuna's ape banner rises above all standards on both sides (lines 2963–2964).
- **Between the armies:** the empty ground where the car stops (lines 3498–3508). It is the stage of the pilot: a long, bare stripe of earth with the two armies as walls.
- **Sky by act:** apricot dawn haze (A), cloud cover with a hidden sun (B), opened cosmos (C), hot rising sun with red dust (D).
- **3D build:** one large ground plane with displacement, instanced army cards (3 tiers), a sky dome with a painted texture swapped per act.

## The cosmic space (Vishvarupa)

- Not a place but a frame: concentric yantra rings that fill the sky, the field still visible below as a thin line.
- Built as 2D layers on cards in 3D space, so the camera can push through them.

## Props

| Prop | Description | Source |
|---|---|---|
| **Arjuna's chariot** | Two large spoked wheels, a tall carved car "decked with Jamvunada gold", "furnished with a hundred bells", "possessed of the effulgence of fire". Four white steeds. The ape banner on a tall pole. | Lines 3208–3213 |
| **Ape banner** | A gigantic ape figure on the standard, crouched and alive, outlined against the sky. Our design: a stylized ape in gold on a saffron field, mouth open as if roaring. | Lines 2963–2964, 3212 |
| **Panchajanya** | Krishna's conch: large, white, spiral, gold-tipped mouthpiece and jewelled band. | Line 3480; "decked with gold and jewels", line 7428 |
| **Devadatta** | Arjuna's conch: slightly smaller, pearl white with silver bands and blue stones. | Line 3481 |
| **Paundra** | Bhima's conch: "huge", heavy, rough-ribbed, iron bands. | Line 3482 |
| **Anantavijaya** | Yudhishthira's conch: elegant, white with gold bands. | Line 3483 |
| **Sughosa, Manipushpaka** | The twins' conches: paired, silver and rose. | Line 3484 |
| **Gandiva** | A tall recurve bow, dark horn limbs with gold bindings. Larger than Arjuna when strung. | Lines 3213, 3520 |
| **Bhishma's car and banner** | White car, silver fittings. A tall standard with a gold palmyra tree and five stars. | Lines 2689, 2760, 6631 |
| **Kaurava standards** | Duryodhana's serpent standard in crimson and gold, plus many crowded banners. | |

## 3D proxy status

The Blender blockout scripts in `scripts/` build simple proxies for the field, the two armies (instanced cards), the chariot (box body, two torus wheels, four horse proxies, banner pole), and the hero figures (capsule bodies with the silhouette features above). These drive the concept frames and later the control passes for AI paint-over.

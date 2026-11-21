#!/usr/bin/env python3
"""Gate 1 of the hand-animated 3D plan: concept paintings of the key moments of the battle.

sai chose on 2026-11-17 to MIX the three look directions ("take best of each of them combine"). The default run paints six
key moments in that combined direction:

  M  combined    : hand-painted oil look on stylized 3D (from A) + divine weapons as colossal forms with sacred-geometry
                   rings (from B) + ink contour lines, speed lines and flat hard-edged 2D effects (from C)
  moments        : volley, clash, serpent, crown, wheel, anjalika

The three separate directions stay in the file for reference and can still be painted with --only:
  A  Painted Epic, B  Astra Storm, C  Ink and Fire   (moments volley and serpent only)

These are concept paintings for choosing a look, not final frames. Each call sends the approved character sheets and
sai's own paintings only. BILLED: one image per job per run (gemini-3.1-flash-image, about $0.07 each). Needs sai's own go
with the cost. No automatic retries. Never overwrites a take. Every call is logged to studio/log.md.

  python studio/tools/gen_concepts.py --project cs-project-07zg2j2c --dry-run
  python studio/tools/gen_concepts.py --project cs-project-07zg2j2c                      (the six combined paintings)
  python studio/tools/gen_concepts.py --project cs-project-07zg2j2c --only M_volley --take 2
"""
import argparse, base64, datetime, json, pathlib, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gen_sheets import MODEL, STUDIO, call, descriptor      # same API call, same model

OUT = "concepts/directions"
RULES = ("One single finished frame, 16:9. No text, no captions, no labels, no borders, no split screen, no watermark. "
         "Every character exactly as on his approved character sheet: same face, same build, same costume, nothing added. "
         "Karna has bare earlobes with NO earrings. Add no jewellery, no tilak, no forehead mark and no shield that is not on a character's sheet. "
         "NO parasol, NO canopy and NO awning on any chariot. No blood, no gore. Not photorealistic.")

LOOK = {
    "A": ("LOOK: a finished frame from an animated feature film made with stylized 3D characters whose surfaces are hand-painted like "
          "classical oil paintings: visible brushwork on skin, gold and cloth, painted light and painted shadow, soft painterly edges, a "
          "strong warm rim light from the low sun, pale gold atmospheric dust, a matte-painted sky. The characters are slightly larger "
          "than life. Effects are hand-drawn 2D shapes with hard edges in two or three tones. Match the painting style, colour and level "
          "of carved gold detail of the reference paintings. Not a glossy plastic 3D render and not flat cel shading."),
    "B": ("LOOK: a finished frame from a stylized 3D fantasy animation of gods at war: clean sculpted characters with smooth stylized "
          "shading, glowing gold trim on the armour and a visible aura of light around each hero. Each divine weapon appears at colossal "
          "scale behind its archer as a translucent luminous form many times his height, with concentric rings of fine sacred-geometry "
          "line art (mandala rings, lotus petals, sun rays) turning around the bow. The sky reacts to the weapon. High contrast, saturated "
          "colour, epic scale, painted backgrounds. Use the reference paintings only for the designs of the armour, the chariots and the "
          "battlefield; the rendering is as described here, not oil paint. Not a video-game screenshot."),
    "C": ("LOOK: a finished frame from a hand-drawn action anime: cel shading with two flat tones per colour, bold black ink outlines of "
          "varying thickness, flat graphic colour blocks, a dramatic foreshortened camera angle, thick hand-drawn speed lines and "
          "hard-edged effect shapes, a simplified painted background. No soft gradients on the characters. Use the reference paintings "
          "only for the designs of the armour, the chariots and the battlefield; the rendering is as described here, not oil paint and "
          "not a 3D render."),
    # v2 of the combined look (2026-11-17): the v1 wording asked for ink contours on everything and the paintings came out as
    # flat outlined comic illustrations. Ink and flat shapes now belong to the effects only; the figures are painted and lit.
    "M": ("LOOK: a single film frame from a big-budget animated feature about gods at war, made as stylized 3D with hand-painted "
          "surfaces. The image is cinematic and deep, never flat: strong directional light from a low sun, deep warm shadows, a bright "
          "coloured rim light on every figure, volumetric dust and haze that separate foreground, midground and background, rich "
          "saturated colour, a slightly soft background, a wide anamorphic lens. Skin, gold and cloth are painted with confident visible "
          "brushwork like the reference oil paintings, with sculpted volume and carved gold detail that catches the light. The heroes are "
          "larger than life, with powerful anatomy and intense expressions, in dynamic foreshortened poses seen from a dramatic low or "
          "tilted camera. There are NO outlines around the characters, chariots or horses. "
          "Only the energy and weapon effects are hand-drawn 2D anime shapes: hard-edged, two or three tones, glowing, with speed lines "
          "and sparks, and they throw coloured light onto the painted figures. Each divine weapon also appears at colossal scale in the "
          "sky as a translucent glowing form ringed by fine sacred-geometry line art (mandala rings, lotus petals, sun rays). Karna's "
          "energy is orange-gold sun-fire; Arjuna's energy is blue-white lightning. "
          "Not a comic book, not a storybook illustration, not flat colour, not cel shading, not a photo, not a glossy plastic render."),
}

MOMENT = {
    "volley": dict(
        refs=["cast/karna/sheet.png", "refs/concept/concept_46.jpeg", "refs/concept/concept_34.jpeg"],
        passports=["cast/karna/passport.md"],
        ref_note="IMAGE 1 is the approved character sheet of Karna. IMAGES 2 and 3 are reference paintings.",
        base=("MOMENT: Karna stands on his carved war chariot at full draw, facing screen LEFT. Seven arrows are nocked together on one "
              "bowstring and fan apart from his bow hand, every arrowhead pointing to screen left, no arrow released yet. A grey-bearded "
              "older charioteer, Shalya, sits low at the front holding the reins of four dun horses. A gold banner on a tall pole stands on "
              "the chariot. The Kaurava host stands far behind in pale gold dust. The low sun is behind Karna."),
        extra={
            "A": "A thin orange-gold sun-fire runs along every shaft and the sun sits directly behind his bow hand. Grounded, weighty, human scale.",
            "B": ("Behind Karna a colossal translucent golden sun disc with a calm carved sun face fills half the sky, ringed by turning circles "
                  "of fine line-art rays; each of the seven arrows trails a ribbon of sun-fire and the dust lifts off the ground around the chariot."),
            "C": ("Extreme low angle from in front of the bow: the seven arrowheads are huge in the foreground, Karna towers behind them, "
                  "speed lines radiate from his bow hand, the palette is black, orange and pale gold."),
            "M": ("Composition: the four dun horses are at the LEFT side of the frame and Karna stands right of centre, aiming over the "
                  "horses' heads: his bow arm points at the LEFT edge of the frame and all the arrowheads point LEFT. Exactly seven arrows. "
                  "Low dramatic angle from the ground at the left front of the chariot looking up at him, so he towers against the sky, his "
                  "face fierce, muscles straining, cloth and hair blown back. A hard-edged orange-gold sun-fire runs along every shaft and "
                  "lights his face and armour from the front. Behind him a colossal translucent golden sun disc with a calm carved sun face "
                  "fills half the sky, ringed by turning circles of fine line-art rays. Dust and grit lift off the ground around the wheels."),
        }),
    "serpent": dict(
        refs=["cast/karna/sheet.png", "cast/arjuna/sheet.png", "cast/krishna/sheet.png", "refs/concept/concept_42.jpeg"],
        passports=["cast/karna/passport.md", "cast/arjuna/passport.md", "cast/krishna/passport.md"],
        ref_note=("IMAGE 1 is the approved character sheet of Karna, IMAGE 2 of Arjuna, IMAGE 3 of Krishna. IMAGE 4 is a reference "
                  "painting of Arjuna's chariot; paint that chariot WITHOUT its parasol."),
        base=("MOMENT: a wide view of the battlefield of Kurukshetra under a blood-red sky with falling meteors. At the RIGHT, Karna on "
              "his chariot with four dun horses has just released a single arrow whose head is a dark serpent; he is still in his release "
              "pose facing screen LEFT. The arrow flies toward screen left and leaves a blazing line of fire that splits the sky in two. At "
              "the far LEFT, smaller, Arjuna's gold chariot with four white horses and a green ape banner: Arjuna in his tall gold crown "
              "stands with his bow Gandiva and looks up at the arrow, blue-skinned Krishna sits at the reins. Both armies stand as distant "
              "ranks along the horizon."),
        extra={
            "A": "The fire line is painted with thick hard-edged brush shapes; the scale stays human and grounded, the danger is in the red light on every face.",
            "B": ("The arrow has become a colossal luminous serpent, a hooded Naga hundreds of metres long with an open mouth, coiling across "
                  "the whole sky toward Arjuna's chariot; rings of sacred-geometry line art still turn around Karna's bow."),
            "C": ("The sky is split into a black half and a red half along a jagged white line; the serpent arrow is drawn with thick ink and "
                  "speed lines; the chariots and armies are near-silhouettes with a few flat colours."),
            "M": ("The arrow has become a colossal luminous serpent of orange-red fire, a hooded Naga hundreds of metres long with an open "
                  "mouth, drawn as a flat hard-edged 2D shape with an ink outline, coiling across the whole sky toward Arjuna's chariot. "
                  "Rings of sacred-geometry line art turn around Karna's bow. Karna's bow is empty and its string still hums: there is NO "
                  "second arrow on his bow. The painted chariots and heroes are lit red from above and rimmed with orange firelight."),
        }),
    "clash": dict(
        refs=["cast/arjuna/sheet.png", "cast/krishna/sheet.png", "refs/concept/concept_06.jpeg", "refs/concept/concept_05.jpeg"],
        passports=["cast/arjuna/passport.md", "cast/krishna/passport.md"],
        ref_note=("IMAGE 1 is the approved character sheet of Arjuna, IMAGE 2 of Krishna. IMAGES 3 and 4 are reference paintings; paint "
                  "the chariot WITHOUT its parasol."),
        base=("MOMENT: Arjuna stands on his gold chariot and shoots toward screen RIGHT at great speed, his bow Gandiva upright in his left "
              "hand with a taut bowstring, his right hand a blur at the string. Blue-skinned Krishna sits at the front holding black reins, "
              "calm, four white horses at a gallop, a green ape banner streaming from a tall pole. In the air at the right, Arjuna's arrows "
              "meet incoming arrows head-on and split them. The Pandava host is far behind in dust under a warm late-afternoon sky."),
        extra={
            "M": ("Three-quarter view from low beside the galloping horses. Arjuna's arrows are blue-white lightning bolts and the incoming "
                  "arrows are orange-gold sun-fire; every collision is a flat hard-edged star-shaped spark with an ink outline. Behind "
                  "Arjuna a colossal translucent thunderbolt of blue-white light stands in the sky, ringed by fine sacred-geometry line art. "
                  "Speed lines streak past the chariot."),
        }),
    "crown": dict(
        refs=["cast/arjuna/sheet.png", "cast/krishna/sheet.png", "refs/concept/concept_06.jpeg"],
        passports=["cast/arjuna/passport.md", "cast/krishna/passport.md"],
        ref_note=("IMAGE 1 is the approved character sheet of Arjuna, IMAGE 2 of Krishna. IMAGE 3 is a reference painting; paint the "
                  "chariot WITHOUT its parasol."),
        base=("MOMENT: Krishna has pressed Arjuna's chariot down into the earth, its wheels sunk to the hubs and the four white horses "
              "fallen to their knees. Arjuna is crouched low on the chariot, looking up toward screen RIGHT. A blazing serpent-headed arrow "
              "coming from the right passes just above him and strikes the tall gold crown off his head; the crown is in the air above "
              "him, torn away, and his black hair is flung loose. Krishna sits calm at the front with the reins, one bare foot pressed "
              "firmly down on the chariot floor. Blood-red sky."),
        extra={
            "M": ("Low angle close to the chariot. The serpent arrow is a flat hard-edged shape of orange-red fire with an ink outline and a "
                  "long trail; the broken crown throws off gold sparks. A soft white-gold light with one fine mandala ring glows under "
                  "Krishna's foot where it presses down. Cracked earth and dust burst out around the sunken wheels."),
        }),
    "wheel": dict(
        refs=["cast/karna/sheet.png", "refs/concept/concept_37.jpeg", "refs/concept/concept_46.jpeg"],
        passports=["cast/karna/passport.md"],
        ref_note="IMAGE 1 is the approved character sheet of Karna. IMAGES 2 and 3 are reference paintings of him.",
        base=("MOMENT: Karna has leapt down from his chariot and stands on the ground, both hands gripping the rim of the chariot's left "
              "wheel, which has sunk to its hub in cracked red earth; the whole chariot leans toward it. He heaves with his whole back, "
              "still wearing his rounded gold crown and full gold cuirass, his face turned in profile toward screen LEFT, grim and "
              "exhausted. The sunken wheel is ATTACHED to the chariot on its axle at the chariot's side, its lower third buried in the "
              "earth; there is NO loose wheel standing apart from the chariot and no broken axle. He crouches right beside the chariot "
              "body and grips the upper rim and spokes. There is nothing on his back: no disc and no shield. Shalya, a grey-bearded older charioteer, sits at the front with the reins of four dun horses. A gold banner on a "
              "tall pole stands on the chariot. The wheel stays on its axle. Open empty battlefield, the armies far away."),
        extra={
            "M": ("Low wide angle near the ground beside the wheel. This is a quiet, heavy moment: no energy effects on Karna at all, only "
                  "painted dust pouring off the rim and long shadows. The low sun behind him is dimming, half hidden by dark cloud, with one "
                  "faint broken ring of line-art rays around it."),
        }),
    "anjalika": dict(
        refs=["cast/arjuna_bare/sheet_v4.png", "cast/krishna/sheet.png", "refs/concept/concept_06.jpeg"],
        passports=["cast/arjuna_bare/passport.md", "cast/krishna/passport.md"],
        ref_note=("IMAGE 1 is the approved character sheet of Arjuna without his crown, IMAGE 2 of Krishna. IMAGE 3 is a reference "
                  "painting; paint the chariot WITHOUT its parasol."),
        base=("MOMENT: Arjuna, bare-headed with loose black hair and nothing on his head, stands on his sunken gold chariot at full draw "
              "facing screen RIGHT. His bow Gandiva is upright with a taut bowstring, and on it is one huge arrow with a broad "
              "crescent-shaped head. His face is set and sorrowful. Krishna sits at the front with the reins and watches. The sky is "
              "darkening to deep blue and violet; far away at the right edge a tiny chariot stands against a low dim sun."),
        extra={
            "M": ("Low three-quarter angle from in front of the bow, the crescent arrowhead large in the foreground. Rings of blue-white "
                  "lightning, drawn as flat hard-edged 2D shapes with ink outlines, ripple outward from Gandiva. Behind Arjuna a colossal "
                  "translucent thunderbolt of blue-white light fills the dark sky, ringed by fine sacred-geometry line art. His hair and "
                  "green sash are blown back and blue light rims his armour."),
        }),
}
JOBS = [f"{d}_{m}" for d in LOOK for m in MOMENT if d in MOMENT[m]["extra"]]
DEFAULT = [f"M_{m}" for m in ("volley", "clash", "serpent", "crown", "wheel", "anjalika")]      # sai's combined direction

def build(job):
    d, m = job.split("_")
    mo = MOMENT[m]
    lines = [LOOK[d], "", mo["ref_note"], ""] + [descriptor(p) for p in mo["passports"]] + ["", mo["base"], mo["extra"][d], "", RULES]
    return mo["refs"], "\n".join(lines)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True); ap.add_argument("--location", default="global")
    ap.add_argument("--only", default=",".join(DEFAULT)); ap.add_argument("--take", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    for i, job in enumerate(a.only.split(",")):
        if i and not a.dry_run:
            time.sleep(25)        # pacing only: the sixth call of the first run hit a 429 rate limit. This is not a retry.
        if job not in JOBS:
            print("unknown job", job, "| jobs:", JOBS); sys.exit(1)
        refs, prompt = build(job)
        missing = [r for r in refs if not (STUDIO / r).exists()]
        if missing:
            print("missing reference", missing); sys.exit(1)
        rel = f"{OUT}/{job}_v{a.take}.png"
        out = STUDIO / rel
        if out.exists():
            print("exists, not overwriting (folder law 1):", rel); sys.exit(1)
        if a.dry_run:
            print("---", job, "->", rel, "\nrefs:", refs, "\n" + prompt, "\n"); continue
        res = call(a.project, a.location, prompt, refs, "16:9")
        imgs = [p for c in res.get("candidates", []) for p in c.get("content", {}).get("parts", []) if "inlineData" in p]
        if not imgs:
            print("no image returned:", json.dumps(res)[:1500]); sys.exit(1)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(imgs[0]["inlineData"]["data"]))
        u = res.get("usageMetadata", {})
        with open(STUDIO / "log.md", "a") as f:
            f.write(f"| {datetime.date.today()} | {rel} | {MODEL} | concept direction {job}, {len(refs)} refs | tokens in {u.get('promptTokenCount')} out {u.get('candidatesTokenCount')} | pending review |\n")
        print("wrote", rel, "usage", u)

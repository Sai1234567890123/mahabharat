#!/usr/bin/env python3
"""Gate 1 of the hand-animated 3D plan: concept paintings of two key moments in three look directions.

  A  Painted Epic : stylized 3D with hand-painted oil textures and painted light, drawn 2D effects
  B  Astra Storm  : cleaner stylized 3D, divine weapons appear as colossal forms with sacred-geometry rings
  C  Ink and Fire : cel shading with ink outlines, flat colour, speed lines

  moments: volley (Karna's seven-arrow volley), serpent (the serpent arrow tears the sky toward Arjuna)

These are concept paintings for choosing a direction, not final frames. Each call sends the approved character sheets
and sai's own paintings only. BILLED: one image per job per run (gemini-3.1-flash-image, about $0.07 each). Needs sai's
own go with the cost. No automatic retries. Never overwrites a take. Every call is logged to studio/log.md.

  python studio/tools/gen_concepts.py --project cs-project-07zg2j2c --dry-run
  python studio/tools/gen_concepts.py --project cs-project-07zg2j2c
  python studio/tools/gen_concepts.py --project cs-project-07zg2j2c --only A_volley,B_serpent --take 2
"""
import argparse, base64, datetime, json, pathlib, sys

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
        }),
}
JOBS = [f"{d}_{m}" for d in LOOK for m in MOMENT]

def build(job):
    d, m = job.split("_")
    mo = MOMENT[m]
    lines = [LOOK[d], "", mo["ref_note"], ""] + [descriptor(p) for p in mo["passports"]] + ["", mo["base"], mo["extra"][d], "", RULES]
    return mo["refs"], "\n".join(lines)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True); ap.add_argument("--location", default="global")
    ap.add_argument("--only", default=",".join(JOBS)); ap.add_argument("--take", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    for job in a.only.split(","):
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

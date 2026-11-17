#!/usr/bin/env python3
"""Gate 2 of the hand-animated 3D plan: model sheets that TRELLIS.2 turns into 3D models.

TRELLIS.2 needs one clean picture of one object: whole in frame, plain white background, neutral light. For a character
that means a relaxed A-pose with empty hands. The front view is the TRELLIS.2 input; the back and side views are
painted from that front view and guide the cleanup, rig and texture work in Blender. Weapons get their own sheet.

Jobs run in the order given. A back or side job needs the front view of the same take, so run the front first
(the default order does). Output: cast/<character>/model/<view>_v<take>.png.

BILLED: one image per job per run (gemini-3.1-flash-image = Nano Banana 2.1, about $0.07 each). Needs sai's own go with
the cost. No automatic retries. Never overwrites a take. Every call is logged to studio/log.md. Only our own approved
sheets and sai's own paintings are attached.

  python studio/tools/gen_model_sheets.py --project cs-project-07zg2j2c --only karna --dry-run
  python studio/tools/gen_model_sheets.py --project cs-project-07zg2j2c --only karna
"""
import argparse, base64, datetime, json, pathlib, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gen_sheets import MODEL, STUDIO, call, descriptor      # same API call, same model

BODY = ("A character model sheet for a 3D modeller: ONE man, full body from the top of the crown to the soles of the feet, centred, with "
        "a clear margin of white around him. He stands upright and symmetrical in a relaxed A-pose: both arms straight and held away "
        "from the body at about 40 degrees below horizontal, hands open and empty with the fingers slightly apart, legs straight and "
        "a shoulder-width apart, feet flat and pointing forward, head level, mouth closed, calm neutral face. "
        "He holds NOTHING: no bow, no arrow, no quiver in the hands. "
        "Look: a stylized 3D animated-film character, slightly larger than life with a powerful build, clean sculpted forms, and "
        "hand-painted surfaces with visible brushwork on skin, gold and cloth, as in the reference painting. "
        "Flat, even, neutral studio light from the front: no dramatic shadows, no rim light, no glow, no dust. "
        "Pure plain white background, no floor line, no cast shadow, no scenery, no other people, no text, no labels, no border, "
        "no extra views in the same picture. Seen straight on at chest height with a long lens, almost no perspective. "
        "Cloth hangs straight down and stays close to the body; nothing flies or billows.")

def char_jobs(tag, name, sheet, passport, paint, back_ref, back_note):
    m = f"cast/{tag}/model"
    same = ("IMAGE 1 is the approved FRONT model sheet of this same man. Paint the very same figure, same pose, same proportions, same "
            "costume and same painted look, as if the camera had walked around him while he stood still.")
    return {
        f"{tag}_front": dict(out=f"{m}/front", refs=[sheet, paint], passport=passport, aspect="3:4",
                             text=f"{BODY}\n\nFRONT VIEW: he faces the camera exactly, chest square to the viewer.\n\n"
                                  f"IMAGE 1 is the approved character sheet of {name}: same face, same body, same costume, nothing "
                                  f"added and nothing left out. IMAGE 2 is a reference painting for the painted look and the carved gold."),
        f"{tag}_back": dict(out=f"{m}/back", refs=[f"{m}/front_v{{take}}.png", sheet] + back_ref, passport=passport, aspect="3:4",
                            text=f"{BODY}\n\nBACK VIEW: he is seen exactly from behind, his back square to the viewer, the back of his head "
                                 f"and crown toward the camera.\n\n{same} IMAGE 2 is his approved character sheet. {back_note}"),
        f"{tag}_side": dict(out=f"{m}/side", refs=[f"{m}/front_v{{take}}.png", sheet], passport=passport, aspect="3:4",
                            text=f"{BODY}\n\nSIDE VIEW: he is seen exactly from his left side in pure profile, facing screen left, the near "
                                 f"arm held slightly forward so the torso stays visible.\n\n{same} IMAGE 2 is his approved character sheet."),
    }

JOBS = {}
JOBS.update(char_jobs("karna", "Karna", "cast/karna/sheet.png", "cast/karna/passport.md", "refs/concept/concept_46.jpeg",
                      ["refs/concept/concept_37.jpeg"],
                      "IMAGE 3 is a reference painting that shows the round gold sun-face disc strapped on his back with black "
                      "gold-studded leather straps: paint that disc flat on the middle of his back. He has bare earlobes, no earrings."))
JOBS["karna_bow"] = dict(
    out="cast/karna/model/bow_vijaya", refs=["cast/karna/sheet.png"], passport=None, aspect="3:4",
    text=("A prop model sheet for a 3D modeller: ONE object only, the great war bow Vijaya from IMAGE 1, shown alone with no person and "
          "no hand. The bow stands upright and is seen exactly from the side, whole in frame with a clear margin of white: a tall recurve "
          "bow with black limbs wrapped in spiral gold bands, gold winged fittings above and below the grip, curled gold tips, and one "
          "thin taut bowstring running straight from tip to tip. No arrow. Stylized 3D animated-film prop with hand-painted surfaces. "
          "Flat even neutral light, pure plain white background, no shadow, no text, no labels, no border, no second view."))
GROUPS = {"karna": ["karna_front", "karna_back", "karna_side", "karna_bow"]}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True); ap.add_argument("--location", default="global")
    ap.add_argument("--only", required=True, help="a group (karna) or job names separated by commas")
    ap.add_argument("--take", type=int, default=1); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    jobs = [j for part in a.only.split(",") for j in GROUPS.get(part, [part])]
    for i, name in enumerate(jobs):
        if name not in JOBS:
            print("unknown job", name, "| jobs:", list(JOBS), "| groups:", list(GROUPS)); sys.exit(1)
        j = JOBS[name]
        refs = [r.format(take=a.take) for r in j["refs"]]
        rel = f"{j['out']}_v{a.take}.png"
        out = STUDIO / rel
        if out.exists():
            print("exists, not overwriting (folder law 1):", rel); sys.exit(1)
        prompt = j["text"] + (f"\n\n{descriptor(j['passport'])}" if j["passport"] else "")
        if a.dry_run:
            print("---", name, "->", rel, "\nrefs:", refs, "\n" + prompt, "\n"); continue
        missing = [r for r in refs if not (STUDIO / r).exists()]
        if missing:
            print("missing reference (a back or side view needs the front view of the same take first):", missing); sys.exit(1)
        if i:
            time.sleep(25)        # pacing only, against the 429 rate limit. This is not a retry.
        res = call(a.project, a.location, prompt, refs, j["aspect"])
        imgs = [p for c in res.get("candidates", []) for p in c.get("content", {}).get("parts", []) if "inlineData" in p]
        if not imgs:
            print("no image returned:", json.dumps(res)[:1500]); sys.exit(1)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(imgs[0]["inlineData"]["data"]))
        u = res.get("usageMetadata", {})
        with open(STUDIO / "log.md", "a") as f:
            f.write(f"| {datetime.date.today()} | {rel} | {MODEL} | model sheet {name}, {len(refs)} refs | tokens in {u.get('promptTokenCount')} out {u.get('candidatesTokenCount')} | pending review |\n")
        print("wrote", rel, "usage", u)

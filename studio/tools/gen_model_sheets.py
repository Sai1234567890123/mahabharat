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
        "Cloth hangs straight down and stays close to the body; nothing flies or billows. "
        "Exactly ONE figure in the picture: no second figure, no second view, no dividing line.")

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
# sai, 2026-11-17: "remove shield of karna back side". Nothing is strapped on Karna's back any more (passport v2.1).
NO_DISC = ("There is NOTHING on his back: NO round disc, NO shield, NO plate or wheel shape behind his shoulders, and nothing shows "
           "behind his silhouette. If a reference image shows a round disc behind his shoulders, do NOT paint it. His gold cuirass wraps "
           "the whole torso and its back is a plain carved gold back plate. He has bare earlobes, no earrings.")
JOBS.update(char_jobs("karna", "Karna", "cast/karna/sheet.png", "cast/karna/passport.md", "refs/concept/concept_46.jpeg", [], NO_DISC))
for _v in ("karna_front", "karna_side"):
    JOBS[_v]["text"] += " " + NO_DISC
JOBS["karna_bow"] = dict(
    out="cast/karna/model/bow_vijaya", refs=["cast/karna/sheet.png"], passport=None, aspect="3:4",
    text=("A prop model sheet for a 3D modeller: ONE object only, the great war bow Vijaya from IMAGE 1, shown alone with no person and "
          "no hand. The bow stands upright and is seen exactly from the side, whole in frame with a clear margin of white: a tall recurve "
          "bow with black limbs wrapped in spiral gold bands, gold winged fittings above and below the grip, curled gold tips, and one "
          "thin taut bowstring running straight from tip to tip. No arrow. Stylized 3D animated-film prop with hand-painted surfaces. "
          "Flat even neutral light, pure plain white background, no shadow, no text, no labels, no border, no second view."))
GROUPS = {"karna": ["karna_front", "karna_back", "karna_side", "karna_bow"]}
# Karna's own chariot (sai, 2026-11-27 "Yes"): replaces the kit rank chariot in A02, A05, A06, A16. Gold car with lion-griffin
# figures at the front and maroon panels with gold scrollwork (paintings 46 and 37). Car only: no horses, no people, no flag.
CHARIOT = ("A prop model sheet for a 3D modeller: ONE object only, the war chariot of Karna, alone, with no horses, no people, no "
           "driver, no flag and no weapons. Seen from the front-left at three-quarters, slightly from above, the whole chariot in frame "
           "with a clear margin of white. It is a two-wheeled open war car: a box with a raised front rail and low side rails, the "
           "floor about knee high. Two very large wheels, taller than a man's chest, with a gold rim, a black-and-gold inlaid felloe and "
           "many turned gold spokes, as in IMAGE 2. Its outer panels are deep maroon with raised gold scrollwork; every edge, rail and "
           "post is carved gold. At the front corners stand two crouching gold lion-griffin figures facing forward, as in IMAGE 1, "
           "and a single straight draught pole runs forward from the middle of the floor with a plain wooden yoke bar across its tip. "
           "Ancient Indian, hand-made, no stirrups, no seat backs, no glass, no machined metal. Stylized 3D animated-film prop with "
           "hand-painted surfaces. Flat even neutral light, pure plain white background, no shadow, no text, no labels, no border, no "
           "second view.")
JOBS["karna_chariot"] = dict(out="cast/karna/model/chariot", refs=["refs/concept/concept_46.jpeg", "refs/concept/concept_37.jpeg"],
                             passport=None, aspect="4:3", text=CHARIOT)
JOBS["karna_chariot_side"] = dict(out="cast/karna/model/chariot_side", refs=["cast/karna/model/chariot_v{take}.png", "refs/concept/concept_37.jpeg"],
                                  passport=None, aspect="4:3",
                                  text=CHARIOT.replace("Seen from the front-left at three-quarters, slightly from above",
                                                       "Seen exactly from the left side, at the height of the floor")
                                  + " IMAGE 1 is the approved three-quarter view of this very chariot: paint the same object.")
GROUPS["chariot"] = ["karna_chariot", "karna_chariot_side"]


# ---- series look (sai, 2026-11-22, "Yes, all three"): 3D models of the LOCKED web series hero set, so each hero can get a
# face rig (tools/blender/face_rig.py). Per hero: a full-body A-pose front view (TRELLIS.2 body) and a head close-up front
# view (a separate high-detail TRELLIS.2 head, the face that gets rigged, as done for Karna take 3 and Krishna).
# Run with --only web (6 images, about $0.42). Output: cast/<hero>/model/web_front_v<take>.png and web_head_v<take>.png.
STYLE_FRAME = "cast/karna/web/close_v1.png"
WEB_LOOK = ("Look: EXACTLY the series look of the style frame: a stylized 3D animated-series character, smooth sculpted forms "
            "with clean painted shading, a long angular face with sharp cheekbones; not a painting, not realistic.")
WEB_BODY = BODY.replace("Look: a stylized 3D animated-film character, slightly larger than life with a powerful build, clean sculpted forms, and "
                        "hand-painted surfaces with visible brushwork on skin, gold and cloth, as in the reference painting. ", WEB_LOOK + " ")
WEB_HEAD = ("A head model sheet for a 3D modeller: ONE man's head, neck and the top of his shoulders, seen exactly from the front, "
            "face square to the camera, centred, the whole crown in frame with a clear margin of white. Calm NEUTRAL face: eyes open "
            "and looking straight into the camera, brows relaxed, mouth closed, lips relaxed, no smile. " + WEB_LOOK +
            " Flat, even, neutral studio light from the front: no dramatic shadows, no rim light, no glow. Pure plain white "
            "background, no scenery, no text, no labels, no border, exactly one view.")
def web_jobs(tag, name, body_ref, face_ref, passport, note):
    m = f"cast/{tag}/model"
    who = (f"IMAGE 1 is the LOCKED series design of {name}: same face, same body, same costume, colours and ornaments, nothing "
           f"added and nothing left out. ")
    return {
        f"{tag}_web_front": dict(out=f"{m}/web_front", refs=[body_ref, STYLE_FRAME], passport=passport, aspect="3:4",
            text=f"{WEB_BODY}\n\nFRONT VIEW: he faces the camera exactly, chest square to the viewer.\n\n{who}"
                 f"IMAGE 2 is the series style frame: take only its rendering style. {note}"),
        f"{tag}_web_head": dict(out=f"{m}/web_head", refs=[face_ref, STYLE_FRAME], passport=passport, aspect="1:1",
            text=f"{WEB_HEAD}\n\n{who}IMAGE 2 is the series style frame: take only its rendering style. {note}"),
    }
JOBS.update(web_jobs("karna", "Karna", "cast/karna/web/full_v2.png", "cast/karna/web/close_v1.png", "cast/karna/passport.md",
    "Karna: bare earlobes with NO earrings, NO tilak, NO hair band, NOTHING on his back (no disc, no shield, no parasol)."))
JOBS.update(web_jobs("arjuna", "Arjuna", "cast/arjuna/web/full_v4.png", "cast/arjuna/web/close_v4.png", "cast/arjuna/passport_web.md",
    "Arjuna: silver-steel armour and crown with thin gold trim (never gold armour), deep green sash over a deep blue dhoti, a THIN "
    "neat moustache, his silver quiver stays on his back but holds no bow."))
JOBS.update(web_jobs("krishna", "Krishna", "cast/krishna/web/close_v2.png", "cast/krishna/web/close_v2.png", "cast/krishna/passport.md",
    "Krishna: blue skin everywhere, as in IMAGE 1. IMAGE 1 shows only his upper body: below it he wears the crimson and gold "
    "dhoti of his description, gold anklets and bare feet."))
JOBS["krishna_web_front"]["refs"].insert(1, "cast/krishna/sheet.png")
JOBS["krishna_web_front"]["text"] = JOBS["krishna_web_front"]["text"].replace("IMAGE 2 is the series style frame", "IMAGE 2 is his older sheet, ONLY for the costume below the chest (never its face, skin or style). IMAGE 3 is the series style frame")
JOBS["karna_web_head"]["refs"] = ["cast/karna/web/close_v1.png"]        # his close-up IS the style frame
JOBS["karna_web_head"]["text"] = JOBS["karna_web_head"]["text"].replace(" IMAGE 2 is the series style frame: take only its rendering style.", "")
for _h in ("karna", "arjuna", "krishna"):
    JOBS[f"{_h}_web_front"]["text"] += " The weapon and any reins in the description below are NOT in this picture: his hands are open and empty."
# Karna's head take 1 came out as a six-view turnaround grid; take 2 insists on one single front view.
JOBS["karna_web_head"]["text"] += (" ONE SINGLE FRONT VIEW ONLY: not a turnaround, not a grid, not several heads; exactly one head "
                                   "filling the picture, seen from the front.")
GROUPS["web"] = [f"{h}_web_{v}" for h in ("karna", "arjuna", "krishna") for v in ("front", "head")]

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

#!/usr/bin/env python3
"""Web series look (bible, "Web series look", 2026-11-20): redesign the locked heroes as stylized 3D series characters.

sai's reference reels (study only, never sent anywhere) showed that the gap is the character design: long angular stylized
faces, big expressive hands, hand-painted textures, soft warm daylight with cool shadows. This keeps each hero's locked
identity and costume (his approved sheet is IMAGE 1) and changes only the rendering style. Nothing from the reels is
attached or named; only our own approved sheets go to the model.

BILLED: one image per job (gemini-3.1-flash-image, about $0.07 each). Needs sai's own go with the cost. No automatic
retries. Never overwrites a take. Every call is logged to studio/log.md.

  python studio/tools/gen_style_redesign.py --project cs-project-07zg2j2c --only heroes --dry-run
  python studio/tools/gen_style_redesign.py --project cs-project-07zg2j2c --only heroes          # take 1: 4 images, about $0.28
  python studio/tools/gen_style_redesign.py --project cs-project-07zg2j2c --only take2 --take 2  # take 2: 3 images, about $0.21
  python studio/tools/gen_style_redesign.py --project cs-project-07zg2j2c --only arjuna_close_t3 --take 3   # 1 image, ~$0.07
Output: cast/<character>/web/<view>_v<take>.png
"""
import argparse, base64, datetime, json, pathlib, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gen_sheets import MODEL, STUDIO, call, descriptor      # same API call, same model

LOOK = ("Look: a character from a premium stylized 3D animated series for adults. Stylized, not realistic: elongated angular face "
        "with sharp sculpted planes (high cheekbones, strong brow and jaw, long straight nose), slightly elongated limbs, large "
        "expressive hands with long fingers. Every surface is hand-painted: visible painterly brush strokes in the skin, the cloth and "
        "the carved gold, painted highlights and soft painted shadow shapes, no photographic texture, no plastic shine. "
        "Light: soft warm golden daylight as the key from the upper left, cool blue-violet shadows and a cool blue fill, a thin warm rim. "
        "Rich but controlled colour. No flat cartoon, no cel outline, no anime, no chibi, no photo realism. Original character, "
        "no real actor likeness. No text, no logos, no watermark, no border.")
FULL = ("ONE man, full body from the top of the crown to the feet, standing in a calm three-quarter front view, weight on one leg, "
        "hands relaxed and empty. Plain painted backdrop: a soft warm-to-cool gradient with loose brush strokes, a soft floor shadow, "
        "no scenery, no other people.")
CLOSE = ("A story close-up of ONE man: head and shoulders, three-quarter view, eyes looking just past the camera, quiet and grave, "
         "lips closed. Shallow depth of field, the background a soft painted wash of a dusty battlefield sky at golden hour.")
SAME = ("IMAGE 1 is the approved character sheet of {name}: keep his identity, age, build, hair, crown, costume, colours and "
        "ornaments exactly; nothing added and nothing left out. Change ONLY the rendering style to the look described.")
KARNA = ("Karna has bare earlobes (NO earrings), NO tilak or mark on the forehead, NO hair band, and NOTHING on his back: no disc, "
         "no shield, no parasol. Saffron-orange dhoti, carved gold cuirass with the sun-face on the chest.")
KRISHNA = "Krishna's skin is blue, as in IMAGE 1."

JOBS = {
    "karna_full": dict(out="cast/karna/web/full", ref="cast/karna/sheet.png", name="Karna", passport="cast/karna/passport.md",
                       aspect="3:4", text=f"{FULL}\n\n{LOOK}\n\n{SAME.format(name='Karna')} {KARNA}"),
    "karna_close": dict(out="cast/karna/web/close", ref="cast/karna/sheet.png", name="Karna", passport="cast/karna/passport.md",
                        aspect="16:9", text=f"{CLOSE}\n\n{LOOK}\n\n{SAME.format(name='Karna')} {KARNA}"),
    "arjuna_full": dict(out="cast/arjuna/web/full", ref="cast/arjuna/sheet.png", name="Arjuna", passport="cast/arjuna/passport.md",
                        aspect="3:4", text=f"{FULL}\n\n{LOOK}\n\n{SAME.format(name='Arjuna')}"),
    "krishna_full": dict(out="cast/krishna/web/full", ref="cast/krishna/sheet.png", name="Krishna", passport="cast/krishna/passport.md",
                         aspect="3:4", text=f"{FULL}\n\n{LOOK}\n\n{SAME.format(name='Krishna')} {KRISHNA}"),
}
GROUPS = {"heroes": ["karna_full", "karna_close", "arjuna_full", "krishna_full"]}

# ---- take 2 (sai, 2026-11-20: "yes"): the Karna close-up close_v1 is the style frame for the series. The old sheets are used
# for costume only, not for faces, proportions or painting style. Run with --only take2 --take 2 (3 images, about $0.21).
STYLE_REF = "cast/karna/web/close_v1.png"
LOOK2 = ("Rendering: match IMAGE 2 exactly. It is the approved style frame of this series: stylized 3D animated-series character, "
         "smooth sculpted forms with clean painted shading, a long angular face with sharp cheekbones, a strong brow and jaw and "
         "a long straight nose, warm gold key light against cool blue-grey sky light, soft painted background. "
         "Not a painting, not realistic: a premium stylized 3D series. No text, no logos, no watermark, no border.")
COSTUME = ("Use IMAGE 1 ONLY for {name}'s costume, crown, ornaments, colours, hair and weapon. Do NOT copy the face shape, the body "
           "proportions or the painting style of IMAGE 1: draw his face and body in the stylized way of IMAGE 2.")
OTHER = ("IMAGE 2 shows a different man (Karna): take ONLY its rendering style and light from it, never his face, crown, "
         "moustache, armour or colours.")
CLOSE2 = ("A story close-up of ONE man: framed from the top of his crown to his upper chest, head and shoulders only, hands and "
          "weapon out of frame, three-quarter view, eyes looking just past the camera, quiet and grave, lips closed. Shallow depth "
          "of field, the background a soft painted wash of a dusty battlefield sky at golden hour.")
FULL2 = ("ONE man, full body from the top of the crown to the feet, standing in a calm three-quarter front view, weight on one "
         "leg, holding his bow low in one hand. Stylized heroic proportions: long legs, broad shoulders, large expressive hands with "
         "long fingers. Soft painted backdrop with a soft floor shadow, no scenery, no other people.")
JOBS.update({
    "karna_full_t2": dict(out="cast/karna/web/full", refs=["cast/karna/sheet.png", STYLE_REF], name="Karna",
                          passport="cast/karna/passport.md", aspect="3:4",
                          text=f"{FULL2}\n\n{LOOK2}\n\nIMAGE 2 is this same man, Karna, in the series style: same face as IMAGE 2. "
                               f"{COSTUME.format(name='Karna')} {KARNA}"),
    "arjuna_close": dict(out="cast/arjuna/web/close", refs=["cast/arjuna/sheet.png", STYLE_REF], name="Arjuna",
                         passport="cast/arjuna/passport.md", aspect="16:9",
                         text=f"{CLOSE2}\n\n{LOOK2}\n\n{COSTUME.format(name='Arjuna')} {OTHER}"),
    "krishna_close": dict(out="cast/krishna/web/close", refs=["cast/krishna/sheet.png", STYLE_REF], name="Krishna",
                          passport="cast/krishna/passport.md", aspect="16:9",
                          text=f"{CLOSE2}\n\n{LOOK2}\n\n{COSTUME.format(name='Krishna')} {OTHER} {KRISHNA}"),
})
GROUPS["take2"] = ["karna_full_t2", "arjuna_close", "krishna_close"]

# ---- take 3, Arjuna close-up only: take 2 copied Karna's face (heavy moustache, brows and jaw) from the style frame.
# Run with --only arjuna_close_t3 --take 3 (1 image, about $0.07).
ARJUNA_FACE = ("His FACE must be clearly a different man from the one in IMAGE 2: Arjuna is younger (early thirties) and leaner, "
               "with a narrow oval face, high sharp cheekbones, a sharp straight profile, a clean narrow jaw, a THIN neat upturned "
               "moustache (not thick, not bushy), lighter arched brows and a focused, alert look. Take his face from IMAGE 1, drawn in "
               "the stylized way of IMAGE 2. From IMAGE 2 take ONLY the lighting, shading and painted background; do NOT copy that "
               "man's face, moustache, brows, jaw, crown or armour.")
JOBS["arjuna_close_t3"] = dict(out="cast/arjuna/web/close", refs=["cast/arjuna/sheet.png", STYLE_REF], name="Arjuna",
                               passport="cast/arjuna/passport.md", aspect="16:9",
                               text=f"{CLOSE2}\n\n{LOOK2}\n\n{ARJUNA_FACE}\n\n{COSTUME.format(name='Arjuna')}")
# Shalya has no approved sheet or passport yet; he is designed after sai approves this look.

# ---- take 4 (sai, 2026-11-21: "Arjuna silver-steel, Karna gold"): Arjuna in his web series costume, cast/arjuna/passport_web.md.
# Run with --only arjuna_t4 --take 4 (2 images, about $0.14).
SILVER = ("COSTUME CHANGE from IMAGE 1: his armour, crown, shoulder guard, bracers and quiver are engraved SILVER-STEEL with thin "
          "gold trim, NOT gold; his dhoti is DEEP BLUE with a thin gold border, NOT white; the deep green sash stays. Everything "
          "else (crown shape, ear-guard, sash, bow Gandiva) as in IMAGE 1.")
for _job, _frame, _aspect in (("arjuna_close_t4", CLOSE2, "16:9"), ("arjuna_full_t4", FULL2, "3:4")):
    JOBS[_job] = dict(out="cast/arjuna/web/" + ("close" if "close" in _job else "full"),
                      refs=["cast/arjuna/sheet.png", STYLE_REF], name="Arjuna", passport="cast/arjuna/passport_web.md",
                      aspect=_aspect, text=f"{_frame}\n\n{LOOK2}\n\n{ARJUNA_FACE}\n\n{SILVER}")
GROUPS["arjuna_t4"] = ["arjuna_close_t4", "arjuna_full_t4"]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True); ap.add_argument("--location", default="global")
    ap.add_argument("--only", required=True, help="a group (heroes) or job names separated by commas")
    ap.add_argument("--take", type=int, default=1); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    jobs = [j for part in a.only.split(",") for j in GROUPS.get(part, [part])]
    for i, name in enumerate(jobs):
        if name not in JOBS:
            print("unknown job", name, "| jobs:", list(JOBS), "| groups:", list(GROUPS)); sys.exit(1)
        j = JOBS[name]
        rel = f"{j['out']}_v{a.take}.png"
        out = STUDIO / rel
        if out.exists():
            print("exists, not overwriting (folder law 1):", rel); sys.exit(1)
        refs = j.get("refs") or [j["ref"]]
        prompt = j["text"] + f"\n\n{descriptor(j['passport'])}"
        if a.dry_run:
            print("---", name, "->", rel, "\nrefs:", refs, "\n" + prompt, "\n"); continue
        missing = [r for r in refs if not (STUDIO / r).exists()]
        if missing:
            print("missing reference:", missing); sys.exit(1)
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
            f.write(f"| {datetime.date.today()} | {rel} | {MODEL} | web series redesign {name}, {len(refs)} refs | tokens in {u.get('promptTokenCount')} out {u.get('candidatesTokenCount')} | pending review |\n")
        print("wrote", rel, "usage", u)


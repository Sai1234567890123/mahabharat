#!/usr/bin/env python3
"""Web series look (bible, "Web series look", 2026-11-20): redesign the locked heroes as stylized 3D series characters.

sai's reference reels (study only, never sent anywhere) showed that the gap is the character design: long angular stylized
faces, big expressive hands, hand-painted textures, soft warm daylight with cool shadows. This keeps each hero's locked
identity and costume (his approved sheet is IMAGE 1) and changes only the rendering style. Nothing from the reels is
attached or named; only our own approved sheets go to the model.

BILLED: one image per job (gemini-3.1-flash-image, about $0.07 each). Needs sai's own go with the cost. No automatic
retries. Never overwrites a take. Every call is logged to studio/log.md.

  python studio/tools/gen_style_redesign.py --project cs-project-07zg2j2c --only heroes --dry-run
  python studio/tools/gen_style_redesign.py --project cs-project-07zg2j2c --only heroes          # 4 images, about $0.28
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
# Shalya has no approved sheet or passport yet; he is designed after sai approves this look.

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
        prompt = j["text"] + f"\n\n{descriptor(j['passport'])}"
        if a.dry_run:
            print("---", name, "->", rel, "\nrefs:", [j["ref"]], "\n" + prompt, "\n"); continue
        if not (STUDIO / j["ref"]).exists():
            print("missing reference:", j["ref"]); sys.exit(1)
        if i:
            time.sleep(25)        # pacing only, against the 429 rate limit. This is not a retry.
        res = call(a.project, a.location, prompt, [j["ref"]], j["aspect"])
        imgs = [p for c in res.get("candidates", []) for p in c.get("content", {}).get("parts", []) if "inlineData" in p]
        if not imgs:
            print("no image returned:", json.dumps(res)[:1500]); sys.exit(1)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(imgs[0]["inlineData"]["data"]))
        u = res.get("usageMetadata", {})
        with open(STUDIO / "log.md", "a") as f:
            f.write(f"| {datetime.date.today()} | {rel} | {MODEL} | web series redesign {name}, 1 ref | tokens in {u.get('promptTokenCount')} out {u.get('candidatesTokenCount')} | pending review |\n")
        print("wrote", rel, "usage", u)

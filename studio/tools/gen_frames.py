#!/usr/bin/env python3
"""Step 4 of the trailer plan: paint a shot's first frame over its 3D layout (Nano Banana 2.1 = gemini-3.1-flash-image).

Each call sends, in this order: the layout still (composition), the approved character sheets of the cast in the shot,
and sai's own concept paintings for the look. The prompt is the bible's global style prompt, the passport descriptors
pasted verbatim, and the shot card's frame line. Output: episodes/ep01_arjuna_vs_karna/frames/<shot>_v<take>.png.

BILLED: one image per shot per run. Needs sai's own go with the cost. No automatic retries. Never overwrites a take.
Every call is logged to studio/log.md. Only sai's own paintings and our own sheets and layouts are ever attached.

  python studio/tools/gen_frames.py --project cs-project-07zg2j2c --only A16,A06 --dry-run
  python studio/tools/gen_frames.py --project cs-project-07zg2j2c --only A16,A06
"""
import argparse, base64, datetime, json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gen_sheets import MODEL, STUDIO, call, descriptor      # same API call, same model

EP = "episodes/ep01_arjuna_vs_karna"
SHEETS = {"@arjuna": "cast/arjuna", "@arjuna_bare": "cast/arjuna_bare", "@karna": "cast/karna", "@krishna": "cast/krishna"}

LAYOUT_RULE = (
    "IMAGE 1 is a rough 3D layout of this exact shot. Keep its camera angle, lens, horizon, composition, screen direction and the "
    "position and pose of every figure, chariot, horse, banner and the sun. Do NOT copy its look: the blocky mannequins, flat colours and "
    "plain models are placeholders. Repaint everything as a finished painting. The layout chariots have no parasol; paint the chariots "
    "richly carved as in the reference paintings.")

# per-shot look references (sai's own paintings) and notes that the layout cannot carry
SHOTS = {
    "A16": dict(look=["refs/concept/concept_37.jpeg", "refs/concept/concept_46.jpeg"],
                note="Karna has leapt down from his chariot and stands on the ground at its sunken left wheel, back and shoulders straining, "
                     "both hands gripping the wheel rim, the round gold sun-face disc on his back toward the camera as in the reference "
                     "painting of him at the wheel. The wheel is buried to the hub in cracked red earth and the chariot leans toward it. "
                     "Shalya, a grey-bearded older charioteer, sits at the front holding the reins of four dun horses. The low sun is "
                     "directly behind the chariot. The horizon is tilted a few degrees as in the layout. Dust pours off the wheel rim."),
    "A06": dict(look=["refs/concept/concept_46.jpeg", "refs/concept/concept_34.jpeg"],
                note="Karna stands on his chariot at full draw facing screen left, seven arrows nocked together as a vertical fan on the "
                     "one bowstring, a thin line of orange-gold sun-fire along each shaft, the low sun directly behind his bow hand. "
                     "Shalya, a grey-bearded older charioteer, sits low in front of him with the reins. The Kaurava host stands far behind "
                     "in pale gold dust. No arrow has been released yet."),
}

def style():
    m = re.search(r"## Global style prompt.*?\n\n> (.+?)\n", (STUDIO / "bible.md").read_text(), re.S)
    return m.group(1).strip()

def build(sid, card):
    cast = [c for c in card["chars"] if c in SHEETS]
    refs = [f"{EP}/layout/{sid}.jpg"] + [f"{SHEETS[c]}/sheet.png" for c in cast] + SHOTS[sid]["look"]
    n = 2
    lines = [style(), "", LAYOUT_RULE]
    for c in cast:
        lines.append(f"IMAGE {n} is the approved character sheet of {c[1:].replace('_', ' ')}: same face, same body, same costume, "
                     f"no additions (no shield, no extra jewellery).")
        n += 1
    lines.append(f"IMAGES {n} and {n + 1} are reference paintings for the painting style, light, dust, armour and chariot detail only. "
                 f"Do not copy their composition.")
    lines.append("")
    for c in cast:
        lines.append(descriptor(f"{SHEETS[c]}/passport.md"))
    lines += ["", f"SHOT {sid}. Camera: {card['camera']}. {card['frame']}", SHOTS[sid]["note"], "",
              "One single finished frame, 16:9. No text, no labels, no borders, no split screen, no mannequins, no 3D render look."]
    return refs, "\n".join(lines)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True); ap.add_argument("--location", default="global")
    ap.add_argument("--only", required=True); ap.add_argument("--take", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cards = {s["id"]: s for s in json.loads((STUDIO / EP / "shots.json").read_text())["shots"]}
    for sid in a.only.split(","):
        if sid not in SHOTS:
            print("no frame recipe yet for", sid); sys.exit(1)
        refs, prompt = build(sid, cards[sid])
        missing = [r for r in refs if not (STUDIO / r).exists()]
        if missing:
            print("missing reference", missing); sys.exit(1)
        rel = f"{EP}/frames/{sid}_v{a.take}.png"
        out = STUDIO / rel
        if out.exists():
            print("exists, not overwriting (folder law 1):", rel); sys.exit(1)
        if a.dry_run:
            print("---", sid, "->", rel, "\nrefs:", refs, "\n" + prompt, "\n"); continue
        res = call(a.project, a.location, prompt, refs, "16:9")
        imgs = [p for c in res.get("candidates", []) for p in c.get("content", {}).get("parts", []) if "inlineData" in p]
        if not imgs:
            print("no image returned:", json.dumps(res)[:1500]); sys.exit(1)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(imgs[0]["inlineData"]["data"]))
        u = res.get("usageMetadata", {})
        with open(STUDIO / "log.md", "a") as f:
            f.write(f"| {datetime.date.today()} | {rel} | {MODEL} | frame over layout, {len(refs)} refs | tokens in {u.get('promptTokenCount')} out {u.get('candidatesTokenCount')} | pending review |\n")
        print("wrote", rel, "usage", u)

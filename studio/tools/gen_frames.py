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
# the approved sheet file of each character (an approved file is never renamed)
SHEET_FILE = {"@arjuna": "sheet.png", "@arjuna_bare": "sheet_v4.png", "@karna": "sheet.png", "@krishna": "sheet.png"}

LAYOUT_RULE = (
    "IMAGE 1 is a rough 3D layout of this exact shot. Keep its camera angle, lens, horizon, composition, screen direction and the "
    "position and pose of every figure, chariot, horse, banner and the sun. Do NOT copy its look: the blocky mannequins, flat colours and "
    "plain models are placeholders. Repaint everything as a finished painting. The layout chariots have no parasol and no canopy: paint "
    "NO parasol, NO canopy and NO awning on any chariot. Paint the chariots richly carved as in the reference paintings. "
    "Karna has bare earlobes: NO earring on any figure, NO tilak on any forehead, NO extra jewellery on the head or ears.")

# per-shot look references (sai's own paintings) and notes that the layout cannot carry
SHOTS = {
    "A16": dict(look=["refs/concept/concept_37.jpeg", "refs/concept/concept_46.jpeg"],
                note="Do NOT mirror or re-stage the layout: the four dun horses are at screen LEFT pulling toward the left, the chariot is "
                     "in the middle, Karna is at the right of centre, the armies are far away at the right edge. "
                     "Karna has leapt down and stands on the ground with his back to the camera, bent forward, both hands on the rim of the "
                     "chariot's OWN left wheel, which is still on its axle. That wheel has sunk into cracked red earth up to its hub and the "
                     "whole chariot leans toward it. He still wears his rounded gold crown and his full gold cuirass; the round gold sun-face "
                     "disc is strapped on his back toward the camera, as in the reference painting of him at the wheel. "
                     "Shalya, a grey-bearded older charioteer, sits at the front holding the reins. A plain gold banner on a pole stands on "
                     "the chariot. Open empty battlefield around them: NO other chariot, NO elephant close by, NO building, NO city, NO palace. "
                     "No loose wheel and no broken pieces on the ground. The low sun glows behind the chariot at the right. "
                     "The horizon is tilted a few degrees as in the layout. Dust pours off the wheel rim."),
    "A06": dict(look=["refs/concept/concept_46.jpeg", "refs/concept/concept_34.jpeg"],
                note="Karna stands on his chariot at full draw facing screen left, bare-eared. Seven arrows are nocked on one bowstring and "
                     "fan out from the bow hand, each shaft visibly angled apart from the others, not parallel. A thin orange-gold sun-fire runs "
                     "along every shaft. The low sun is directly behind his bow hand. Shalya, a grey-bearded older charioteer, sits low in front "
                     "of him with the reins. The Kaurava host stands far behind in pale gold dust. No arrow has been released yet. "
                     "No parasol above the chariot."),
    # Act I batch. `cast` lists the sheets to attach when it differs from the card (tiny or off-frame figures get no sheet);
    # `frame` replaces the card's frame line where the approved layout stages the shot differently from the card.
    "A02": dict(look=["refs/concept/concept_42.jpeg", "refs/concept/concept_06.jpeg"], cast=[],
                note="Extreme wide establishing view exactly as the layout. A broad EMPTY ring of trampled warm red-brown earth fills the "
                     "lower half of the frame. At the LEFT, small, Arjuna's bright gold chariot with four white horses faces right; a green "
                     "banner with a gold ape flies from a tall pole on it; a crowned archer in gold stands on it and a blue-skinned charioteer "
                     "in yellow sits at the front. At the RIGHT, small, Karna's darker bronze and maroon chariot with four dun horses faces "
                     "left; a gold banner flies from a tall pole on it; a crowned archer in gold with a saffron dhoti stands on it, a "
                     "grey-bearded charioteer in front. The two chariots face each other across the empty ring and stand still. Behind each "
                     "one a halted army stands in long ranks along the horizon with spears, banners and a few war towers, hazy in pale gold "
                     "dust, with a clear gap of open horizon between the two armies in the middle. The huge low sun sits just above the "
                     "horizon behind the right chariot and long shadows fall toward the camera. The figures are tiny, about 5 percent of the "
                     "frame height: do NOT enlarge them, do NOT move the chariots closer together, do NOT add anything in the empty ring. "
                     "Wide open late-afternoon sky. No parasol and no canopy on either chariot."),
    "A03": dict(look=["refs/concept/concept_46.jpeg", "refs/concept/concept_37.jpeg"],
                frame="@karna on his chariot in a three-quarter view facing screen left, lifting the bow Vijaya level in both hands to touch "
                      "it to his forehead, the low sun directly behind his head like a halo.",
                note="Medium close-up from a slightly low angle, as in the layout: Karna fills the centre of the frame from the waist up. "
                     "Both arms are raised and hold the bow horizontally at brow height; the bow touches his forehead in a silent vow. "
                     "His face is clearly visible in three-quarter profile turned to screen left, calm and grave, eyes closed. He wears his "
                     "rounded gold crown and his full carved gold cuirass with the sun-face relief on the chest, a saffron-orange dhoti, "
                     "bare earlobes. He carries NO shield: ignore the round gold shape behind his shoulder in the layout and paint only his "
                     "armoured back and shoulder there. There is no arrow on the bow. The white disc of the low sun is directly behind his "
                     "crown and rims his head and arms with light. A carved bronze lion figure of his chariot sits at the right, the gold "
                     "banner pole rises at the far right edge. Far behind and below at the left the Kaurava host stands in ranks with spears "
                     "and round shields, soft in pale gold dust. No charioteer and no other person is in this frame."),
    "A04": dict(look=["refs/concept/concept_05.jpeg", "refs/concept/concept_06.jpeg"], cast=["@arjuna"],
                frame="@arjuna on his chariot facing screen right at full draw, the bow Gandiva upright in his left hand, one arrow nocked, "
                      "warm gold late-afternoon sky.",
                note="Medium close-up as in the layout, the mirror of Karna's shot: Arjuna fills the centre of the frame from the waist up, "
                     "seen from slightly behind his right shoulder, his face in clear profile to screen right, eyes fixed on his target. "
                     "His left arm is straight out and holds Gandiva upright at the right of the frame; the bow's black limbs wrapped in "
                     "spiral gold bands curve from the top edge of the frame to the bottom edge. His right hand has drawn the taut bowstring "
                     "back to his cheek, the string clearly visible; one steel-tipped arrow lies across the bow and points to screen right. "
                     "He wears his tall gold crown, the sleeveless carved gold cuirass with black enamel inlay, wide gold bracers and the "
                     "deep green silk sash at his waist over a white dhoti. A bright gold lion figure of his own chariot sits at the left, a "
                     "gold banner pole rises at the far left. Behind him the Pandava host stands in ranks in saffron and gold with tall "
                     "pennants and a war tower, soft in pale gold dust. Krishna is NOT in this frame and no other person is close. "
                     "No lightning, no sparks and no glow on the bow: that effect is added later. No shield."),
    "A05": dict(look=["refs/concept/concept_06.jpeg", "refs/concept/concept_42.jpeg"], cast=["@krishna", "@arjuna"],
                frame="Low angle close to the ground in front of the gold chariot: the four white horses fill the right half, @krishna at "
                      "the reins and @arjuna standing behind him are small on the chariot at the left.",
                note="Low wide view from near the ground, as in the layout. The four white horses, harnessed side by side with gold "
                     "collars, gold tassels and maroon saddle cloths, are large at the right with their heads high, caught at the instant "
                     "they begin to surge forward: muscles bunched, front hooves lifting, manes and tassels thrown back, red dust kicking up "
                     "at their hooves. Exactly four horses, all white. Behind them at the left is Arjuna's gold chariot with tall spoked "
                     "wheels and gold lion figures; a green banner with a gold ape flies from its pole. Krishna, blue-skinned, sits at the "
                     "front of the chariot holding black reins that have just snapped taut; Arjuna in his tall gold crown stands behind him "
                     "holding Gandiva. Both men are small in the frame, as in the layout. The Pandava host stands along the horizon in "
                     "pale dust, the ground is open trampled red-brown earth, the sky is clear late afternoon. "
                     "No parasol and no canopy on the chariot."),
}

def style():
    m = re.search(r"## Global style prompt.*?\n\n> (.+?)\n", (STUDIO / "bible.md").read_text(), re.S)
    return m.group(1).strip()

def build(sid, card):
    recipe = SHOTS[sid]
    cast = recipe.get("cast", [c for c in card["chars"] if c in SHEETS])
    refs = [f"{EP}/layout/{sid}.jpg"] + [f"{SHEETS[c]}/{SHEET_FILE[c]}" for c in cast] + recipe["look"]
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
    lines += ["", f"SHOT {sid}. Camera: {card['camera']}. {recipe.get('frame', card['frame'])}", recipe["note"], "",
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

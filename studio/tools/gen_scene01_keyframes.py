#!/usr/bin/env python3
"""Story scene 01 "Suryaputra" (Karna at dawn, the 17th day): the 9 key frames for image-to-video.

Plan: episodes/ep01_arjuna_vs_karna/story_scene_01_karna_dawn.md (sai, 2026-11-21: "yes").
References are only our own locked web series hero set (bible, "Series hero set: LOCKED") and sai's own concept paintings.
Every frame is 16:9 with the subject inside the centre 9:16 band, so the vertical cut works. No text in any frame
(subtitles are added in the edit).

BILLED: one image per job (gemini-3.1-flash-image, about $0.07 each, all 9 about $0.63). Needs sai's own go with the cost.
No automatic retries. Never overwrites a take. Every call is logged to studio/log.md.

  python studio/tools/gen_scene01_keyframes.py --project cs-project-07zg2j2c --only scene01 --dry-run
  python studio/tools/gen_scene01_keyframes.py --project cs-project-07zg2j2c --only scene01          # 9 images, about $0.63
  python studio/tools/gen_scene01_keyframes.py --project cs-project-07zg2j2c --only s01_04 --take 2   # one retake, about $0.07
Output: episodes/ep01_arjuna_vs_karna/keyframes/s01_<NN>_v<take>.png
"""
import argparse, base64, datetime, json, pathlib, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gen_sheets import MODEL, STUDIO, call, descriptor      # same API call, same model

STYLE = "cast/karna/web/close_v1.png"     # locked style frame and Karna's face
BODY = "cast/karna/web/full_v2.png"       # locked Karna full body (costume, build, bow Vijaya)
PLAIN = "refs/concept/concept_42.jpeg"    # sai's painting: the red plain, dust and sky of Kurukshetra
OUT = "episodes/ep01_arjuna_vs_karna/keyframes"

LOOK = ("Rendering: match IMAGE 1 exactly. It is the approved style frame of this series: stylized 3D animated-series character, "
        "smooth sculpted forms with clean painted shading, a long angular face with sharp cheekbones, a strong brow and jaw and a "
        "long straight nose. Backgrounds are painted matte plates with visible soft brushwork, not photographs. Light: the first "
        "light of dawn, a warm gold key (#FFC27A) from the low sun against cool blue shadow and fill (#3E5A86), shadows lean blue. "
        "Glow only on the sun and on light on water, never on skin or armour. Not a painting, not realistic, not a cartoon: a "
        "premium stylized 3D series. No text, no letters, no subtitles, no logos, no watermark, no border.")
FRAME = ("Framing: 16:9 frame, and the subject sits inside the centre third of the frame (a vertical 9:16 crop of the centre "
         "must hold the whole action). Cinematic shallow depth of field.")
FACE = ("Karna's face is the face of the man in IMAGE 1: same face, same thick upturned moustache, same brows, same age. "
        "Bare earlobes with NO earrings: each earlobe has a faint, pale, fully healed scar, bloodless. NO tilak or mark on the "
        "forehead, NO hair band, NOTHING on his back.")
BATHING = ("THIS SHOT OVERRIDES HIS COSTUME: he is at his dawn prayer in the river, so he has taken off his crown, cuirass, sash, "
           "bracers and sandals. He wears only the saffron-orange dhoti with black borders, wet and clinging. Bare broad chest, "
           "long black wavy hair wet and loose on his shoulders. His chest is smooth and unmarked.")
ARMED = ("He wears his full costume exactly as in IMAGE 2: rounded gold crown with the sun disc, carved gold cuirass with the "
         "sun-face, black and gold sash, saffron-orange dhoti, gold bracers.")
RIVER = ("Place: a wide, slow river on the edge of Kurukshetra, blue pre-dawn haze lying on the water, the far bank low and flat "
         "with the tiny orange fires of a sleeping war camp, the sky a painted wash from deep blue to pale gold at the east horizon.")

def karna(shot, refs, text, costume):
    return dict(out=f"{OUT}/s01_{shot}", refs=refs, passport="cast/karna/passport.md", costume=costume, text=text)

JOBS = {
    "s01_01": karna("01", [STYLE, BODY],
        f"Shot 1, extreme wide, locked camera. {RIVER} In the middle of the river, small in the frame and centred, ONE man stands "
        "waist-deep facing the east horizon (frame left), seen in profile, his hands joined. Mist drifts low over the water. "
        "Colossal sky, tiny figure for scale.", BATHING),
    "s01_02": karna("02", [STYLE, BODY],
        "Shot 2, close-up of his two large cupped hands, held up at chest height, full of river water, lifted toward the "
        "dawn horizon on frame left. A thin stream of water is just starting to spill from between his fingers and the first "
        "gold light catches it. His bare chest and the misty river soft and out of focus behind. Dark warm brown skin, long "
        "fingers, no rings.", BATHING),
    "s01_03": karna("03", [STYLE],
        "Shot 3, extreme close-up of Karna's eyes and brows only, the frame cut just above the brows and just below the eyes, "
        "the eyes in the centre of the frame. He looks straight ahead at the rising sun; a tiny gold rim of the sun is reflected "
        "in each dark iris. Calm, grave, wet lashes, drops of river water on the skin.", BATHING),
    "s01_04": karna("04", [STYLE, BODY],
        "Shot 4, close-up in clean profile, Karna facing frame left toward the sunrise, head and bare shoulders, his ear and "
        "bare earlobe clearly visible in the centre of the frame with its faint pale healed scar. Gold dawn light falls on the "
        "front of his face; the back of his head is still in cool blue shadow. Eyes half closed in prayer, lips closed. "
        "Painted blue river haze behind.", BATHING),
    "s01_05": karna("05", [STYLE, BODY],
        "Shot 5, medium shot from a low angle, waist up. Karna stands in the river in profile facing frame left; on frame left "
        "the upper rim of the sun disc is just breaking the painted horizon behind thin mist. In the near foreground on the "
        "right, out of focus, his gold cuirass rests on a dark river stone and the sun-face on its chest catches a bright gold "
        "glint. He is centred.", BATHING),
    "s01_06": karna("06", [STYLE, BODY],
        "Shot 6, close-up of the bow Vijaya resting across a flat dark river stone by the water, black limbs wrapped in spiral gold "
        "bands, gold winged ornaments above and below the grip, exactly as in IMAGE 2. Karna's large right hand has just come down "
        "and rests on the grip, the fingers about to close around it. Wet forearm, no bracer yet. Warm dawn light from the left, "
        "blue shadow, the river soft behind. Only the hand, the forearm and the bow in frame.", BATHING),
    "s01_07": karna("07", [STYLE, BODY],
        "Shot 7, medium wide, camera on the river bank looking out over the water toward the dawn. In the background, on the "
        "bank at frame right, a gold war chariot and a team of four DUN horses (sandy brown, not white) stand as dark backlit "
        "silhouettes; beside the chariot stands a second man, the charioteer, ONLY as a flat dark silhouette with no visible face "
        "or costume detail. In the centre, Karna wades up out of the river toward the camera, knee-deep, water streaming off "
        "him, head high, the low sun behind him giving him a gold rim light.", BATHING),
    "s01_08": karna("08", [STYLE, BODY],
        "Shot 8, close-up, head and shoulders, three-quarter view, Karna facing frame left. The low sun lights exactly half his "
        "face warm gold; the other half falls into deep cool blue shadow. A small, quiet smile at one corner of his mouth, eyes "
        "steady. Behind him, soft and out of focus, the bank, the chariot and a painted dawn sky.", ARMED),
    "s01_09": dict(out=f"{OUT}/s01_09", refs=[STYLE, PLAIN], passport=None, costume=None,
        text="Shot 9, extreme wide, locked camera. IMAGE 2 is sai's painting of this plain: take its red trampled earth, its "
             "flat horizon and its painted dust and sky ONLY; do not copy its chariot, its white horses, its people or its green "
             "banner. Here: at sunrise, small in the centre of the frame and seen from behind, ONE gold war chariot drawn by four "
             "DUN horses (sandy brown, not white) rolls away from the camera across the plain toward a far wall of pale gold dust "
             "where two armies wait. A tall pole on the chariot carries Karna's standard: a gold banner with the emblem of an "
             "elephant's rope (a coiled rope), small and clear against the sky. The sun disc stands just above the horizon on frame "
             "left; long blue shadows stretch to frame right, dust lifts from the wheels. Colossal sky, tiny chariot for scale. "
             "The figures on the chariot are tiny dark silhouettes."),
}
GROUPS = {"scene01": list(JOBS)}

# ---- take 2 for shots 8 and 9 (review of v1, 2026-11-21): in 8 the crown drifted from the style frame and the chariot behind
# had a canopy and a pale horse; in 9 the horses ran beside the chariot instead of in front of it and the banner was plain.
# Run with --only retake2 --take 2 (2 images, about $0.14).
CHARIOT = ("The chariot has NO canopy, NO parasol and NO roof: an open gold war car with two big wheels and a tall standard pole. "
           "All four horses are DUN (sandy brown with dark manes), never white or grey.")
JOBS["s01_08_t2"] = karna("08", [STYLE, BODY],
    "Shot 8, close-up, head and shoulders, three-quarter view, Karna facing frame left. His crown is EXACTLY the crown of "
    "IMAGE 1: same shape, same gold, same crest, nothing added behind his head (no halo, no ring, no disc behind it). The low "
    "sun lights exactly half his face warm gold; the other half falls into deep cool blue shadow. A small, quiet smile at one "
    "corner of his mouth, eyes steady. Behind him, soft and out of focus, the river bank, his chariot and a painted dawn sky. "
    + CHARIOT, ARMED)
JOBS["s01_09_t2"] = dict(out=f"{OUT}/s01_09", refs=[STYLE, PLAIN], passport=None, costume=None,
    text=JOBS["s01_09"]["text"].replace(
        "ONE gold war chariot drawn by four DUN horses (sandy brown, not white) rolls away",
        "ONE gold war chariot rolls away") +
        " The four horses run side by side IN FRONT of the chariot, harnessed to its pole and yoke, farther from the camera than "
        "the chariot, pulling it away; no horse is beside or behind the wheels. The banner shows a clear dark coiled rope on "
        "gold. " + CHARIOT)
GROUPS["retake2"] = ["s01_08_t2", "s01_09_t2"]

def prompt_for(j):
    if j["passport"] is None:
        return f"{j['text']}\n\n{FRAME}\n\n{LOOK}"
    ref2 = ("IMAGE 2 is the approved full body of this same man, Karna: same build, same costume, same bow." if len(j["refs"]) > 1 else "")
    return (f"{j['text']}\n\n{FRAME}\n\n{LOOK}\n\n{FACE} {ref2}\n\nCharacter: {descriptor(j['passport'])}\n\n{j['costume']}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True); ap.add_argument("--location", default="global")
    ap.add_argument("--only", required=True, help="scene01, or job names separated by commas (s01_01 ... s01_09)")
    ap.add_argument("--take", type=int, default=1); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    jobs = [j for part in a.only.split(",") for j in GROUPS.get(part, [part])]
    unknown = [n for n in jobs if n not in JOBS]
    if unknown:
        print("unknown job", unknown, "| jobs:", list(JOBS), "| groups:", list(GROUPS)); sys.exit(1)
    for i, name in enumerate(jobs):
        j = JOBS[name]
        rel = f"{j['out']}_v{a.take}.png"
        out = STUDIO / rel
        if out.exists():
            print("exists, not overwriting (folder law 1):", rel); continue
        prompt = prompt_for(j)
        missing = [r for r in j["refs"] if not (STUDIO / r).exists()]
        if a.dry_run:
            print("---", name, "->", rel, "\nrefs:", j["refs"], "missing:" if missing else "", missing or "", "\n" + prompt, "\n"); continue
        if missing:
            print("missing reference:", missing); sys.exit(1)
        if i:
            time.sleep(25)        # pacing only, against the 429 rate limit. This is not a retry.
        res = call(a.project, a.location, prompt, j["refs"], "16:9")
        imgs = [p for c in res.get("candidates", []) for p in c.get("content", {}).get("parts", []) if "inlineData" in p]
        if not imgs:
            print("no image returned for", name, json.dumps(res)[:1500]); sys.exit(1)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(imgs[0]["inlineData"]["data"]))
        u = res.get("usageMetadata", {})
        with open(STUDIO / "log.md", "a") as f:
            f.write(f"| {datetime.date.today()} | {rel} | {MODEL} | scene 01 key frame {name}, {len(j['refs'])} refs | tokens in {u.get('promptTokenCount')} out {u.get('candidatesTokenCount')} | pending review |\n")
        print("wrote", rel, "usage", u)

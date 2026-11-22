#!/usr/bin/env python3
"""Talking close-up tests for Arjuna and Krishna (sai, 2026-11-22: "do similar for arjuna and krishna").

Same recipe as gen_talk_test.py (Karna): Veo 3.1 Fast on Vertex, image to video, 720p, 8 s, with generated audio so the
lips follow the line. First frame: each hero's locked series close-up (bible, "Series hero set: LOCKED").
Price: $0.10 per second with audio, so 8 s is about $0.80 per hero. The generated voice is a placeholder.

BILLED. One clip per hero per run. No automatic retries: `--resume` fetches the same clip without paying again.
Never overwrites a take. Logged to studio/log.md.

  python studio/tools/gen_talk_test_heroes.py --project cs-project-07zg2j2c --only arjuna,krishna --dry-run
  python studio/tools/gen_talk_test_heroes.py --project cs-project-07zg2j2c --only arjuna,krishna    # 2 clips, about $1.60
"""
import argparse, base64, datetime, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gen_video import STUDIO, post, wait        # same Vertex call and polling as the earlier Veo tests

MODEL, RES, SECONDS, RATE = "veo-3.1-fast-generate-001", "720p", 8, 0.10
OUT = "episodes/ep01_arjuna_vs_karna/renders/talk_test_{hero}"
LOCK = ("Story close-up from a stylized 3D animated series. Locked-off camera on a tripod: no pan, no zoom, no dolly, no cut, "
        "no reframing; the framing of the first frame is held exactly for the whole clip. The same man, the same face, crown, "
        "armour, costume and light in every frame; nothing is added to the costume. Only small natural movements of the head, "
        "no gestures, hands still.")
HEROES = {
    "arjuna": dict(
        frame="cast/arjuna/web/close_v4.png",
        beats=("0-2s: Arjuna is still, eyes looking just past the camera toward the enemy line; he blinks once and his jaw "
               "sets. 2-6s: he speaks one line in a clear, firm, younger male voice with an Indian accent, his lips moving "
               "clearly with every word: \"Whatever comes, I will not lower my bow.\" 6-8s: he falls silent, breathes out "
               "slowly, and his eyes narrow with resolve."),
        negative="earrings added, gold armour (his armour is silver-steel), white dhoti"),
    "krishna": dict(
        frame="cast/krishna/web/close_v2.png",
        beats=("0-2s: Krishna is still and serene, eyes looking just past the camera; a faint calm smile. 2-6s: he speaks one "
               "line in a warm, gentle, unhurried male voice with an Indian accent, his lips moving clearly with every word: "
               "\"Rise, Partha. Do what is right, and leave the rest to me.\" 6-8s: he falls silent and gives a small, kind "
               "nod; the smile stays."),
        negative="skin colour changing from blue, missing peacock feather"),
}
BASE_NEG = ("text, captions, subtitles, watermark, logo, extra people, morphing face, changing crown or armour, added shoulder "
            "guards, shouting, music, camera movement, zoom, cuts, blood")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True); ap.add_argument("--only", required=True, help="arjuna,krishna")
    ap.add_argument("--take", type=int, default=1); ap.add_argument("--wait-minutes", type=int, default=12)
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    for hero in a.only.split(","):
        h = HEROES[hero]
        frame, rel = STUDIO / h["frame"], f"{OUT.format(hero=hero)}_v{a.take}.mp4"
        out, opfile = STUDIO / rel, STUDIO / (rel + ".operation.txt")
        prompt = f"{LOCK} {h['beats']} Sound: only his voice and a soft wind; no music."
        negative = f"{BASE_NEG}, {h['negative']}"
        cost = SECONDS * RATE
        if out.exists():
            print("exists, not overwriting (folder law 1):", rel); continue
        if a.dry_run:
            print(f"--- {rel}\nmodel {MODEL} | {SECONDS}s | {RES} | with audio | about ${cost:.2f}\nfirst frame: {h['frame']}\n{prompt}\nnegative: {negative}\n")
            continue
        body = {"instances": [{"prompt": prompt, "image": {"bytesBase64Encoded": base64.b64encode(frame.read_bytes()).decode(), "mimeType": "image/png"}}],
                "parameters": {"aspectRatio": "16:9", "durationSeconds": SECONDS, "resolution": RES, "sampleCount": 1,
                               "generateAudio": True, "negativePrompt": negative, "personGeneration": "allow_adult"}}
        if a.resume:
            if not opfile.exists():
                print("nothing to resume for", hero); continue
            op = opfile.read_text().strip()
        else:
            if opfile.exists():
                print("an operation was already started for", hero, "; use --resume"); continue
            op = post(a.project, MODEL, "predictLongRunning", body)["name"]
            out.parent.mkdir(parents=True, exist_ok=True)
            opfile.write_text(op)
            print("started", hero, op)
        r = wait(a.project, MODEL, op, a.wait_minutes)
        if r is None:
            print("still running; run again with --resume (no new charge):", opfile.name); continue
        if "error" in r:
            print("operation failed:", hero, str(r["error"])[:1500]); continue
        vids = r.get("response", {}).get("videos", [])
        if not vids or "bytesBase64Encoded" not in vids[0]:
            print("no video returned:", hero, str(r.get("response", {}))[:1500]); continue
        out.write_bytes(base64.b64decode(vids[0]["bytesBase64Encoded"]))
        opfile.unlink()
        with open(STUDIO / "log.md", "a") as f:
            f.write(f"| {datetime.date.today()} | {rel} | {MODEL} | talking test {hero}, {SECONDS}s {RES} with audio, first frame {h['frame']} | about ${cost:.2f} at ${RATE:.2f}/s | pending review |\n")
        print("wrote", rel, f"about ${cost:.2f}")

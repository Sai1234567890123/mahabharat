#!/usr/bin/env python3
"""Talking close-up test (sai, 2026-11-22, "Both"): can a locked hero close-up speak a line with lip-sync and expressions?

First frame: the locked series close-up of Karna, cast/karna/web/close_v1.png (bible, "Series hero set: LOCKED").
Model: Veo 3.1 Fast on Vertex, image to video, 720p, 8 s, WITH generated audio so the lips follow the spoken line.
Price (Vertex pricing page, read 2026-11-22): Veo 3.1 Fast video + audio 720p $0.10 per second, so 8 s is about $0.80.
The generated voice is a placeholder: the real voice is recorded and the edit re-times it.

BILLED. One clip per run. Needs sai's own go with the cost. No automatic retries: if the wait times out, `--resume` fetches
the same clip without paying again. Never overwrites a take. Logged to studio/log.md.

  python studio/tools/gen_talk_test.py --project cs-project-07zg2j2c --dry-run
  python studio/tools/gen_talk_test.py --project cs-project-07zg2j2c            # 1 clip, 8 s, about $0.80
  python studio/tools/gen_talk_test.py --project cs-project-07zg2j2c --resume
  python studio/tools/gen_talk_test.py --project cs-project-07zg2j2c --hero arjuna,krishna   # 2 clips, about $1.60

Karna's take 1 showed three faults (camera drift, shoulder guards that are not in the close-up, a small face), so the
Arjuna and Krishna prompts push in to head and shoulders in the first 1.5 s, then lock the camera, and forbid new armour.
"""
import argparse, base64, datetime, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gen_video import STUDIO, post, wait        # same Vertex call and polling as the earlier Veo tests

MODEL, RES, SECONDS, RATE = "veo-3.1-fast-generate-001", "720p", 8, 0.10
HEROES = {}
FRAME = "cast/karna/web/close_v1.png"
OUT = "episodes/ep01_arjuna_vs_karna/renders/talk_test_karna"
PROMPT = (
    "Story close-up from a stylized 3D animated series. Locked-off camera, no pan, no zoom, no cut: the framing of the first "
    "frame is held for the whole clip. The same man, the same face, crown, armour and light in every frame. "
    "0-2s: Karna is still, eyes looking just past the camera; he blinks once and draws a slow breath, his brows lower a "
    "little in quiet sorrow. 2-6s: he speaks one line in a deep, calm, low male voice with an Indian accent, his lips "
    "moving clearly with every word: \"Today I keep only my word.\" 6-8s: he falls silent, his eyes lift and steady, and "
    "a small proud smile appears at one corner of his mouth. Only small natural movements of the head, no gestures, hands "
    "out of frame. Sound: only his voice and a soft wind; no music.")
HEROES["karna"] = (FRAME, OUT, PROMPT)

PUSH = ("Story close-up from a stylized 3D animated series. 0-1.5s: the camera pushes in slowly and smoothly from the first "
        "frame to a head-and-shoulders close-up of his face, then it is LOCKED for the rest of the clip: no drift, no pan, no "
        "re-framing, no cut. The same man, the same face, crown, costume, colours and light in every frame; no armour pieces, "
        "jewellery or objects appear that are not in the first frame. ")
HEROES["arjuna"] = ("cast/arjuna/web/close_v4.png", "episodes/ep01_arjuna_vs_karna/renders/talk_test_arjuna", PUSH +
    "1.5-3s: Arjuna's eyes narrow and his jaw sets, focused and alert, he breathes in once. 3-6s: he speaks one line in a "
    "clear, firm, controlled male voice with an Indian accent, his lips moving clearly with every word: \"Karna, today this "
    "ends.\" 6-8s: he falls silent, a flicker of doubt crosses his face, his brows draw together, then his gaze hardens again. "
    "Only small natural head movements, hands out of frame. Sound: only his voice and a soft wind; no music.")
HEROES["krishna"] = ("cast/krishna/web/close_v2.png", "episodes/ep01_arjuna_vs_karna/renders/talk_test_krishna", PUSH +
    "His skin stays blue in every frame. 1.5-2.5s: Krishna looks steadily just past the camera with a faint, calm smile, "
    "and blinks once. 2.5-7s: he speaks one line in a soft, deep, unhurried male voice with an Indian accent, his lips "
    "moving clearly with every word: \"Where was your dharma, Karna, when Draupadi was dragged into the hall?\" 7-8s: he "
    "falls silent, the smile gone, his eyes grave and still. Only small natural head movements, hands out of frame. "
    "Sound: only his voice and a soft wind; no music.")

NEGATIVE = ("text, captions, subtitles, watermark, logo, extra people, morphing face, changing crown or armour, earrings, "
            "tilak, shouting, music, camera movement, cuts, blood")
NEG_PUSH = ("text, captions, subtitles, watermark, logo, extra people, morphing face, changing crown or armour, new shoulder "
            "guards, new jewellery, shouting, music, camera drift, camera shake, cuts, blood")
NEG = {"karna": NEGATIVE, "arjuna": NEG_PUSH, "krishna": NEG_PUSH}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True); ap.add_argument("--take", type=int, default=1)
    ap.add_argument("--wait-minutes", type=int, default=12); ap.add_argument("--hero", default="karna")
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    for hero in a.hero.split(","):
        frame_rel, out_rel, prompt = HEROES[hero]
        frame, rel = STUDIO / frame_rel, f"{out_rel}_v{a.take}.mp4"
        out, opfile = STUDIO / rel, STUDIO / (rel + ".operation.txt")
        cost = SECONDS * RATE
        if out.exists():
            print("exists, not overwriting (folder law 1):", rel); sys.exit(1)
        body = {"instances": [{"prompt": prompt, "image": {"bytesBase64Encoded": base64.b64encode(frame.read_bytes()).decode(), "mimeType": "image/png"}}],
                "parameters": {"aspectRatio": "16:9", "durationSeconds": SECONDS, "resolution": RES, "sampleCount": 1,
                               "generateAudio": True, "negativePrompt": NEG[hero], "personGeneration": "allow_adult"}}
        if a.dry_run:
            print(f"--- {rel}\nmodel {MODEL} | {SECONDS}s | {RES} | with audio | about ${cost:.2f}\nfirst frame: {frame_rel}\n{prompt}\nnegative: {NEG[hero]}")
            continue
        if a.resume:
            if not opfile.exists():
                print("nothing to resume"); sys.exit(1)
            op = opfile.read_text().strip()
        else:
            if opfile.exists():
                print("an operation was already started for this take; use --resume:", opfile.name); sys.exit(1)
            op = post(a.project, MODEL, "predictLongRunning", body)["name"]
            out.parent.mkdir(parents=True, exist_ok=True)
            opfile.write_text(op)
            print("started", op)
        r = wait(a.project, MODEL, op, a.wait_minutes)
        if r is None:
            print("still running; run again with --resume (no new charge):", opfile.name); sys.exit(2)
        if "error" in r:
            print("operation failed:", str(r["error"])[:1500]); sys.exit(1)
        vids = r.get("response", {}).get("videos", [])
        if not vids or "bytesBase64Encoded" not in vids[0]:
            print("no video returned:", str(r.get("response", {}))[:1500]); sys.exit(1)
        out.write_bytes(base64.b64decode(vids[0]["bytesBase64Encoded"]))
        opfile.unlink()
        with open(STUDIO / "log.md", "a") as f:
            f.write(f"| {datetime.date.today()} | {rel} | {MODEL} | talking test {hero}, {SECONDS}s {RES} with audio, first frame {frame_rel} | about ${cost:.2f} at ${RATE:.2f}/s | pending review |\n")
        print("wrote", rel, f"about ${cost:.2f}")

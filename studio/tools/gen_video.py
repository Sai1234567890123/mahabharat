#!/usr/bin/env python3
"""Step 5 of the trailer plan: turn an approved frame into a video take with Veo 3.1 on Vertex AI (image to video).

  draft: veo-3.1-fast-generate-001, 720p, no sound      (cheap look at the motion)
  hero : veo-3.1-generate-001, 1080p, no sound          (only after the draft is approved)

The first frame is episodes/ep01_arjuna_vs_karna/frames/<shot>_v<frame-take>.png. The prompt is the shot card's camera
and motion beats. Sound is added in the edit, so generateAudio is off.

BILLED per second of video. One video per run per shot. Needs sai's own go with the cost. No automatic retries:
if the wait times out, the operation name is saved next to the output and `--resume` fetches the same video without
starting (or paying for) a new one. Never overwrites a take. Every call is logged to studio/log.md.

  python studio/tools/gen_video.py --project cs-project-07zg2j2c --only A06 --frame-take 2 --dry-run
  python studio/tools/gen_video.py --project cs-project-07zg2j2c --only A06 --frame-take 2
  python studio/tools/gen_video.py --project cs-project-07zg2j2c --only A06 --frame-take 2 --resume
"""
import argparse, base64, datetime, json, pathlib, shutil, subprocess, sys, time, urllib.error, urllib.request

STUDIO = pathlib.Path(__file__).resolve().parent.parent
EP = "episodes/ep01_arjuna_vs_karna"
LOCATION = "us-central1"                       # the only region listed for Veo 3.1
TIERS = {   # model, resolution, USD per second without sound (Vertex pricing page, read 2026-11-15)
    "draft": ("veo-3.1-fast-generate-001", "720p", 0.08),
    "hero": ("veo-3.1-generate-001", "1080p", 0.20),
}
NEGATIVE = ("text, captions, subtitles, watermark, logo, extra people, extra limbs, morphing faces, changing costume, earrings, "
            "parasol, modern objects, cartoon, cel shading, 3D render look, blood, gore")
STYLE = ("Keep the look of the first frame for the whole clip: classical oil painting, visible brushwork, warm low sun, pale gold dust. "
         "The same man, the same face and the same costume in every frame. Physically weighted movement, cloth and dust react to motion.")

def token():
    gcloud = shutil.which("gcloud") or shutil.which("gcloud.cmd") or "gcloud"
    return subprocess.run([gcloud, "auth", "application-default", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()

def post(project, model, method, body):
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{project}/locations/{LOCATION}/publishers/google/models/{model}:{method}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json", "x-goog-user-project": project})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=300).read())
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode(errors="replace")[:2000]); raise SystemExit(1)

def prompt_for(card):
    beats = " ".join(card["motion"])
    return f"{card['action']} Camera: {card['camera']}. Timing: {beats} {STYLE}"

def wait(project, model, op, minutes):
    end = time.time() + minutes * 60
    while time.time() < end:
        r = post(project, model, "fetchPredictOperation", {"operationName": op})
        if r.get("done"):
            return r
        time.sleep(15)
    return None

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True); ap.add_argument("--only", required=True)
    ap.add_argument("--frame-take", type=int, required=True, help="which approved frame take is the first frame")
    ap.add_argument("--tier", choices=list(TIERS), default="draft"); ap.add_argument("--seconds", type=int, choices=[4, 6, 8], default=6)
    ap.add_argument("--take", type=int, default=1); ap.add_argument("--wait-minutes", type=int, default=12)
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    model, res, rate = TIERS[a.tier]
    cards = {s["id"]: s for s in json.loads((STUDIO / EP / "shots.json").read_text())["shots"]}
    for sid in a.only.split(","):
        frame = STUDIO / EP / "frames" / f"{sid}_v{a.frame_take}.png"
        if not frame.exists():
            print("missing frame", frame); sys.exit(1)
        rel = f"{EP}/renders/{sid}_{a.tier}_v{a.take}.mp4"
        out, opfile = STUDIO / rel, STUDIO / (rel + ".operation.txt")
        if out.exists():
            print("exists, not overwriting (folder law 1):", rel); sys.exit(1)
        prompt, cost = prompt_for(cards[sid]), a.seconds * rate
        body = {"instances": [{"prompt": prompt, "image": {"bytesBase64Encoded": base64.b64encode(frame.read_bytes()).decode(), "mimeType": "image/png"}}],
                "parameters": {"aspectRatio": "16:9", "durationSeconds": a.seconds, "resolution": res, "sampleCount": 1,
                               "generateAudio": False, "negativePrompt": NEGATIVE, "personGeneration": "allow_adult"}}
        if a.dry_run:
            print(f"--- {sid} -> {rel}\nmodel {model} | {a.seconds}s | {res} | no sound | estimated ${cost:.2f}\nfirst frame: {frame.relative_to(STUDIO)}\n{prompt}\nnegative: {NEGATIVE}\n")
            continue
        if a.resume:
            if not opfile.exists():
                print("nothing to resume for", sid); sys.exit(1)
            op = opfile.read_text().strip()
        else:
            if opfile.exists():
                print("an operation was already started for this take; use --resume, do not start a second one:", opfile.name); sys.exit(1)
            op = post(a.project, model, "predictLongRunning", body)["name"]
            out.parent.mkdir(parents=True, exist_ok=True)
            opfile.write_text(op)
            print("started", op)
        r = wait(a.project, model, op, a.wait_minutes)
        if r is None:
            print("still running after the wait; run again with --resume (no new charge):", opfile.name); sys.exit(2)
        if "error" in r:
            print("operation failed:", json.dumps(r["error"])[:1500]); sys.exit(1)
        resp = r.get("response", {})
        vids = resp.get("videos", [])
        if not vids or "bytesBase64Encoded" not in vids[0]:
            print("no video returned:", json.dumps({k: v for k, v in resp.items() if k != "videos"})[:1500]); sys.exit(1)
        out.write_bytes(base64.b64decode(vids[0]["bytesBase64Encoded"]))
        opfile.unlink()
        with open(STUDIO / "log.md", "a") as f:
            f.write(f"| {datetime.date.today()} | {rel} | {model} | {a.tier}, {a.seconds}s {res} no sound, first frame {frame.name} | about ${cost:.2f} at ${rate:.2f}/s | pending review |\n")
        print("wrote", rel, f"about ${cost:.2f}")

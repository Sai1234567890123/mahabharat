"""Image-to-video for the picked keyframes with Veo on Vertex AI.

Takes each picked keyframe in art/selected/ (PICKS below), sends it with the
motion_prompt from data/shots.json, and saves art/motion/SHxxx.mp4. Results
and errors are logged to art/motion/log.json.

Run it on a machine that is logged in to Google Cloud
(`gcloud auth application-default login`). Start with --dry-run, which calls
nothing and prints the plan. Then test one shot before the full run:

  python scripts/animate.py --dry-run
  python scripts/animate.py --shot SH050
  python scripts/animate.py

Settings come from the environment, with these defaults:
  GOOGLE_CLOUD_PROJECT=aiautomationplatform
  GOOGLE_CLOUD_LOCATION=us-central1   (Veo is served from a regional endpoint)
  VIDEO_MODEL=veo-3.0-generate-001   (the Veo 3 model enabled in this project; the fast variant returned 404)

Veo bills per generated second, so check the Vertex AI pricing page before a
full run. Clip lengths are snapped to 4, 6 or 8 seconds.
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))

PICKS = {
    "SH010": "SH010_v07.png",
    "SH020": "SH020_v01.png",
    "SH030": "SH030_v04.png",
    "SH040": "SH040_v01.png",
    "SH050": "SH050_v04.png",
    "SH060": "SH060_v01.png",
    "SH070": "SH070_v08.png",
    "SH080": "SH080_v01.png",
    "SH090": "SH090_v06.png",
    "SH100": "SH100_v02.png",
    "SH110": "SH110_v01.png",
    "SH120": "SH120_v02.png",
    "SH130": "SH130_v09.png",
    "SH140": "SH140_v05.png",
    "SH150": "SH150_v23.png",
    "SH160": "SH160_v36.png",
    "SH170": "SH170_v09.png",
    "SH180": "SH180_v04.png",
}
CLIP_LENGTHS = (4, 6, 8)
STYLE = ("Painterly stylized 3D animation, hand-painted textures with visible brushwork, "
         "soft light and haze, no outlines. Keep the composition and camera of the still image.")
POLL_SECONDS = 15
MAX_WAIT_SECONDS = 900


def clip_length(seconds):
    return min(CLIP_LENGTHS, key=lambda c: abs(c - seconds))


def build_prompt(shot):
    motion = shot.get("motion_prompt") or shot.get("keyframe_prompt", "")
    return f"{motion}. {STYLE}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", action="append", help="shot id, repeatable (default: all picks)")
    ap.add_argument("--model", default=os.environ.get("VIDEO_MODEL", "veo-3.0-generate-001"))
    ap.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT", "aiautomationplatform"))
    ap.add_argument("--location", default=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"))
    ap.add_argument("--dry-run", action="store_true", help="print the plan, call nothing")
    a = ap.parse_args()

    data = json.load(open(os.path.join(ROOT, "data", "shots.json"), encoding="utf-8"))
    shots = {s["id"]: s for s in data["shots"]}
    ids = a.shot or list(PICKS)

    jobs = []
    for sid in ids:
        if sid not in PICKS or sid not in shots:
            print(f"{sid}: not a picked shot, skipped")
            continue
        still = os.path.join(ROOT, "art", "selected", PICKS[sid])
        if not os.path.exists(still):
            print(f"{sid}: no keyframe at {still}, skipped")
            continue
        seconds = clip_length(shots[sid].get("duration", 6))
        jobs.append((sid, still, build_prompt(shots[sid]), seconds))

    if a.dry_run:
        for sid, still, prompt, seconds in jobs:
            print(f"--- {sid}: {PICKS[sid]} -> {seconds}s\n{prompt}\n")
        print(f"{len(jobs)} clips, {sum(j[3] for j in jobs)} generated seconds in total")
        return

    out = os.path.join(ROOT, "art", "motion")
    os.makedirs(out, exist_ok=True)
    log_path = os.path.join(out, "log.json")
    log = json.load(open(log_path, encoding="utf-8")) if os.path.exists(log_path) else {}

    from google import genai
    from google.genai import types
    client = genai.Client(vertexai=True, project=a.project, location=a.location)
    print(f"Vertex AI project={a.project} location={a.location} model={a.model}")

    for sid, still, prompt, seconds in jobs:
        dest = os.path.join(out, f"{sid}.mp4")
        entry = {"still": PICKS[sid], "model": a.model, "seconds": seconds}
        try:
            with open(still, "rb") as f:
                image = types.Image(image_bytes=f.read(), mime_type="image/png")
            op = client.models.generate_videos(
                model=a.model,
                source=types.GenerateVideosSource(prompt=prompt, image=image),
                config=types.GenerateVideosConfig(aspect_ratio="16:9", duration_seconds=seconds,
                                                  number_of_videos=1))
            waited = 0
            while not op.done:
                if waited >= MAX_WAIT_SECONDS:
                    raise RuntimeError("timed out waiting for the video")
                time.sleep(POLL_SECONDS)
                waited += POLL_SECONDS
                op = client.operations.get(op)
            if op.error:
                raise RuntimeError(str(op.error)[:300])
            videos = (op.response.generated_videos or []) if op.response else []
            if not videos:
                raise RuntimeError("no video returned (possibly filtered by safety settings)")
            video = videos[0].video
            if video.video_bytes:
                with open(dest, "wb") as f:
                    f.write(video.video_bytes)
                entry["file"] = os.path.basename(dest)
                print(f"{sid}: wrote {os.path.basename(dest)} ({seconds}s)")
            else:
                entry["uri"] = video.uri
                print(f"{sid}: video stored at {video.uri}, not downloaded")
        except Exception as e:
            entry["error"] = str(e)[:300]
            print(f"{sid}: failed: {entry['error']}")
        log[sid] = entry
        json.dump(log, open(log_path, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()

"""Veo 3.1 video generation for all 18 pilot shots from VIDEO_PROMPTS.md.

Outputs:
  art/motion/SHxxx_takeN.mp4
  art/motion/log.json
"""
import argparse
import json
import os
import re
import sys
import time
from google import genai
from google.genai import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
HANDOFF = os.path.join(ROOT, "video_handoff")
PROMPTS_FILE = os.path.join(HANDOFF, "VIDEO_PROMPTS.md")
KEYFRAMES_DIR = os.path.join(HANDOFF, "keyframes")
OUT_DIR = os.path.join(ROOT, "art", "motion")
LOG_PATH = os.path.join(OUT_DIR, "log.json")

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "aiautomationplatform")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
HERO_MODEL = "veo-3.1-generate-001"
FAST_MODEL = "veo-3.1-fast-generate-001"

POLL_INTERVAL = 15
MAX_WAIT_SECONDS = 900


def parse_prompts():
    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    sections = re.split(r"\n##\s+(SH\d{3})\b", text)
    shots = {}
    for i in range(1, len(sections), 2):
        sid = sections[i]
        body = sections[i + 1]
        lines = [line.strip() for line in body.strip().split("\n") if line.strip()]
        title = lines[0] if lines else sid
        is_hero = "(hero)" in title.lower()

        # Extract start image
        img_match = re.search(r"Start image:\s*`([^`]+)`", body)
        img_name = f"{sid}.png"
        if img_match:
            img_name = os.path.basename(img_match.group(1))

        # Extract duration
        len_match = re.search(r"Length:\s*(\d+)\s*s", body)
        length = int(len_match.group(1)) if len_match else 4

        # Extract prompt
        prompt_match = re.search(r"Prompt:\s*```(?:\w+)?\s*\n(.*?)\n```", body, re.DOTALL)
        prompt = prompt_match.group(1).strip() if prompt_match else ""

        # Extract negative prompt
        neg_match = re.search(r"Negative prompt:\s*```(?:\w+)?\s*\n(.*?)\n```", body, re.DOTALL)
        neg_prompt = neg_match.group(1).strip() if neg_match else ""

        keyframe_path = os.path.join(KEYFRAMES_DIR, img_name)
        if not os.path.exists(keyframe_path):
            alt = os.path.join(ROOT, "art", "selected", f"{sid}.png")
            if os.path.exists(alt):
                keyframe_path = alt

        shots[sid] = {
            "id": sid,
            "title": title.replace("(hero)", "").strip(),
            "hero": is_hero,
            "length": length,
            "keyframe_path": keyframe_path,
            "prompt": prompt,
            "negative_prompt": neg_prompt,
            "model": HERO_MODEL if is_hero else FAST_MODEL,
        }
    return shots


def generate_shot(client, shot_info, take, max_retries=3):
    sid = shot_info["id"]
    dest = os.path.join(OUT_DIR, f"{sid}_take{take}.mp4")
    if os.path.exists(dest) and os.path.getsize(dest) > 100000:
        print(f"[{sid}] Take {take} already exists ({os.path.getsize(dest)} bytes), skipping.")
        return dest

    kf_path = shot_info["keyframe_path"]
    if not os.path.exists(kf_path):
        raise FileNotFoundError(f"Keyframe not found: {kf_path}")

    with open(kf_path, "rb") as f:
        img_bytes = f.read()
    image = types.Image(image_bytes=img_bytes, mime_type="image/png")

    config = types.GenerateVideosConfig(
        aspect_ratio="16:9",
        duration_seconds=shot_info["length"],
        negative_prompt=shot_info["negative_prompt"],
        number_of_videos=1,
    )

    model = shot_info["model"]
    print(f"\n[{sid}] Generating take {take} with {model} ({shot_info['length']}s)...")
    print(f"[{sid}] Prompt snippet: {shot_info['prompt'][:100]}...")

    for attempt in range(1, max_retries + 1):
        try:
            op = client.models.generate_videos(
                model=model,
                source=types.GenerateVideosSource(prompt=shot_info["prompt"], image=image),
                config=config,
            )
            print(f"[{sid}] Job launched: {op.name}")
            start_time = time.time()
            while not op.done:
                elapsed = int(time.time() - start_time)
                if elapsed >= MAX_WAIT_SECONDS:
                    raise TimeoutError(f"Operation timed out after {MAX_WAIT_SECONDS}s")
                print(f"[{sid}] Waiting... ({elapsed}s elapsed)")
                time.sleep(POLL_INTERVAL)
                op = client.operations.get(operation=op)

            if op.error:
                raise RuntimeError(f"Operation error: {op.error}")

            videos = (op.response.generated_videos or []) if op.response else []
            if not videos:
                raise RuntimeError("No videos returned from Veo")

            v = videos[0].video
            if v.video_bytes:
                with open(dest, "wb") as f:
                    f.write(v.video_bytes)
                print(f"[{sid}] Saved: {dest} ({os.path.getsize(dest)} bytes)")
                return dest
            elif v.uri:
                print(f"[{sid}] Video stored in Cloud Storage: {v.uri}")
                return v.uri
            else:
                raise RuntimeError("Empty video payload returned")

        except Exception as e:
            err_str = str(e)
            print(f"[{sid}] Attempt {attempt} failed: {err_str[:200]}")
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                sleep_sec = 30 * attempt
                print(f"[{sid}] Rate limit hit, sleeping {sleep_sec}s before retry...")
                time.sleep(sleep_sec)
            elif attempt < max_retries:
                time.sleep(15)
            else:
                raise


def main():
    parser = argparse.ArgumentParser(description="Generate pilot video clips using Veo 3.1")
    parser.add_argument("--shot", action="append", help="Shot ID to generate (e.g. SH010). Can repeat.")
    parser.add_argument("--take", type=int, default=1, help="Take number to generate (default: 1)")
    parser.add_argument("--all-takes", action="store_true", help="Generate both take 1 and take 2")
    parser.add_argument("--dry-run", action="store_true", help="Print plan and exit")
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    shots = parse_prompts()
    print(f"Loaded {len(shots)} shots from {PROMPTS_FILE}")

    targets = args.shot or list(shots.keys())
    takes = [1, 2] if args.all_takes else [args.take]

    if args.dry_run:
        print("\n--- Plan ---")
        for sid in targets:
            s = shots[sid]
            for t in takes:
                print(f"{sid} take {t}: {s['model']} | {s['length']}s | {os.path.basename(s['keyframe_path'])}")
        return

    client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
    log = {}
    if os.path.exists(LOG_PATH):
        try:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                log = json.load(f)
        except Exception:
            pass

    for sid in targets:
        s = shots[sid]
        for t in takes:
            key = f"{sid}_take{t}"
            try:
                out_path = generate_shot(client, s, t)
                log[key] = {
                    "shot": sid,
                    "take": t,
                    "status": "success",
                    "file": os.path.basename(out_path) if os.path.exists(out_path) else out_path,
                    "model": s["model"],
                    "length": s["length"],
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            except Exception as e:
                log[key] = {
                    "shot": sid,
                    "take": t,
                    "status": "error",
                    "error": str(e)[:300],
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            with open(LOG_PATH, "w", encoding="utf-8") as f:
                json.dump(log, f, indent=2)


if __name__ == "__main__":
    main()

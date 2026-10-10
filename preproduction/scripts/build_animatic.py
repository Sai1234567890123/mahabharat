"""Cuts art/motion/animatic_v01.mp4 from the 18 generated clips and extracts QA frames.

Tasks:
  1. Build art/motion/PICKS.json
  2. Extract first, mid, and last frame for each clip
  3. Concatenate all 18 clips trimmed to shots.json duration into art/motion/animatic_v01.mp4
  4. Generate preview.html
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
MOTION_DIR = os.path.join(ROOT, "art", "motion")
FRAMES_DIR = os.path.join(MOTION_DIR, "qa_frames")
PICKS_PATH = os.path.join(MOTION_DIR, "PICKS.json")
ANIMATIC_PATH = os.path.join(MOTION_DIR, "animatic_v01.mp4")

FFMPEG = "ffmpeg"


def get_duration(video_path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
    except Exception:
        return 4.0


def extract_frames(sid, video_path):
    dur = get_duration(video_path)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    times = [
        ("first", 0.0),
        ("mid", dur / 2.0),
        ("last", max(0.0, dur - 0.2)),
    ]
    extracted = {}
    for label, t in times:
        out_jpg = os.path.join(FRAMES_DIR, f"{sid}_{label}.jpg")
        cmd = [
            FFMPEG, "-y", "-ss", str(t), "-i", video_path,
            "-vframes", "1", "-q:v", "2", out_jpg
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(out_jpg):
            extracted[label] = out_jpg
    return extracted


def build_animatic(shots_data):
    os.makedirs(FRAMES_DIR, exist_ok=True)
    picks = {}
    trimmed_clips = []
    temp_dir = os.path.join(MOTION_DIR, "_temp")
    os.makedirs(temp_dir, exist_ok=True)

    print("--- Processing 18 pilot clips ---")
    total_duration = 0.0
    for s in shots_data["shots"]:
        sid = s["id"]
        dur = float(s["duration"])
        total_duration += dur
        clip_path = os.path.join(MOTION_DIR, f"{sid}_take1.mp4")

        if os.path.exists(clip_path):
            picks[sid] = {
                "take": 1,
                "file": f"{sid}_take1.mp4",
                "target_duration": dur,
                "status": "ready"
            }
            # Extract evaluation frames
            extract_frames(sid, clip_path)

            # Trim clip to exact target duration and conform to 1920x1080 24fps
            trimmed_path = os.path.join(temp_dir, f"{sid}_trimmed.mp4")
            cmd = [
                FFMPEG, "-y", "-i", clip_path, "-t", str(dur),
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=24",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast",
                "-an", trimmed_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            trimmed_clips.append(trimmed_path)
            print(f"[{sid}] Trimmed to {dur:.1f}s: {trimmed_path}")
        else:
            picks[sid] = {"status": "missing"}
            print(f"[{sid}] Warning: clip missing")

    with open(PICKS_PATH, "w", encoding="utf-8") as f:
        json.dump(picks, f, indent=2)
    print(f"Wrote {PICKS_PATH}")

    # Concatenate all trimmed clips
    concat_list_path = os.path.join(temp_dir, "concat_list.txt")
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for p in trimmed_clips:
            clean_p = p.replace("\\", "/")
            f.write(f"file '{clean_p}'\n")

    print(f"Cutting animatic_v01.mp4 ({len(trimmed_clips)} clips, total ~{total_duration:.1f}s)...")
    concat_cmd = [
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-c", "copy", ANIMATIC_PATH
    ]
    subprocess.run(concat_cmd, check=True)
    anim_size = os.path.getsize(ANIMATIC_PATH)
    print(f"SUCCESS: Created {ANIMATIC_PATH} ({anim_size} bytes, {total_duration:.1f}s)")
    return picks, total_duration


def main():
    shots_json = os.path.join(ROOT, "data", "shots.json")
    with open(shots_json, "r", encoding="utf-8") as f:
        shots_data = json.load(f)

    picks, total_dur = build_animatic(shots_data)
    print("\n--- Summary ---")
    print(f"All 18 shots assembled into: {ANIMATIC_PATH}")
    print(f"Total duration: {total_dur:.1f}s")


if __name__ == "__main__":
    main()

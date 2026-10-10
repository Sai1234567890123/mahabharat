"""Vertical YouTube Short from the pilot takes, with captions, sound and transitions.

Reads the picked takes in art/motion/ (PICKS.json), trims each to its shot
duration from data/shots.json, lays each 16:9 take over a blurred 9:16
background, adds a caption and a series tag, joins the shots with white
flash transitions, and mixes a sound bed. The sound is generated here (a low
drone plus conch, impact and whoosh cues), so there is no music licence to
clear. The takes' own Veo audio is not used.

  python scripts/make_short.py --dry-run
  python scripts/make_short.py
  python scripts/make_short.py --out art/shorts/short_v02.mp4

Needs ffmpeg and ffprobe on PATH, and numpy.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
MOTION = os.path.join(ROOT, "art", "motion")
SR = 48000
FPS = 24
XF = 0.25  # white flash transition length, seconds
MAX_SECONDS = 60  # classic Shorts limit
FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]

# shot, on-screen caption, sound cues at the start of the shot
EDL = [
    ("SH070", "They blow together", ["conch"]),
    ("SH010", "Dawn at Kurukshetra", []),
    ("SH020", "The ape banner", []),
    ("SH030", "The grandsire roars", []),
    ("SH040", "Bhishma's conch", ["conch"]),
    ("SH050", "Like a thousand suns", []),
    ("SH060", "Two conches, one chariot", []),
    ("SH090", "The blare", ["boom"]),
    ("SH130", "Gandiva slips", []),
    ("SH150", "The universal form", ["boom"]),
    ("SH170", "Arjuna rises", ["boom"]),
    ("SH180", "Then black", []),
]
SERIES_TAG = "THE FIRST CONCH"


def font():
    for f in FONTS:
        if os.path.exists(f):
            return f
    sys.exit("no font found; add one to FONTS in make_short.py")


def fp(path):
    """Escape a path for an ffmpeg filter argument (also works on Windows)."""
    return path.replace("\\", "/").replace(":", "\\:")


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True).stdout
    return float(out)


def active_area(path):
    """The picture inside the black letterbox bars the takes come with, as crop=W:H:X:Y."""
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-ss", "1", "-t", "1", "-i", path,
         "-vf", "cropdetect=24:16:0", "-f", "null", "-"],
        capture_output=True, text=True)
    found = re.findall(r"crop=(\d+:\d+:\d+:\d+)", r.stderr)
    return found[-1] if found else None


def plan(picks, shots):
    segs = []
    for sid, caption, cues in EDL:
        if sid not in picks:
            sys.exit(f"{sid} has no pick in PICKS.json")
        src = os.path.join(MOTION, picks[sid]["file"])
        d = float(shots[sid]["duration"])
        have = probe_duration(src)
        if have + 1e-3 < d:
            sys.exit(f"{sid}: take is {have:.2f}s, shorter than the {d}s shot")
        crop = active_area(src) or "iw:ih:0:0"
        segs.append({"id": sid, "src": src, "d": d, "caption": caption, "cues": cues, "crop": crop})
    return segs


def write_captions(segs, cap_dir):
    os.makedirs(cap_dir, exist_ok=True)
    for s in segs:
        s["cap_file"] = os.path.join(cap_dir, f"{s['id']}.txt")
        with open(s["cap_file"], "w", encoding="utf-8") as f:
            f.write(s["caption"] + "\n")
    tag = os.path.join(cap_dir, "tag.txt")
    with open(tag, "w", encoding="utf-8") as f:
        f.write(SERIES_TAG + "\n")
    return tag


def segment_chain(i, s, tag, fontfile, fit):
    """One shot as a 9:16 video, with its captions."""
    head = f"[{i}:v]crop={s['crop']},trim=0:{s['d']},setpts=PTS-STARTPTS,fps={FPS},"
    if fit == "fill":
        # crop-to-fill: the centre of the picture, scaled up to the frame
        body = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=saturation=1.05"
    else:
        # blur: the whole picture centred over a blurred copy of itself
        body = (f"split[a{i}][b{i}];[a{i}]scale=1080:1920:force_original_aspect_ratio=increase,"
                f"crop=1080:1920,boxblur=20:1,eq=brightness=-0.08:saturation=0.9[bg{i}];"
                f"[b{i}]scale=1080:-2:flags=lanczos,eq=contrast=1.06:saturation=1.1[fg{i}];"
                f"[bg{i}][fg{i}]overlay=(W-w)/2:(H-h)/2")
    cap = (f"drawtext=textfile='{fp(s['cap_file'])}':fontfile='{fp(fontfile)}':fontsize=64:"
           f"fontcolor=white:borderw=4:bordercolor=black@0.7:x=(w-text_w)/2:y=200,"
           f"drawtext=textfile='{fp(tag)}':fontfile='{fp(fontfile)}':fontsize=40:"
           f"fontcolor=white@0.85:x=(w-text_w)/2:y=1640[v{i}]")
    if fit == "fill":
        return head + body + "," + cap
    return head + body + "," + cap


def video_graph(segs, tag, fontfile, fit):
    parts = [segment_chain(i, s, tag, fontfile, fit) for i, s in enumerate(segs)]
    prev, offset = "v0", 0.0
    for i in range(1, len(segs)):
        offset += segs[i - 1]["d"] - XF
        parts.append(f"[{prev}][v{i}]xfade=transition=fadewhite:duration={XF}:offset={offset:.3f}[x{i}]")
        prev = f"x{i}"
    parts.append(f"[{prev}]format=yuv420p[vout]")
    return ";".join(parts)


def tone_env(n, attack, decay):
    t = np.arange(n) / SR
    return np.minimum(t / attack, 1.0) * np.exp(-t / decay)


def conch(dur=2.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5 * t) * np.clip((t - 0.6) / 0.6, 0, 1)
    phase = 2 * np.pi * np.cumsum(146.8 * vib) / SR  # D3
    sig = sum(w * np.sin(k * phase) for k, w in zip(range(1, 7), [1, .6, .35, .2, .12, .06]))
    breath = np.random.default_rng(1).standard_normal(n) * 0.02 * tone_env(n, 0.25, 0.6)
    return (sig * tone_env(n, 0.35, 1.8) + breath) * 0.35


def boom(dur=1.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    phase = 2 * np.pi * np.cumsum(90 * np.exp(-t * 1.6) + 35) / SR
    return np.sin(phase) * tone_env(n, 0.005, 0.45) * 0.6


def whoosh(dur=0.35):
    n = int(dur * SR)
    noise = np.random.default_rng(2).standard_normal(n)
    smooth = np.convolve(noise, np.ones(60) / 60, mode="same")  # crude low-pass
    t = np.arange(n) / SR
    return smooth * np.sin(np.pi * np.clip(t / dur, 0, 1)) * 0.5


def drone(total):
    n = int(total * SR)
    t = np.arange(n) / SR
    bed = 0.5 * np.sin(2 * np.pi * 55 * t) + 0.35 * np.sin(2 * np.pi * 82.4 * t) + 0.2 * np.sin(2 * np.pi * 110.1 * t)
    swell = 0.6 + 0.4 * np.sin(2 * np.pi * t / 8)
    fade = np.minimum(t / 1.0, 1) * np.minimum((total - t) / 1.5, 1)
    return bed * swell * fade * 0.25


def add_at(buf, sig, t0):
    i = int(t0 * SR)
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[:j - i]


def mix(segs, total):
    out = drone(total)
    starts = np.cumsum([0] + [s["d"] - XF for s in segs])[:-1]
    cues = {"conch": conch, "boom": boom}
    for i, s in enumerate(segs):
        if i > 0:
            add_at(out, whoosh(), starts[i])  # the flash transition starts at the cut
        for cue in s["cues"]:
            add_at(out, cues[cue](), starts[i])
    return out / np.abs(out).max() * 0.8


def write_wav(path, mono):
    st = np.clip(mono, -1, 1)
    pcm = (np.stack([st, st], axis=1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "art", "shorts", "short_v01.mp4"))
    ap.add_argument("--fit", choices=["blur", "fill"], default="blur",
                    help="blur: whole picture over a blurred background; fill: crop to fill the frame")
    ap.add_argument("--dry-run", action="store_true", help="print the edit list, render nothing")
    a = ap.parse_args()

    data = json.load(open(os.path.join(ROOT, "data", "shots.json"), encoding="utf-8"))
    shots = {s["id"]: s for s in data["shots"]}
    picks = json.load(open(os.path.join(MOTION, "PICKS.json"), encoding="utf-8"))
    segs = plan(picks, shots)
    total = sum(s["d"] for s in segs) - XF * (len(segs) - 1)
    for s in segs:
        print(f"{s['id']}  {s['d']:>4.1f}s  {s['caption']}  [{', '.join(s['cues']) or '-'}]  {s['crop']}")
    print(f"{len(segs)} shots, {total:.2f} s total (limit {MAX_SECONDS} s)")
    if total > MAX_SECONDS:
        sys.exit("too long for a Short; drop a shot")
    if a.dry_run:
        return

    work = os.path.join(ROOT, "art", "shorts")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    tag = write_captions(segs, os.path.join(work, "captions"))
    wav = os.path.join(work, os.path.splitext(os.path.basename(a.out))[0] + "_mix.wav")
    write_wav(wav, mix(segs, total))

    n = len(segs)
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for s in segs:
        cmd += ["-i", s["src"]]
    cmd += ["-i", wav]
    graph = (video_graph(segs, tag, font(), a.fit)
             + f";[{n}:a]loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{total:.3f}[aout]")
    cmd += ["-filter_complex", graph, "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)
    print("wrote", a.out)


if __name__ == "__main__":
    main()

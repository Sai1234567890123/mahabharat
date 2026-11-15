"""Build shots.md, frame_prompts.md and motion_prompts.md from shots.json.

Usage: python studio/tools/build_docs.py studio/episodes/ep01_arjuna_vs_karna
Passport descriptors are pasted verbatim from studio/cast/<tag>/passport.md.
"""
import json, re, sys, pathlib

STUDIO = pathlib.Path(__file__).resolve().parent.parent
ep = pathlib.Path(sys.argv[1]).resolve()
d = json.loads((ep / "shots.json").read_text())

bible = (STUDIO / "bible.md").read_text()
style = re.search(r"## Global style prompt.*?\n\n> (.+?)\n", bible, re.S).group(1).strip()

def descriptor(tag):
    p = STUDIO / "cast" / tag.lstrip("@") / "passport.md"
    txt = p.read_text()
    return re.search(r"## Descriptor.*?\n\n(.+?)\n", txt, re.S).group(1).strip()

LOCATION = ("Kurukshetra battlefield, late afternoon, trampled red earth, hot orange low sun in the west, "
            "burnt umber shadows, red dust haze in flat layers. Screen direction: Arjuna's side on the left, "
            "Karna's side on the right.")

t = 0
md = [f"# {d['title']}: shot cards ({d['runtime_s']} s, {len(d['shots'])} shots)\n",
      f"Source: {d['source']}. Aspect {d['aspect']}.\n",
      "Rules: one action per shot; hook readable with the sound off in the first 3 s; no text in frame; the last shot holds its pose to the last frame.\n",
      "| Shot | In | Dur | Beat | Characters | Camera | The one action | Sound |", "|---|---|---|---|---|---|---|---|"]
fp = [f"# {d['title']}: starting-frame prompts\n",
      "Each prompt = global style + passport descriptors verbatim + location + the calm starting picture. Attach the listed reference image. Generate nothing until sai approves the quote.\n"]
mp = [f"# {d['title']}: motion prompts (image-to-video)\n",
      "The scene lives in the frame. These prompts are motion only: one action, one camera move, timed in beats. Render each at 5 to 8 s and trim to the card length in the edit.\n"]
for s in d["shots"]:
    chars = ", ".join(s["chars"]) or "none"
    md.append(f"| {s['id']} | {t//60}:{t%60:02d} | {s['dur']} s | {s['beat']} | {chars} | {s['camera']} | {s['action']} | {s['sound']} |")
    parts = [style]
    for c in s["chars"]:
        parts.append(f"{c}: {descriptor(c)}")
    parts += [LOCATION, s["frame"], "No text, no extra characters, 16:9."]
    fp.append(f"## {s['id']} ({s['dur']} s)\n")
    if s["ref"]:
        fp.append(f"Reference image: `studio/{s['ref']}`\n")
    fp.append("```\n" + "\n\n".join(parts) + "\n```\n")
    mp.append(f"## {s['id']}\n\n```\nImage-to-video, {max(5, s['dur'])} seconds, from the attached still.\n" + "\n".join(s["motion"]) +
              f"\nCamera: {s['camera']}.\nSound: {s['sound']}\nPainterly stylized animation, 2D effects on twos, no text, the characters do not speak.\n```\n")
    t += s["dur"]
md.append(f"\nTotal: {t} s.\n")
(ep / "shots.md").write_text("\n".join(md))
(ep / "frame_prompts.md").write_text("\n".join(fp))
(ep / "motion_prompts.md").write_text("\n".join(mp))
print("total", t, "s")

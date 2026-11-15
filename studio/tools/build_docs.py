#!/usr/bin/env python3
"""Build shots.md, prompts.md and script.md for an episode from shots.json.

shots.json is the single source of truth. Edit it, then run:
    python3 studio/tools/build_docs.py ep01
Passport descriptors are read from studio/cast/<name>/passport.md and pasted
verbatim, so a prompt can never drift from the passport.
"""
import json
import re
import sys
from pathlib import Path

STUDIO = Path(__file__).resolve().parent.parent


def passports():
    """Return {tag: descriptor} for every '# @tag' or '## @tag' block."""
    out = {}
    for f in sorted((STUDIO / "cast").glob("*/passport.md")):
        if f.parent.name.startswith("_"):
            continue
        text = f.read_text(encoding="utf-8")
        for m in re.finditer(r"^#{1,2} (@\w+).*?```\n(.*?)\n```", text, re.S | re.M):
            out[m.group(1)] = m.group(2).strip()
    return out


def bible_block(heading):
    text = (STUDIO / "bible.md").read_text(encoding="utf-8")
    m = re.search(re.escape(heading) + r".*?```\n(.*?)\n```", text, re.S)
    return m.group(1).strip()


def main(ep):
    ep_dir = STUDIO / "episodes" / ep
    data = json.loads((ep_dir / "shots.json").read_text(encoding="utf-8"))
    shots = data["shots"]
    cast = passports()
    style = bible_block("## Global style line")
    location = bible_block("**Location descriptor")
    total = sum(s["cut_s"] for s in shots)
    assert total == data["length_s"], f"cut lengths add up to {total}, not {data['length_s']}"
    for s in shots:
        for tag in s["cast"]:
            assert tag in cast, f"{s['id']}: no passport for {tag}"

    # ---------- shots.md ----------
    md = [f"# {data['title']}: shot cards", "",
          f"{len(shots)} shots, {total} seconds, {data['format']}. One action per shot. "
          "Built from `shots.json` by `tools/build_docs.py`; edit the JSON, not this file.", ""]
    t = 0
    act = None
    for s in shots:
        if s["act"] != act:
            act = s["act"]
            md += [f"## {data['acts'][act]}", ""]
        md += [f"### {s['id']} · {t:.0f} to {t + s['cut_s']:.0f} s · {s['cut_s']} s on screen (generate {s['gen_s']} s)",
               "",
               f"- **Action:** {s['action']}",
               f"- **Cast:** {', '.join(s['cast']) if s['cast'] else 'no characters'}",
               f"- **Camera:** {s['size']}, {s['angle']}, {s['lens']}, {s['move']}",
               f"- **Sound:** {s['sound']}",
               f"- **Beat:** {s['beat']}",
               f"- **Impact frame:** {s['impact'] if s['impact'] else 'none'}",
               f"- **Risk for the video model:** {s['risk']}",
               ""]
        t += s["cut_s"]
    (ep_dir / "shots.md").write_text("\n".join(md), encoding="utf-8")

    # ---------- prompts.md ----------
    pm = [f"# {data['title']}: prompts v1", "",
          "Two prompts per shot. The **frame prompt** makes the still (first frame). "
          "The **motion prompt** animates that still, timed in beats. "
          "Character descriptors are pasted verbatim from the passports. "
          "Attach the character's `crop-34.png` reference to every frame call once it exists.", "",
          "Rules for every call: 16:9, no text in frame, no real person's likeness, "
          "energy colors only on their owner. Log every attempt in `log.md`.", ""]
    for s in shots:
        chars = "\n\n".join(f"{tag}: {cast[tag]}" for tag in s["cast"])
        frame = f"{style}\n\nLOCATION: {location}\n\n"
        if chars:
            frame += f"CHARACTERS:\n{chars}\n\n"
        frame += (f"SHOT: {s['size']}, {s['angle']}, {s['lens']} lens. {s['start']}\n\n"
                  "FORMAT: 16:9 cinematic frame composed for a 2.39:1 center crop, no text, no watermark, "
                  "no border, original faces only.")
        beats = "\n".join(f"{a:g} to {b:g} s: {txt}." for a, b, txt in s["motion"])
        motion = (f"Animate this exact frame. Keep the painterly look, the costumes and the faces unchanged.\n"
                  f"Camera: {s['move']}.\n{beats}\n"
                  f"One action only: {s['action']}\n"
                  "No new characters, no text, no cuts inside the shot. "
                  f"Length {s['gen_s']} s. Sound: {s['sound']}")
        pm += [f"## {s['id']} ({s['gen_s']} s to generate, {s['cut_s']} s used)", "",
               "Frame prompt:", "", "```", frame, "```", "",
               "Motion prompt:", "", "```", motion, "```", ""]
    (ep_dir / "prompts.md").write_text("\n".join(pm), encoding="utf-8")

    # ---------- script.md ----------
    sc = [f"# {data['title']}: script", "",
          "No dialogue. Read it top to bottom as one piece of action; each line is one shot.", ""]
    act = None
    t = 0
    for s in shots:
        if s["act"] != act:
            act = s["act"]
            sc += [f"## {data['acts'][act]}", ""]
        sc += [f"**{s['id']}** ({t:.0f} s) {s['action']} *{s['sound']}*", ""]
        t += s["cut_s"]
    (ep_dir / "script.md").write_text("\n".join(sc), encoding="utf-8")

    # ---------- shots.js (the animatic reads this; file:// pages cannot fetch JSON) ----------
    (ep_dir / "shots.js").write_text("window.EP = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")

    gen = sum(s["gen_s"] for s in shots)
    print(f"{len(shots)} shots, {total} s on screen, {gen} s to generate")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "ep01")

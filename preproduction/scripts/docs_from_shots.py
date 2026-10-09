"""Writes 05-shot-list.md and 06-prompt-pack.md from data/shots.json."""
import json
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

GLOBAL = ("Painterly stylized CG animation, hand-painted textures with visible brushwork, flat value blocks, "
          "hard-edged tinted shadows, strong colored rim light, layered atmospheric haze, matte-painted sky, "
          "anamorphic lens flare, subtle film grain, Indian epic iconography, simplified readable silhouettes. "
          "No text, no logos, no watermarks. No photorealism, no plastic 3D look, no real actor likeness.")
NEGATIVE = "photorealistic, live action, plastic CGI, video game render, text, watermark, logo, extra fingers, deformed hands, modern objects, western fantasy armor, real celebrity face"
WHO = {"krishna": ["krishna."], "arjuna": ["arjuna", "archer"], "bhishma": ["bhishma", "white-bearded", "white beard"],
       "duryodhana": ["duryodhana"], "bhima": ["bhima", "massive warrior"], "yudhishthira": ["yudhishthira", "parasol"]}


def cast(s):
    txt = (s["description"] + " " + s["keyframe_prompt"]).lower()
    out = [k for k, keys in WHO.items() if any(w in txt for w in keys)]
    if "blue-skinned" in txt or "krishna" in txt:
        out = ["krishna"] + [k for k in out if k != "krishna"]
    return list(dict.fromkeys(out))


def main():
    d = json.load(open(os.path.join(ROOT, "data", "shots.json")))
    shots, acts, chars = d["shots"], d["acts"], d["characters"]
    total = sum(s["duration"] for s in shots)

    L = ["# Pilot shot list: \"The First Conch\"", "",
         f"{len(shots)} shots, {total:.0f} seconds at {d['fps']} fps (2D FX on {d['fx_fps']} fps), aspect {d['aspect']}:1.",
         "Generated from `data/shots.json` by `scripts/docs_from_shots.py`; edit the JSON, not this file.",
         "Concept frames for every shot are in `art/frames/`, with impact frames as `*_impact.jpg`. "
         "Storyboard sheets: `art/storyboard-1.jpg`, `art/storyboard-2.jpg`.", "",
         "| Shot | Beat | Act | Sec | Lens | Camera | What we see | FX | Sound | Source |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for s in shots:
        fx = ", ".join(sorted({f["type"] for f in s["fx"]})) or "none"
        if s.get("impact"):
            fx += f"; impact frame x{s['impact']['frames']}"
        desc = s["description"].replace("|", "/")
        if s.get("dialogue"):
            desc += " " + s["dialogue"].replace("|", "/")
        L.append(f"| {s['id']} {s['title']} | {s['beat']} | {s['act']} | {s['duration']:.0f} | {s['camera']['lens']}mm | "
                 f"{s['camera']['move']} | {desc} | {fx} | {s['sound']} | {s['source']} |")
    L += ["", "## Camera and edit notes", "",
          "- Act A is loud and kinetic: low angles, arcs, whip pans and camera shake on every conch.",
          "- Act B is still: locked frames, long lenses, symmetry around Krishna, silence under Arjuna's collapse.",
          "- Act C breaks scale: ultra-wide lenses, the chariot as a speck, the form filling the frame.",
          "- Act D returns to heat and motion and ends on a hard cut to black.",
          "- Impact frames are cut in on the frame of the blast, 1 to 3 frames, never more.",
          "- Hero shots for the 10-shot pipeline test: " + ", ".join(s["id"] for s in shots if s.get("hero")) + "."]
    open(os.path.join(ROOT, "05-shot-list.md"), "w").write("\n".join(L) + "\n")

    P = ["# Prompt pack (pilot)", "",
         "Ready-to-run prompts for each shot, generated from `data/shots.json`. Use them with the control passes in "
         "`art/control/` (depth, line art, IDs) so the AI paint-over keeps the Blender layout. Never add a reference "
         "image from another film or a real actor.", "",
         "## How to use", "",
         "1. **Keyframe (image).** Nano Banana (Gemini 2.5 Flash Image) or Imagen on Vertex AI for quick passes; "
         "Flux or Qwen-Image with ControlNet depth + line art in ComfyUI for layout-locked passes. "
         "Prompt = global style + act line + cast lines + shot prompt. Feed `SHxxx_depth.png` and `SHxxx_lineart.png` "
         "as control images at strength 0.5 to 0.7, and the concept frame `art/frames/SHxxx.jpg` as the color reference.",
         "2. **QA.** Ask Gemini to score the keyframe against the style bible checklist (palette, rim light, silhouette, "
         "no photorealism, character codes) and regenerate below 8/10.",
         "3. **Motion.** Veo 3.1 image-to-video (first frame = approved keyframe; for shots with a big change, first and "
         "last frame) or Wan 2.2 VACE video-to-video over the Blender animatic. Use the motion prompt.",
         "4. **2D FX and impact frames** are composited afterwards (`scripts/compose.py`), not generated, so they stay "
         "on model and on twos.", "",
         "## Global style (every prompt)", "", "> " + GLOBAL, "",
         "Negative prompt (models that take one): `" + NEGATIVE + "`", "",
         "## Act lines", ""]
    for k, a in acts.items():
        P.append(f"- **Act {k}, {a['name']}:** {a['prompt']}")
    P += ["", "## Cast lines", ""]
    for k, c in chars.items():
        P.append(f"- **{c['name']}:** {c['prompt']}.")
    P += ["", "## Shots", ""]
    for s in shots:
        cl = cast(s)
        P += [f"### {s['id']} {s['title']} (act {s['act']}, {s['duration']:.0f}s)", "",
              f"Control passes: `art/control/{s['id']}_depth.png`, `art/control/{s['id']}_lineart.png`. "
              f"Color reference: `art/frames/{s['id']}.jpg`.", "",
              "**Keyframe prompt**", "", "```",
              GLOBAL, acts[s["act"]]["prompt"]]
        for k in cl:
            P.append(chars[k]["prompt"] + ".")
        P += [s["keyframe_prompt"] + f". {s['camera']['lens']}mm lens, 2.39:1 widescreen.", "```", "",
              "**Motion prompt (Veo 3.1 / Wan 2.2)**", "", "```",
              s["motion_prompt"] + ". Painterly stylized animation, keep the art style of the first frame, no photorealism.",
              "```", ""]
        if s.get("dialogue"):
            P += [f"Dialogue: {s['dialogue']}", ""]
    open(os.path.join(ROOT, "06-prompt-pack.md"), "w").write("\n".join(P) + "\n")
    print("wrote 05-shot-list.md and 06-prompt-pack.md")


if __name__ == "__main__":
    main()

"""AI paint-over of the concept frames with Gemini image models on Vertex AI.

Takes each blockout frame from art/frames/, sends it to Nano Banana
(gemini-3.1-flash-image) with the style bible, act, cast and shot prompts
from data/shots.json, and asks for a finished painterly keyframe that keeps
the exact layout. A second model scores each result against the style bible.

Run it on a machine that is already logged in to Google Cloud
(`gcloud auth application-default login`), or set GCP_SA_KEY to a service
account's JSON key (Vertex AI User role). For example:

  pip install google-genai
  python paint_over.py                      # the 8 hero shots
  python paint_over.py --shot SH050 --shot SH150
  python paint_over.py --all --takes 2

Settings come from the environment, with these defaults:
  GOOGLE_CLOUD_PROJECT=aiautomationplatform
  GOOGLE_CLOUD_LOCATION=us        (try "global" if the model is not found)
  PAINT_MODEL=gemini-3.1-flash-image
  QA_MODEL=gemini-3.8-flash

Output: art/painted/SHxxx_vNN.png and art/painted/qa.json (scores and notes).
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from docs_from_shots import GLOBAL, NEGATIVE, cast  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, ".."))

QA_CHECKLIST = """Score this keyframe from 0 to 10 against the style bible and return JSON only:
{"score": <0-10>, "keeps_layout": true/false, "painterly_not_photoreal": true/false,
 "palette_matches_act": true/false, "rim_light": true/false, "characters_on_model": true/false,
 "problems": ["short notes"]}
Rules: painterly stylized CG, visible brushwork, flat value blocks, hard tinted shadows, colored rim light,
layered haze, readable silhouettes, no text or logos, no photorealism, no real actor likeness.
The second image is the layout frame it must follow (composition, camera, horizon, positions, scale)."""


def build_prompt(shot, data):
    act = data["acts"][shot["act"]]
    lines = [
        "Repaint the attached layout frame as a finished keyframe for an animated feature.",
        "Keep the exact composition, camera angle, lens, horizon line, character positions and scale, "
        "and the overall color palette of the layout. Replace the simple proxy figures, horses and props "
        "with fully designed, detailed ones. Keep the hand-drawn effects (sound rings, light rays, halos, "
        "geometry) in the same places, cleaner and more beautiful.",
        GLOBAL,
        act["prompt"],
    ]
    for k in cast(shot):
        lines.append(data["characters"][k]["prompt"] + ".")
    lines.append(shot["keyframe_prompt"] + f". {shot['camera']['lens']}mm lens, 2.39:1 widescreen.")
    lines.append("Avoid: " + NEGATIVE + ".")
    return "\n".join(lines)


def image_part(types, path):
    mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    with open(path, "rb") as f:
        return types.Part.from_bytes(data=f.read(), mime_type=mime)


def call(fn, tries=4):
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # rate limits and transient errors
            if i == tries - 1:
                raise
            wait = 10 * (i + 1)
            print(f"  retry in {wait}s: {str(e)[:160]}")
            time.sleep(wait)


def paint(client, types, model, prompt, frame, aspect):
    contents = [prompt, image_part(types, frame)]
    try:
        cfg = types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"],
                                          image_config=types.ImageConfig(aspect_ratio=aspect))
        r = call(lambda: client.models.generate_content(model=model, contents=contents, config=cfg))
    except Exception as e:
        if "aspect" not in str(e).lower() and "image_config" not in str(e).lower():
            raise
        cfg = types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"])
        r = call(lambda: client.models.generate_content(model=model, contents=contents, config=cfg))
    for cand in r.candidates or []:
        for part in cand.content.parts or []:
            if getattr(part, "inline_data", None) and part.inline_data.data:
                return part.inline_data.data
    text = getattr(r, "text", None)
    raise RuntimeError(f"no image returned{': ' + text[:200] if text else ''}")


def qa(client, types, model, painted, frame):
    cfg = types.GenerateContentConfig(response_mime_type="application/json")
    r = call(lambda: client.models.generate_content(
        model=model, contents=[QA_CHECKLIST, image_part(types, painted), image_part(types, frame)], config=cfg))
    try:
        return json.loads(r.text)
    except Exception:
        return {"raw": (r.text or "")[:500]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", action="append", help="shot id, repeatable (default: hero shots)")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--takes", type=int, default=1, help="images per shot")
    ap.add_argument("--aspect", default="21:9")
    ap.add_argument("--no-qa", action="store_true")
    ap.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT", "aiautomationplatform"))
    ap.add_argument("--location", default=os.environ.get("GOOGLE_CLOUD_LOCATION", "us"))
    ap.add_argument("--model", default=os.environ.get("PAINT_MODEL", "gemini-3.1-flash-image"))
    ap.add_argument("--qa-model", default=os.environ.get("QA_MODEL", "gemini-3.8-flash"))
    ap.add_argument("--dry-run", action="store_true", help="print prompts, call nothing")
    a = ap.parse_args()

    data = json.load(open(os.path.join(ROOT, "data", "shots.json"), encoding="utf-8"))
    shots = [s for s in data["shots"] if a.all or (a.shot and s["id"] in a.shot) or (not a.shot and s.get("hero"))]
    out = os.path.join(ROOT, "art", "painted")
    os.makedirs(out, exist_ok=True)
    qa_path = os.path.join(out, "qa.json")
    report = json.load(open(qa_path, encoding="utf-8")) if os.path.exists(qa_path) else {}

    if a.dry_run:
        for s in shots:
            print(f"--- {s['id']}\n{build_prompt(s, data)}\n")
        return

    from google import genai
    from google.genai import types
    creds = None
    if os.environ.get("GCP_SA_KEY"):  # service-account JSON in an env var (cloud sessions)
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_info(
            json.loads(os.environ["GCP_SA_KEY"]), scopes=["https://www.googleapis.com/auth/cloud-platform"])
    client = genai.Client(vertexai=True, project=a.project, location=a.location, credentials=creds)
    print(f"Vertex AI project={a.project} location={a.location} model={a.model}")

    for s in shots:
        frame = os.path.join(ROOT, "art", "frames", f"{s['id']}.jpg")
        if not os.path.exists(frame):
            print(f"{s['id']}: no frame at {frame}, skipped")
            continue
        prompt = build_prompt(s, data)
        for t in range(a.takes):
            n = 1
            while os.path.exists(os.path.join(out, f"{s['id']}_v{n:02d}.png")):
                n += 1
            dest = os.path.join(out, f"{s['id']}_v{n:02d}.png")
            try:
                img = paint(client, types, a.model, prompt, frame, a.aspect)
            except Exception as e:
                print(f"{s['id']}: failed: {str(e)[:300]}")
                break
            with open(dest, "wb") as f:
                f.write(img)
            entry = {"frame": os.path.basename(frame), "model": a.model}
            if not a.no_qa:
                try:
                    entry["qa"] = qa(client, types, a.qa_model, dest, frame)
                except Exception as e:
                    entry["qa"] = {"error": str(e)[:300]}
            report[os.path.basename(dest)] = entry
            json.dump(report, open(qa_path, "w", encoding="utf-8"), indent=2)
            score = entry.get("qa", {}).get("score", "-")
            print(f"{s['id']}: wrote {os.path.basename(dest)} (QA score {score})")


if __name__ == "__main__":
    main()

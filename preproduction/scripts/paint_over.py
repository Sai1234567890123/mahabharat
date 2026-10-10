"""AI paint-over of the concept frames with Gemini image models on Vertex AI.

Takes each blockout frame from art/frames/, sends it to Nano Banana
(gemini-3.1-flash-image) with the style bible, act, cast, shot prompts, and
canonical epic requirements from data/canon_checks.json. A second model
scores each result against both the style bible and the epic canon.

Run it on a machine that is already logged in to Google Cloud
(`gcloud auth application-default login`), or set GCP_SA_KEY to a service
account's JSON key (Vertex AI User role). For example:

  pip install google-genai
  python paint_over.py                      # the 8 hero shots
  python paint_over.py --qa-only            # score existing frames without repainting
  python paint_over.py --shots SH010,SH050  # target specific shots
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
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from docs_from_shots import GLOBAL, NEGATIVE, cast  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, ".."))

QA_BASE_CHECKLIST = """Score this keyframe from 0 to 10 against the style bible and canonical text requirements, and return JSON only:
{
  "score": <0-10>,
  "keeps_layout": true/false,
  "painterly_not_photoreal": true/false,
  "palette_matches_act": true/false,
  "rim_light": true/false,
  "characters_on_model": true/false,
  "canon": {
    "pass": true/false,
    "failed_must": ["list of any failed 'must' requirements"],
    "found_must_not": ["list of any prohibited 'must_not' elements found in the image"]
  },
  "problems": ["short notes"]
}
Rules:
1. Style: painterly stylized CG, visible brushwork, flat value blocks, hard tinted shadows, colored rim light, layered haze, readable silhouettes, no text or logos, no photorealism, no real actor likeness.
2. Layout: The second image is the layout frame it must follow (composition, camera, horizon, positions, scale).
3. Canon: The frame MUST strictly obey the epic passage and all 'must' checklist items, and MUST NOT contain any 'must_not' items.
If ANY 'must' item fails, or ANY 'must_not' item is detected in the image, canon.pass MUST be false, regardless of style score."""


def find_b06_file():
    candidates = [
        os.path.join(ROOT, "..", "mahabharat-research", "source", "B06-bhishma.txt"),
        os.path.join(ROOT, "..", "mahabharat-site", "source", "B06-bhishma.txt"),
        os.path.join(ROOT, "..", "mahabharat-source", "B06-bhishma.txt"),
        os.path.join(ROOT, "source", "B06-bhishma.txt"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def load_b06_lines():
    p = find_b06_file()
    if p and os.path.exists(p):
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.readlines()
    return []


def get_epic_snippet(source_ref, b06_lines):
    if not b06_lines or not source_ref:
        return ""
    after_b = re.sub(r'B\d+\s*', '', source_ref)
    snippets = []
    for part in after_b.split(','):
        part = part.strip()
        nums = [int(x) for x in re.findall(r'\d+', part)]
        if len(nums) == 2:
            s, e = nums[0], nums[1]
            snippets.append(" ".join(l.strip() for l in b06_lines[s - 1:min(e, len(b06_lines))]))
        elif len(nums) == 1:
            s = nums[0]
            if 0 < s <= len(b06_lines):
                snippets.append(b06_lines[s - 1].strip())
    return " | ".join(snippets)


def build_prompt(shot, data, canon_data=None, b06_lines=None):
    act = data["acts"][shot["act"]]
    lines = [
        "Repaint the attached layout frame as a finished keyframe for an animated feature.",
        "Keep the exact composition, camera angle, lens, horizon line, and the position and size of every "
        "chariot, figure and army block. Do not move or resize anything, and do not add or remove figures. "
        "Keep the overall color palette of the layout. Replace the simple proxy figures, horses and props "
        "with fully designed, detailed ones. Keep the hand-drawn effects (sound rings, light rays, halos, "
        "geometry) in the same places, cleaner and more beautiful.",
        "Render style: painterly stylized 3D animation with visible brushwork on every surface, soft painted "
        "gradients and textured shading. Do NOT use flat 2D cel shading, thick ink outlines or simple vector "
        "shapes. Define every shape by light, value and color, never by dark contour lines: no outlines around "
        "characters, horses, chariots or armies. Model form with soft volumetric shading and colored rim light, "
        "with brush texture on skin, cloth, metal and sky. Sparkles and light should glow softly, not look like "
        "flat stickers. Keep background ornaments and geometry as abstract shapes; do not turn them into faces.",
        GLOBAL,
        act["prompt"],
    ]
    for k in cast(shot):
        lines.append(data["characters"][k]["prompt"] + ".")

    # Inject canon rules if available
    shot_canon = (canon_data.get("shots", {}).get(shot["id"]) if canon_data else None)
    global_rules = canon_data.get("global", {}) if canon_data else {}
    if shot_canon:
        epic_snippet = get_epic_snippet(shot_canon.get("source", ""), b06_lines)
        lines.append(f"Epic source passage ({shot_canon.get('source', '')}): {shot_canon.get('epic', '')}")
        if epic_snippet:
            lines.append(f"Canonical text excerpt: \"{epic_snippet}\"")
        must_list = global_rules.get("must", []) + shot_canon.get("must", [])
        if must_list:
            lines.append("Canonical MUST requirements (mandatory):\n- " + "\n- ".join(must_list))

    lines.append(shot["keyframe_prompt"] + f". {shot['camera']['lens']}mm lens, 2.39:1 widescreen.")

    avoid_items = [NEGATIVE, "black ink outlines", "anime cel shading", "faces in the background"]
    if shot_canon:
        must_not_list = global_rules.get("must_not", []) + shot_canon.get("must_not", [])
        if must_not_list:
            avoid_items.extend(must_not_list)
    lines.append("Avoid: " + ", ".join(avoid_items) + ".")
    return "\n".join(lines)


def image_part(types, path):
    mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    with open(path, "rb") as f:
        return types.Part.from_bytes(data=f.read(), mime_type=mime)


def call(fn, tries=5, base_wait=25):
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            if i == tries - 1:
                raise
            wait = base_wait * (i + 1)
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


def qa(client, types, model, painted, frame, shot_id=None, canon_data=None, b06_lines=None):
    cfg = types.GenerateContentConfig(response_mime_type="application/json")
    prompt = QA_BASE_CHECKLIST
    if shot_id and canon_data and "shots" in canon_data:
        sc = canon_data["shots"].get(shot_id, {})
        global_rules = canon_data.get("global", {})
        b06_snippet = get_epic_snippet(sc.get("source", ""), b06_lines)
        canon_spec = f"""
Canonical Checklist for Shot {shot_id}:
Source Reference: {sc.get("source", "")}
Epic Summary: {sc.get("epic", "")}
Text Excerpt: {b06_snippet}

MUST HAVE (Every item must be present and verified in the image):
- """ + "\n- ".join(global_rules.get("must", []) + sc.get("must", [])) + """

MUST NOT HAVE (Strictly prohibited; fail if any are detected):
- """ + "\n- ".join(global_rules.get("must_not", []) + sc.get("must_not", []))
        prompt += "\n\n" + canon_spec

    contents = [prompt, image_part(types, painted), image_part(types, frame)]
    r = call(lambda: client.models.generate_content(
        model=model, contents=contents, config=cfg))
    try:
        return json.loads(r.text)
    except Exception:
        return {"raw": (r.text or "")[:500]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", action="append", help="shot id, repeatable (default: hero shots)")
    ap.add_argument("--shots", help="comma-separated list of shot IDs (e.g. SH010,SH050)")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--takes", type=int, default=1, help="images per shot")
    ap.add_argument("--aspect", default="21:9")
    ap.add_argument("--no-qa", action="store_true")
    ap.add_argument("--qa-only", action="store_true", help="re-score existing frames without repainting")
    ap.add_argument("--version", help="specific version to QA (e.g. v02)")
    ap.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT", "aiautomationplatform"))
    ap.add_argument("--location", default=os.environ.get("GOOGLE_CLOUD_LOCATION", "us"))
    ap.add_argument("--model", default=os.environ.get("PAINT_MODEL", "gemini-3.1-flash-image"))
    ap.add_argument("--qa-model", default=os.environ.get("QA_MODEL", "gemini-3.8-flash"))
    ap.add_argument("--dry-run", action="store_true", help="print prompts, call nothing")
    a = ap.parse_args()

    # Parse --shots comma-separated
    shot_ids = list(a.shot or [])
    if a.shots:
        shot_ids.extend([s.strip() for s in a.shots.split(",") if s.strip()])

    data = json.load(open(os.path.join(ROOT, "data", "shots.json"), encoding="utf-8"))
    shots = [s for s in data["shots"] if a.all or (shot_ids and s["id"] in shot_ids) or (not shot_ids and s.get("hero"))]

    canon_path = os.path.join(ROOT, "data", "canon_checks.json")
    canon_data = json.load(open(canon_path, encoding="utf-8")) if os.path.exists(canon_path) else {}
    b06_lines = load_b06_lines()

    out = os.path.join(ROOT, "art", "painted")
    os.makedirs(out, exist_ok=True)
    qa_path = os.path.join(out, "qa.json")
    report = json.load(open(qa_path, encoding="utf-8")) if os.path.exists(qa_path) else {}

    if a.dry_run:
        for s in shots:
            print(f"--- {s['id']}\n{build_prompt(s, data, canon_data, b06_lines)}\n")
        return

    from google import genai
    from google.genai import types
    creds = None
    if os.environ.get("GCP_SA_KEY"):
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_info(
            json.loads(os.environ["GCP_SA_KEY"]), scopes=["https://www.googleapis.com/auth/cloud-platform"])
    client = genai.Client(vertexai=True, project=a.project, location=a.location, credentials=creds)
    print(f"Vertex AI project={a.project} location={a.location} model={a.model} qa_model={a.qa_model}")

    # QA-ONLY MODE
    if a.qa_only:
        print("\n--- RUNNING CANON QA AUDIT (--qa-only) ---")
        for s in shots:
            frame = os.path.join(ROOT, "art", "frames", f"{s['id']}.jpg")
            if not os.path.exists(frame):
                print(f"{s['id']}: no layout frame at {frame}, skipped")
                continue

            # Find matching painted versions
            targets = []
            if a.version:
                f_name = f"{s['id']}_{a.version}.png"
                if os.path.exists(os.path.join(out, f_name)):
                    targets.append(os.path.join(out, f_name))
            else:
                # Find all or highest version
                v = 1
                while os.path.exists(os.path.join(out, f"{s['id']}_v{v:02d}.png")):
                    targets.append(os.path.join(out, f"{s['id']}_v{v:02d}.png"))
                    v += 1

            if not targets:
                print(f"{s['id']}: no painted frames found in {out}")
                continue

            # Evaluate each target version (or highest version)
            target = targets[-1]  # Highest existing version
            base_target = os.path.basename(target)
            print(f"\nEvaluating {s['id']} [{base_target}]...")
            entry = report.get(base_target, {"frame": os.path.basename(frame), "model": a.model})
            res = qa(client, types, a.qa_model, target, frame, s["id"], canon_data, b06_lines)
            entry["qa"] = res
            report[base_target] = entry
            json.dump(report, open(qa_path, "w", encoding="utf-8"), indent=2)

            score = res.get("score", "-")
            canon_res = res.get("canon", {})
            c_pass = canon_res.get("pass", False)
            failed_must = canon_res.get("failed_must", [])
            found_must_not = canon_res.get("found_must_not", [])
            print(f"  Result: Score {score}/10 | Canon: {'PASS' if c_pass else 'FAIL'}")
            if failed_must:
                print(f"  Failed must: {failed_must}")
            if found_must_not:
                print(f"  Found must_not: {found_must_not}")
        print("\nQA audit complete. Results saved to qa.json.")
        return

    # GENERATION + QA MODE
    for s in shots:
        frame = os.path.join(ROOT, "art", "frames", f"{s['id']}.jpg")
        if not os.path.exists(frame):
            print(f"{s['id']}: no frame at {frame}, skipped")
            continue
        prompt = build_prompt(s, data, canon_data, b06_lines)
        for t in range(a.takes):
            n = 1
            while os.path.exists(os.path.join(out, f"{s['id']}_v{n:02d}.png")):
                n += 1
            dest = os.path.join(out, f"{s['id']}_v{n:02d}.png")
            print(f"\nGenerating {s['id']} take {t+1}/{a.takes} -> {os.path.basename(dest)}...")
            try:
                img = paint(client, types, a.model, prompt, frame, a.aspect)
            except Exception as e:
                print(f"{s['id']}: generation failed: {str(e)[:300]}")
                break
            with open(dest, "wb") as f:
                f.write(img)
            entry = {"frame": os.path.basename(frame), "model": a.model}
            if not a.no_qa:
                try:
                    entry["qa"] = qa(client, types, a.qa_model, dest, frame, s["id"], canon_data, b06_lines)
                except Exception as e:
                    entry["qa"] = {"error": str(e)[:300]}
            report[os.path.basename(dest)] = entry
            json.dump(report, open(qa_path, "w", encoding="utf-8"), indent=2)
            score = entry.get("qa", {}).get("score", "-")
            canon_res = entry.get("qa", {}).get("canon", {})
            c_pass = canon_res.get("pass", False)
            print(f"{s['id']}: wrote {os.path.basename(dest)} (Score {score}, Canon: {'PASS' if c_pass else 'FAIL'})")
            time.sleep(15)


if __name__ == "__main__":
    main()

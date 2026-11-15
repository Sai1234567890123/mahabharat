"""Stage 1 of ep01 (approved by sai 2026-11-15 as 'go stage 1'): passport reference images only.

Calls gemini-2.5-flash-image on Vertex AI. Needs gcloud ADC (run on the PC: gcloud auth application-default login).
Each call is logged to studio/log.md. Run one job at a time; the script stops at the first error.
Usage: python studio/tools/gen_stage1.py --project cs-project-07zg2j2c --dry-run
"""
import argparse, base64, json, subprocess, pathlib, datetime, urllib.request

STUDIO = pathlib.Path(__file__).resolve().parent.parent
JOBS = [
    ("cast/karna/hero.png", "Karna, the archer of Kurukshetra. Full body, neutral grey background, calm pose, bow Vijaya held low. " ),
    ("cast/arjuna/turnaround_front.png", "Arjuna, front view, full body, same character as the reference image, same face, grey background."),
]
PASSPORT = {
    "cast/karna/hero.png": "cast/karna/passport.md",
    "cast/arjuna/turnaround_front.png": "cast/arjuna/passport.md",
}
REFS = {"cast/arjuna/turnaround_front.png": "cast/arjuna/ref_SH170_v09.png"}

def descriptor(path):
    import re
    txt = (STUDIO / path).read_text()
    return re.search(r"## Descriptor.*?\n\n(.+?)\n", txt, re.S).group(1).strip()

def style():
    import re
    return re.search(r"> (Painterly stylized CG animation still.+?)\n", (STUDIO / "bible.md").read_text(), re.S).group(1).strip()

def call(project, prompt, ref=None):
    import shutil
    gcloud = shutil.which("gcloud") or shutil.which("gcloud.cmd") or "gcloud"  # Windows installs gcloud as gcloud.cmd
    tok = subprocess.run([gcloud, "auth", "application-default", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
    parts = [{"text": prompt}]
    if ref:
        parts.append({"inline_data": {"mime_type": "image/png", "data": base64.b64encode((STUDIO / ref).read_bytes()).decode()}})
    body = {"contents": [{"role": "user", "parts": parts}], "generationConfig": {"responseModalities": ["IMAGE"]}}
    url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{project}/locations/us-central1/publishers/google/models/gemini-2.5-flash-image:generateContent"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--project", required=True); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    for out, brief in JOBS:
        prompt = f"{style()}\n\n{descriptor(PASSPORT[out])}\n\n{brief}\n\nno text, no extra characters."
        if a.dry_run:
            print("---", out, "\n", prompt[:400], "...\n"); continue
        res = call(a.project, prompt, REFS.get(out))
        data = [p for c in res["candidates"] for p in c["content"]["parts"] if "inlineData" in p][0]["inlineData"]["data"]
        (STUDIO / out).parent.mkdir(parents=True, exist_ok=True)
        (STUDIO / out).write_bytes(base64.b64decode(data))
        usage = res.get("usageMetadata", {})
        with open(STUDIO / "log.md", "a") as f:
            f.write(f"| {datetime.date.today()} | {out} | gemini-2.5-flash-image | stage1 v1 | tokens out {usage.get('candidatesTokenCount')} (about $0.039) | pending review |\n")
        print("wrote", out)

"""Step 2 of the trailer plan: character sheets in the concept-art look (Nano Banana 2.1 = gemini-3.1-flash-image).

Each job sends the passport descriptor plus sai's own concept paintings as references and writes cast/<tag>/sheet.png.
Needs gcloud ADC on the PC. One call per job, no automatic retries of billed calls. Every call is logged to studio/log.md.

Usage:
  python studio/tools/gen_sheets.py --project cs-project-07zg2j2c --dry-run
  python studio/tools/gen_sheets.py --project cs-project-07zg2j2c --only karna,arjuna,krishna
"""
import argparse, base64, datetime, json, pathlib, re, shutil, subprocess, sys, urllib.error, urllib.request

STUDIO = pathlib.Path(__file__).resolve().parent.parent
MODEL = "gemini-3.1-flash-image"
SHEET = ("Character design painting of ONE person, full body from the top of the crown to the feet, standing calm in a "
         "three-quarter front view, weapon held low. Classical academic oil painting, the same painting style, brushwork, "
         "lighting and level of carved gold detail as the attached reference paintings. Realistic anatomy and face. "
         "Plain warm cream studio backdrop like an unpainted canvas, soft floor shadow only: no scenery, no chariot, no other people, "
         "no frame, no border. No text, no captions, no watermarks, no signature. No flat cartoon, no cel shading, no vector look.")
JOBS = {
    "karna": dict(out="cast/karna/sheet.png", passport="cast/karna/passport.md",
                  refs=["refs/concept/concept_46.jpeg", "refs/concept/concept_37.jpeg"],
                  brief="Use the references for this man's face, build, crown, armour style and bow. Costume exactly as described above: "
                        "saffron-orange dhoti, sun-face relief on the chest, no earrings."),
    # draft look after sai's reference pictures (2026-11-15); run only with sai's go. Never overwrites the locked sheet.png
    "karna_v3": dict(out="cast/karna/sheet_v3.png", passport="cast/karna/passport_v3_draft.md",
                     refs=["refs/concept/concept_46.jpeg", "refs/concept/concept_37.jpeg"],
                     brief="Use the references ONLY for the crown, the carved gold armour, the sun-face disc and the bow. Do NOT copy the "
                           "face, moustache or heavy build from the references. Face, hair, beard and build exactly as described above: "
                           "a leaner man in his late thirties with long flowing hair and a short trimmed beard, no moustache-only face, "
                           "no earrings, a deep crimson sash over the left shoulder, saffron-orange dhoti."),
    "arjuna": dict(out="cast/arjuna/sheet.png", passport="cast/arjuna/passport.md",
                   refs=["refs/concept/concept_05.jpeg", "refs/concept/concept_42.jpeg"],
                   brief="Use the first reference for this man's face, crown, armour and bow; the second shows him small on his chariot. "
                         "Costume exactly as described above: deep green sash over a white dhoti."),
    "krishna": dict(out="cast/krishna/sheet.png", passport="cast/krishna/passport.md",
                    refs=["refs/concept/concept_28.jpeg", "refs/concept/concept_13.jpeg"],
                    brief="Use the references for his face, blue skin, crown and ornaments. He holds black leather reins loosely in one hand."),
    # run only after cast/arjuna/sheet.png is approved
    "arjuna_bare": dict(out="cast/arjuna_bare/sheet.png", passport="cast/arjuna_bare/passport.md",
                        refs=["cast/arjuna/sheet.png", "refs/concept/concept_05.jpeg"],
                        brief="The first reference is the approved sheet of this same man. Same face, body and costume, but without the crown, "
                              "as described above."),
}

def descriptor(path):
    return re.search(r"## Descriptor.*?\n\n(.+?)\n", (STUDIO / path).read_text(), re.S).group(1).strip()

def mime(p):
    return "image/png" if str(p).lower().endswith(".png") else "image/jpeg"

def call(project, location, prompt, refs, aspect):
    gcloud = shutil.which("gcloud") or shutil.which("gcloud.cmd") or "gcloud"
    tok = subprocess.run([gcloud, "auth", "application-default", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
    parts = [{"inline_data": {"mime_type": mime(r), "data": base64.b64encode((STUDIO / r).read_bytes()).decode()}} for r in refs]
    parts.append({"text": prompt})
    gen = {"responseModalities": ["IMAGE"]}
    if aspect:
        gen["imageConfig"] = {"aspectRatio": aspect}
    host = "aiplatform.googleapis.com" if location == "global" else f"{location}-aiplatform.googleapis.com"
    url = f"https://{host}/v1/projects/{project}/locations/{location}/publishers/google/models/{MODEL}:generateContent"
    req = urllib.request.Request(url, data=json.dumps({"contents": [{"role": "user", "parts": parts}], "generationConfig": gen}).encode(),
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json", "x-goog-user-project": project})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=300).read())
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode(errors="replace")[:2000]); raise SystemExit(1)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True); ap.add_argument("--location", default="global")
    ap.add_argument("--only", default="karna,arjuna,krishna"); ap.add_argument("--aspect", default="3:4")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    for name in a.only.split(","):
        j = JOBS[name]
        missing = [r for r in j["refs"] if not (STUDIO / r).exists()]
        if missing:
            print("missing reference", missing); sys.exit(1)
        out = STUDIO / j["out"]
        if out.exists():
            print("exists, not overwriting (folder law 1):", j["out"]); sys.exit(1)
        prompt = f"{SHEET}\n\n{descriptor(j['passport'])}\n\n{j['brief']}"
        if a.dry_run:
            print("---", name, "->", j["out"], "| refs:", j["refs"], "\n", prompt, "\n"); continue
        res = call(a.project, a.location, prompt, j["refs"], a.aspect)
        imgs = [p for c in res.get("candidates", []) for p in c.get("content", {}).get("parts", []) if "inlineData" in p]
        if not imgs:
            print("no image returned:", json.dumps(res)[:1500]); sys.exit(1)
        out.write_bytes(base64.b64decode(imgs[0]["inlineData"]["data"]))
        u = res.get("usageMetadata", {})
        with open(STUDIO / "log.md", "a") as f:
            f.write(f"| {datetime.date.today()} | {j['out']} | {MODEL} | sheets v1 (concept-art look) | tokens in {u.get('promptTokenCount')} out {u.get('candidatesTokenCount')} | pending review |\n")
        print("wrote", j["out"], "usage", u)

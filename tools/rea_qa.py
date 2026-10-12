"""Project QA with REA (https://github.com/morluto/rea). No cloud calls, no credits.

Checks:
  1. pages    Loads index.html and motion_preview.html in headless Chromium through
              `rea capture-browser-scenario` and fails on any local 404 or page error.
  2. pipeline Re-runs make_shots.py + docs_from_shots.py in a temp copy under
              `rea capture-process` and fails if shots.json, 05 or 06 differ from the repo
              (catches hand edits that the next render_all.sh would silently revert).
  3. handoff  Compares video_handoff_pilot.zip with video_handoff/ file by file
              (via `rea inspect-artifact` + the compare_artifacts MCP tool),
              ignoring CRLF/LF-only differences.

Usage:  python3 tools/rea_qa.py [pages] [pipeline] [handoff]
Needs:  npm install --global rea-agents@6.4.0 ; a Chromium (set CHROME=/path if not found).
Writes screenshots and raw Evidence JSON to qa/rea/ (git-ignored).
"""
import collections
import glob
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import zipfile
from functools import partial

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "qa", "rea")
PRE = os.path.join(ROOT, "preproduction")


def rea(*args):
    r = subprocess.run(["rea", *args, "--format", "json"], capture_output=True, text=True)
    return json.loads(r.stdout)


def rea_mcp(tool, arguments):
    """Calls one REA MCP tool over stdio (for tools the CLI does not expose)."""
    p = subprocess.Popen(["rea", "mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True)

    def send(m):
        p.stdin.write(json.dumps(m) + "\n")
        p.stdin.flush()

    def recv(i):
        for line in p.stdout:
            m = json.loads(line)
            if m.get("id") == i:
                return m

    send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "rea_qa", "version": "1"}}})
    recv(1)
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": tool, "arguments": arguments}})
    res = recv(2)["result"]
    p.stdin.close()
    p.terminate()
    return res.get("structuredContent") or json.loads(res["content"][0]["text"])


def find_chrome():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for pat in ["/opt/pw-browsers/chromium-*/chrome-linux/chrome",
                os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux/chrome"),
                "/usr/bin/chromium", "/usr/bin/google-chrome",
                r"C:\Program Files\Google\Chrome\Application\chrome.exe"]:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    sys.exit("No Chromium found; set CHROME=/path/to/chrome")


def find_png(o):
    if isinstance(o, dict):
        if "data_base64" in o:
            return o
        for v in o.values():
            r = find_png(v)
            if r:
                return r


def check_pages():
    import base64
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = socketserver.TCPServer(("127.0.0.1", 0), partial(Quiet, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    chrome, problems = find_chrome(), []
    for page in ["index.html", "motion_preview.html"]:
        scen = {"browser": {"mode": "launch", "executable_path": chrome},
                "start_url": {"url": f"{base}/{page}"},
                "actions": [{"step_id": "settle", "action": "wait_for_timeout", "duration_ms": 3000}],
                "capture": {"at_end": ["screenshot", "url"], "events": ["console", "page-errors", "network"]},
                "environment": {"viewport": {"width": 1280, "height": 900, "device_scale_factor": 1}}}
        path = os.path.join(OUT, f"scenario_{page}.json")
        json.dump(scen, open(path, "w"))
        ev = rea("capture-browser-scenario", path)
        json.dump(ev, open(os.path.join(OUT, f"capture_{page}.json"), "w"))
        items = ev["normalized_result"]["events"]["items"]
        bad = collections.Counter(e["url"]["url"].split("?")[0].replace(base + "/", "")
                                  for e in items if e.get("kind") == "response" and (e.get("status") or 0) >= 400
                                  and e["url"]["url"].startswith(base) and not e["url"]["url"].endswith("favicon.ico"))
        errs = [e for e in items if e.get("kind") in ("page-error", "pageerror")]
        png = find_png(ev["normalized_result"]["steps"][-1]["artifacts"].get("screenshot", {}))
        if png:
            open(os.path.join(OUT, f"{page}.png"), "wb").write(base64.b64decode(png["data_base64"]))
        print(f"  {page}: {len(items)} events, {sum(bad.values())} local 404s, {len(errs)} page errors")
        for u, n in bad.most_common(5):
            problems.append(f"{page}: 404 x{n} {u}")
        problems += [f"{page}: page error {json.dumps(e)[:200]}" for e in errs]
    srv.shutdown()
    return problems


def check_pipeline():
    work = tempfile.mkdtemp(prefix="rea_qa_")
    for d in ("scripts", "data"):
        shutil.copytree(os.path.join(PRE, d), os.path.join(work, d))
    scen = {"executable": sys.executable,
            "arguments": ["-c", "import runpy; runpy.run_path('scripts/make_shots.py', run_name='__main__'); "
                                "runpy.run_path('scripts/docs_from_shots.py', run_name='__main__')"],
            "working_directory": work, "filesystem_observation_paths": [work], "timeout_ms": 60000}
    path = os.path.join(OUT, "scenario_pipeline.json")
    json.dump(scen, open(path, "w"))
    ev = rea("capture-process", path)
    json.dump(ev, open(os.path.join(OUT, "capture_pipeline.json"), "w"))
    code = ev["normalized_result"]["exit"]["code"]
    problems = [] if code == 0 else [f"pipeline exited with {code}"]
    for rel in ("data/shots.json", "05-shot-list.md", "06-prompt-pack.md"):
        a, b = os.path.join(PRE, rel), os.path.join(work, rel)
        same = (json.load(open(a)) == json.load(open(b))) if rel.endswith(".json") else open(a).read() == open(b).read()
        print(f"  {rel}: {'matches' if same else 'DIFFERS from a fresh regeneration'}")
        if not same:
            problems.append(f"{rel} differs from what make_shots.py/docs_from_shots.py produce")
    shutil.rmtree(work)
    return problems


def check_handoff():
    zpath, folder = os.path.join(PRE, "video_handoff_pilot.zip"), os.path.join(PRE, "video_handoff")
    fresh = os.path.join(tempfile.mkdtemp(prefix="rea_qa_"), "handoff_now.zip")
    with zipfile.ZipFile(fresh, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, dirs, files in os.walk(folder):
            for d in sorted(dirs):
                z.write(os.path.join(dirpath, d), os.path.relpath(os.path.join(dirpath, d), folder) + "/")
            for f in sorted(files):
                full = os.path.join(dirpath, f)
                z.write(full, os.path.relpath(full, folder))
    inv = [rea("inspect-artifact", p)["normalized_result"]["substeps"][0]["evidence"] for p in (zpath, fresh)]
    res = rea_mcp("compare_artifacts", {"left": inv[0], "right": inv[1]})["normalized_result"]
    json.dump(res, open(os.path.join(OUT, "compare_handoff.json"), "w"))
    print(f"  REA summary: {res['summary']}")
    problems, old = [], zipfile.ZipFile(zpath)
    for c in res["changes"]:
        p = c["logical_path"]
        if p == "." or p.endswith("/") or "content" not in c.get("dimensions", ["content"]):
            continue
        if c["classification"] == "changed" and p in old.namelist():
            a = old.read(p).replace(b"\r\n", b"\n")
            b = open(os.path.join(folder, p), "rb").read().replace(b"\r\n", b"\n")
            if a == b:
                print(f"  {p}: line endings only")
                continue
        problems.append(f"handoff zip {c['classification']}: {p}")
    return problems


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    checks = {"pages": check_pages, "pipeline": check_pipeline, "handoff": check_handoff}
    problems = []
    for name in (sys.argv[1:] or checks):
        print(f"[{name}]")
        problems += checks[name]()
    print("\n" + ("\n".join("FAIL " + p for p in problems) if problems else "All REA checks passed."))
    sys.exit(1 if problems else 0)

"""Inject shots.json into animatic.html (between the /*SHOTS*/ and /*ACTS*/ markers)."""
import json, re, sys, pathlib
ep = pathlib.Path(sys.argv[1])
d = json.loads((ep / "shots.json").read_text())
keep = [{k: s[k] for k in ("id", "dur", "action", "camera", "panel")} for s in d["shots"]]
h = (ep / "animatic.html").read_text()
h = re.sub(r"const SHOTS = /\*SHOTS\*/.*?;\n", "const SHOTS = /*SHOTS*/" + json.dumps(keep).replace("\\", "\\\\") + ";\n", h, count=1)
h = re.sub(r"const ACTS = /\*ACTS\*/.*?;\n", "const ACTS = /*ACTS*/" + json.dumps(d["acts"]).replace("\\", "\\\\") + ";\n", h, count=1)
(ep / "animatic.html").write_text(h)
print("injected", len(keep), "shots")

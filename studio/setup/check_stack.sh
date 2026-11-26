#!/usr/bin/env bash
# Prints what is installed and renders one EEVEE test frame. Run from the repo root.
export EGL_PLATFORM=surfaceless
for t in ffmpeg sox rhubarb; do printf "%-8s " "$t"; command -v "$t" >/dev/null && echo ok || echo MISSING; done
python3 - <<'PY'
import importlib
for m in ["bpy", "numpy", "PIL", "scipy", "soundfile", "opentimelineio"]:
    try:
        mod = importlib.import_module(m); print(f"{m:15} ok", getattr(mod, "__version__", ""))
    except Exception as e:
        print(f"{m:15} MISSING ({e.__class__.__name__})")
PY
python3 "$(dirname "$0")/eevee_test.py" /tmp/eevee_test.png 2>&1 | grep -E "EEVEE|Error" | grep -v EGL_BAD_MATCH

#!/bin/bash
# Render every pilot shot and the character lineup, then composite.
# Usage: ./render_all.sh [width] [samples]
# BPY_PYTHON can point at Blender's python or a venv with `pip install bpy`.
set -e
cd "$(dirname "$0")"
W=${1:-1920}
S=${2:-12}
PY=${BPY_PYTHON:-python3}
python3 make_shots.py
for id in $(python3 -c "import json;print(' '.join(s['id'] for s in json.load(open('../data/shots.json'))['shots']))"); do
  echo "render $id"
  $PY blockout.py --shot "$id" --out ../art/render --width "$W" --samples "$S" > /dev/null
done
$PY blockout.py --lineup --out ../art/render --width "$W" --samples "$S" > /dev/null
python3 compose.py --all --control
python3 sheets.py
python3 docs_from_shots.py

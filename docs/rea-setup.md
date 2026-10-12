# REA (Reverse Engineer Anything) MCP setup

REA is the open source MCP server at https://github.com/morluto/rea (npm package `rea-agents`, MIT).
It gives Claude Code tools to inspect apps, binaries, websites, browser sessions and process runs locally.
It does not generate images, video or audio.

## What is configured

`.mcp.json` at the repo root registers REA for Claude Code, pinned to the version that was tested:

```json
{
  "mcpServers": {
    "rea": { "command": "npx", "args": ["-y", "rea-agents@6.4.0", "mcp"] }
  }
}
```

Claude Code asks once to approve project MCP servers the first time it opens the repo.
No API keys or secrets are needed.

## Install commands (as run on 2026-10-12)

Requires Node.js 22.19+ or 24.11+.

```bash
npm install --global rea-agents@6.4.0   # puts `rea` on PATH
rea --version                           # 6.4.0
rea doctor --json                       # read-only health check
```

Optional, only for native binary decompiling: Hopper (commercial), Ghidra 12.1.x with JDK 21
(`export GHIDRA_INSTALL_DIR=...`), or IDA. None of these are needed for the web, process and
artifact-comparison tools this project would use.

## Windows (sai's PC)

REA issue #1066 notes that a bare `npx` in MCP configs can fail on native Windows.
If the server does not start there, change the entry to:

```json
"rea": { "command": "cmd", "args": ["/c", "npx", "-y", "rea-agents@6.4.0", "mcp"] }
```

Or run `npx --yes rea-agents@6.4.0 setup`, which detects installed agents and writes their config.

## Verified

`rea mcp` started over stdio, reported server `rea` 6.4.0 and listed 170 tools
(for example `inspect_web_page`, `capture_web_screenshot`, `capture_process_scenario`,
`compare_process_captures`, `compare_artifacts`, `analyze_javascript_application`).

## How this project uses REA

`python3 tools/rea_qa.py` runs three local checks (no cloud calls, no credits) and exits non-zero on any problem.
It writes screenshots and raw Evidence JSON to `qa/rea/`, which git ignores.

| Check | REA tool | What it catches |
|---|---|---|
| `pages` | `capture-browser-scenario` | Broken image or video paths, 404s and JS errors on `index.html` and `motion_preview.html`, plus a screenshot of each page |
| `pipeline` | `capture-process` | Hand edits to `data/shots.json`, `05` or `06` that the next `render_all.sh` would silently overwrite |
| `handoff` | `inspect-artifact` + `compare_artifacts` | `video_handoff_pilot.zip` drifting from `video_handoff/` before it goes to Veo |

Run it before a commit that touches the pages, `shots.json` or the handoff folder.

Other REA tools worth using by hand from Claude Code:
- `analyze_web_bundle` lists every backend call a page makes (it found `/api/reiterate` and `/api/compare` in `index.html`).
- `compare_web_screenshots` gives a pixel diff of a page before and after a change.
- `compare_process_captures` diffs two runs of any script (for example two `paint_over.py` runs) across output, exit code and files written.
- `capture_process_scenario` with `filesystem_observation_paths` records exactly which files a Blender or ffmpeg run created.

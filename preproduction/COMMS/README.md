# Agent communication protocol

Three parties work on this repo:

- **Sai** (the human) sets the goals, approves hero work and decides anything creative.
- **Claude** (Claude Code, on Sai's PC) runs the pipeline: Blender renders, Unreal Engine scenes, data and scripts.
- **Antigravity** (the Antigravity IDE agent, opened on this repo) takes delegated writing and repo tasks: docs, prompt packs, review passes and code cleanup.

They never talk directly. They talk through files in this folder, so every step is visible in git.

## Folders

| Path | Who writes | Purpose |
|---|---|---|
| `COMMS/tasks/` | Claude (creates), Antigravity (updates status) | One file per task, named `T-NNN-short-slug.md` |
| `COMMS/reports/` | Antigravity and Claude | Results: `R-NNN-short-slug.md`, one per finished task |
| `COMMS/log.md` | both | Append-only log, newest at the bottom, one line per event |
| `COMMS/PLAN.md` | Claude | The current plan and task order. Sai can edit it. |

## Task file format

Each task file starts with a header block, then a body:

```
---
id: T-001
owner: antigravity | claude | sai
status: todo | doing | blocked | review | done
created: 2026-10-10
depends_on: []
---
## Goal
One or two sentences on the outcome.

## Inputs
Files to read, with paths relative to the repo root.

## Steps
Numbered, concrete steps.

## Done when
A checkable condition, for example "docs/xx.md exists and `python scripts/check.py` passes".

## Do not
Things that are out of bounds (for example: do not touch `art/` or `data/shots.json`).
```

## Rules

1. **One owner per task.** Only the owner edits the task's status. Others comment in the report.
2. **Status changes are the handshake.** Antigravity sets `doing` when it starts and `review` when it's finished. Claude picks up `review` tasks, checks them against "Done when", and sets `done` or reopens them as `todo` with a note.
3. **Reports go in `COMMS/reports/`**, not in the task file. A report lists the files changed, the checks run and anything blocked.
4. **Log every status change** in `COMMS/log.md`, one line: `YYYY-MM-DD HH:MM | T-001 | owner | status | note`.
5. **Do not edit each other's files mid-task.** If a task needs a change to an output owned by someone else, write a new task for them.
6. **Blender and Unreal outputs go to `art/` and `unreal/` only after Sai approves a hero shot.** Working renders go to a scratch folder.
7. **Creative decisions belong to Sai.** Anything that changes the story, the look, or the style bible becomes a `blocked` task with a question in the report.
8. **Never copy film frames** into this repo, and never use them as model inputs. Analysis only, as in `trailer-analysis/`.
9. **Commit in small steps** with the task id in the message, for example `T-004: add prompt pack for SH010`.
10. **Reassigning a task:** set it to `blocked` with a note in the log, and wait for the current owner to confirm in the log before the new owner starts. This stops two agents doing the same task at once.
11. **Shared files** (`data/canon_checks.json`, `data/shots.json`, `scripts/paint_over.py`) have one owner at a time: whoever holds the task that changes them. Re-read the file just before editing it.

## How Sai starts a task for Antigravity

1. Open this repo in Antigravity.
2. Tell its agent: "Read COMMS/README.md, then do every task in COMMS/tasks/ whose owner is antigravity and status is todo."
3. When it reports `review`, ask Claude in the project thread to check it. Claude will read the report and mark it done.

## How Claude picks up work

Claude reads `COMMS/tasks/`, `COMMS/reports/` and `COMMS/log.md` at the start of each session. It creates new tasks for Antigravity when a step is text, docs or repo work, and does Blender and Unreal work itself.

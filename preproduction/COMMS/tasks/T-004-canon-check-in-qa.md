---
id: T-004
owner: claude
status: done
created: 2026-10-10
depends_on: []
---
## Goal
Make the QA step in `scripts/paint_over.py` check each frame against the epic, not only the style.

## Inputs
- `scripts/paint_over.py` (`QA_CHECKLIST` and `qa()`)
- `data/canon_checks.json`
- `../mahabharat-site/source/B06-bhishma.txt` (the shot's `source` lines)

## Steps
1. For each shot, load its entry from `canon_checks.json` plus the `global` rules, and read the cited lines from `B06-bhishma.txt`.
2. Add those to the QA prompt. Ask the reviewer for a `canon` object: `{"pass": bool, "failed_must": [...], "found_must_not": [...]}`.
3. A frame with `canon.pass == false` is rejected, whatever its style score.
4. Keep the existing style fields as they are.
5. Add a `--qa-only` flag that re-scores existing frames without repainting, and run it on the current 8 hero frames. Put the results in the report; they should match R-003.

## Done when
`python scripts/paint_over.py --qa-only --shots SH010,...` writes a `canon` result for each hero frame to `qa.json`, and the failures it finds agree with R-003.

## Do not
Change the paint model or the style checks. Put API keys in the repo.

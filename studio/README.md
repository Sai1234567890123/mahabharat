# studio

The directing folder for the Mahabharat battle shorts. Start with `bible.md`.

- `bible.md`: the two folder laws, world, engine, tone, palette, never list.
- `cast/`: one passport per character. Descriptors are pasted verbatim into every prompt.
- `episodes/ep01/`: Arjuna and Karna, 90 seconds, 24 shots.
  - `shots.json` is the single source of truth. `python3 studio/tools/build_docs.py ep01` rebuilds `shots.md`, `prompts.md`, `script.md` and `shots.js`.
  - `animatic.html` is the zero-cost animatic (open it in a browser, click to play). `node studio/tools/record_animatic.js ep01` records `animatic.mp4`.
  - `quote.md` is the price of the paid steps. Nothing is generated before sai's go.
- `.claude/agents/`: the seven roles (showrunner, designer, storyboarder, reviewer, renderer, editor, publisher).
- `frames/`, `renders/`, `selects/`: empty until generation starts.
- `log.md`: one line per generation attempt.

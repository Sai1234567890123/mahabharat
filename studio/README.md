# Studio

The article-style studio for Mahabharat battle shorts: direct on paper and in stills first, lock the characters with passports, draft cheap, approve before a final, log every generation. Read `bible.md` first.

- `pipeline.md`: the twelve steps every episode goes through, the shot grades, and where each episode stands. Start here.
- `research/epic_film_pipelines.md`: the research behind the pipeline (how epic, mythological and animated films and series are made).
- `bible.md`: the two folder laws, world, tone, palette, style prompt, never-list.
- `cast/<tag>/passport.md`: one locked descriptor per character, pasted verbatim into every prompt. Variants are separate passports.
- `episodes/ep01_arjuna_vs_karna/`: `shots.json` (source of truth, with each shot's grade and canon lines), `shots.md`, `canon_check.md`, `frame_prompts.md`, `motion_prompts.md`, `animatic.html`, `animatic.mp4`, `quote.md`.
- `frames/`, `renders/`, `selects/`: empty until sai approves the quote.
- `log.md`: every generation, including free ones.

Rebuild after editing `shots.json`:

```
python studio/tools/build_docs.py studio/episodes/ep01_arjuna_vs_karna
python studio/tools/build_animatic_data.py studio/episodes/ep01_arjuna_vs_karna
node studio/tools/record_animatic.js studio/episodes/ep01_arjuna_vs_karna/animatic.html studio/episodes/ep01_arjuna_vs_karna/animatic.mp4 30
```

The crew is in `.claude/agents/` (showrunner, designer, storyboarder, reviewer, renderer, editor, publisher).

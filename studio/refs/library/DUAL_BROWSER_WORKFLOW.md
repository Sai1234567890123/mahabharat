# 2-Stage Dual-Browser Triage & Inspection Workflow

Use this workflow for large reference batches (Instagram Saved Reels beyond `#265`, or 25+ Fab listings).

---

## Stage 1 — Grid Harvesting & Cheap Triage (1 Agent, 1 Browser)
1. Use **1 browser agent** on your primary Chrome (`port 9222`).
2. Scroll the Instagram Saved grid once from top to bottom into a `Map` (no video downloads, no opening individual reels).
3. Tag each pending item (`LOOK`, `STAGING`, `FX`, `STORY`, `SKIP`) and score `1–3` for S1E01 / EP01 relevance.
4. Save to `studio/refs/library/triage_XXX.csv`.

---

## Stage 2 — Split Heavy Per-Page Inspections (2 Agents, 2 Browsers, 2 Accounts)
1. Split the high-value Score-3 list cleanly in half:
   ```powershell
   python studio/refs/library/split_stage2_batches.py --input studio/refs/library/triage_229.csv --min-score 3 --mode instagram
   ```
   *(For Fab listings, pass `--mode fab`.)*
2. Launch the isolated second browser & second Antigravity window:
   ```powershell
   .\studio\refs\library\launch_browser2.ps1 -StartUrl "https://www.instagram.com"
   .\launch_gemini_agent2.ps1
   ```
3. Paste `studio/refs/library/stage2_batches/stage2_agent1_prompt.md` into **Account #1** (Chrome `9222`) and `stage2_agent2_prompt.md` into **Account #2** (Chrome `9223`).

### Pacing Rules
- **Fab.com / public docs:** Both agents can run at full speed (1 tool call per turn, read-only).
- **Instagram (same IG account in both browsers):** Keep each agent opening **1 page at a time** (~2s pause between navigations) to avoid Instagram rate-limiting.
- **On any `429 / RESOURCE_EXHAUSTED`:** Stop immediately and report progress.

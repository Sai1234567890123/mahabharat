# Handoff: motion clips for the pilot "The First Conch"

For: Antigravity agent, running on sai's Windows PC in `C:\Users\dharm\OneDrive\Desktop\claude projects\mahabharat-preproduction`.

## Final goal

Eight short motion clips, one per picked keyframe in `art/selected/`, saved as `art/motion/SHxxx.mp4`, reviewed by sai, with a short review note. Clip list and timing come from `data/shots.json`, read through `scripts/animate.py`.

## Where things stand

- Keyframes are done. `art/selected/` holds the 8 picks: SH010_v01, SH050_v03, SH070_v02, SH090_v01, SH130_v02, SH150_v02, SH170_v02, SH180_v01.
- `scripts/animate.py` is written and reaches the Vertex AI API correctly. Dry run: `python scripts\animate.py --dry-run` (8 clips, 36 generated seconds).
- Blocker: Veo returns 404 NOT_FOUND for `veo-3.0-generate-001` in `us-central1` on project `aiautomationplatform`. The Model Garden page lists the model, so the cause is project access (Veo not enabled, billing not linked, or an access request needed). The code is not the problem. Fast variants also returned 404.

## Step 1: Clear the Veo access blocker (sai, in the Google Cloud console)

1. Open Vertex AI, then Agent Studio, and try "Generate videos" with any still image. If it works there, copy the model name and region it uses into `animate.py`.
2. Check Billing: the project `aiautomationplatform` must have a billing account linked and the $300 credit active.
3. If Veo is gated, request access from the console and stop here until it is granted.
4. Re-test one shot: `python scripts\animate.py --shot SH050`. Success means `art/motion/SH050.mp4` exists and `art/motion/log.json` has a `file` entry, not an `error`.

## Step 2a: If Veo works

1. Check the Vertex AI pricing page for the Veo model. Estimate the cost for 36 seconds before the full run.
2. Ask sai to approve the spend in chat. Do not run the full set without that approval.
3. Run `python scripts\animate.py`. It saves every clip and writes `art/motion/log.json`.
4. Review each clip against its still. Note artifacts, drift from the still, and whether the motion matches `motion_prompt`. Write the notes to `art/motion/REVIEW.md`.

## Step 2b: If Veo stays blocked (free, local fallback)

Make the clips with a 2D camera move (parallax push, pan or dolly) over each keyframe, using the depth and line-art passes from the blockout. No cloud calls are needed.

1. Find the depth pass and line-art pass for each shot in `art/` (check the file names first; do not assume them).
2. Write `scripts/parallax.py` that takes the still plus depth pass, applies a slow camera move matching the shot's camera in `data/shots.json`, and writes `art/motion/SHxxx.mp4` at the shot's duration (4, 6 or 8 seconds, 16:9).
3. Keep the same output names so the review step works unchanged.
4. Tell sai which path was taken (Veo or parallax) in the review note.

## Rules

- Do not paste, print or commit any service account key or token. Use the existing `gcloud auth application-default login` session on the PC.
- Do not try to get around the org policy (no key creation, no changes to IAM).
- Do not run the full Veo set without a pricing check and sai's yes.
- Commit only generated files and scripts to the repo. Keep large media out of git unless sai asks for it.

## Done means

- `art/motion/` has 8 `SHxxx.mp4` files, or the parallax fallback has produced them.
- `art/motion/log.json` shows no errors for the shots that were run.
- `art/motion/REVIEW.md` lists each clip with a keep, redo or drop verdict.

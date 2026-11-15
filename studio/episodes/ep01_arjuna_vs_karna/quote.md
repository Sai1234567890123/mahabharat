# Cost quote: The Anjalika (90 s) · waiting for sai's approval

Nothing below has been generated. No money has been spent. Rates were read from Google's Vertex AI pricing page on 2026-11-15, and `veo-3.1-generate-001`, `veo-3.1-fast-generate-001` and `gemini-2.5-flash-image` are listed on the project. Still unconfirmed: quota, and that the trial credit pays for these calls. **Check both in the console before the first run** (rule 1 of `10-cost-and-safety-rules.md`). Billing would come from the new GCP trial credit (about $300, project `cs-project-07zg2j2c`).

| Stage | What | Count | Unit rate (estimate) | Estimate |
|---|---|---|---|---|
| 1. Passports | Karna hero image (4 tries), Karna turnaround (3), Arjuna turnaround from SH170 (3). Crops are made locally for free. | 10 images | Gemini image, $0.039 each | about $0.40 |
| 2. Starting frames | 22 shot frames, up to 3 tries each. Impact frames A01, A07, A20 are drawn in 2D for free. | up to 66 images | $0.039 each | about $2.60 |
| 3. Motion drafts | 22 shots, image-to-video, about 5 s each, 2 takes, no audio | about 220 s of video | Veo 3.1 Fast 720p no sound, $0.08 per second | about $18 |
| 4. Hero finals | 8 hero shots re-rendered on the full model (A02, A06, A08, A13, A14, A16, A19, A21) | about 48 s | Veo 3.1, $0.20 per second (no sound) | about $10 |
| 5. Sound | Drums, drone, conch: free library sounds first; generated music bed only if needed | 1 to 2 clips | small | under $1 |
| | **Total** | | | **about $32, cap $45** |

Gates, as in the bible: stages run one at a time, I report the real cost after each stage, the daily cap is $15, and nothing passes to stage 3 until a fresh reviewer pass has checked every frame against the passports.

## Picsart route (the article's route)

The Picsart MCP is not connected in this project and needs a Picsart account and credits. If sai wants that route instead: add it on the PC with `claude mcp add --transport http picsart-gen-ai https://api.picsart.com/gen-ai/mcp`, authenticate, and I will quote exact Picsart prices before anything runs.

## What I need from sai

Reply with one of: "go stage 1" (about $0.40, Karna and Arjuna references only), "go stages 1-2" (about $3), or a different budget.

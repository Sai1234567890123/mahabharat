# EP01 quote: what the paid steps would cost (nothing is spent yet)

Prices are from Google's Vertex AI pricing page, read on 15 Nov 2026. Rupees use the rate of the credit itself (₹28,569 for $300, about ₹95 per dollar). The PC check on 15 Nov found these models listed on project `cs-project-07zg2j2c`: `gemini-2.5-flash-image`, `veo-3.1-fast-generate-001`, `veo-3.1-generate-001`.

| Unit | Price |
|---|---|
| Gemini 2.5 Flash Image, one 1024 px image | $0.039 |
| Veo 3.1 Fast, 720p with sound, per second | $0.10 |
| Veo 3.1 Fast, 1080p with sound, per second | $0.12 |
| Veo 3.1, 720p or 1080p with sound, per second | $0.40 |

The 24 shots need 115 seconds of video. Veo makes clips of 4, 6 or 8 seconds (to be confirmed on the first call), so rounded up that is 124 seconds per full pass.

## Steps, in the order they would run (one billed step at a time)

| Step | What | Count | Cost cap |
|---|---|---|---|
| 1 | Character reference images: Arjuna, Karna, Shalya (hero, 5-view turnaround, 3/4 crop). Krishna reuses his approved images. | up to 30 images | $1.20, about ₹115 |
| 2 | First frame of each of the 24 shots, about 3 attempts each, then a read-only review against the passports | up to 75 images | $3.00, about ₹285 |
| 3 | Draft video, every shot once, Veo 3.1 Fast 720p | 124 s | $12.40, about ₹1,180 |
| 4 | Retakes of the shots that fail review, Veo 3.1 Fast 720p | up to 124 s | $12.40, about ₹1,180 |
| 5 | Finals, Veo 3.1 Fast 1080p | 124 s | $14.90, about ₹1,420 |
| 6 | Edit, impact frames, letterbox, sound mix with ffmpeg | none | 0 |

**Total with every cap used: about $44, about ₹4,200**, from the ₹28,569 credit.

Optional upgrade: finals on full Veo 3.1 instead of Fast is $49.60 a pass (about ₹4,700) instead of $14.90. Worth deciding only after the Fast drafts are seen.

## Not confirmed yet

- Whether the free-trial credit pays for Veo and Gemini image calls. The pricing page does not say. Step 1 is small on purpose: Billing → Reports (group by SKU) after it will show whether the credit absorbed it.
- Veo and image quota on the new project. The first call will show it.
- Clip lengths Veo accepts on this model version.

## Other routes considered

- **Wan 2.2 on the existing L4 VM:** about ₹150 to ₹300 of VM time, but lower quality, no sound, and about an hour of new setup.
- **Picsart, as in the article:** needs sai's own Picsart account and bills Picsart credits, not the Google credit.

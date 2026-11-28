# Stage 2 Per-Page Inspection — Agent 2 (INSTAGRAM)

**Browser:** Chrome Profile 2 (port 9223 via launch_browser2.ps1)
**Account:** Google Pro Account #2 (launch_gemini_agent2.ps1)
**Pacing Rule:** Open 1 Instagram page at a time (~2s pause between navigations) to avoid account throttling.

Rules:
- Strictly ONE `chrome_devtools` tool call per turn.
- Stop immediately on any `429 / RESOURCE_EXHAUSTED` or login/rate-limit wall and report how far you got.
- Do NOT download videos or bypass any auth/CAPTCHA.

URLs assigned to this agent (10 total):

1. https://www.instagram.com/p/DdWkOLdPg9v/ (`STORY` • Score 3) — "Danveer Surya putra Karn" Mahabharat art (EP01 Karna!)
2. https://www.instagram.com/p/Dc1AepAgKLc/ (`STORY` • Score 3) — "When Arjuna charged, Kurukshetra trembled" Mahabharata AI video (direct EP01!)
3. https://www.instagram.com/p/DeULGUrBXzN/ (`STORY` • Score 3) — Virata War: Arjuna alone vs Bhishma, Drona, Karna, Ashwatthama, Duryodhana — Gandiva thunder (EP01!)
4. https://www.instagram.com/p/DeHPKFns4yj/ (`STORY` • Score 3) — Shri Krishna reveals Vishwaroopa to Arjuna (deep research on ornaments, weapons, crowns, composition!)
5. https://www.instagram.com/p/DaqEMkbgPt1/ (`LOOK` • Score 3) — "Kasumi-dera — Mist Temple" Blender + Octaspace (@borisut__) — misty ancient temple atmosphere (S1E01!)
6. https://www.instagram.com/p/DdjJIxmBsuj/ (`LOOK` • Score 3) — "Arcane-inspired painterly animation style" Ramayana Battle of Lanka (direct Eternal War / Arcane target!)
7. https://www.instagram.com/p/DKo88I8tQqY/ (`LOOK` • Score 3) — "What if Mahabharat movie was made in the style of 300?" (Dreamscapes Ep 10 — stylized Epic combat look!)
8. https://www.instagram.com/p/DKj1S1cvPD4/ (`STORY` • Score 3) — "Dreamscapes 10: Karna - Blood & Dharma" saturated orange Blade Runner 2049 / 300 style (EP01 Karna!)
9. https://www.instagram.com/p/C74BSlnIdAc/ (`STORY` • Score 3) — Karna on 17th day cutting Gandiva string 11 times (EP01 beat!)
10. https://www.instagram.com/p/C3prABMP_DA/ (`STORY` • Score 3) — "Karna Arjuna Last Battle" (EP01 climax reference!)

#!/usr/bin/env python3
"""Sound design for Scene 01 "Suryaputra", made in code (numpy only, free): no samples, no AI.

  python studio/tools/scene01_sound.py <out.wav> [--voices <dir>]

Shot starts (s): 1 0, 2 5, 3 10, 4 14, 5 19, 6 24, 7 29, 8 33, 9 38, title 45 to 48.5 (scene01_cut.py timing).
Layers:
  river     a soft bed of filtered noise with slow swells and small laps, shots 1 to 8
  pour      water trickling from his cupped hands, shot 2 from 2.3 s
  birds     dawn chirps, sparse at first and more as the sun rises
  drone     a tanpura-like drone on D (Sa) and A (Pa), plucked in a slow cycle, swelling at sunrise and under the title
  wade      splashes on each step as he wades out, shot 7
  horses    the team stamping (7, 8), then hooves at a gallop and the wheels' rumble (9)
  conch     one long conch call over the title card
  voices    with --voices: Karna/Shalya lines (line1.wav ... line5.wav) placed at the subtitle times, if present
"""
import math, pathlib, sys, wave
import numpy as np

SR = 48000
DUR = 48.5
SHOT = {1: 0, 2: 5, 3: 10, 4: 14, 5: 19, 6: 24, 7: 29, 8: 33, 9: 38, 10: 45}
rng = np.random.default_rng(7)
N = int(SR * DUR)
t = np.arange(N) / SR
L = np.zeros(N); R = np.zeros(N)


def band(x, lo, hi):
    """band-pass by zeroing FFT bins (soft edges)"""
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.clip((f - lo * 0.7) / (lo * 0.3 + 1e-9), 0, 1) if lo > 0 else np.ones_like(f)
    g *= np.clip((hi * 1.3 - f) / (hi * 0.3), 0, 1)
    return np.fft.irfft(X * g, len(x))


def env(a, b, rise=0.5, fall=0.5):
    """0 outside [a, b] seconds, smooth ramps in and out"""
    u = np.clip((t - a) / max(rise, 1e-3), 0, 1) * np.clip((b - t) / max(fall, 1e-3), 0, 1)
    return u * u * (3 - 2 * u)


def place(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N or i + len(sig) <= 0:
        return
    s = sig[: max(0, N - i)]
    gl, gr = gain * math.sqrt((1 - pan) / 2), gain * math.sqrt((1 + pan) / 2)
    L[i:i + len(s)] += s * gl; R[i:i + len(s)] += s * gr


def norm(x):
    return x / (np.abs(x).max() + 1e-9)


# ---- river ---------------------------------------------------------------------------------------------------------------------
bed = norm(band(rng.standard_normal(N), 80, 900)) * 0.5 + norm(band(rng.standard_normal(N), 900, 4000)) * 0.12
swell = 0.75 + 0.25 * np.sin(2 * math.pi * 0.11 * t) * np.sin(2 * math.pi * 0.037 * t + 1)
river = bed * swell * env(0, SHOT[9] + 0.8, 1.5, 1.2)
L += river * 0.16; R += band(np.roll(river, 2400), 60, 4000) * 0.16
for k in range(70):                                                  # small laps against him
    at = rng.uniform(0, SHOT[9]); d = rng.uniform(0.15, 0.4)
    n = int(d * SR); x = band(rng.standard_normal(n), 300, 2200) * np.exp(-np.linspace(0, 6, n)) * np.clip(np.arange(n) / (0.04 * SR), 0, 1)
    place(norm(x), at, 0.05, rng.uniform(-0.5, 0.5))

# ---- the pour in shot 2 --------------------------------------------------------------------------------------------------------
for k in range(160):
    at = SHOT[2] + 2.3 + rng.uniform(0, 2.6)
    n = int(rng.uniform(0.02, 0.06) * SR); tt = np.arange(n) / SR; f0 = rng.uniform(900, 3200)
    drop = np.sin(2 * math.pi * (f0 * tt + 4000 * tt * tt)) * np.exp(-tt * rng.uniform(60, 140))
    place(drop, at, 0.05 * (1 - (at - SHOT[2] - 2.3) / 3.5), rng.uniform(-0.3, 0.3))
trickle = band(rng.standard_normal(int(2.7 * SR)), 1500, 6000) * np.linspace(1, 0.0, int(2.7 * SR)) ** 1.5 * np.clip(np.arange(int(2.7 * SR)) / (0.1 * SR), 0, 1)
place(norm(trickle), SHOT[2] + 2.3, 0.025, -0.1)

# ---- dawn birds ----------------------------------------------------------------------------------------------------------------
def chirp(kind):
    if kind == 0:                                                    # quick upward chirps in a run of 2 to 4
        out = []
        for j in range(rng.integers(2, 5)):
            n = int(0.07 * SR); tt = np.arange(n) / SR; f0 = rng.uniform(2800, 3600)
            s = np.sin(2 * math.pi * (f0 * tt + 9000 * tt * tt)) * np.sin(math.pi * tt / tt[-1]) ** 2
            out += [s, np.zeros(int(0.05 * SR))]
        return np.concatenate(out)
    n = int(0.5 * SR); tt = np.arange(n) / SR                         # a falling whistle
    f = 2600 - 900 * tt / tt[-1]
    return np.sin(2 * math.pi * np.cumsum(f) / SR) * np.sin(math.pi * tt / tt[-1]) ** 1.5 * (1 + 0.3 * np.sin(2 * math.pi * 23 * tt))


at = 1.5
while at < SHOT[9] + 3:
    dens = 0.25 + 0.9 * min(max((at - SHOT[4]) / 12, 0), 1)          # more birds as the sun comes up
    place(chirp(int(rng.random() < 0.3)), at, rng.uniform(0.015, 0.04) * (0.6 + dens), rng.uniform(-0.9, 0.9))
    at += rng.exponential(1.6 / dens)

# ---- drone (Sa and Pa on D) ------------------------------------------------------------------------------------------------------
def pluck(f0, dur=3.2):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = sum((0.9 ** h) / h * np.sin(2 * math.pi * f0 * h * tt + rng.uniform(0, 6.28)) * (1 + 0.15 * np.sin(2 * math.pi * (0.7 + h * 0.13) * tt))
            for h in range(1, 14))                                   # rich harmonics: the jivari buzz
    return s * np.exp(-tt * 0.9) * np.clip(tt / 0.02, 0, 1) * np.clip((tt[-1] - tt) / 0.4, 0, 1)   # no click at either end


drone_gain = 0.18 + 0.22 * env(SHOT[5] - 1, DUR + 1, 3, 0.1) + 0.15 * env(SHOT[10] - 1, DUR + 1, 1.5, 0.1)
D = np.zeros(N)
cycle = [110.0 * 2 ** (-5 / 12) * 2, 146.83, 146.83, 73.42]           # Pa (A3), Sa, Sa, low Sa
k, at = 0, 0.3
while at < DUR:
    p = pluck(cycle[k % 4]); i = int(at * SR); n = min(len(p), N - i)
    D[i:i + n] += p[:n]; k += 1; at += 1.2
D = norm(D) * drone_gain * env(0, DUR, 2.5, 1.0)
L += D * 0.6; R += np.roll(D, 900) * 0.6

# ---- wading, shot 7 ------------------------------------------------------------------------------------------------------------
for j in range(7):
    at = SHOT[7] + 0.15 + j * 0.6
    n = int(0.45 * SR); x = band(rng.standard_normal(n), 250, 3500) * np.exp(-np.linspace(0, 7, n)) * np.clip(np.arange(n) / (0.012 * SR), 0, 1)
    place(norm(x), at, 0.22 * (0.6 + 0.4 * (j / 6)), 0.15 if j % 2 else -0.15)

# ---- horses and wheels ---------------------------------------------------------------------------------------------------------
def hoof(gain):
    n = int(0.12 * SR); tt = np.arange(n) / SR
    thump = np.sin(2 * math.pi * rng.uniform(70, 110) * tt) * np.exp(-tt * 45)
    click = band(rng.standard_normal(n), 800, 4000) * np.exp(-tt * 120) * 0.5
    return (thump + click) * gain


for j in range(9):                                                   # stamping at rest, shots 7 and 8
    place(hoof(1), SHOT[7] + rng.uniform(0, 8.5), 0.07, 0.6)
at = SHOT[9] + 0.3
while at < SHOT[10] + 1.5:                                           # four hooves a stride, four horses, quickening
    g = min(1.0, (at - SHOT[9]) / 1.5) * (1 - 0.7 * min(max((at - SHOT[10] + 1) / 2.5, 0), 1))
    stride = 0.62 - 0.22 * min((at - SHOT[9]) / 2, 1)
    for hh in range(4):
        for q in (0.0, 0.09, 0.27, 0.36):
            place(hoof(1), at + q + hh * 0.023 + rng.uniform(0, 0.01), 0.09 * g, rng.uniform(-0.4, 0.4))
    at += stride
rumble = norm(band(rng.standard_normal(N), 30, 220)) * env(SHOT[9] + 0.3, SHOT[10] + 2.5, 1.5, 2.5) * 0.35
L += rumble; R += rumble
creak = np.sin(2 * math.pi * (180 + 25 * np.sin(2 * math.pi * 1.7 * t)) * t) * (np.sin(2 * math.pi * 1.7 * t) > 0.85)
L += band(creak, 150, 1200) * env(SHOT[9] + 0.5, SHOT[10], 1, 2) * 0.03
wind = norm(band(rng.standard_normal(N), 200, 1400)) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.09 * t))
L += wind * env(SHOT[9] - 0.5, DUR, 2, 2) * 0.10; R += np.roll(wind, 5000) * env(SHOT[9] - 0.5, DUR, 2, 2) * 0.10

# ---- the conch over the title ----------------------------------------------------------------------------------------------------
n = int(3.2 * SR); tt = np.arange(n) / SR
f = 233.0 * (1 + 0.006 * np.sin(2 * math.pi * 5.2 * tt)) * (1 - 0.015 * np.exp(-tt * 4))
ph = 2 * math.pi * np.cumsum(f) / SR
conch = sum((0.75 ** h) * np.sin(h * ph) for h in range(1, 9)) + 0.15 * band(rng.standard_normal(n), 400, 3000)
conch *= np.clip(tt / 0.35, 0, 1) * np.clip((tt[-1] - tt) / 0.8, 0, 1)
place(norm(conch), SHOT[10] + 0.2, 0.32, 0.0)

# ---- voices (optional) -----------------------------------------------------------------------------------------------------------
if "--voices" in sys.argv:
    vd = pathlib.Path(sys.argv[sys.argv.index("--voices") + 1])
    at_ = {1: SHOT[2] + 2.5, 2: SHOT[4] + 0.6, 3: SHOT[6] + 2.0, 4: SHOT[7] + 0.5, 5: SHOT[8] + 1.3}
    for k_, a_ in at_.items():
        p = vd / f"line{k_}.wav"
        if p.exists():
            with wave.open(str(p)) as w:
                x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float)
                if w.getnchannels() == 2:
                    x = x.reshape(-1, 2).mean(1)
                if w.getframerate() != SR:
                    x = np.interp(np.arange(int(len(x) * SR / w.getframerate())) * w.getframerate() / SR, np.arange(len(x)), x)
            place(norm(x), a_, 0.7, 0.0)

# ---- master ----------------------------------------------------------------------------------------------------------------------
fade = np.clip((DUR - t) / 1.2, 0, 1) * np.clip(t / 0.8, 0, 1)
mix = np.stack([L, R], 1) * fade[:, None]
mix = np.tanh(mix * 1.2) / np.tanh(1.2)                              # gentle limiter
mix = mix / np.abs(mix).max() * 0.89
out = pathlib.Path(sys.argv[1])
with wave.open(str(out), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("wrote", out, round(DUR, 1), "s")

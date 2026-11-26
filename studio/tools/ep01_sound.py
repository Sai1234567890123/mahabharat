#!/usr/bin/env python3
"""Temp sound design for EP01 "The Anjalika" animatic (numpy only, free: no samples, no AI).

Reads exact shot timings from studio/episodes/ep01_arjuna_vs_karna/shots.json (90.0 s).
Usage:
  python studio/tools/ep01_sound.py <out.wav>
"""
import json, math, pathlib, sys, wave
import numpy as np

SR = 48000
EP = pathlib.Path(__file__).resolve().parent.parent / "episodes" / "ep01_arjuna_vs_karna"
data = json.loads((EP / "shots.json").read_text())

SHOT = {}
DUR_MAP = {}
clock = 0.0
for s in data["shots"]:
    SHOT[s["id"]] = clock
    DUR_MAP[s["id"]] = float(s["dur"])
    clock += float(s["dur"])

DUR = clock
N = int(round(SR * DUR))
t = np.arange(N) / SR
rng = np.random.default_rng(17)
L = np.zeros(N)
R = np.zeros(N)


def band(x, lo, hi):
    """Band-pass filter by soft-tapering FFT bins."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.clip((f - lo * 0.7) / (lo * 0.3 + 1e-9), 0, 1) if lo > 0 else np.ones_like(f)
    g *= np.clip((hi * 1.3 - f) / (hi * 0.3 + 1e-9), 0, 1)
    return np.fft.irfft(X * g, len(x))


def env(a, b, rise=0.4, fall=0.4):
    """Smooth raised-cosine style gate inside [a, b] seconds."""
    u = np.clip((t - a) / max(rise, 1e-3), 0, 1) * np.clip((b - t) / max(fall, 1e-3), 0, 1)
    return u * u * (3 - 2 * u)


def place(sig, at, gain=1.0, pan=0.0):
    i = int(round(at * SR))
    if i >= N or i + len(sig) <= 0:
        return
    if i < 0:
        sig = sig[-i:]
        i = 0
    s = sig[: max(0, N - i)]
    gl = gain * math.sqrt((1 - pan) / 2)
    gr = gain * math.sqrt((1 + pan) / 2)
    L[i : i + len(s)] += s * gl
    R[i : i + len(s)] += s * gr


def norm(x):
    return x / (np.abs(x).max() + 1e-9)


def drum_hit(f0=62.0, dur=0.38):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    pitch = f0 * (1 + 1.4 * np.exp(-tt * 38))
    body = np.sin(2 * math.pi * np.cumsum(pitch) / SR) * np.exp(-tt * 9.5)
    skin = band(rng.standard_normal(n), 140, 1800) * np.exp(-tt * 35) * 0.45
    return norm(body + skin)


def arrow_whoosh(dur=0.42, f_hi=2800.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    noise = band(rng.standard_normal(n), 450, f_hi)
    whistle = np.sin(2 * math.pi * (1450 - 700 * tt / dur) * tt) * 0.35
    shape = np.sin(math.pi * tt / dur) ** 1.6
    return norm((noise + whistle) * shape)


def metal_click(f0=2200.0, dur=0.18):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    partials = sum(np.sin(2 * math.pi * f0 * r * tt) * np.exp(-tt * (22 + 12 * r)) for r in (1.0, 1.53, 2.31))
    transient = band(rng.standard_normal(n), 1800, 7500) * np.exp(-tt * 140)
    return norm(partials + transient * 0.8)


# ---- A01 (0-4s): silence, then one hard crack + ring ---------------------------------------------------------------------------
crack_n = int(0.8 * SR)
ct = np.arange(crack_n) / SR
crack = norm(band(rng.standard_normal(crack_n), 200, 7000) * np.exp(-ct * 28) + np.sin(2 * math.pi * 85 * np.exp(-ct * 18) * ct) * np.exp(-ct * 12))
place(crack, SHOT["A01"] + 2.0, 0.72, 0.0)

# ---- Ambient Kurukshetra wind bed (A02-A22, ducked in silent moments A09, A19, A20) ---------------------------------------------
wind_raw = norm(band(rng.standard_normal(N), 110, 850)) * (0.65 + 0.35 * np.sin(2 * math.pi * 0.08 * t))
wind_env = env(SHOT["A02"], DUR, 0.8, 1.5) * (1 - 0.65 * env(SHOT["A09"], SHOT["A10"], 0.3, 0.3)) * (1 - 0.85 * env(SHOT["A19"], SHOT["A21"], 0.2, 0.5))
L += wind_raw * wind_env * 0.13
R += np.roll(wind_raw, 3600) * wind_env * 0.13

# ---- A02 (4-9s): far drum heartbeat & banner snaps ------------------------------------------------------------------------------
for k in range(5):
    place(drum_hit(54.0, 0.45), SHOT["A02"] + 0.4 + k * 0.95, 0.32, -0.2 if k % 2 == 0 else 0.2)
for k in range(3):
    snap = norm(band(rng.standard_normal(int(0.14 * SR)), 500, 3200) * np.exp(-np.linspace(0, 8, int(0.14 * SR))))
    place(snap, SHOT["A02"] + 1.0 + k * 1.4, 0.12, rng.uniform(-0.6, 0.6))

# ---- A03 (9-13s): low tanpura-like war drone enters + single bronze bell ---------------------------------------------------------
drone = sum((0.78 ** h) * np.sin(2 * math.pi * 73.42 * h * t + h * 0.5) for h in range(1, 9))
drone_env = (
    env(SHOT["A03"], SHOT["A09"] + 0.2, 1.2, 0.4) * 0.18
    + env(SHOT["A10"], SHOT["A13"] + 0.2, 0.8, 0.3) * 0.20
    + env(SHOT["A15"], SHOT["A19"] + 0.1, 0.5, 0.3) * 0.16
)
L += norm(drone) * drone_env
R += norm(np.roll(drone, 800)) * drone_env

bell_n = int(2.4 * SR)
bt = np.arange(bell_n) / SR
bell = sum(np.sin(2 * math.pi * 440.0 * r * bt) * np.exp(-bt * (1.8 * r)) for r in (1.0, 2.0, 2.76, 4.07))
place(norm(bell), SHOT["A03"] + 1.8, 0.28, 0.35)

# ---- A04 (13-17s): bowstring creak + electric blue static crackle ---------------------------------------------------------------
creak_n = int(2.2 * SR)
crt = np.arange(creak_n) / SR
creak = np.sin(2 * math.pi * np.cumsum(160 + 90 * crt / 2.2) / SR) * (np.sin(2 * math.pi * 24 * crt) > 0.2) * np.sin(math.pi * crt / 2.2)
place(norm(band(creak, 180, 1800)), SHOT["A04"] + 0.4, 0.16, -0.4)
for k in range(18):
    sn = int(0.05 * SR)
    st = np.arange(sn) / SR
    zap = band(rng.standard_normal(sn), 2400, 8500) * np.exp(-st * 90)
    place(norm(zap), SHOT["A04"] + 1.1 + k * 0.14, 0.14, -0.35)

# ---- A05 (17-20s): reins crack, 4-horse gallop hooves, war drums at 120 BPM -----------------------------------------------------
place(norm(band(rng.standard_normal(int(0.12 * SR)), 800, 6500) * np.exp(-np.linspace(0, 12, int(0.12 * SR)))), SHOT["A05"] + 0.2, 0.36, -0.25)
for k in range(14):
    hoof = drum_hit(rng.uniform(85, 115), 0.11)
    place(hoof, SHOT["A05"] + 0.45 + k * 0.18, 0.18, rng.uniform(-0.5, 0.1))
for k in range(6):
    place(drum_hit(65.0, 0.35), SHOT["A05"] + k * 0.5, 0.42, 0.0)

# ---- A06-A08 (20-34s): 120 BPM drum drive, 7 arrow whistles, 7 metallic splits, arrow-storm roar -------------------------------
for k in range(18):
    place(drum_hit(62.0, 0.32), SHOT["A06"] + k * 0.5, 0.38 if k < 16 else 0.22, 0.0)

for k in range(7):
    place(arrow_whoosh(0.36, 3200.0 + k * 140), SHOT["A06"] + 1.0 + k * 0.22, 0.26, 0.5 - k * 0.14)

for k in range(7):
    place(metal_click(2100.0 + k * 180, 0.2), SHOT["A07"] + 0.35 + k * 0.46, 0.42, -0.3 + k * 0.1)

roar_n = int(4.4 * SR)
rt = np.arange(roar_n) / SR
roar = norm(band(rng.standard_normal(roar_n), 180, 2600)) * np.clip(rt / 2.2, 0, 1) ** 1.4 * np.clip((4.4 - rt) / 0.15, 0, 1)
place(roar, SHOT["A08"] + 0.1, 0.46, 0.0)

# ---- A09 (34-38s): heavy breathing + one heartbeat, quiet -----------------------------------------------------------------------
for k in range(2):
    bn = int(0.65 * SR)
    br = norm(band(rng.standard_normal(bn), 300, 1600)) * np.sin(math.pi * np.arange(bn) / bn) ** 1.5
    place(br, SHOT["A09"] + 0.5 + k * 1.55, 0.16, -0.35 if k == 0 else 0.35)
place(drum_hit(45.0, 0.3), SHOT["A09"] + 1.9, 0.45, 0.0)
place(drum_hit(42.0, 0.35), SHOT["A09"] + 2.18, 0.32, 0.0)

# ---- A10 (38-42s): dry serpent hiss ---------------------------------------------------------------------------------------------
hn = int(3.0 * SR)
hiss = norm(band(rng.standard_normal(hn), 3200, 9000)) * np.sin(math.pi * np.arange(hn) / hn)
place(hiss, SHOT["A10"] + 0.6, 0.15, 0.3)

# ---- A11 (42-46s): thunder + low choir swell ------------------------------------------------------------------------------------
th_n = int(3.2 * SR)
tht = np.arange(th_n) / SR
thunder = norm(band(rng.standard_normal(th_n), 35, 320)) * np.exp(-tht * 0.9) * np.clip(tht / 0.15, 0, 1)
place(thunder, SHOT["A11"] + 0.3, 0.50, 0.2)
choir = sum(np.sin(2 * math.pi * f * tht) for f in (110.0, 164.81, 220.0)) * np.sin(math.pi * tht / 3.2)
place(norm(choir), SHOT["A11"] + 0.5, 0.16, 0.0)

# ---- A12 (46-50s): piercing hawk + serpent shriek right-to-left ------------------------------------------------------------------
sh_n = int(3.2 * SR)
sht = np.arange(sh_n) / SR
f_sh = 2600 - 1100 * (sht / 3.2) + 120 * np.sin(2 * math.pi * 19 * sht)
shriek = norm(np.sin(2 * math.pi * np.cumsum(f_sh) / SR) + 0.35 * band(rng.standard_normal(sh_n), 2500, 6000))
shriek *= np.clip(sht / 0.2, 0, 1) * np.clip((3.2 - sht) / 0.5, 0, 1)
place(shriek, SHOT["A12"] + 0.2, 0.36, 0.0)

# ---- A13 (50-54s): deep earth boom -----------------------------------------------------------------------------------------------
boom_n = int(2.6 * SR)
bmt = np.arange(boom_n) / SR
boom = norm(np.sin(2 * math.pi * np.cumsum(95 * np.exp(-bmt * 3.5) + 36) / SR) * np.exp(-bmt * 1.4) + 0.4 * band(rng.standard_normal(boom_n), 30, 180) * np.exp(-bmt * 2.2))
place(boom, SHOT["A13"] + 0.9, 0.78, -0.2)

# ---- A14 (54-58s): crown hit + slowed long metallic tone ------------------------------------------------------------------------
place(metal_click(1480.0, 0.25), SHOT["A14"] + 0.9, 0.52, -0.3)
rt_n = int(2.6 * SR)
rtt = np.arange(rt_n) / SR
ring = sum(np.sin(2 * math.pi * 620.0 * r * rtt) * np.exp(-rtt * (1.1 * r)) for r in (1.0, 1.49, 2.02))
place(norm(ring), SHOT["A14"] + 1.0, 0.26, -0.25)

# ---- A15 (58-61s): breath + single deep drum ------------------------------------------------------------------------------------
place(drum_hit(52.0, 0.5), SHOT["A15"] + 1.5, 0.52, -0.2)

# ---- A16 (61-66s): grinding earth rumble ----------------------------------------------------------------------------------------
gr_n = int(4.2 * SR)
grt = np.arange(gr_n) / SR
grind = norm(band(rng.standard_normal(gr_n), 40, 340)) * (0.6 + 0.4 * np.sin(2 * math.pi * 6.5 * grt)) * np.sin(math.pi * grt / 4.2)
place(grind, SHOT["A16"] + 0.4, 0.44, 0.3)

# ---- A17 (66-70s): quiet beat + distant child's battle cry swell ----------------------------------------------------------------
cry_n = int(1.6 * SR)
crt2 = np.arange(cry_n) / SR
cry = norm(np.sin(2 * math.pi * np.cumsum(580 + 180 * np.sin(math.pi * crt2 / 1.6)) / SR)) * np.sin(math.pi * crt2 / 1.6) ** 1.8
place(cry, SHOT["A17"] + 1.8, 0.14, -0.15)

# ---- A18 (70-74s): sharp pole snap + crowd gasp ---------------------------------------------------------------------------------
snap_n = int(0.25 * SR)
place(norm(band(rng.standard_normal(snap_n), 600, 5500) * np.exp(-np.linspace(0, 18, snap_n))), SHOT["A18"] + 0.9, 0.58, 0.35)
gasp_n = int(2.4 * SR)
gt = np.arange(gasp_n) / SR
gasp = norm(band(rng.standard_normal(gasp_n), 350, 1500)) * np.clip(gt / 0.35, 0, 1) * np.exp(-gt * 1.1)
place(gasp, SHOT["A18"] + 1.1, 0.34, 0.3)

# ---- A19 (74-78s): rising Anjalika harmonic tone into silence -------------------------------------------------------------------
anj_n = int(3.8 * SR)
ant = np.arange(anj_n) / SR
f_anj = 146.83 * (1 + 1.5 * (ant / 3.8) ** 2)
anj = sum((0.7 ** h) * np.sin(2 * math.pi * np.cumsum(f_anj * h) / SR) for h in range(1, 6)) * np.clip(ant / 0.6, 0, 1) ** 1.3
place(norm(anj), SHOT["A19"] + 0.1, 0.34, -0.2)

# ---- A20 (78-81s): single thunder crack then dead silence -----------------------------------------------------------------------
th2_n = int(2.0 * SR)
th2t = np.arange(th2_n) / SR
crack2 = norm(band(rng.standard_normal(th2_n), 40, 4200) * np.exp(-th2t * 4.5) + np.sin(2 * math.pi * 55 * th2t) * np.exp(-th2t * 3.0))
place(crack2, SHOT["A20"] + 0.15, 0.85, 0.0)

# ---- A21 (81-86s): low warm choir chord as light rises --------------------------------------------------------------------------
ch2_n = int(4.6 * SR)
ch2t = np.arange(ch2_n) / SR
chord = sum(np.sin(2 * math.pi * f * ch2t) for f in (146.83, 220.0, 293.66, 369.99)) * np.sin(math.pi * ch2t / 4.6) ** 1.2
place(norm(chord), SHOT["A21"] + 0.2, 0.24, 0.0)

# ---- A22 (86-90s): one far conch call, quiet final hold -------------------------------------------------------------------------
cn_n = int(3.2 * SR)
cnt = np.arange(cn_n) / SR
f_c = 233.0 * (1 + 0.005 * np.sin(2 * math.pi * 4.8 * cnt)) * (1 - 0.012 * np.exp(-cnt * 3))
ph = 2 * math.pi * np.cumsum(f_c) / SR
conch = sum((0.72 ** h) * np.sin(h * ph) for h in range(1, 8)) + 0.12 * band(rng.standard_normal(cn_n), 400, 2600)
conch *= np.clip(cnt / 0.45, 0, 1) * np.clip((cn_n / SR - cnt) / 1.0, 0, 1)
place(norm(conch), SHOT["A22"] + 0.5, 0.24, -0.35)

# ---- Master fade & limit --------------------------------------------------------------------------------------------------------
fade = np.clip((DUR - t) / 1.0, 0, 1) * np.clip(t / 0.2, 0, 1)
mix = np.stack([L, R], 1) * fade[:, None]
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
peak = np.abs(mix).max()
if peak > 0:
    mix = mix / peak * 0.89

out = pathlib.Path(sys.argv[1])
with wave.open(str(out), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("wrote", out, round(DUR, 1), "s")

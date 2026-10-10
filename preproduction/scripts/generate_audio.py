import wave
import math
import struct
import os

sample_rate = 44100
duration = 84.0
num_samples = int(sample_rate * duration)

def generate_tone(freq, duration_s, vol=0.5):
    samples = int(sample_rate * duration_s)
    data = []
    for i in range(samples):
        t = float(i) / sample_rate
        val = math.sin(2.0 * math.pi * freq * t) * vol
        data.append(val)
    return data

def generate_noise(duration_s, vol=0.1):
    import random
    samples = int(sample_rate * duration_s)
    data = []
    for _ in range(samples):
        data.append((random.random() * 2 - 1) * vol)
    return data

# Master track
audio_data = [0.0] * num_samples

def add_audio(start_time, add_data):
    start_idx = int(start_time * sample_rate)
    for i in range(len(add_data)):
        idx = start_idx + i
        if idx < num_samples:
            audio_data[idx] += add_data[i]

# Background drone (0-84s)
for i in range(num_samples):
    t = float(i) / sample_rate
    audio_data[i] += math.sin(2.0 * math.pi * 55.0 * t) * 0.1 # Low drone

# SH020: 7.0s - Drum hit (short burst of low noise)
add_audio(7.0, generate_noise(0.5, 0.4))

# SH040: 15.0s - Bhishma's conch (horn-like tone)
add_audio(15.0, generate_tone(300.0, 2.0, 0.6))
add_audio(15.0, generate_noise(3.0, 0.2))

# SH070: 26.0s - Two conches and boom
add_audio(26.0, generate_tone(350.0, 3.0, 0.5))
add_audio(26.0, generate_tone(400.0, 3.0, 0.5))
add_audio(26.5, generate_noise(1.0, 0.6)) # boom

# SH080: 30.0s - Paundra and Anantavijaya
add_audio(30.0, generate_tone(250.0, 2.0, 0.5)) # Rough blast
add_audio(32.0, generate_tone(500.0, 2.0, 0.4)) # High blast

# SH090: 35.0s - The blare (every conch)
for f in [250, 300, 350, 400, 450, 500]:
    add_audio(35.0, generate_tone(f, 3.0, 0.2))
add_audio(35.0, generate_noise(1.5, 0.7)) # sub-bass hit placeholder

# SH150: 65.0s - Vishvarupa swell
swell = []
swell_duration = 6.0
for i in range(int(swell_duration * sample_rate)):
    t = float(i) / sample_rate
    freq = 100.0 + (t / swell_duration) * 300.0 # rising freq
    vol = (t / swell_duration) * 0.8
    val = math.sin(2.0 * math.pi * freq * t) * vol
    swell.append(val)
add_audio(65.0, swell)

# Normalize and clamp
max_val = max(max(audio_data), abs(min(audio_data)))
if max_val > 1.0:
    audio_data = [x / max_val for x in audio_data]

output_path = r"c:\Users\dharm\.gemini\antigravity-ide\scratch\mahabharat\preproduction\art\shorts\audio_v01.wav"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with wave.open(output_path, 'w') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)
    
    packed_data = bytearray()
    for val in audio_data:
        # clamp
        val = max(-1.0, min(1.0, val))
        short_val = int(val * 32767.0)
        packed_data.extend(struct.pack('<h', short_val))
    
    wav_file.writeframes(packed_data)
    
print(f"Generated {output_path}")

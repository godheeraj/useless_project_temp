"""
sound.py — Procedural audio synthesis and sound manager.
Synthesizes all audio effects programmatically using NumPy and pygame.sndarray:
- Meaty physical hand slap
- Spider-Man web shooter "THWIP"
- Tactical laser "PEW PEW"
- Mosquito swarm buzzing with proximity modulation
- Combo arpeggio chimes
- Cartoon squishy splats
"""

import math
import os
# pyrefly: ignore [missing-import]
import pygame
import numpy as np
import config

SAMPLE_RATE = config.AUDIO_SAMPLE_RATE

def generate_slap_sound():
    """Heavy physical hand slap: bass impact thud + crisp white noise clap."""
    duration = 0.22
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, False)

    # 1. Low frequency bass thud (75 Hz with exponential decay)
    thud = np.sin(2 * np.pi * 75 * t) * np.exp(-t * 28.0)

    # 2. Crisp noise clap
    noise = np.random.uniform(-1.0, 1.0, n_samples)
    noise_env = np.exp(-t * 45.0)
    clap = noise * noise_env

    # Mix and normalize
    mixed = (thud * 0.75 + clap * 0.85)
    mixed = np.clip(mixed, -1.0, 1.0)
    samples = (mixed * 32767 * config.SFX_VOLUME).astype(np.int16)
    stereo = np.column_stack((samples, samples))
    return pygame.sndarray.make_sound(stereo)

def generate_web_sound():
    """Spider-Man web shooter 'THWIP!': Fast exponential upward frequency chirp."""
    duration = 0.16
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, False)

    # Frequency sweeps rapidly from 350 Hz to 2400 Hz
    freq = 350.0 + (2400.0 - 350.0) * (t / duration) ** 2
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    chirp = np.sin(phase)

    # Envelope with fast attack and smooth release
    env = np.sin(np.pi * (t / duration) ** 0.6)
    mixed = chirp * env * 0.85
    samples = (mixed * 32767 * config.SFX_VOLUME).astype(np.int16)
    stereo = np.column_stack((samples, samples))
    return pygame.sndarray.make_sound(stereo)

def generate_laser_sound():
    """Sci-fi laser 'PEW PEW': Rapid downward frequency sweep with square harmonics."""
    duration = 0.20
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, False)

    # Downward chirp: 1600 Hz down to 220 Hz
    freq = 1600.0 * np.exp(-t * 14.0) + 180.0
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    # Slight square-ish distortion
    wave = np.sin(phase) + 0.3 * np.sin(3 * phase)
    env = np.exp(-t * 12.0)
    mixed = np.clip(wave * env * 0.8, -1.0, 1.0)
    samples = (mixed * 32767 * config.SFX_VOLUME).astype(np.int16)
    stereo = np.column_stack((samples, samples))
    return pygame.sndarray.make_sound(stereo)

def generate_splat_sound():
    """Squishy cartoon bug splat."""
    duration = 0.18
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, False)

    noise = np.random.uniform(-1.0, 1.0, n_samples)
    env = np.exp(-t * 24.0)
    # Layer with a low squish pop (120 Hz)
    squish = np.sin(2 * np.pi * 120 * t) * np.exp(-t * 30.0)
    mixed = np.clip((noise * 0.5 + squish * 0.6) * env, -1.0, 1.0)
    samples = (mixed * 32767 * config.SFX_VOLUME).astype(np.int16)
    stereo = np.column_stack((samples, samples))
    return pygame.sndarray.make_sound(stereo)

def generate_miss_sound():
    """Air whoosh on missed slap."""
    duration = 0.15
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, False)

    noise = np.random.uniform(-1.0, 1.0, n_samples)
    # Bandpass / Bell curve envelope
    env = np.sin(np.pi * (t / duration)) ** 2
    mixed = noise * env * 0.4
    samples = (mixed * 32767 * config.SFX_VOLUME).astype(np.int16)
    stereo = np.column_stack((samples, samples))
    return pygame.sndarray.make_sound(stereo)

def generate_combo_chimes():
    """Set of cheerful ascending pentatonic arpeggio chimes."""
    notes = [523.25, 659.25, 783.99, 1046.50, 1318.51, 1567.98]
    chimes = []
    for freq in notes:
        duration = 0.28
        n_samples = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, n_samples, False)
        tone = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)
        env = np.exp(-t * 10.0)
        samples = (tone * env * 0.55 * 32767).astype(np.int16)
        stereo = np.column_stack((samples, samples))
        chimes.append(pygame.sndarray.make_sound(stereo))
    return chimes

def generate_fanfare_sound():
    """Triumphant level complete fanfare."""
    duration = 0.65
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, False)
    # Major triad chord (C5, E5, G5)
    c5 = np.sin(2 * np.pi * 523.25 * t)
    e5 = np.sin(2 * np.pi * 659.25 * t)
    g5 = np.sin(2 * np.pi * 783.99 * t)
    chord = (c5 + e5 + g5) / 3.0
    env = np.minimum(t * 8.0, 1.0) * np.exp(-t * 3.5)
    samples = (chord * env * 0.65 * 32767).astype(np.int16)
    stereo = np.column_stack((samples, samples))
    return pygame.sndarray.make_sound(stereo)

def generate_buzz_loop():
    """Continuous mosquito buzzing loop with oscillating modulation."""
    duration = 1.0
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, False)

    # 210 Hz saw-like harmonic tone
    base_freq = 210.0
    tone = (
        0.55 * np.sin(2 * np.pi * base_freq * t) +
        0.30 * np.sin(4 * np.pi * base_freq * t) +
        0.15 * np.sin(6 * np.pi * base_freq * t)
    )
    # Subtle amplitude vibrato (5 Hz)
    vibrato = 0.8 + 0.2 * np.sin(2 * np.pi * 5.5 * t)
    samples = (tone * vibrato * 0.30 * 32767).astype(np.int16)
    stereo = np.column_stack((samples, samples))
    snd = pygame.sndarray.make_sound(stereo)
    return snd

class SoundManager:
    """Manages all game audio, volume controls, and sound effect triggers."""
    def __init__(self):
        self.enabled = False
        self.buzz_channel = None
        self.buzz_sound = None
        self.sounds = {}
        self.combo_chimes = []

        self._init_audio()

    def _init_audio(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=config.AUDIO_CHANNELS, buffer=512)

            self.sounds["slap"] = generate_slap_sound()
            self.sounds["web"] = generate_web_sound()
            self.sounds["laser"] = generate_laser_sound()
            self.sounds["splat"] = generate_splat_sound()
            self.sounds["miss"] = generate_miss_sound()
            self.sounds["fanfare"] = generate_fanfare_sound()
            self.combo_chimes = generate_combo_chimes()
            self.buzz_sound = generate_buzz_loop()

            self.buzz_channel = pygame.mixer.Channel(7)
            self.enabled = True
            print("[SoundManager] Procedural sound engine successfully initialized.")
        except Exception as e:
            print("[SoundManager] Warning: Audio init failed, running silently:", e)
            self.enabled = False

    def play_slap(self):
        if self.enabled and "slap" in self.sounds:
            self.sounds["slap"].play()

    def play_web(self):
        if self.enabled and "web" in self.sounds:
            self.sounds["web"].play()

    def play_laser(self):
        if self.enabled and "laser" in self.sounds:
            self.sounds["laser"].play()

    def play_splat(self):
        if self.enabled and "splat" in self.sounds:
            self.sounds["splat"].play()

    def play_miss(self):
        if self.enabled and "miss" in self.sounds:
            self.sounds["miss"].play()

    def play_fanfare(self):
        if self.enabled and "fanfare" in self.sounds:
            self.sounds["fanfare"].play()

    def play_combo(self, streak):
        if self.enabled and self.combo_chimes:
            idx = min(max(0, streak - 1), len(self.combo_chimes) - 1)
            self.combo_chimes[idx].play()

    def update_buzz(self, mosquito_count):
        """Modulates mosquito swarm buzzing volume based on alive mosquito count."""
        if not self.enabled or self.buzz_sound is None or self.buzz_channel is None:
            return

        if mosquito_count > 0:
            if not self.buzz_channel.get_busy():
                self.buzz_channel.play(self.buzz_sound, loops=-1)
            # Volume scales smoothly with mosquito count
            vol = min(config.BUZZ_MAX_VOLUME, 0.08 + (mosquito_count * 0.025))
            self.buzz_channel.set_volume(vol)
        else:
            if self.buzz_channel.get_busy():
                self.buzz_channel.stop()

    def stop_all(self):
        if self.enabled:
            pygame.mixer.stop()

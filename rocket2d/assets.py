from __future__ import annotations

import math
import random
import wave
from pathlib import Path

import pygame


ASSET_ROOT = Path("assets")
GENERATED = ASSET_ROOT / "generated"
AUDIO_DIR = ASSET_ROOT / "audio"


def ensure_generated_assets() -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    _generate_image_assets()
    _generate_audio_assets()


def _generate_image_assets() -> None:
    ball_path = GENERATED / "ball.png"
    if not ball_path.exists():
        surf = pygame.Surface((128, 128), pygame.SRCALPHA)
        center = (64, 64)
        pygame.draw.circle(surf, (235, 239, 246), center, 58)
        pygame.draw.circle(surf, (35, 43, 58), center, 58, 5)
        for angle in range(0, 360, 60):
            x = 64 + math.cos(math.radians(angle)) * 34
            y = 64 + math.sin(math.radians(angle)) * 34
            pygame.draw.circle(surf, (99, 122, 148), (int(x), int(y)), 15, 3)
        pygame.draw.arc(surf, (60, 75, 95), (20, 28, 88, 72), 0, math.pi, 4)
        pygame.image.save(surf, ball_path)

    pad_path = GENERATED / "boost_pad.png"
    if not pad_path.exists():
        surf = pygame.Surface((128, 52), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (255, 190, 64, 55), (4, 4, 120, 44))
        pygame.draw.ellipse(surf, (255, 182, 46), (18, 10, 92, 32))
        pygame.draw.ellipse(surf, (255, 247, 154), (36, 17, 56, 18))
        pygame.image.save(surf, pad_path)


def _tone(path: Path, freq: float, seconds: float, volume: float = 0.45) -> None:
    if path.exists():
        return
    sample_rate = 44100
    count = int(seconds * sample_rate)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = bytearray()
        for i in range(count):
            t = i / sample_rate
            envelope = min(1.0, i / 400) * min(1.0, (count - i) / 1000)
            wave_a = math.sin(math.tau * freq * t)
            wave_b = 0.35 * math.sin(math.tau * (freq * 1.5) * t)
            sample = int(32767 * volume * envelope * (wave_a + wave_b) * 0.7)
            frames += sample.to_bytes(2, "little", signed=True)
            frames += sample.to_bytes(2, "little", signed=True)
        handle.writeframes(frames)


def _music(path: Path, base: float, seconds: float) -> None:
    if path.exists():
        return
    sample_rate = 44100
    count = int(seconds * sample_rate)
    notes = [base, base * 1.25, base * 1.5, base * 2.0]
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = bytearray()
        for i in range(count):
            t = i / sample_rate
            beat = int(t * 2) % len(notes)
            freq = notes[beat]
            pulse = 0.5 + 0.5 * math.sin(math.tau * 2 * t)
            bass = math.sin(math.tau * (freq * 0.5) * t)
            lead = math.sin(math.tau * freq * t) * pulse
            sample = int(32767 * 0.08 * (bass * 0.65 + lead * 0.35))
            frames += sample.to_bytes(2, "little", signed=True)
            frames += sample.to_bytes(2, "little", signed=True)
        handle.writeframes(frames)


def _generate_audio_assets() -> None:
    _tone(AUDIO_DIR / "boost.wav", 170, 0.16, 0.28)
    _tone(AUDIO_DIR / "jump.wav", 520, 0.13, 0.38)
    _tone(AUDIO_DIR / "collision.wav", 95, 0.12, 0.55)
    _tone(AUDIO_DIR / "goal.wav", 220, 1.1, 0.55)
    _tone(AUDIO_DIR / "countdown.wav", 690, 0.18, 0.45)
    _tone(AUDIO_DIR / "select.wav", 420, 0.08, 0.28)
    _music(AUDIO_DIR / "menu_loop.wav", 146, 8.0)
    _music(AUDIO_DIR / "match_loop.wav", 110, 8.0)


class AudioManager:
    def __init__(self, settings) -> None:
        self.settings = settings
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.current_music = ""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.enabled = True
        except pygame.error:
            self.enabled = False
        if self.enabled:
            self.load()

    def load(self) -> None:
        for name in ("boost", "jump", "collision", "goal", "countdown", "select"):
            path = AUDIO_DIR / f"{name}.wav"
            if path.exists():
                self.sounds[name] = pygame.mixer.Sound(str(path))
        self.set_volumes(self.settings)

    def set_volumes(self, settings) -> None:
        self.settings = settings
        if not self.enabled:
            return
        for name, sound in self.sounds.items():
            base = 0.36 if name == "boost" else 0.72
            sound.set_volume(settings.master_volume * settings.effects_volume * base)
        pygame.mixer.music.set_volume(settings.master_volume * settings.music_volume)

    def play(self, name: str) -> None:
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound:
            sound.play()

    def play_varied(self, name: str) -> None:
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound:
            sound.set_volume(
                self.settings.master_volume
                * self.settings.effects_volume
                * random.uniform(0.45, 0.8)
            )
            sound.play()

    def music(self, name: str) -> None:
        if not self.enabled or self.current_music == name:
            return
        path = AUDIO_DIR / f"{name}_loop.wav"
        if path.exists():
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.play(-1)
            self.current_music = name

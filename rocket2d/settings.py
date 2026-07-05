from __future__ import annotations

from dataclasses import dataclass, field

RESOLUTIONS = [(1280, 720), (1600, 900), (1920, 1080)]
GRAPHICS_QUALITY = ["Performance", "Balanced", "High"]

DEFAULT_KEYS = {
    "throttle": "w",
    "brake": "s",
    "steer_left": "a",
    "steer_right": "d",
    "jump": "space",
    "boost": "left shift",
    "air_roll_left": "q",
    "air_roll_right": "e",
    "powerslide": "left ctrl",
    "pause": "escape",
}

ACTION_LABELS = {
    "throttle": "Throttle",
    "brake": "Brake / Reverse",
    "steer_left": "Steer Left",
    "steer_right": "Steer Right",
    "jump": "Jump / Flip",
    "boost": "Boost",
    "air_roll_left": "Air Roll Left",
    "air_roll_right": "Air Roll Right",
    "powerslide": "Powerslide",
    "pause": "Pause",
}


@dataclass
class Settings:
    resolution: tuple[int, int] = (1600, 900)
    fullscreen: bool = False
    master_volume: float = 0.8
    music_volume: float = 0.45
    effects_volume: float = 0.8
    graphics_quality: str = "High"
    screen_shake: bool = True
    show_fps: bool = False
    key_bindings: dict[str, str] = field(default_factory=lambda: DEFAULT_KEYS.copy())

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        settings = cls()
        if not isinstance(data, dict):
            return settings
        if "resolution" in data:
            res = data["resolution"]
            if isinstance(res, (list, tuple)) and len(res) == 2:
                settings.resolution = (int(res[0]), int(res[1]))
        for name in (
            "fullscreen",
            "master_volume",
            "music_volume",
            "effects_volume",
            "graphics_quality",
            "screen_shake",
            "show_fps",
        ):
            if name in data:
                setattr(settings, name, data[name])
        if isinstance(data.get("key_bindings"), dict):
            merged = DEFAULT_KEYS.copy()
            merged.update({str(k): str(v) for k, v in data["key_bindings"].items()})
            settings.key_bindings = merged
        settings.master_volume = float(max(0.0, min(1.0, settings.master_volume)))
        settings.music_volume = float(max(0.0, min(1.0, settings.music_volume)))
        settings.effects_volume = float(max(0.0, min(1.0, settings.effects_volume)))
        if settings.graphics_quality not in GRAPHICS_QUALITY:
            settings.graphics_quality = "High"
        if settings.resolution not in RESOLUTIONS:
            settings.resolution = (1600, 900)
        return settings

    def to_dict(self) -> dict:
        return {
            "resolution": list(self.resolution),
            "fullscreen": self.fullscreen,
            "master_volume": self.master_volume,
            "music_volume": self.music_volume,
            "effects_volume": self.effects_volume,
            "graphics_quality": self.graphics_quality,
            "screen_shake": self.screen_shake,
            "show_fps": self.show_fps,
            "key_bindings": self.key_bindings.copy(),
        }

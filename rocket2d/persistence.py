from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .settings import Settings

DEFAULT_STATS = {
    "goals": 0,
    "assists": 0,
    "saves": 0,
    "shots": 0,
    "wins": 0,
    "losses": 0,
    "mvp_awards": 0,
    "matches_played": 0,
    "training_targets": 0,
}

DEFAULT_GARAGE = {
    "body": "Octane",
    "primary_color": [38, 161, 255],
    "accent_color": [245, 247, 252],
    "boost_effect": "Ion",
    "unlocked_bodies": ["Octane", "Dominus", "Breakout", "Merc"],
    "unlocked_boosts": ["Ion", "Flame", "Plasma", "Spark"],
}

DEFAULT_CAREER = {
    "level": 1,
    "xp": 0,
    "rank": "Rookie",
    "unlocked_arenas": ["Standard Arena", "Urban Arena", "Desert Arena", "Neo Arena"],
}


class SaveStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path("save")
        self.root.mkdir(parents=True, exist_ok=True)

    def load_json(self, name: str, default: dict[str, Any]) -> dict[str, Any]:
        path = self.root / name
        if not path.exists():
            self.save_json(name, default)
            return deepcopy(default)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                merged = deepcopy(default)
                merged.update(data)
                return merged
        except (OSError, json.JSONDecodeError):
            data = None
        self.save_json(name, default)
        return deepcopy(default)

    def save_json(self, name: str, data: dict[str, Any]) -> None:
        path = self.root / name
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load_settings(self) -> Settings:
        return Settings.from_dict(self.load_json("settings.json", Settings().to_dict()))

    def save_settings(self, settings: Settings) -> None:
        self.save_json("settings.json", settings.to_dict())

    def load_stats(self) -> dict[str, Any]:
        return self.load_json("stats.json", DEFAULT_STATS)

    def save_stats(self, stats: dict[str, Any]) -> None:
        merged = deepcopy(DEFAULT_STATS)
        merged.update(stats)
        self.save_json("stats.json", merged)

    def load_garage(self) -> dict[str, Any]:
        return self.load_json("garage.json", DEFAULT_GARAGE)

    def save_garage(self, garage: dict[str, Any]) -> None:
        merged = deepcopy(DEFAULT_GARAGE)
        merged.update(garage)
        self.save_json("garage.json", merged)

    def load_career(self) -> dict[str, Any]:
        return self.load_json("career.json", DEFAULT_CAREER)

    def save_career(self, career: dict[str, Any]) -> None:
        merged = deepcopy(DEFAULT_CAREER)
        merged.update(career)
        self.save_json("career.json", merged)

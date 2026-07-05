from __future__ import annotations

from dataclasses import dataclass

from .constants import (
    CEILING_Y,
    FLOOR_Y,
    GOAL_BOTTOM,
    GOAL_TOP,
    LEFT_WALL,
    RIGHT_WALL,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)


@dataclass(frozen=True)
class BoostPadSpec:
    x: float
    y: float
    amount: int


@dataclass(frozen=True)
class Arena:
    name: str
    key: str
    sky: tuple[int, int, int]
    horizon: tuple[int, int, int]
    floor: tuple[int, int, int]
    trim: tuple[int, int, int]
    accent: tuple[int, int, int]
    left_wall: int = LEFT_WALL
    right_wall: int = RIGHT_WALL
    ceiling_y: int = CEILING_Y
    floor_y: int = FLOOR_Y
    goal_top: int = GOAL_TOP
    goal_bottom: int = GOAL_BOTTOM
    width: int = WORLD_WIDTH
    height: int = WORLD_HEIGHT
    pads: tuple[BoostPadSpec, ...] = ()


COMMON_PADS = (
    BoostPadSpec(420, FLOOR_Y - 42, 100),
    BoostPadSpec(850, FLOOR_Y - 44, 12),
    BoostPadSpec(1280, FLOOR_Y - 44, 12),
    BoostPadSpec(1600, FLOOR_Y - 44, 100),
    BoostPadSpec(1920, FLOOR_Y - 44, 12),
    BoostPadSpec(2350, FLOOR_Y - 44, 12),
    BoostPadSpec(2780, FLOOR_Y - 42, 100),
    BoostPadSpec(980, FLOOR_Y - 390, 12),
    BoostPadSpec(2220, FLOOR_Y - 390, 12),
    BoostPadSpec(1600, FLOOR_Y - 650, 100),
)

ARENAS = {
    "Standard Arena": Arena(
        "Standard Arena",
        "standard",
        sky=(21, 35, 58),
        horizon=(28, 72, 100),
        floor=(28, 119, 95),
        trim=(92, 220, 141),
        accent=(38, 161, 255),
        pads=COMMON_PADS,
    ),
    "Urban Arena": Arena(
        "Urban Arena",
        "urban",
        sky=(18, 22, 34),
        horizon=(56, 66, 83),
        floor=(45, 53, 63),
        trim=(255, 218, 83),
        accent=(255, 142, 43),
        pads=COMMON_PADS,
    ),
    "Desert Arena": Arena(
        "Desert Arena",
        "desert",
        sky=(49, 32, 37),
        horizon=(151, 81, 56),
        floor=(97, 73, 50),
        trim=(255, 181, 83),
        accent=(92, 220, 141),
        pads=COMMON_PADS,
    ),
    "Neo Arena": Arena(
        "Neo Arena",
        "neo",
        sky=(12, 14, 30),
        horizon=(44, 22, 74),
        floor=(22, 31, 54),
        trim=(204, 93, 255),
        accent=(48, 235, 255),
        pads=COMMON_PADS,
    ),
}


def get_arena(name: str) -> Arena:
    return ARENAS.get(name, ARENAS["Standard Arena"])

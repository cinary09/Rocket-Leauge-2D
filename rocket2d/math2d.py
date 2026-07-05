from __future__ import annotations

import math

import pygame


Vec2 = pygame.math.Vector2


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * clamp(t, 0.0, 1.0)


def approach(value: float, target: float, amount: float) -> float:
    if value < target:
        return min(target, value + amount)
    return max(target, value - amount)


def shortest_angle(current: float, target: float) -> float:
    return (target - current + math.pi) % (math.tau) - math.pi


def rotate(vec: Vec2, radians: float) -> Vec2:
    c = math.cos(radians)
    s = math.sin(radians)
    return Vec2(vec.x * c - vec.y * s, vec.x * s + vec.y * c)


def from_angle(radians: float) -> Vec2:
    return Vec2(math.cos(radians), math.sin(radians))


def safe_normalize(vec: Vec2, fallback: Vec2 | None = None) -> Vec2:
    if vec.length_squared() > 0.000001:
        return vec.normalize()
    return fallback.copy() if fallback is not None else Vec2(1, 0)


def format_time(seconds: float, overtime: bool = False) -> str:
    seconds = max(0, int(seconds))
    minutes = seconds // 60
    secs = seconds % 60
    prefix = "OT " if overtime else ""
    return f"{prefix}{minutes}:{secs:02d}"

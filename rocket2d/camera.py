from __future__ import annotations

import random

import pygame

from .constants import WORLD_HEIGHT, WORLD_WIDTH
from .math2d import Vec2, clamp, lerp


class Camera:
    def __init__(self) -> None:
        self.center = Vec2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
        self.zoom = 0.62
        self.shake = 0.0
        self.offset = Vec2()

    def add_shake(self, amount: float) -> None:
        self.shake = max(self.shake, amount)

    def update(self, dt: float, screen_size: tuple[int, int], points: list[Vec2]) -> None:
        if points:
            min_x = min(point.x for point in points)
            max_x = max(point.x for point in points)
            min_y = min(point.y for point in points)
            max_y = max(point.y for point in points)
            target = Vec2((min_x + max_x) / 2, (min_y + max_y) / 2 - 70)
            spread_x = max(900, max_x - min_x + 900)
            spread_y = max(620, max_y - min_y + 520)
            target_zoom = min(screen_size[0] / spread_x, screen_size[1] / spread_y)
            target_zoom = clamp(target_zoom, 0.42, 0.86)
        else:
            target = Vec2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
            target_zoom = 0.62

        self.center.x = lerp(self.center.x, target.x, dt * 2.8)
        self.center.y = lerp(self.center.y, target.y, dt * 2.8)
        self.center.x = clamp(self.center.x, 650, WORLD_WIDTH - 650)
        self.center.y = clamp(self.center.y, 500, WORLD_HEIGHT - 420)
        self.zoom = lerp(self.zoom, target_zoom, dt * 2.2)

        self.shake = max(0.0, self.shake - dt * 18.0)
        if self.shake > 0.0:
            self.offset = Vec2(
                random.uniform(-self.shake, self.shake),
                random.uniform(-self.shake, self.shake),
            )
        else:
            self.offset.update(0, 0)

    def world_to_screen(self, point: Vec2, screen_size: tuple[int, int]) -> Vec2:
        screen = Vec2(screen_size) / 2
        return (point - self.center) * self.zoom + screen + self.offset

    def scalar(self, value: float) -> int:
        return max(1, int(value * self.zoom))

    def rect(self, x: float, y: float, w: float, h: float, screen_size: tuple[int, int]) -> pygame.Rect:
        p = self.world_to_screen(Vec2(x, y), screen_size)
        return pygame.Rect(int(p.x), int(p.y), int(w * self.zoom), int(h * self.zoom))

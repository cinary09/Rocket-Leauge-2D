from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

from .math2d import Vec2


@dataclass
class Particle:
    pos: Vec2
    vel: Vec2
    color: tuple[int, int, int]
    life: float
    size: float
    gravity: float = 0.0
    age: float = 0.0

    def update(self, dt: float) -> bool:
        self.age += dt
        self.vel.y += self.gravity * dt
        self.pos += self.vel * dt
        return self.age < self.life

    @property
    def alpha(self) -> int:
        return int(255 * max(0.0, 1.0 - self.age / self.life))


class ParticleSystem:
    def __init__(self) -> None:
        self.particles: list[Particle] = []
        self.quality = 1.0

    def set_quality(self, quality_name: str) -> None:
        self.quality = {"Performance": 0.45, "Balanced": 0.75, "High": 1.0}.get(quality_name, 1.0)

    def _count(self, base: int) -> int:
        return max(1, int(base * self.quality))

    def update(self, dt: float) -> None:
        self.particles = [p for p in self.particles if p.update(dt)]

    def emit_boost(self, pos: Vec2, direction: Vec2, color: tuple[int, int, int]) -> None:
        for _ in range(self._count(3)):
            spread = Vec2(random.uniform(-90, 90), random.uniform(-90, 90))
            vel = direction * random.uniform(360, 640) + spread
            self.particles.append(
                Particle(pos.copy(), vel, color, random.uniform(0.18, 0.32), random.uniform(8, 18))
            )

    def emit_sparks(self, pos: Vec2, normal: Vec2, color: tuple[int, int, int]) -> None:
        for _ in range(self._count(12)):
            tangent = Vec2(-normal.y, normal.x)
            vel = normal * random.uniform(160, 460) + tangent * random.uniform(-240, 240)
            self.particles.append(
                Particle(pos.copy(), vel, color, random.uniform(0.18, 0.45), random.uniform(3, 8), 250)
            )

    def emit_ball_trail(self, pos: Vec2) -> None:
        if random.random() > self.quality:
            return
        self.particles.append(
            Particle(
                pos.copy(),
                Vec2(random.uniform(-30, 30), random.uniform(-30, 30)),
                (210, 235, 255),
                0.22,
                random.uniform(7, 13),
            )
        )

    def emit_goal(self, pos: Vec2, color: tuple[int, int, int]) -> None:
        for _ in range(self._count(140)):
            angle = random.uniform(0, 6.28318)
            speed = random.uniform(160, 980)
            vel = Vec2(speed, 0).rotate_rad(angle)
            self.particles.append(
                Particle(pos.copy(), vel, color, random.uniform(0.5, 1.35), random.uniform(5, 22), 120)
            )

    def draw(self, surface: pygame.Surface, camera, screen_size: tuple[int, int]) -> None:
        for particle in self.particles:
            p = camera.world_to_screen(particle.pos, screen_size)
            radius = camera.scalar(particle.size)
            if radius <= 0:
                continue
            temp = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(
                temp,
                (*particle.color, particle.alpha),
                (radius + 1, radius + 1),
                radius,
            )
            surface.blit(temp, (p.x - radius, p.y - radius), special_flags=pygame.BLEND_PREMULTIPLIED)

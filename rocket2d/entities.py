from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from .constants import BALL_GRAVITY, GRAVITY, TEAM_BLUE
from .math2d import Vec2, clamp, from_angle, rotate, safe_normalize, shortest_angle


CAR_BODIES = {
    "Octane": {"size": (154, 66), "mass": 760.0, "turn": 8.2, "speed": 1840.0},
    "Dominus": {"size": (178, 58), "mass": 790.0, "turn": 7.4, "speed": 1890.0},
    "Breakout": {"size": (168, 54), "mass": 735.0, "turn": 8.8, "speed": 1810.0},
    "Merc": {"size": (146, 76), "mass": 830.0, "turn": 6.9, "speed": 1760.0},
}

BOOST_COLORS = {
    "Ion": (72, 190, 255),
    "Flame": (255, 132, 45),
    "Plasma": (206, 91, 255),
    "Spark": (255, 232, 92),
}


@dataclass
class BoostPad:
    pos: Vec2
    amount: int
    radius: float
    cooldown_time: float
    cooldown: float = 0.0

    @property
    def active(self) -> bool:
        return self.cooldown <= 0.0

    def update(self, dt: float) -> None:
        self.cooldown = max(0.0, self.cooldown - dt)

    def try_collect(self, car: "Car") -> bool:
        if not self.active:
            return False
        if car.pos.distance_squared_to(self.pos) <= (self.radius + 62) ** 2:
            car.boost = min(100.0, car.boost + self.amount)
            self.cooldown = self.cooldown_time
            return True
        return False


class Car:
    def __init__(
        self,
        team: int,
        pos: tuple[float, float],
        body: str,
        color: tuple[int, int, int],
        accent: tuple[int, int, int],
        boost_effect: str = "Ion",
        name: str = "Player",
    ) -> None:
        spec = CAR_BODIES.get(body, CAR_BODIES["Octane"])
        self.team = team
        self.name = name
        self.body = body
        self.color = color
        self.accent = accent
        self.boost_effect = boost_effect
        self.size = Vec2(spec["size"])
        self.half = self.size / 2
        self.mass = float(spec["mass"])
        self.turn_rate = float(spec["turn"])
        self.max_speed = float(spec["speed"])
        self.pos = Vec2(pos)
        self.vel = Vec2()
        self.angle = 0.0 if team == TEAM_BLUE else math.pi
        self.facing = 1 if team == TEAM_BLUE else -1
        self.angular_velocity = 0.0
        self.boost = 34.0
        self.grounded = False
        self.jumps_used = 0
        self.flip_timer = 0.0
        self.boosting = False
        self.last_jump_was_flip = ""
        self.touch_cooldown = 0.0

    def reset(self, pos: tuple[float, float], facing: int) -> None:
        self.pos.update(pos)
        self.vel.update(0, 0)
        self.facing = facing
        self.angle = 0.0 if facing > 0 else math.pi
        self.angular_velocity = 0.0
        self.grounded = False
        self.jumps_used = 0
        self.flip_timer = 0.0
        self.boosting = False
        self.last_jump_was_flip = ""
        self.touch_cooldown = 0.0

    @property
    def nose(self) -> Vec2:
        return from_angle(self.angle)

    def update(self, dt: float, controls: dict[str, bool], arena, particles=None, audio=None) -> None:
        throttle = controls.get("throttle", False)
        brake = controls.get("brake", False)
        steer_left = controls.get("steer_left", False)
        steer_right = controls.get("steer_right", False)
        jump_pressed = controls.get("jump_pressed", False)
        boost = controls.get("boost", False)
        roll_left = controls.get("air_roll_left", False)
        roll_right = controls.get("air_roll_right", False)
        powerslide = controls.get("powerslide", False)

        self.touch_cooldown = max(0.0, self.touch_cooldown - dt)
        self.flip_timer = max(0.0, self.flip_timer - dt)
        self.boosting = False

        if jump_pressed:
            self._jump_or_flip(controls, audio)

        if self.grounded:
            if steer_left and not steer_right:
                self.facing = -1
            elif steer_right and not steer_left:
                self.facing = 1

            target_angle = 0.0 if self.facing > 0 else math.pi
            correction = shortest_angle(self.angle, target_angle)
            snap = 14.0 if powerslide else 8.5
            self.angle += correction * min(1.0, snap * dt)
            self.angular_velocity = 0.0

            forward_speed = self.vel.x * self.facing
            if throttle:
                accel = 2500.0 if forward_speed < 0 else 1880.0
                self.vel.x += self.facing * accel * dt
            if brake:
                if forward_speed > 130.0:
                    self.vel.x -= self.facing * 3350.0 * dt
                else:
                    self.vel.x -= self.facing * 1350.0 * dt
            if not throttle and not brake:
                self.vel.x *= max(0.0, 1.0 - (2.0 if powerslide else 3.4) * dt)
            self.vel.y += GRAVITY * 0.12 * dt
        else:
            turn = (1 if steer_right else 0) - (1 if steer_left else 0)
            roll = (1 if roll_right else 0) - (1 if roll_left else 0)
            self.angular_velocity += (turn * self.turn_rate + roll * 10.5) * dt
            self.angular_velocity *= max(0.0, 1.0 - 1.15 * dt)
            self.angle += self.angular_velocity * dt
            if throttle:
                self.vel += self.nose * 280.0 * dt
            if brake:
                self.vel -= self.nose * 180.0 * dt
            self.vel.y += GRAVITY * dt
            self.vel *= max(0.0, 1.0 - 0.13 * dt)

        if boost and self.boost > 0.0:
            self.boosting = True
            self.boost = max(0.0, self.boost - 34.0 * dt)
            self.vel += self.nose * 1760.0 * dt
            if particles:
                exhaust = self.pos - self.nose * (self.half.x + 10)
                color = BOOST_COLORS.get(self.boost_effect, BOOST_COLORS["Ion"])
                particles.emit_boost(exhaust, -self.nose, color)

        speed_limit = self.max_speed + (420 if self.boosting or self.flip_timer > 0 else 0)
        if self.vel.length_squared() > speed_limit * speed_limit:
            self.vel.scale_to_length(speed_limit)

        self.pos += self.vel * dt
        self._arena_collision(arena)

    def _jump_or_flip(self, controls: dict[str, bool], audio=None) -> None:
        if self.grounded:
            self.vel.y = -950.0
            self.grounded = False
            self.jumps_used = 1
            self.angular_velocity += -self.facing * 1.5
            self.last_jump_was_flip = ""
            if audio:
                audio.play("jump")
            return

        if self.jumps_used >= 2:
            return
        self.jumps_used = 2
        steer = (1 if controls.get("steer_right", False) else 0) - (
            1 if controls.get("steer_left", False) else 0
        )
        self.flip_timer = 0.38
        self.vel.y = min(self.vel.y, -360.0)
        if controls.get("throttle", False):
            self.vel.x += self.facing * 760.0
            self.angular_velocity = -self.facing * 16.0
            self.last_jump_was_flip = "Front Flip"
        elif controls.get("brake", False):
            self.vel.x -= self.facing * 690.0
            self.angular_velocity = self.facing * 14.0
            self.last_jump_was_flip = "Back Flip"
        elif steer != 0:
            self.vel.x += steer * 820.0
            self.angular_velocity = -steer * 17.0
            self.last_jump_was_flip = "Side Flip"
        else:
            self.vel.y -= 390.0
            self.angular_velocity = -self.facing * 7.0
            self.last_jump_was_flip = "Double Jump"
        if audio:
            audio.play("jump")

    def _arena_collision(self, arena) -> None:
        floor = arena.floor_y - self.half.y
        ceiling = arena.ceiling_y + self.half.y
        left = arena.left_wall + self.half.x
        right = arena.right_wall - self.half.x
        was_grounded = self.grounded
        self.grounded = False

        if self.pos.y >= floor:
            self.pos.y = floor
            if self.vel.y > 0:
                self.vel.y = -self.vel.y * 0.08 if self.vel.y > 520 else 0.0
            self.grounded = True
            self.jumps_used = 0
        elif was_grounded and abs(self.pos.y - floor) < 6 and self.vel.y >= -30:
            self.pos.y = floor
            self.vel.y = 0
            self.grounded = True
            self.jumps_used = 0

        if self.pos.y < ceiling:
            self.pos.y = ceiling
            if self.vel.y < 0:
                self.vel.y *= -0.22

        if self.pos.x < left:
            self.pos.x = left
            if self.vel.x < 0:
                self.vel.x *= -0.38
        elif self.pos.x > right:
            self.pos.x = right
            if self.vel.x > 0:
                self.vel.x *= -0.38

    def draw(self, surface: pygame.Surface, camera, screen_size: tuple[int, int]) -> None:
        hx, hy = self.half.x, self.half.y
        roof = -hy * 0.78
        local = [
            Vec2(-hx, hy * 0.38),
            Vec2(-hx * 0.85, -hy * 0.35),
            Vec2(-hx * 0.36, roof),
            Vec2(hx * 0.42, roof * 0.92),
            Vec2(hx * 0.88, -hy * 0.18),
            Vec2(hx, hy * 0.42),
        ]
        if self.facing < 0:
            local = [Vec2(-p.x, p.y) for p in local]
        points = [camera.world_to_screen(self.pos + rotate(p, self.angle), screen_size) for p in local]
        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.polygon(surface, (8, 12, 20), points, max(2, camera.scalar(4)))

        cabin = [
            Vec2(-hx * 0.32, -hy * 0.68),
            Vec2(hx * 0.36, -hy * 0.62),
            Vec2(hx * 0.22, -hy * 0.18),
            Vec2(-hx * 0.47, -hy * 0.18),
        ]
        if self.facing < 0:
            cabin = [Vec2(-p.x, p.y) for p in cabin]
        cpoints = [camera.world_to_screen(self.pos + rotate(p, self.angle), screen_size) for p in cabin]
        pygame.draw.polygon(surface, self.accent, cpoints)

        for wx in (-hx * 0.58, hx * 0.58):
            wlocal = Vec2(wx, hy * 0.42)
            if self.facing < 0:
                wlocal.x *= -1
            wp = camera.world_to_screen(self.pos + rotate(wlocal, self.angle), screen_size)
            radius = camera.scalar(18)
            pygame.draw.circle(surface, (9, 12, 17), wp, radius)
            pygame.draw.circle(surface, (88, 100, 122), wp, max(2, radius // 2))

        boost_width = int(76 * self.boost / 100)
        bar_pos = camera.world_to_screen(self.pos + Vec2(-38, -92), screen_size)
        rect = pygame.Rect(bar_pos.x, bar_pos.y, camera.scalar(76), camera.scalar(7))
        pygame.draw.rect(surface, (4, 7, 12), rect, border_radius=4)
        fill = rect.copy()
        fill.width = max(0, int(rect.width * self.boost / 100))
        pygame.draw.rect(surface, BOOST_COLORS.get(self.boost_effect, (72, 190, 255)), fill, border_radius=4)


class Ball:
    def __init__(self, pos: tuple[float, float]) -> None:
        self.pos = Vec2(pos)
        self.vel = Vec2()
        self.radius = 52.0
        self.mass = 32.0
        self.angular_velocity = 0.0
        self.rotation = 0.0
        self.last_touch_team: int | None = None
        self.last_touch_name = ""

    def reset(self, pos: tuple[float, float]) -> None:
        self.pos.update(pos)
        self.vel.update(0, 0)
        self.angular_velocity = 0.0
        self.rotation = 0.0
        self.last_touch_team = None
        self.last_touch_name = ""

    def update(self, dt: float, arena, particles=None) -> None:
        self.vel.y += BALL_GRAVITY * dt
        self.vel *= max(0.0, 1.0 - 0.045 * dt)
        self.pos += self.vel * dt
        self.rotation += self.angular_velocity * dt
        if particles and self.vel.length_squared() > 620 * 620:
            particles.emit_ball_trail(self.pos - safe_normalize(self.vel) * self.radius)
        self._arena_collision(arena)

    def _arena_collision(self, arena) -> None:
        restitution = 0.78
        if self.pos.y + self.radius > arena.floor_y:
            self.pos.y = arena.floor_y - self.radius
            if self.vel.y > 0:
                self.vel.y *= -restitution
                self.vel.x *= 0.985
                self.angular_velocity += self.vel.x * 0.002
        if self.pos.y - self.radius < arena.ceiling_y:
            self.pos.y = arena.ceiling_y + self.radius
            if self.vel.y < 0:
                self.vel.y *= -restitution

        in_goal_mouth = arena.goal_top < self.pos.y < arena.goal_bottom
        if self.pos.x - self.radius < arena.left_wall and not in_goal_mouth:
            self.pos.x = arena.left_wall + self.radius
            if self.vel.x < 0:
                self.vel.x *= -restitution
                self.angular_velocity += self.vel.y * 0.001
        if self.pos.x + self.radius > arena.right_wall and not in_goal_mouth:
            self.pos.x = arena.right_wall - self.radius
            if self.vel.x > 0:
                self.vel.x *= -restitution
                self.angular_velocity += self.vel.y * 0.001

    def draw(self, surface: pygame.Surface, camera, screen_size: tuple[int, int]) -> None:
        p = camera.world_to_screen(self.pos, screen_size)
        r = camera.scalar(self.radius)
        pygame.draw.circle(surface, (238, 242, 249), p, r)
        pygame.draw.circle(surface, (18, 24, 34), p, r, max(2, camera.scalar(4)))
        for angle in (0, 72, 144, 216, 288):
            point = Vec2(r * 0.45, 0).rotate(angle + math.degrees(self.rotation))
            pygame.draw.circle(surface, (76, 94, 118), p + point, max(2, r // 9), max(1, r // 20))
        seam_rect = pygame.Rect(0, 0, r * 1.42, r * 0.64)
        seam_rect.center = (p.x, p.y)
        pygame.draw.arc(surface, (84, 101, 126), seam_rect, 0.2, math.pi - 0.2, max(1, r // 18))


def resolve_ball_car(ball: Ball, car: Car, particles=None, audio=None) -> bool:
    local = rotate(ball.pos - car.pos, -car.angle)
    closest = Vec2(clamp(local.x, -car.half.x, car.half.x), clamp(local.y, -car.half.y, car.half.y))
    world_closest = car.pos + rotate(closest, car.angle)
    diff = ball.pos - world_closest
    dist = diff.length()
    if dist >= ball.radius:
        return False

    normal = safe_normalize(diff, safe_normalize(ball.pos - car.pos, Vec2(0, -1)))
    penetration = ball.radius - dist + 0.5
    ball.pos += normal * penetration * 0.86
    car.pos -= normal * penetration * 0.08

    rel_vel = ball.vel - car.vel
    vel_along = rel_vel.dot(normal)
    if vel_along < 0:
        restitution = 0.76
        impulse_mag = -(1 + restitution) * vel_along
        impulse_mag /= (1 / ball.mass) + (1 / car.mass)
        impulse = normal * impulse_mag
        ball.vel += impulse / ball.mass
        car.vel -= impulse / car.mass

    strike = max(0.0, car.vel.dot(normal)) * 0.36
    if car.flip_timer > 0:
        strike += 780.0
    if car.boosting:
        strike += 180.0
    if strike > 0:
        ball.vel += normal * strike
    tangent = Vec2(-normal.y, normal.x)
    ball.angular_velocity += tangent.dot(ball.vel) * 0.002
    ball.last_touch_team = car.team
    ball.last_touch_name = car.name
    car.touch_cooldown = 0.12

    if particles:
        particles.emit_sparks(world_closest, normal, (255, 240, 172))
    if audio:
        audio.play_varied("collision")
    return True


def resolve_car_car(a: Car, b: Car, particles=None) -> None:
    radius = (a.half.x + b.half.x) * 0.56
    diff = b.pos - a.pos
    dist = diff.length()
    if dist <= 0 or dist >= radius:
        return
    normal = diff / dist
    penetration = radius - dist
    a.pos -= normal * penetration * 0.5
    b.pos += normal * penetration * 0.5
    rel = b.vel - a.vel
    vel_along = rel.dot(normal)
    if vel_along > 0:
        return
    j = -(1.0 + 0.45) * vel_along
    j /= (1 / a.mass) + (1 / b.mass)
    impulse = normal * j
    a.vel -= impulse / a.mass
    b.vel += impulse / b.mass
    if particles:
        particles.emit_sparks((a.pos + b.pos) * 0.5, normal, (200, 220, 255))

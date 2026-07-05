from __future__ import annotations

import random

from .constants import TEAM_BLUE
from .math2d import Vec2


DIFFICULTY = {
    "Rookie": {"lookahead": 0.22, "tolerance": 120, "boost": 0.22, "jump": 0.16, "aerial": 0.04},
    "Pro": {"lookahead": 0.42, "tolerance": 80, "boost": 0.55, "jump": 0.42, "aerial": 0.28},
    "All-Star": {"lookahead": 0.62, "tolerance": 48, "boost": 0.82, "jump": 0.68, "aerial": 0.52},
}


class AIController:
    def __init__(self, difficulty: str = "Pro") -> None:
        self.difficulty = difficulty if difficulty in DIFFICULTY else "Pro"
        self.jump_cooldown = 0.0
        self.strategy_timer = 0.0
        self.mode = "attack"

    def controls(self, car, ball, arena, dt: float, score: tuple[int, int]) -> dict[str, bool]:
        params = DIFFICULTY[self.difficulty]
        self.jump_cooldown = max(0.0, self.jump_cooldown - dt)
        self.strategy_timer -= dt
        attack_dir = 1 if car.team == TEAM_BLUE else -1
        own_goal_x = arena.left_wall if car.team == TEAM_BLUE else arena.right_wall
        opp_goal_x = arena.right_wall if car.team == TEAM_BLUE else arena.left_wall

        ball_to_own = (ball.vel.x < -160 and car.team == TEAM_BLUE) or (
            ball.vel.x > 160 and car.team != TEAM_BLUE
        )
        danger_zone = (ball.pos.x - own_goal_x) * attack_dir < 1050
        if self.strategy_timer <= 0:
            if danger_zone or ball_to_own:
                self.mode = "defend"
            elif (ball.pos.x - car.pos.x) * attack_dir > -260:
                self.mode = "attack"
            else:
                self.mode = "rotate"
            self.strategy_timer = random.uniform(0.35, 0.8)

        predicted = ball.pos + ball.vel * params["lookahead"]
        if self.mode == "defend":
            target = Vec2(own_goal_x + attack_dir * 430, arena.floor_y - 130)
            if abs(ball.pos.x - own_goal_x) < 520:
                target = Vec2(ball.pos.x - attack_dir * 90, ball.pos.y)
        elif self.mode == "rotate":
            target = Vec2(ball.pos.x - attack_dir * 420, arena.floor_y - 105)
        else:
            target = Vec2(predicted.x - attack_dir * 110, predicted.y)

        target.x = max(arena.left_wall + 120, min(arena.right_wall - 120, target.x))
        target.y = max(arena.ceiling_y + 130, min(arena.floor_y - 80, target.y))

        controls = {
            "throttle": False,
            "brake": False,
            "steer_left": False,
            "steer_right": False,
            "jump_pressed": False,
            "boost": False,
            "air_roll_left": False,
            "air_roll_right": False,
            "powerslide": False,
        }

        dx = target.x - car.pos.x
        desired = 1 if dx >= 0 else -1
        if desired > 0:
            controls["steer_right"] = True
        else:
            controls["steer_left"] = True
        if abs(dx) > params["tolerance"]:
            controls["throttle"] = True
        else:
            controls["brake"] = abs(car.vel.x) > 320

        aligned = car.facing == desired
        distance = abs(dx)
        moving_to_target = car.vel.x * desired > 220
        if (
            aligned
            and moving_to_target
            and distance > 420
            and car.boost > 8
            and random.random() < params["boost"]
        ):
            controls["boost"] = True

        ball_close = car.pos.distance_to(ball.pos) < 360
        high_ball = ball.pos.y < arena.floor_y - 215
        if self.jump_cooldown <= 0 and ball_close and random.random() < params["jump"]:
            if high_ball or abs(ball.pos.x - car.pos.x) < 180:
                controls["jump_pressed"] = True
                self.jump_cooldown = random.uniform(0.45, 0.9)

        if (
            self.jump_cooldown <= 0
            and high_ball
            and ball_close
            and random.random() < params["aerial"]
        ):
            controls["jump_pressed"] = True
            controls["boost"] = car.boost > 18
            self.jump_cooldown = random.uniform(0.55, 1.05)

        if not car.grounded:
            if ball.pos.x > car.pos.x:
                controls["steer_right"] = True
                controls["steer_left"] = False
            else:
                controls["steer_left"] = True
                controls["steer_right"] = False

        if self.mode == "attack" and abs(ball.pos.x - opp_goal_x) < 600:
            controls["boost"] = controls["boost"] or (car.boost > 25 and aligned)
        return controls

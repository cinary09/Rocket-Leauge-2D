from __future__ import annotations

import math
import random
from copy import deepcopy

import pygame

from .ai import AIController
from .arenas import ARENAS, get_arena
from .camera import Camera
from .constants import COLORS, TEAM_BLUE, TEAM_ORANGE
from .entities import (
    BOOST_COLORS,
    CAR_BODIES,
    Ball,
    BoostPad,
    Car,
    resolve_ball_car,
    resolve_car_car,
)
from .math2d import Vec2, format_time
from .particles import ParticleSystem
from .persistence import DEFAULT_STATS
from .settings import ACTION_LABELS, DEFAULT_KEYS, GRAPHICS_QUALITY, RESOLUTIONS, Settings
from .ui import Button, KeyBind, Selector, Slider, Toggle, draw_text


class Scene:
    def __init__(self, game) -> None:
        self.game = game

    def enter(self) -> None:
        return None

    def handle_event(self, event: pygame.event.Event) -> None:
        return None

    def update(self, dt: float) -> None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        return None


class MenuScene(Scene):
    title = ""

    def __init__(self, game) -> None:
        super().__init__(game)
        self.widgets: list = []
        self.bg_time = 0.0

    def enter(self) -> None:
        self.game.audio.music("menu")
        self.layout()

    def layout(self) -> None:
        self.widgets = []

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.VIDEORESIZE:
            self.layout()
        for widget in self.widgets:
            if widget.handle_event(event):
                self.game.audio.play("select")
                break

    def update(self, dt: float) -> None:
        self.bg_time += dt

    def draw_background(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        top = pygame.Color(13, 18, 31)
        bottom = pygame.Color(30, 50, 78)
        for y in range(0, h, 4):
            t = y / max(1, h)
            color = top.lerp(bottom, t)
            pygame.draw.rect(surface, color, (0, y, w, 4))
        floor_y = int(h * 0.76)
        pygame.draw.rect(surface, (25, 86, 78), (0, floor_y, w, h - floor_y))
        pygame.draw.line(surface, (92, 220, 141), (0, floor_y), (w, floor_y), 4)
        for i in range(18):
            x = int((i * 173 + self.bg_time * 28) % (w + 160) - 80)
            height = 80 + (i * 37) % 170
            rect = pygame.Rect(x, floor_y - height, 80 + (i * 13) % 70, height)
            pygame.draw.rect(surface, (18, 28, 45), rect)
            if i % 3 == 0:
                pygame.draw.rect(surface, (38, 161, 255), rect.inflate(-24, -height + 18))

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_background(surface)
        for widget in self.widgets:
            widget.draw(surface, self.game.font(28))


class MainMenuScene(MenuScene):
    def layout(self) -> None:
        w, h = self.game.screen.get_size()
        bw, bh = 340, 56
        x = int(w * 0.12)
        y = int(h * 0.38)
        gap = 14
        self.widgets = [
            Button(pygame.Rect(x, y + (bh + gap) * 0, bw, bh), "Play", lambda: self.game.change_scene(PlayMenuScene(self.game)), "PLAY"),
            Button(pygame.Rect(x, y + (bh + gap) * 1, bw, bh), "Training", lambda: self.game.change_scene(TrainingMenuScene(self.game)), "TRAIN"),
            Button(pygame.Rect(x, y + (bh + gap) * 2, bw, bh), "Garage", lambda: self.game.change_scene(GarageScene(self.game)), "CAR"),
            Button(pygame.Rect(x, y + (bh + gap) * 3, bw, bh), "Settings", lambda: self.game.change_scene(SettingsScene(self.game, MainMenuScene(self.game))), "SET"),
            Button(pygame.Rect(x, y + (bh + gap) * 4, bw, bh), "Statistics", lambda: self.game.change_scene(StatsScene(self.game)), "STATS"),
            Button(pygame.Rect(x, y + (bh + gap) * 5, bw, bh), "Quit", self.game.quit, "QUIT"),
        ]

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        w, h = surface.get_size()
        title_font = self.game.font(82, bold=True)
        sub_font = self.game.font(28)
        pulse = 0.5 + 0.5 * math.sin(self.bg_time * 2.5)
        draw_text(surface, title_font, "ROCKET 2D", COLORS["white"], (int(w * 0.12), int(h * 0.16)), "topleft")
        draw_text(surface, title_font, "LEAGUE", (38, 161 + int(50 * pulse), 255), (int(w * 0.12), int(h * 0.25)), "topleft")
        draw_text(surface, sub_font, "Side-view car soccer with boost, flips, saves, and overtime.", COLORS["muted"], (int(w * 0.12), int(h * 0.34)), "topleft")
        car = pygame.Rect(int(w * 0.62), int(h * 0.56), 260, 82)
        pygame.draw.rect(surface, COLORS["blue"], car, border_radius=20)
        pygame.draw.polygon(surface, (238, 242, 249), [(car.x + 80, car.y), (car.x + 180, car.y + 8), (car.x + 205, car.y + 42), (car.x + 50, car.y + 42)])
        pygame.draw.circle(surface, (8, 12, 20), (car.x + 54, car.bottom), 34)
        pygame.draw.circle(surface, (8, 12, 20), (car.right - 54, car.bottom), 34)
        pygame.draw.circle(surface, (238, 242, 249), (int(w * 0.74), int(h * 0.36)), 48)


class PlayMenuScene(MenuScene):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.difficulty = "Pro"
        self.arena = "Standard Arena"
        self.length = "5 Minutes"

    def layout(self) -> None:
        w, h = self.game.screen.get_size()
        x = int(w * 0.5) - 190
        y = int(h * 0.28)
        self.widgets = [
            Selector(pygame.Rect(x, y, 380, 56), "Difficulty", ["Rookie", "Pro", "All-Star"], self.difficulty, self._difficulty),
            Selector(pygame.Rect(x, y + 86, 380, 56), "Arena", list(ARENAS.keys()), self.arena, self._arena),
            Selector(pygame.Rect(x, y + 172, 380, 56), "Match Length", ["3 Minutes", "5 Minutes", "10 Minutes"], self.length, self._length),
            Button(pygame.Rect(x, y + 275, 380, 58), "Start Exhibition", self.start, "PLAY"),
            Button(pygame.Rect(x, y + 345, 380, 54), "Back", lambda: self.game.change_scene(MainMenuScene(self.game)), "BACK"),
        ]

    def _difficulty(self, value: str) -> None:
        self.difficulty = value

    def _arena(self, value: str) -> None:
        self.arena = value

    def _length(self, value: str) -> None:
        self.length = value

    def start(self) -> None:
        minutes = int(self.length.split()[0])
        self.game.change_scene(
            MatchScene(self.game, "Exhibition Match", get_arena(self.arena), self.difficulty, minutes * 60)
        )

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        draw_text(surface, self.game.font(58, True), "Exhibition Match", COLORS["white"], (surface.get_width() // 2, int(surface.get_height() * 0.16)), "center")


class TrainingMenuScene(MenuScene):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.arena = "Standard Arena"

    def layout(self) -> None:
        w, h = self.game.screen.get_size()
        x = w // 2 - 190
        y = int(h * 0.3)
        self.widgets = [
            Selector(pygame.Rect(x, y, 380, 56), "Arena", list(ARENAS.keys()), self.arena, self._arena),
            Button(pygame.Rect(x, y + 105, 380, 58), "Free Play", self.free_play, "FREE"),
            Button(pygame.Rect(x, y + 175, 380, 58), "Practice Arena", self.practice, "SHOT"),
            Button(pygame.Rect(x, y + 255, 380, 54), "Back", lambda: self.game.change_scene(MainMenuScene(self.game)), "BACK"),
        ]

    def _arena(self, value: str) -> None:
        self.arena = value

    def free_play(self) -> None:
        self.game.change_scene(MatchScene(self.game, "Free Play", get_arena(self.arena), "Pro", 0))

    def practice(self) -> None:
        self.game.change_scene(MatchScene(self.game, "Practice Arena", get_arena(self.arena), "Pro", 0))

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        draw_text(surface, self.game.font(58, True), "Training", COLORS["white"], (surface.get_width() // 2, int(surface.get_height() * 0.17)), "center")


class GarageScene(MenuScene):
    COLORS = {
        "Blue": [38, 161, 255],
        "Orange": [255, 142, 43],
        "Green": [92, 220, 141],
        "Crimson": [255, 82, 96],
        "Violet": [204, 93, 255],
        "White": [242, 246, 252],
    }

    def __init__(self, game) -> None:
        super().__init__(game)
        self.garage = deepcopy(game.garage)
        self.body = self.garage["body"]
        self.primary_name = self._color_name(self.garage["primary_color"])
        self.accent_name = self._color_name(self.garage["accent_color"])
        self.boost_effect = self.garage["boost_effect"]

    def _color_name(self, rgb: list[int]) -> str:
        for name, color in self.COLORS.items():
            if list(color) == list(rgb):
                return name
        return "Blue"

    def layout(self) -> None:
        w, h = self.game.screen.get_size()
        x = int(w * 0.1)
        y = int(h * 0.3)
        self.widgets = [
            Selector(pygame.Rect(x, y, 380, 56), "Car Body", self.garage["unlocked_bodies"], self.body, self._body),
            Selector(pygame.Rect(x, y + 86, 380, 56), "Primary Color", list(self.COLORS), self.primary_name, self._primary),
            Selector(pygame.Rect(x, y + 172, 380, 56), "Accent Color", list(self.COLORS), self.accent_name, self._accent),
            Selector(pygame.Rect(x, y + 258, 380, 56), "Boost Effect", self.garage["unlocked_boosts"], self.boost_effect, self._boost),
            Button(pygame.Rect(x, y + 365, 180, 54), "Save", self.save, "SAVE"),
            Button(pygame.Rect(x + 200, y + 365, 180, 54), "Back", lambda: self.game.change_scene(MainMenuScene(self.game)), "BACK"),
        ]

    def _body(self, value: str) -> None:
        self.body = value

    def _primary(self, value: str) -> None:
        self.primary_name = value

    def _accent(self, value: str) -> None:
        self.accent_name = value

    def _boost(self, value: str) -> None:
        self.boost_effect = value

    def save(self) -> None:
        self.garage.update(
            {
                "body": self.body,
                "primary_color": self.COLORS[self.primary_name],
                "accent_color": self.COLORS[self.accent_name],
                "boost_effect": self.boost_effect,
            }
        )
        self.game.garage = deepcopy(self.garage)
        self.game.store.save_garage(self.game.garage)
        self.game.toast("Garage saved")

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        w, h = surface.get_size()
        draw_text(surface, self.game.font(58, True), "Garage", COLORS["white"], (int(w * 0.1), int(h * 0.16)), "topleft")
        preview = pygame.Rect(int(w * 0.55), int(h * 0.32), 460, 190)
        pygame.draw.rect(surface, (11, 16, 28), preview, border_radius=8)
        pygame.draw.rect(surface, (72, 92, 122), preview, 2, border_radius=8)
        car = Car(TEAM_BLUE, (preview.centerx, preview.centery + 35), self.body, tuple(self.COLORS[self.primary_name]), tuple(self.COLORS[self.accent_name]), self.boost_effect)
        cam = Camera()
        cam.center = car.pos.copy()
        cam.zoom = 1.6
        cam.offset = Vec2(preview.centerx - w / 2, preview.centery - h / 2)
        car.angle = math.sin(self.bg_time * 1.4) * 0.08
        car.boost = 100
        car.draw(surface, cam, surface.get_size())
        color = BOOST_COLORS.get(self.boost_effect, COLORS["blue"])
        for i in range(12):
            pygame.draw.circle(surface, color, (preview.centerx - 150 - i * 12, preview.centery + 35 + int(math.sin(self.bg_time * 8 + i) * 12)), max(2, 12 - i // 2))


class SettingsScene(MenuScene):
    def __init__(self, game, back_scene: Scene) -> None:
        super().__init__(game)
        self.back_scene = back_scene
        self.working = Settings.from_dict(game.settings.to_dict())

    def layout(self) -> None:
        w, h = self.game.screen.get_size()
        left = int(w * 0.08)
        right = int(w * 0.55)
        y = int(h * 0.22)
        self.widgets = [
            Selector(pygame.Rect(left, y, 370, 54), "Resolution", [f"{a}x{b}" for a, b in RESOLUTIONS], f"{self.working.resolution[0]}x{self.working.resolution[1]}", self._resolution),
            Selector(pygame.Rect(left, y + 82, 370, 54), "Graphics", GRAPHICS_QUALITY, self.working.graphics_quality, self._graphics),
            Toggle(pygame.Rect(left, y + 162, 370, 46), "Fullscreen", self.working.fullscreen, self._fullscreen),
            Toggle(pygame.Rect(left, y + 222, 370, 46), "Screen Shake", self.working.screen_shake, self._shake),
            Toggle(pygame.Rect(left, y + 282, 370, 46), "Show FPS", self.working.show_fps, self._fps),
            Slider(pygame.Rect(left, y + 380, 370, 42), "Master", self.working.master_volume, self._master),
            Slider(pygame.Rect(left, y + 450, 370, 42), "Music", self.working.music_volume, self._music),
            Slider(pygame.Rect(left, y + 520, 370, 42), "Effects", self.working.effects_volume, self._effects),
        ]
        key_y = y
        for index, action in enumerate(DEFAULT_KEYS):
            self.widgets.append(
                KeyBind(
                    pygame.Rect(right, key_y + index * 48, 430, 42),
                    ACTION_LABELS[action],
                    self.working.key_bindings[action],
                    lambda value, a=action: self._key(a, value),
                )
            )
        self.widgets.extend(
            [
                Button(pygame.Rect(left, h - 92, 180, 54), "Apply", self.apply, "SAVE"),
                Button(pygame.Rect(left + 200, h - 92, 180, 54), "Back", self.back, "BACK"),
            ]
        )

    def _resolution(self, value: str) -> None:
        a, b = value.split("x")
        self.working.resolution = (int(a), int(b))

    def _graphics(self, value: str) -> None:
        self.working.graphics_quality = value

    def _fullscreen(self, value: bool) -> None:
        self.working.fullscreen = value

    def _shake(self, value: bool) -> None:
        self.working.screen_shake = value

    def _fps(self, value: bool) -> None:
        self.working.show_fps = value

    def _master(self, value: float) -> None:
        self.working.master_volume = value
        self.game.audio.set_volumes(self.working)

    def _music(self, value: float) -> None:
        self.working.music_volume = value
        self.game.audio.set_volumes(self.working)

    def _effects(self, value: float) -> None:
        self.working.effects_volume = value
        self.game.audio.set_volumes(self.working)

    def _key(self, action: str, value: str) -> None:
        self.working.key_bindings[action] = value

    def apply(self) -> None:
        self.game.settings = Settings.from_dict(self.working.to_dict())
        self.game.store.save_settings(self.game.settings)
        self.game.audio.set_volumes(self.game.settings)
        self.game.apply_display_settings()
        self.layout()
        self.game.toast("Settings applied")

    def back(self) -> None:
        self.apply()
        self.game.change_scene(self.back_scene)

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        draw_text(surface, self.game.font(54, True), "Settings", COLORS["white"], (int(surface.get_width() * 0.08), int(surface.get_height() * 0.12)), "topleft")


class StatsScene(MenuScene):
    def layout(self) -> None:
        w, h = self.game.screen.get_size()
        self.widgets = [
            Button(pygame.Rect(int(w * 0.1), h - 92, 210, 54), "Reset Stats", self.reset_stats, "RESET"),
            Button(pygame.Rect(int(w * 0.1) + 230, h - 92, 180, 54), "Back", lambda: self.game.change_scene(MainMenuScene(self.game)), "BACK"),
        ]

    def reset_stats(self) -> None:
        self.game.stats = deepcopy(DEFAULT_STATS)
        self.game.store.save_stats(self.game.stats)
        self.game.toast("Statistics reset")

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        x = int(surface.get_width() * 0.1)
        y = int(surface.get_height() * 0.16)
        draw_text(surface, self.game.font(58, True), "Statistics", COLORS["white"], (x, y), "topleft")
        stat_font = self.game.font(32)
        for index, (key, value) in enumerate(self.game.stats.items()):
            label = key.replace("_", " ").title()
            draw_text(surface, stat_font, f"{label}: {value}", COLORS["white"], (x, y + 100 + index * 42), "topleft")


class MatchScene(Scene):
    def __init__(self, game, mode: str, arena, difficulty: str, length_seconds: int) -> None:
        super().__init__(game)
        self.mode = mode
        self.arena = arena
        self.difficulty = difficulty
        self.length_seconds = length_seconds
        self.camera = Camera()
        self.particles = ParticleSystem()
        self.player: Car | None = None
        self.ai_car: Car | None = None
        self.ai = AIController(difficulty)
        self.ball = Ball((arena.width / 2, arena.floor_y - 360))
        self.pads: list[BoostPad] = []
        self.score = [0, 0]
        self.match_time = float(length_seconds)
        self.overtime = False
        self.phase = "kickoff"
        self.countdown = 3.2
        self.goal_timer = 0.0
        self.pending_end = False
        self.paused = False
        self.pause_widgets: list[Button] = []
        self.jump_edge = False
        self.countdown_beep = 4
        self.local_stats = {"goals": 0, "shots": 0, "saves": 0, "training_targets": 0}
        self.practice_target = Vec2(self.arena.right_wall - 120, self.arena.goal_top + 160)
        self.initialized = False

    def enter(self) -> None:
        self.game.audio.music("match")
        if not self.initialized:
            self._create_entities()
            self._kickoff_reset()
            self.initialized = True
        self._layout_pause()

    def _create_entities(self) -> None:
        garage = self.game.garage
        primary = tuple(garage["primary_color"])
        accent = tuple(garage["accent_color"])
        self.player = Car(TEAM_BLUE, (620, self.arena.floor_y - 80), garage["body"], primary, accent, garage["boost_effect"], "You")
        if self.mode == "Exhibition Match":
            self.ai_car = Car(TEAM_ORANGE, (2580, self.arena.floor_y - 80), "Dominus", COLORS["orange"], COLORS["white"], "Flame", self.difficulty)
        else:
            self.ai_car = None
        self.pads = [
            BoostPad(Vec2(pad.x, pad.y), pad.amount, 68 if pad.amount >= 100 else 46, 10.0 if pad.amount >= 100 else 4.0)
            for pad in self.arena.pads
        ]

    def _kickoff_reset(self) -> None:
        self.phase = "kickoff"
        self.countdown = 3.2
        self.countdown_beep = 4
        self.pending_end = False
        self.ball.reset((self.arena.width / 2, self.arena.floor_y - 360))
        if self.player:
            self.player.reset((650, self.arena.floor_y - 80), 1)
            self.player.boost = max(self.player.boost, 34)
        if self.ai_car:
            self.ai_car.reset((2550, self.arena.floor_y - 80), -1)
            self.ai_car.boost = max(self.ai_car.boost, 34)
        for pad in self.pads:
            pad.cooldown = 0

    def _layout_pause(self) -> None:
        w, h = self.game.screen.get_size()
        x = w // 2 - 170
        y = h // 2 - 130
        self.pause_widgets = [
            Button(pygame.Rect(x, y, 340, 54), "Resume", self.resume, "PLAY"),
            Button(pygame.Rect(x, y + 66, 340, 54), "Restart", self.restart, "RESET"),
            Button(pygame.Rect(x, y + 132, 340, 54), "Settings", lambda: self.game.change_scene(SettingsScene(self.game, self)), "SET"),
            Button(pygame.Rect(x, y + 198, 340, 54), "Main Menu", lambda: self.game.change_scene(MainMenuScene(self.game)), "MENU"),
        ]

    def resume(self) -> None:
        self.paused = False

    def restart(self) -> None:
        self.score = [0, 0]
        self.match_time = float(self.length_seconds)
        self.overtime = False
        self.paused = False
        self._kickoff_reset()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.VIDEORESIZE:
            self._layout_pause()
        if event.type == pygame.KEYDOWN:
            if self._action_from_key(event.key, "pause"):
                self.paused = not self.paused
                return
            if self._action_from_key(event.key, "jump"):
                self.jump_edge = True
            if self.mode in ("Free Play", "Practice Arena") and event.key == pygame.K_r:
                self._kickoff_reset()
        if self.paused:
            for widget in self.pause_widgets:
                if widget.handle_event(event):
                    self.game.audio.play("select")
                    break

    def _action_from_key(self, key: int, action: str) -> bool:
        name = self.game.settings.key_bindings.get(action, DEFAULT_KEYS[action])
        try:
            return key == pygame.key.key_code(name)
        except ValueError:
            return False

    def _player_controls(self) -> dict[str, bool]:
        pressed = pygame.key.get_pressed()

        def down(action: str) -> bool:
            name = self.game.settings.key_bindings.get(action, DEFAULT_KEYS[action])
            try:
                return pressed[pygame.key.key_code(name)]
            except (ValueError, IndexError):
                return False

        return {
            "throttle": down("throttle"),
            "brake": down("brake"),
            "steer_left": down("steer_left"),
            "steer_right": down("steer_right"),
            "jump_pressed": self.jump_edge,
            "boost": down("boost"),
            "air_roll_left": down("air_roll_left"),
            "air_roll_right": down("air_roll_right"),
            "powerslide": down("powerslide"),
        }

    def update(self, dt: float) -> None:
        if not self.player:
            return
        if self.paused:
            self.jump_edge = False
            return

        self.particles.set_quality(self.game.settings.graphics_quality)
        self.particles.update(dt)
        if self.phase == "kickoff":
            self.countdown -= dt
            next_beep = math.ceil(self.countdown)
            if next_beep < self.countdown_beep and next_beep >= 0:
                self.game.audio.play("countdown")
                self.countdown_beep = next_beep
            if self.countdown <= 0:
                self.phase = "play"
            self._camera_update(dt)
            self.jump_edge = False
            return

        if self.phase == "goal":
            self.goal_timer -= dt
            if self.goal_timer <= 0:
                if self.pending_end:
                    self._end_match()
                else:
                    self._kickoff_reset()
            self._camera_update(dt)
            self.jump_edge = False
            return

        if self.mode == "Exhibition Match" and not self.overtime:
            self.match_time -= dt
            if self.match_time <= 0:
                self.match_time = 0
                if self.score[0] == self.score[1]:
                    self.overtime = True
                    self.game.toast("Overtime: next goal wins")
                else:
                    self._end_match()
                    return

        if self.mode in ("Free Play", "Practice Arena"):
            self.player.boost = min(100.0, self.player.boost + 18.0 * dt)

        steps = 3
        step_dt = min(dt, 1 / 30) / steps
        for _ in range(steps):
            self._physics_step(step_dt)

        if self.mode == "Practice Arena":
            self._practice_update()
        self._check_goal()
        self._camera_update(dt)
        self.jump_edge = False

    def _physics_step(self, dt: float) -> None:
        assert self.player is not None
        controls = self._player_controls()
        self.player.update(dt, controls, self.arena, self.particles, self.game.audio)
        if self.ai_car:
            ai_controls = self.ai.controls(self.ai_car, self.ball, self.arena, dt, tuple(self.score))
            self.ai_car.update(dt, ai_controls, self.arena, self.particles, self.game.audio)
            resolve_car_car(self.player, self.ai_car, self.particles)

        self.ball.update(dt, self.arena, self.particles)
        if resolve_ball_car(self.ball, self.player, self.particles, self.game.audio):
            self._award_touch_stats(self.player)
        if self.ai_car:
            resolve_ball_car(self.ball, self.ai_car, self.particles, self.game.audio)

        for pad in self.pads:
            pad.update(dt)
            if pad.try_collect(self.player):
                self.game.audio.play("boost")
            if self.ai_car:
                pad.try_collect(self.ai_car)

    def _award_touch_stats(self, car: Car) -> None:
        if car.team != TEAM_BLUE:
            return
        if self.ball.vel.x > 520 and self.ball.pos.x > self.arena.width * 0.45:
            self.local_stats["shots"] += 1
        if self.ball.pos.x < self.arena.left_wall + 620 and self.ball.vel.x > 180:
            self.local_stats["saves"] += 1

    def _practice_update(self) -> None:
        if self.ball.pos.distance_to(self.practice_target) < 92:
            self.local_stats["training_targets"] += 1
            self.game.stats["training_targets"] += 1
            self.game.store.save_stats(self.game.stats)
            self.game.audio.play("goal")
            self.particles.emit_goal(self.practice_target, COLORS["green"])
            self.practice_target = Vec2(
                random.choice([self.arena.left_wall + 140, self.arena.right_wall - 140]),
                random.uniform(self.arena.goal_top + 80, self.arena.floor_y - 220),
            )
            self.ball.reset((self.arena.width / 2, self.arena.floor_y - 380))

    def _check_goal(self) -> None:
        if self.phase != "play":
            return
        goal_team = None
        goal_pos = None
        if self.ball.pos.x < self.arena.left_wall - 120 and self.arena.goal_top < self.ball.pos.y < self.arena.goal_bottom + 80:
            goal_team = TEAM_ORANGE
            goal_pos = Vec2(self.arena.left_wall, self.ball.pos.y)
        elif self.ball.pos.x > self.arena.right_wall + 120 and self.arena.goal_top < self.ball.pos.y < self.arena.goal_bottom + 80:
            goal_team = TEAM_BLUE
            goal_pos = Vec2(self.arena.right_wall, self.ball.pos.y)
        if goal_team is None:
            return

        if self.mode == "Exhibition Match":
            self.score[goal_team] += 1
            if goal_team == TEAM_BLUE:
                self.local_stats["goals"] += 1
            self.pending_end = self.overtime
        else:
            self.pending_end = False
        self.phase = "goal"
        self.goal_timer = 2.2
        self.ball.vel *= 0.15
        color = COLORS["blue"] if goal_team == TEAM_BLUE else COLORS["orange"]
        self.particles.emit_goal(goal_pos or self.ball.pos, color)
        self.game.audio.play("goal")
        if self.game.settings.screen_shake:
            self.camera.add_shake(20)

    def _camera_update(self, dt: float) -> None:
        points = [self.ball.pos]
        if self.player:
            points.append(self.player.pos)
        if self.ai_car:
            points.append(self.ai_car.pos)
        self.camera.update(dt, self.game.screen.get_size(), points)

    def _end_match(self) -> None:
        if self.mode == "Exhibition Match":
            self.game.stats["matches_played"] += 1
            self.game.stats["goals"] += self.local_stats["goals"]
            self.game.stats["shots"] += self.local_stats["shots"]
            self.game.stats["saves"] += self.local_stats["saves"]
            if self.score[0] > self.score[1]:
                self.game.stats["wins"] += 1
                self.game.stats["mvp_awards"] += 1 if self.local_stats["goals"] or self.local_stats["saves"] else 0
                self.game.career["xp"] += 150 + self.local_stats["goals"] * 40 + self.local_stats["saves"] * 25
            else:
                self.game.stats["losses"] += 1
                self.game.career["xp"] += 60 + self.local_stats["goals"] * 35
            while self.game.career["xp"] >= self.game.career["level"] * 300:
                self.game.career["xp"] -= self.game.career["level"] * 300
                self.game.career["level"] += 1
                if self.game.career["level"] >= 5:
                    self.game.career["rank"] = "Pro"
                if self.game.career["level"] >= 12:
                    self.game.career["rank"] = "All-Star"
            self.game.store.save_stats(self.game.stats)
            self.game.store.save_career(self.game.career)
        self.game.change_scene(MatchEndScene(self.game, self.mode, tuple(self.score), self.local_stats, self.arena, self.difficulty, self.length_seconds))

    def draw(self, surface: pygame.Surface) -> None:
        self._draw_arena(surface)
        self.particles.draw(surface, self.camera, surface.get_size())
        for pad in self.pads:
            self._draw_pad(surface, pad)
        if self.ball:
            self.ball.draw(surface, self.camera, surface.get_size())
        if self.ai_car:
            self.ai_car.draw(surface, self.camera, surface.get_size())
        if self.player:
            self.player.draw(surface, self.camera, surface.get_size())
        if self.mode == "Practice Arena":
            p = self.camera.world_to_screen(self.practice_target, surface.get_size())
            r = self.camera.scalar(86)
            pygame.draw.circle(surface, COLORS["green"], p, r, max(3, self.camera.scalar(8)))
            pygame.draw.circle(surface, (255, 255, 255), p, max(4, r // 4), max(2, self.camera.scalar(4)))
        self._draw_hud(surface)
        if self.paused:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surface.blit(overlay, (0, 0))
            draw_text(surface, self.game.font(56, True), "Paused", COLORS["white"], (surface.get_width() // 2, surface.get_height() // 2 - 190), "center")
            for widget in self.pause_widgets:
                widget.draw(surface, self.game.font(28))

    def _draw_arena(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        surface.fill(self.arena.sky)
        horizon = self.camera.world_to_screen(Vec2(0, self.arena.floor_y - 540), (w, h)).y
        pygame.draw.rect(surface, self.arena.horizon, (0, horizon, w, h - horizon))
        building_count = {"Performance": 10, "Balanced": 15, "High": 20}.get(
            self.game.settings.graphics_quality, 20
        )
        for i in range(building_count):
            x_world = i * 180 + (i % 3) * 60
            p = self.camera.world_to_screen(Vec2(x_world, self.arena.floor_y - 540), (w, h))
            height = self.camera.scalar(150 + (i * 37) % 260)
            rect = pygame.Rect(p.x, p.y - height, self.camera.scalar(90 + (i * 13) % 90), height)
            pygame.draw.rect(surface, tuple(max(0, c - 18) for c in self.arena.horizon), rect)
        floor_rect = pygame.Rect(
            self.camera.world_to_screen(Vec2(0, self.arena.floor_y), (w, h)).x,
            self.camera.world_to_screen(Vec2(0, self.arena.floor_y), (w, h)).y,
            int(self.arena.width * self.camera.zoom),
            h,
        )
        pygame.draw.rect(surface, self.arena.floor, floor_rect)
        self._world_line(surface, Vec2(self.arena.left_wall, self.arena.floor_y), Vec2(self.arena.right_wall, self.arena.floor_y), self.arena.trim, 6)
        self._world_line(surface, Vec2(self.arena.left_wall, self.arena.ceiling_y), Vec2(self.arena.right_wall, self.arena.ceiling_y), self.arena.trim, 5)
        self._world_line(surface, Vec2(self.arena.left_wall, self.arena.ceiling_y), Vec2(self.arena.left_wall, self.arena.goal_top), self.arena.trim, 5)
        self._world_line(surface, Vec2(self.arena.right_wall, self.arena.ceiling_y), Vec2(self.arena.right_wall, self.arena.goal_top), self.arena.trim, 5)
        self._world_line(surface, Vec2(self.arena.width / 2, self.arena.ceiling_y), Vec2(self.arena.width / 2, self.arena.floor_y), (255, 255, 255), 2)
        self._draw_goal(surface, TEAM_BLUE)
        self._draw_goal(surface, TEAM_ORANGE)

    def _world_line(self, surface, a: Vec2, b: Vec2, color, width: int) -> None:
        pygame.draw.line(
            surface,
            color,
            self.camera.world_to_screen(a, surface.get_size()),
            self.camera.world_to_screen(b, surface.get_size()),
            self.camera.scalar(width),
        )

    def _draw_goal(self, surface: pygame.Surface, team: int) -> None:
        x = self.arena.left_wall if team == TEAM_BLUE else self.arena.right_wall
        color = COLORS["blue"] if team == TEAM_BLUE else COLORS["orange"]
        direction = -1 if team == TEAM_BLUE else 1
        mouth_top = Vec2(x, self.arena.goal_top)
        back = Vec2(x + direction * 210, self.arena.goal_bottom)
        p1 = self.camera.world_to_screen(mouth_top, surface.get_size())
        p2 = self.camera.world_to_screen(back, surface.get_size())
        rect = pygame.Rect(min(p1.x, p2.x), p1.y, abs(p2.x - p1.x), p2.y - p1.y)
        pygame.draw.rect(surface, (*color, 35), rect)
        pygame.draw.rect(surface, color, rect, self.camera.scalar(4))
        for i in range(5):
            y = self.arena.goal_top + i * (self.arena.goal_bottom - self.arena.goal_top) / 4
            self._world_line(surface, Vec2(x, y), Vec2(x + direction * 210, y), (*color,), 1)

    def _draw_pad(self, surface: pygame.Surface, pad: BoostPad) -> None:
        p = self.camera.world_to_screen(pad.pos, surface.get_size())
        rx = self.camera.scalar(pad.radius)
        ry = self.camera.scalar(pad.radius * 0.34)
        color = COLORS["yellow"] if pad.active else (70, 72, 78)
        pygame.draw.ellipse(surface, color, pygame.Rect(p.x - rx, p.y - ry, rx * 2, ry * 2))
        pygame.draw.ellipse(surface, (255, 248, 170) if pad.active else (94, 96, 104), pygame.Rect(p.x - rx // 2, p.y - ry // 2, rx, ry))

    def _draw_hud(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        hud_font = self.game.font(42, True)
        small = self.game.font(24)
        if self.mode == "Exhibition Match":
            draw_text(surface, hud_font, str(self.score[0]), COLORS["blue"], (w // 2 - 110, 44), "center")
            draw_text(surface, hud_font, str(self.score[1]), COLORS["orange"], (w // 2 + 110, 44), "center")
            draw_text(surface, self.game.font(34, True), format_time(self.match_time, self.overtime), COLORS["white"], (w // 2, 45), "center")
        else:
            draw_text(surface, self.game.font(34, True), self.mode, COLORS["white"], (w // 2, 44), "center")
            draw_text(surface, small, "Press R to reset the drill", COLORS["muted"], (w // 2, 78), "center")
        if self.player:
            meter = pygame.Rect(w - 176, h - 84, 132, 34)
            pygame.draw.rect(surface, (8, 12, 20), meter, border_radius=7)
            fill = meter.copy()
            fill.width = int(meter.width * self.player.boost / 100)
            pygame.draw.rect(surface, BOOST_COLORS.get(self.player.boost_effect, COLORS["blue"]), fill, border_radius=7)
            pygame.draw.rect(surface, (220, 230, 245), meter, 2, border_radius=7)
            draw_text(surface, small, f"{int(self.player.boost)} BOOST", COLORS["white"], meter.center, "center")
            speed = int(self.player.vel.length() / 18)
            draw_text(surface, small, f"{speed} km/h", COLORS["white"], (48, h - 58), "midleft")
        if self.phase == "kickoff":
            text = "GO" if self.countdown <= 0.4 else str(max(1, math.ceil(self.countdown)))
            draw_text(surface, self.game.font(96, True), text, COLORS["yellow"], (w // 2, h // 2 - 40), "center")
        elif self.phase == "goal":
            draw_text(surface, self.game.font(64, True), "GOAL", COLORS["yellow"], (w // 2, h // 2 - 70), "center")
        if self.mode == "Practice Arena":
            draw_text(surface, small, f"Targets: {self.local_stats['training_targets']}", COLORS["green"], (48, 46), "midleft")


class MatchEndScene(MenuScene):
    def __init__(self, game, mode: str, score: tuple[int, int], local_stats: dict, arena, difficulty: str, length_seconds: int) -> None:
        super().__init__(game)
        self.mode = mode
        self.score = score
        self.local_stats = local_stats
        self.arena = arena
        self.difficulty = difficulty
        self.length_seconds = length_seconds

    def layout(self) -> None:
        w, h = self.game.screen.get_size()
        x = w // 2 - 180
        y = int(h * 0.55)
        self.widgets = [
            Button(pygame.Rect(x, y, 360, 56), "Rematch", self.rematch, "PLAY"),
            Button(pygame.Rect(x, y + 70, 360, 56), "Garage", lambda: self.game.change_scene(GarageScene(self.game)), "CAR"),
            Button(pygame.Rect(x, y + 140, 360, 56), "Main Menu", lambda: self.game.change_scene(MainMenuScene(self.game)), "MENU"),
        ]

    def rematch(self) -> None:
        self.game.change_scene(MatchScene(self.game, self.mode, self.arena, self.difficulty, self.length_seconds))

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        w, h = surface.get_size()
        result = "Blue Wins" if self.score[0] > self.score[1] else "Orange Wins"
        if self.score[0] == self.score[1]:
            result = "Session Complete"
        draw_text(surface, self.game.font(64, True), result, COLORS["white"], (w // 2, int(h * 0.18)), "center")
        draw_text(surface, self.game.font(48, True), f"{self.score[0]} - {self.score[1]}", COLORS["yellow"], (w // 2, int(h * 0.28)), "center")
        stat_font = self.game.font(28)
        lines = [
            f"Goals: {self.local_stats.get('goals', 0)}",
            f"Shots: {self.local_stats.get('shots', 0)}",
            f"Saves: {self.local_stats.get('saves', 0)}",
            f"Training Targets: {self.local_stats.get('training_targets', 0)}",
        ]
        for i, line in enumerate(lines):
            draw_text(surface, stat_font, line, COLORS["white"], (w // 2, int(h * 0.36) + i * 34), "center")

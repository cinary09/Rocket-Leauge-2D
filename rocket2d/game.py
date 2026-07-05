from __future__ import annotations

import os
import sys
from pathlib import Path

import pygame

from .assets import AudioManager, ensure_generated_assets
from .constants import BASE_RESOLUTION, COLORS, FPS
from .persistence import SaveStore
from .scenes import MainMenuScene
from .ui import Toast, draw_text


class Rocket2D:
    def __init__(self) -> None:
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.store = SaveStore(Path("save"))
        self.settings = self.store.load_settings()
        self.stats = self.store.load_stats()
        self.garage = self.store.load_garage()
        self.career = self.store.load_career()
        ensure_generated_assets()
        self.screen = pygame.display.set_mode(self.settings.resolution, self._display_flags())
        pygame.display.set_caption("Rocket 2D League")
        self.clock = pygame.time.Clock()
        self.running = True
        self._fonts: dict[tuple[int, bool], pygame.font.Font] = {}
        self.audio = AudioManager(self.settings)
        self.scene = MainMenuScene(self)
        self.scene.enter()
        self.toasts: list[Toast] = []

    def _display_flags(self) -> int:
        flags = pygame.DOUBLEBUF
        if self.settings.fullscreen:
            flags |= pygame.FULLSCREEN
        else:
            flags |= pygame.RESIZABLE
        return flags

    def apply_display_settings(self) -> None:
        self.screen = pygame.display.set_mode(self.settings.resolution, self._display_flags())
        if hasattr(self.scene, "layout"):
            self.scene.layout()

    def font(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        if key not in self._fonts:
            self._fonts[key] = pygame.font.SysFont("Segoe UI", size, bold=bold)
        return self._fonts[key]

    def change_scene(self, scene) -> None:
        self.scene = scene
        self.scene.enter()

    def toast(self, text: str) -> None:
        self.toasts.append(Toast(text, 2.0))

    def quit(self) -> None:
        self.running = False

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 1 / 20)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.scene.handle_event(event)
            self.scene.update(dt)
            self.toasts = [toast for toast in self.toasts if toast.update(dt)]
            self.scene.draw(self.screen)
            self._draw_overlays()
            pygame.display.flip()
        self.store.save_settings(self.settings)
        pygame.quit()

    def _draw_overlays(self) -> None:
        if self.settings.show_fps:
            draw_text(
                self.screen,
                self.font(18),
                f"{self.clock.get_fps():.0f} FPS",
                COLORS["white"],
                (self.screen.get_width() - 12, 10),
                "topright",
            )
        y = 18
        for toast in self.toasts[-3:]:
            image = self.font(22).render(toast.text, True, COLORS["white"])
            rect = image.get_rect(center=(self.screen.get_width() // 2, y + image.get_height() // 2))
            bg = rect.inflate(36, 16)
            pygame.draw.rect(self.screen, (10, 14, 24), bg, border_radius=8)
            pygame.draw.rect(self.screen, (90, 110, 140), bg, 2, border_radius=8)
            self.screen.blit(image, rect)
            y += bg.height + 10


def run_self_test() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    app = Rocket2D()
    for event in pygame.event.get():
        app.scene.handle_event(event)
    app.scene.update(1 / FPS)
    app.scene.draw(app.screen)
    pygame.display.flip()
    app.store.save_settings(app.settings)
    pygame.quit()
    print("Self-test passed: game initialized, generated assets, updated and rendered one frame.")

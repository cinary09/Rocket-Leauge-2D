from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pygame

from .constants import COLORS


def draw_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    pos: tuple[int, int],
    anchor: str = "topleft",
) -> pygame.Rect:
    image = font.render(text, True, color)
    rect = image.get_rect()
    setattr(rect, anchor, pos)
    surface.blit(image, rect)
    return rect


class Button:
    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        callback: Callable[[], None],
        icon: str = "",
        enabled: bool = True,
    ) -> None:
        self.rect = rect
        self.text = text
        self.callback = callback
        self.icon = icon
        self.enabled = enabled
        self.hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.hovered = self.rect.collidepoint(event.pos)
            if self.hovered:
                self.callback()
                return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        base = COLORS["panel_2"] if self.enabled else (36, 40, 49)
        fill = (45, 75, 111) if self.hovered and self.enabled else base
        pygame.draw.rect(surface, (3, 6, 12), self.rect.move(0, 4), border_radius=8)
        pygame.draw.rect(surface, fill, self.rect, border_radius=8)
        pygame.draw.rect(surface, (90, 110, 140), self.rect, width=2, border_radius=8)
        label = f"{self.icon} {self.text}".strip()
        color = COLORS["white"] if self.enabled else (130, 136, 148)
        draw_text(surface, font, label, color, self.rect.center, "center")


class Toggle:
    def __init__(self, rect: pygame.Rect, label: str, value: bool, callback: Callable[[bool], None]) -> None:
        self.rect = rect
        self.label = label
        self.value = value
        self.callback = callback
        self.hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.value = not self.value
            self.callback(self.value)
            return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        draw_text(surface, font, self.label, COLORS["white"], (self.rect.x, self.rect.centery), "midleft")
        track = pygame.Rect(self.rect.right - 78, self.rect.centery - 16, 64, 32)
        pygame.draw.rect(surface, (45, 52, 66), track, border_radius=16)
        knob_x = track.right - 16 if self.value else track.left + 16
        color = COLORS["green"] if self.value else (108, 116, 130)
        pygame.draw.circle(surface, color, (knob_x, track.centery), 13)


class Slider:
    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        value: float,
        callback: Callable[[float], None],
    ) -> None:
        self.rect = rect
        self.label = label
        self.value = value
        self.callback = callback
        self.dragging = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.dragging = True
            self._set_from_x(event.pos[0])
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_x(event.pos[0])
            return True
        return False

    def _set_from_x(self, x: int) -> None:
        self.value = max(0.0, min(1.0, (x - self.rect.x) / self.rect.width))
        self.callback(self.value)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        draw_text(surface, font, f"{self.label} {int(self.value * 100)}", COLORS["white"], (self.rect.x, self.rect.y - 8), "bottomleft")
        bar = pygame.Rect(self.rect.x, self.rect.centery - 5, self.rect.width, 10)
        pygame.draw.rect(surface, (48, 56, 70), bar, border_radius=5)
        fill = bar.copy()
        fill.width = int(bar.width * self.value)
        pygame.draw.rect(surface, COLORS["blue"], fill, border_radius=5)
        pygame.draw.circle(surface, COLORS["white"], (self.rect.x + fill.width, bar.centery), 13)


class Selector:
    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        options: list[str],
        value: str,
        callback: Callable[[str], None],
    ) -> None:
        self.rect = rect
        self.label = label
        self.options = options
        self.value = value if value in options else options[0]
        self.callback = callback

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            direction = -1 if event.pos[0] < self.rect.centerx else 1
            idx = self.options.index(self.value)
            self.value = self.options[(idx + direction) % len(self.options)]
            self.callback(self.value)
            return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        draw_text(surface, font, self.label, COLORS["white"], (self.rect.x, self.rect.y - 8), "bottomleft")
        pygame.draw.rect(surface, COLORS["panel_2"], self.rect, border_radius=8)
        pygame.draw.rect(surface, (90, 110, 140), self.rect, width=2, border_radius=8)
        draw_text(surface, font, "<", COLORS["muted"], (self.rect.x + 24, self.rect.centery), "center")
        draw_text(surface, font, ">", COLORS["muted"], (self.rect.right - 24, self.rect.centery), "center")
        draw_text(surface, font, self.value, COLORS["white"], self.rect.center, "center")


class KeyBind:
    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        key_name: str,
        callback: Callable[[str], None],
    ) -> None:
        self.rect = rect
        self.label = label
        self.key_name = key_name
        self.callback = callback
        self.capturing = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if self.capturing and event.type == pygame.KEYDOWN:
            self.key_name = pygame.key.name(event.key)
            self.capturing = False
            self.callback(self.key_name)
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.capturing = True
            return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        draw_text(surface, font, self.label, COLORS["white"], (self.rect.x, self.rect.centery), "midleft")
        box = pygame.Rect(self.rect.right - 180, self.rect.y + 3, 170, self.rect.height - 6)
        pygame.draw.rect(surface, (58, 68, 86) if self.capturing else COLORS["panel_2"], box, border_radius=8)
        pygame.draw.rect(surface, (110, 128, 156), box, width=2, border_radius=8)
        text = "Press key" if self.capturing else self.key_name.upper()
        draw_text(surface, font, text, COLORS["white"], box.center, "center")


@dataclass
class Toast:
    text: str
    timer: float

    def update(self, dt: float) -> bool:
        self.timer -= dt
        return self.timer > 0

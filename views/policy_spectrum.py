from __future__ import annotations

from typing import Callable

import pygame


def draw_spectrum_bar(surface: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, (38, 40, 52), rect, border_radius=6)
    left_rect = pygame.Rect(rect.x, rect.y, rect.width // 2, rect.height)
    right_rect = pygame.Rect(rect.centerx, rect.y, rect.width // 2, rect.height)
    left_fill = pygame.Surface(left_rect.size, pygame.SRCALPHA)
    left_fill.fill((48, 99, 191, 70))
    right_fill = pygame.Surface(right_rect.size, pygame.SRCALPHA)
    right_fill.fill((212, 64, 64, 70))
    surface.blit(left_fill, left_rect.topleft)
    surface.blit(right_fill, right_rect.topleft)
    pygame.draw.line(
        surface,
        (90, 95, 110),
        (rect.centerx, rect.y + 1),
        (rect.centerx, rect.bottom - 1),
        1,
    )
    pygame.draw.rect(surface, (70, 75, 90), rect, 1, border_radius=6)


def draw_policy_marker(
    surface: pygame.Surface,
    bar_rect: pygame.Rect,
    score: float,
    *,
    interactive: bool = False,
    dragging: bool = False,
) -> None:
    marker_x = bar_rect.x + int(bar_rect.width * (score / 100.0))
    marker_y = bar_rect.centery
    radius = 9 if interactive else 7
    if dragging:
        radius = 10
    pygame.draw.circle(surface, (245, 245, 250), (marker_x, marker_y), radius)
    border = (90, 150, 220) if interactive else (30, 32, 42)
    pygame.draw.circle(surface, border, (marker_x, marker_y), radius, 2)


def draw_policy_row(
    surface: pygame.Surface,
    x: int,
    y: int,
    bar_width: int,
    title: str,
    left_label: str,
    right_label: str,
    score: float,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    *,
    interactive: bool = False,
    dragging: bool = False,
) -> tuple[int, pygame.Rect]:
    title_surface = font.render(title, True, (200, 205, 215))
    surface.blit(title_surface, (x, y))
    y += title_surface.get_height() + 6

    bar_height = 14 if interactive else 12
    bar_rect = pygame.Rect(x, y, bar_width, bar_height)
    draw_spectrum_bar(surface, bar_rect)
    draw_policy_marker(
        surface, bar_rect, score, interactive=interactive, dragging=dragging
    )
    y += bar_height + 6

    left = small_font.render(left_label, True, (110, 145, 210))
    right = small_font.render(right_label, True, (210, 120, 120))
    surface.blit(left, (x, y))
    surface.blit(right, (x + bar_width - right.get_width(), y))
    y += left.get_height() + 22
    return y, bar_rect


class PolicySlider:
    """Draggable marker on a left–right policy spectrum (0–100)."""

    def __init__(
        self,
        policy_id: str,
        bar_rect: pygame.Rect,
        get_value: Callable[[], float],
        set_value: Callable[[float], None],
    ) -> None:
        self.policy_id = policy_id
        self.bar_rect = bar_rect
        self.get_value = get_value
        self.set_value = set_value
        self.dragging = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._hit_rect().collidepoint(event.pos):
                self.dragging = True
                self._set_from_pos(event.pos[0])
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True
            return False
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_pos(event.pos[0])
            return True
        return False

    def _hit_rect(self) -> pygame.Rect:
        pad = 12
        return self.bar_rect.inflate(0, pad * 2)

    def _set_from_pos(self, x: int) -> None:
        clamped = max(self.bar_rect.left, min(self.bar_rect.right, x))
        fraction = (clamped - self.bar_rect.left) / max(self.bar_rect.width, 1)
        self.set_value(max(0.0, min(100.0, fraction * 100.0)))

from __future__ import annotations

import pygame

from views.layout import NAV_HEIGHT, NAV_Y

HOME_BUTTON_WIDTH = 72
HOME_BUTTON_HEIGHT = NAV_HEIGHT


def draw_home_button(
    surface: pygame.Surface,
    rect: pygame.Rect,
    font: pygame.font.Font,
    *,
    enabled: bool = True,
) -> None:
    hovered = enabled and rect.collidepoint(pygame.mouse.get_pos())
    if enabled:
        fill = (55, 62, 82) if hovered else (45, 50, 64)
        border = (140, 150, 175) if hovered else (110, 118, 140)
        text_color = (240, 240, 245)
    else:
        fill = (40, 42, 50)
        border = (70, 75, 90)
        text_color = (120, 125, 140)
    pygame.draw.rect(surface, fill, rect, border_radius=6)
    pygame.draw.rect(surface, border, rect, 1, border_radius=6)
    label = font.render("Home", True, text_color)
    surface.blit(label, label.get_rect(center=rect.center))


def home_button_rect(screen_width: int, *, right_margin: int = 24) -> pygame.Rect:
    return pygame.Rect(
        screen_width - right_margin - HOME_BUTTON_WIDTH,
        NAV_Y,
        HOME_BUTTON_WIDTH,
        HOME_BUTTON_HEIGHT,
    )

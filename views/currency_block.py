from __future__ import annotations

import pygame

BLOCK_WIDTH = 220
BLOCK_HEIGHT = 108
BLOCK_MARGIN = 24


def currency_block_rect(screen_size: tuple[int, int]) -> pygame.Rect:
    width, height = screen_size
    return pygame.Rect(
        width - BLOCK_WIDTH - BLOCK_MARGIN,
        height - BLOCK_HEIGHT - BLOCK_MARGIN,
        BLOCK_WIDTH,
        BLOCK_HEIGHT,
    )


def draw_currency_block(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    influence: float,
    influence_max: float,
    money: float,
    money_max: float,
    title_font: pygame.font.Font,
    label_font: pygame.font.Font,
) -> None:
    pygame.draw.rect(surface, (26, 28, 38), rect, border_radius=8)
    pygame.draw.rect(surface, (55, 60, 75), rect, 1, border_radius=8)

    x = rect.x + 14
    y = rect.y + 10
    header = title_font.render("Resources", True, (210, 215, 225))
    surface.blit(header, (x, y))
    y += header.get_height() + 8

    bar_width = rect.width - 28
    y = _draw_resource_row(
        surface, x, y, bar_width, "Influence", influence, influence_max, label_font
    )
    _draw_resource_row(
        surface, x, y, bar_width, "Money", money, money_max, label_font
    )


def _draw_resource_row(
    surface: pygame.Surface,
    x: int,
    y: int,
    bar_width: int,
    label: str,
    current: float,
    maximum: float,
    font: pygame.font.Font,
) -> int:
    text = font.render(label, True, (170, 175, 190))
    surface.blit(text, (x, y))

    value_text = font.render(f"{int(current)}/{int(maximum)}", True, (150, 155, 170))
    surface.blit(value_text, (x + bar_width - value_text.get_width(), y))
    y += text.get_height() + 3

    bar_height = 8
    bar_rect = pygame.Rect(x, y, bar_width, bar_height)
    pygame.draw.rect(surface, (38, 40, 52), bar_rect, border_radius=4)
    fill_width = int(bar_width * (current / maximum)) if maximum > 0 else 0
    if fill_width > 0:
        fill_rect = pygame.Rect(x, y, fill_width, bar_height)
        color = (80, 130, 200) if label == "Influence" else (90, 170, 110)
        pygame.draw.rect(surface, color, fill_rect, border_radius=4)
    pygame.draw.rect(surface, (70, 75, 90), bar_rect, 1, border_radius=4)
    return y + bar_height + 8

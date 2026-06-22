from __future__ import annotations

import pygame

from core.politician import Politician

TOOLTIP_PADDING = 10
TOOLTIP_LINE_GAP = 4
TOOLTIP_BG = (32, 36, 48)
TOOLTIP_BORDER = (90, 98, 120)


def politicians_summary_lines(politicians: list[Politician], heading: str | None = None) -> list[str]:
    lines: list[str] = []
    if heading:
        lines.append(heading)
    for index, politician in enumerate(politicians):
        if index > 0:
            lines.append("")
        lines.extend(politician_summary_lines(politician))
    return lines


def politician_summary_lines(politician: Politician) -> list[str]:
    lines = [
        politician.name,
        politician.role,
        politician.party.value.title(),
    ]
    if politician.district is not None:
        lines.append(f"District: {politician.district}")
    if politician.seat is not None:
        lines.append(f"Seat: {politician.seat}")
    return lines


def draw_tooltip(
    surface: pygame.Surface,
    anchor: tuple[int, int],
    lines: list[str],
    font: pygame.font.Font,
) -> None:
    if not lines:
        return

    rendered = [font.render(line, True, (235, 235, 240)) for line in lines]
    width = max(text.get_width() for text in rendered) + TOOLTIP_PADDING * 2
    height = (
        sum(text.get_height() for text in rendered)
        + TOOLTIP_LINE_GAP * (len(rendered) - 1)
        + TOOLTIP_PADDING * 2
    )

    screen_w, screen_h = surface.get_size()
    x = anchor[0] + 16
    y = anchor[1] + 16
    if x + width > screen_w - 8:
        x = anchor[0] - width - 16
    if y + height > screen_h - 8:
        y = anchor[1] - height - 16
    x = max(8, x)
    y = max(8, y)

    rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, TOOLTIP_BG, rect, border_radius=6)
    pygame.draw.rect(surface, TOOLTIP_BORDER, rect, 1, border_radius=6)

    text_y = y + TOOLTIP_PADDING
    for text in rendered:
        surface.blit(text, (x + TOOLTIP_PADDING, text_y))
        text_y += text.get_height() + TOOLTIP_LINE_GAP

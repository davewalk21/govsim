from __future__ import annotations

import pygame

from core.party import PARTY_COLORS, Party


def draw_party_bar(
    surface: pygame.Surface,
    rect: pygame.Rect,
    counts: dict[Party, int],
    font: pygame.font.Font,
) -> None:
    total = sum(counts.values())
    if total <= 0:
        return

    pygame.draw.rect(surface, (35, 38, 48), rect, border_radius=6)
    pygame.draw.rect(surface, (70, 75, 90), rect, 1, border_radius=6)

    dem = counts[Party.DEMOCRAT]
    ind = counts[Party.INDEPENDENT]
    rep = counts[Party.REPUBLICAN]

    dem_w = round(rect.width * dem / total)
    ind_w = round(rect.width * ind / total)
    rep_w = rect.width - dem_w - ind_w

    x = rect.x
    for party, width in (
        (Party.DEMOCRAT, dem_w),
        (Party.INDEPENDENT, ind_w),
        (Party.REPUBLICAN, rep_w),
    ):
        if width <= 0:
            continue
        segment = pygame.Rect(x, rect.y, width, rect.height)
        pygame.draw.rect(surface, PARTY_COLORS[party], segment)
        if width >= 36:
            label = font.render(str(counts[party]), True, (245, 245, 245))
            surface.blit(label, label.get_rect(center=segment.center))
        x += width

    total_label = font.render(f"{total} total", True, (170, 175, 190))
    surface.blit(total_label, (rect.right + 12, rect.y + 6))

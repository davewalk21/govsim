from __future__ import annotations

import pygame

from core.party import PARTY_COLORS, UNDECIDED_ELECTION_COLOR, Party, competitiveness_map_color


def party_bar_rect(screen_width: int, y: int = 98, height: int = 32) -> pygame.Rect:
    width = min(720, screen_width - 200)
    return pygame.Rect((screen_width - width) // 2, y, width, height)


def draw_party_bar(
    surface: pygame.Surface,
    rect: pygame.Rect,
    counts: dict[Party, int],
    font: pygame.font.Font,
    *,
    total_label: str = "total",
    votes_to_win: int | None = None,
    total_votes: int | None = None,
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

    if votes_to_win is not None and total_votes is not None and total_votes > 0:
        win_x = rect.x + round(rect.width * votes_to_win / total_votes)
        pygame.draw.line(
            surface,
            (240, 240, 245),
            (win_x, rect.y - 2),
            (win_x, rect.bottom + 2),
            2,
        )
        win_label = font.render(str(votes_to_win), True, (200, 205, 215))
        surface.blit(win_label, (win_x - win_label.get_width() // 2, rect.bottom + 6))

    total_label_surface = font.render(f"{total} {total_label}", True, (170, 175, 190))
    label_y = rect.bottom + (22 if votes_to_win is not None else 4)
    surface.blit(total_label_surface, total_label_surface.get_rect(midtop=(rect.centerx, label_y)))


def draw_revealing_party_bar(
    surface: pygame.Surface,
    rect: pygame.Rect,
    dem_votes: int,
    rep_votes: int,
    font: pygame.font.Font,
    *,
    total_votes: int,
    votes_to_win: int,
    total_label: str = "electoral votes",
) -> None:
    """Dem | undecided | Rep bar while states are being called."""
    pygame.draw.rect(surface, (35, 38, 48), rect, border_radius=6)
    pygame.draw.rect(surface, (70, 75, 90), rect, 1, border_radius=6)

    if total_votes <= 0:
        return

    dem_w = round(rect.width * dem_votes / total_votes)
    rep_w = round(rect.width * rep_votes / total_votes)
    und_w = max(0, rect.width - dem_w - rep_w)

    x = rect.x
    for color, width in (
        (PARTY_COLORS[Party.DEMOCRAT], dem_w),
        (UNDECIDED_ELECTION_COLOR, und_w),
        (PARTY_COLORS[Party.REPUBLICAN], rep_w),
    ):
        if width <= 0:
            continue
        segment = pygame.Rect(x, rect.y, width, rect.height)
        pygame.draw.rect(surface, color, segment)
        x += width

    if dem_w >= 36:
        label = font.render(str(dem_votes), True, (245, 245, 245))
        surface.blit(label, label.get_rect(center=(rect.x + dem_w // 2, rect.centery)))
    if rep_w >= 36:
        label = font.render(str(rep_votes), True, (245, 245, 245))
        surface.blit(
            label,
            label.get_rect(center=(rect.right - rep_w // 2, rect.centery)),
        )

    win_x = rect.x + round(rect.width * votes_to_win / total_votes)
    pygame.draw.line(
        surface,
        (240, 240, 245),
        (win_x, rect.y - 2),
        (win_x, rect.bottom + 2),
        2,
    )
    win_label = font.render(str(votes_to_win), True, (200, 205, 215))
    surface.blit(win_label, (win_x - win_label.get_width() // 2, rect.bottom + 6))

    total_label_surface = font.render(f"{total_votes} {total_label}", True, (170, 175, 190))
    surface.blit(total_label_surface, total_label_surface.get_rect(midtop=(rect.centerx, rect.bottom + 22)))


def draw_competitiveness_party_bar(
    surface: pygame.Surface,
    rect: pygame.Rect,
    tier_votes: dict,
    font: pygame.font.Font,
    *,
    total_votes: int,
    votes_to_win: int,
    total_label: str = "electoral votes",
) -> None:
    """Pre-election bar with one segment per competitiveness tier (Safe Dem → Safe Rep)."""
    from core.electorate import CompetitivenessTier

    pygame.draw.rect(surface, (35, 38, 48), rect, border_radius=6)
    pygame.draw.rect(surface, (70, 75, 90), rect, 1, border_radius=6)

    if total_votes <= 0:
        return

    x = rect.x
    for tier in CompetitivenessTier:
        ev = tier_votes.get(tier, 0)
        if ev <= 0:
            continue
        width = round(rect.width * ev / total_votes)
        if width <= 0:
            continue
        segment = pygame.Rect(x, rect.y, width, rect.height)
        pygame.draw.rect(surface, competitiveness_map_color(tier), segment)
        if width >= 28:
            label = font.render(str(ev), True, (245, 245, 245))
            surface.blit(label, label.get_rect(center=segment.center))
        x += width

    win_x = rect.x + round(rect.width * votes_to_win / total_votes)
    pygame.draw.line(
        surface,
        (240, 240, 245),
        (win_x, rect.y - 2),
        (win_x, rect.bottom + 2),
        2,
    )
    win_label = font.render(str(votes_to_win), True, (200, 205, 215))
    surface.blit(win_label, (win_x - win_label.get_width() // 2, rect.bottom + 6))

    total_label_surface = font.render(f"{total_votes} {total_label}", True, (170, 175, 190))
    surface.blit(total_label_surface, total_label_surface.get_rect(midtop=(rect.centerx, rect.bottom + 22)))

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from core.electorate import StateElectorate
from core.party import PARTY_COLORS, Party
from views.tooltip import draw_tooltip

PIE_COLORS = {
    "dem": PARTY_COLORS[Party.DEMOCRAT],
    "rep": PARTY_COLORS[Party.REPUBLICAN],
    "ind": PARTY_COLORS[Party.INDEPENDENT],
    "other": pygame.Color(120, 125, 140),
}

PIE_LABELS = {
    "dem": "Democrat",
    "rep": "Republican",
    "ind": "Independent",
    "other": "Other",
}

SLICE_ORDER = ("dem", "rep", "ind", "other")


@dataclass
class PieSlice:
    key: str
    start: float
    end: float
    share: float


@dataclass
class PieChartLayout:
    center: tuple[int, int]
    radius: int
    slices: tuple[PieSlice, ...]

    @classmethod
    def from_electorate(
        cls, center: tuple[int, int], radius: int, electorate: StateElectorate
    ) -> PieChartLayout:
        shares = electorate.affiliation_shares()
        slices: list[PieSlice] = []
        start = -math.pi / 2
        for key in SLICE_ORDER:
            sweep = shares[key] * 2 * math.pi
            if sweep <= 0:
                continue
            slices.append(PieSlice(key, start, start + sweep, shares[key]))
            start += sweep
        return cls(center=center, radius=radius, slices=tuple(slices))

    def hit_test(self, point: tuple[int, int]) -> PieSlice | None:
        cx, cy = self.center
        dx = point[0] - cx
        dy = point[1] - cy
        if dx * dx + dy * dy > self.radius * self.radius:
            return None
        angle = math.atan2(dy, dx)
        for slc in self.slices:
            if _angle_in_slice(angle, slc.start, slc.end):
                return slc
        return None


def _angle_in_slice(angle: float, start: float, end: float) -> bool:
    two_pi = 2 * math.pi
    angle = (angle + two_pi) % two_pi
    start_n = (start + two_pi) % two_pi
    end_n = (end + two_pi) % two_pi
    if start_n <= end_n:
        return start_n <= angle <= end_n
    return angle >= start_n or angle <= end_n


def draw_electorate_pie(
    surface: pygame.Surface,
    layout: PieChartLayout,
    font: pygame.font.Font,
    *,
    hover_slice: PieSlice | None = None,
    tooltip_font: pygame.font.Font | None = None,
    mouse_pos: tuple[int, int] | None = None,
) -> None:
    shares = {slc.key: slc.share for slc in layout.slices}
    _draw_pie_slices(surface, layout.center, layout.radius, shares, hover_slice)
    pygame.draw.circle(surface, (70, 75, 90), layout.center, layout.radius, 1)

    label = font.render("Eligible voters", True, (150, 155, 170))
    surface.blit(
        label,
        label.get_rect(midtop=(layout.center[0], layout.center[1] + layout.radius + 6)),
    )

    if hover_slice and mouse_pos and tooltip_font:
        pct = hover_slice.share * 100.0
        lines = [PIE_LABELS[hover_slice.key], f"{pct:.1f}%"]
        draw_tooltip(surface, mouse_pos, lines, tooltip_font)


def _draw_pie_slices(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    shares: dict[str, float],
    hover_slice: PieSlice | None,
) -> None:
    cx, cy = center
    start = -math.pi / 2
    for key in SLICE_ORDER:
        sweep = shares.get(key, 0.0) * 2 * math.pi
        if sweep <= 0:
            continue
        points = [(cx, cy)]
        steps = max(8, int(sweep * 20))
        for step in range(steps + 1):
            angle = start + sweep * step / steps
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        color = PIE_COLORS[key]
        if hover_slice and hover_slice.key == key:
            color = pygame.Color(
                min(255, color.r + 30),
                min(255, color.g + 30),
                min(255, color.b + 30),
            )
        if len(points) >= 3:
            pygame.draw.polygon(surface, color, points)
        start += sweep


def draw_poll_bar_chart(
    surface: pygame.Surface,
    rect: pygame.Rect,
    electorate: StateElectorate,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
) -> None:
    header = font.render("Polls", True, (210, 215, 225))
    surface.blit(header, (rect.x, rect.y))
    margin = electorate.poll_margin
    moe = small_font.render(f"±{margin:.1f}% MOE", True, (130, 135, 150))
    surface.blit(moe, (rect.right - moe.get_width(), rect.y + 2))

    chart_top = rect.y + header.get_height() + 12
    chart_bottom = rect.bottom - 26
    chart_height = max(180, chart_bottom - chart_top)
    chart_rect = pygame.Rect(rect.x + 8, chart_top, rect.width - 16, chart_height)

    pygame.draw.rect(surface, (32, 34, 44), chart_rect, border_radius=6)
    pygame.draw.rect(surface, (55, 60, 75), chart_rect, 1, border_radius=6)

    parties = (
        ("Dem", electorate.poll_dem_pct, PARTY_COLORS[Party.DEMOCRAT]),
        ("Rep", electorate.poll_rep_pct, PARTY_COLORS[Party.REPUBLICAN]),
        ("Ind", electorate.poll_ind_pct, PARTY_COLORS[Party.INDEPENDENT]),
    )
    bar_slot = chart_rect.width // len(parties)
    plot_height = chart_rect.height - 36
    bar_bottom = chart_rect.bottom - 10

    for index, (label, pct, color) in enumerate(parties):
        slot_x = chart_rect.x + index * bar_slot + bar_slot // 2
        bar_w = min(52, bar_slot - 12)
        bar_h = max(8, int(plot_height * (pct / 100.0)))
        bar_rect = pygame.Rect(slot_x - bar_w // 2, bar_bottom - bar_h, bar_w, bar_h)
        pygame.draw.rect(surface, color, bar_rect, border_radius=4)

        err_top = bar_bottom - int(plot_height * min(100.0, pct + margin) / 100.0)
        err_bot = bar_bottom - int(plot_height * max(0.0, pct - margin) / 100.0)
        err_top = max(chart_rect.top + 6, err_top)
        pygame.draw.line(surface, (200, 205, 220), (slot_x, err_top), (slot_x, err_bot), 2)
        pygame.draw.line(surface, (200, 205, 220), (slot_x - 7, err_top), (slot_x + 7, err_top), 2)
        pygame.draw.line(surface, (200, 205, 220), (slot_x - 7, err_bot), (slot_x + 7, err_bot), 2)

        pct_text = small_font.render(f"{pct:.0f}%", True, (220, 220, 225))
        surface.blit(pct_text, pct_text.get_rect(midbottom=(slot_x, bar_rect.top - 4)))
        name = small_font.render(label, True, (150, 155, 170))
        surface.blit(name, name.get_rect(midtop=(slot_x, bar_bottom + 4)))

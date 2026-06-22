from __future__ import annotations

import pygame

from core.election import PresidentialElection
from core.party import Party
from core.policies import POLICIES
from core.states import ELECTORAL_VOTES_BY_STATE, STATE_ABBREV_TO_NAME
from views.electorate_charts import (
    PIE_LABELS,
    PieChartLayout,
    draw_electorate_pie,
    draw_poll_bar_chart,
)
from views.layout import NAV_BOTTOM
from views.policy_spectrum import draw_policy_row
from views.tooltip import draw_tooltip

PANEL_WIDTH = 380
PANEL_MARGIN = 24
PIE_RADIUS = 48
POLL_CHART_HEIGHT = 340
HEADER_HEIGHT = 72
SCROLL_STEP = 36
OPINION_ROW_HEIGHT = 58


def detail_panel_rect(screen_size: tuple[int, int]) -> pygame.Rect:
    width, _ = screen_size
    return pygame.Rect(
        width - PANEL_WIDTH - PANEL_MARGIN,
        NAV_BOTTOM + 8,
        PANEL_WIDTH,
        screen_size[1] - NAV_BOTTOM - 16,
    )


class StateDetailPanel:
    """Scrollable right-side panel for state drill-down."""

    def __init__(self, screen_size: tuple[int, int]) -> None:
        self.screen_size = screen_size
        self.scroll_offset = 0
        self.content_height = 0
        self._pie_layout: PieChartLayout | None = None

    def reset_scroll(self) -> None:
        self.scroll_offset = 0

    def panel_rect(self) -> pygame.Rect:
        return detail_panel_rect(self.screen_size)

    def content_top(self) -> int:
        return self.panel_rect().y + HEADER_HEIGHT

    def viewport_height(self) -> int:
        panel = self.panel_rect()
        return panel.height - HEADER_HEIGHT

    def max_scroll(self) -> int:
        return max(0, self.content_height - self.viewport_height())

    def handle_event(self, event: pygame.event.Event) -> bool:
        panel = self.panel_rect()
        if event.type == pygame.MOUSEWHEEL:
            if not panel.collidepoint(pygame.mouse.get_pos()):
                return False
            self.scroll_offset = max(
                0,
                min(self.max_scroll(), self.scroll_offset - event.y * SCROLL_STEP),
            )
            return True
        return False

    def _content_y(self, mouse_y: int) -> int:
        return mouse_y - self.content_top() + self.scroll_offset

    def draw(
        self,
        surface: pygame.Surface,
        election: PresidentialElection,
        state_abbrev: str,
        *,
        title_font: pygame.font.Font,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
        mouse_pos: tuple[int, int] | None = None,
    ) -> None:
        panel = self.panel_rect()
        pygame.draw.rect(surface, (26, 28, 38), panel, border_radius=8)
        pygame.draw.rect(surface, (55, 60, 75), panel, 1, border_radius=8)

        electorate = election.electorates[state_abbrev]
        self._draw_header(surface, panel, state_abbrev, electorate, election, title_font, small_font)

        content = pygame.Surface((panel.width, 2000), pygame.SRCALPHA)
        content.fill((0, 0, 0, 0))
        y = 12
        inner_w = panel.width - 32
        x = 16

        pie_cx = panel.width // 2
        pie_cy = y + PIE_RADIUS
        pie_layout = PieChartLayout.from_electorate((pie_cx, pie_cy), PIE_RADIUS, electorate)
        self._pie_layout = pie_layout

        hover_slice = None
        if mouse_pos and panel.collidepoint(mouse_pos):
            local_x = mouse_pos[0] - panel.x
            local_y = self._content_y(mouse_pos[1])
            hover_slice = pie_layout.hit_test((local_x, local_y))

        draw_electorate_pie(
            content,
            pie_layout,
            small_font,
            hover_slice=hover_slice,
        )
        y += PIE_RADIUS * 2 + 28

        turnout_pct = (
            electorate.actual_turnout * 100
            if electorate.actual_turnout is not None
            else electorate.efficacy * 100
        )
        shares = electorate.affiliation_shares()
        stat_lines = [
            f"Population {electorate.population:,}",
            f"Eligible {electorate.eligible_voters:,} · Turnout {turnout_pct:.1f}%",
            (
                f"Dem {electorate.dem_voters:,} · Rep {electorate.rep_voters:,} · "
                f"Ind {electorate.ind_voters:,} · Other {electorate.other_voters:,}"
            ),
            (
                f"Affiliation: D {shares['dem'] * 100:.1f}% · "
                f"R {shares['rep'] * 100:.1f}% · I {shares['ind'] * 100:.1f}%"
            ),
        ]
        for line in stat_lines:
            text = small_font.render(line, True, (130, 135, 150))
            content.blit(text, (x, y))
            y += text.get_height() + 4
        y += 10

        poll_rect = pygame.Rect(x, y, inner_w, POLL_CHART_HEIGHT)
        draw_poll_bar_chart(content, poll_rect, electorate, font, small_font)
        y += POLL_CHART_HEIGHT + 16

        header = font.render("Issue Opinions", True, (210, 215, 225))
        content.blit(header, (x, y))
        y += header.get_height() + 8

        opinions = election.state_opinions[state_abbrev]
        for policy in POLICIES:
            y, _ = draw_policy_row(
                content,
                x,
                y,
                inner_w,
                policy.title,
                policy.left_label,
                policy.right_label,
                opinions.score(policy.id),
                font,
                small_font,
            )

        self.content_height = y + 12
        self.scroll_offset = min(self.scroll_offset, self.max_scroll())

        clip = pygame.Rect(panel.x, self.content_top(), panel.width, self.viewport_height())
        surface.set_clip(clip)
        surface.blit(content, (panel.x, self.content_top() - self.scroll_offset))
        surface.set_clip(None)

        if self.max_scroll() > 0:
            self._draw_scrollbar(surface, panel)

        if hover_slice and mouse_pos:
            pct = hover_slice.share * 100.0
            draw_tooltip(
                surface,
                mouse_pos,
                [PIE_LABELS[hover_slice.key], f"{pct:.1f}%"],
                small_font,
            )

    def _draw_header(
        self,
        surface: pygame.Surface,
        panel: pygame.Rect,
        state_abbrev: str,
        electorate,
        election: PresidentialElection,
        title_font: pygame.font.Font,
        small_font: pygame.font.Font,
    ) -> None:
        x = panel.x + 16
        y = panel.y + 12
        state_name = STATE_ABBREV_TO_NAME.get(state_abbrev, state_abbrev)
        title = title_font.render(state_name, True, (235, 235, 240))
        surface.blit(title, (x, y))
        y += title.get_height() + 2

        ev = ELECTORAL_VOTES_BY_STATE[state_abbrev]
        summary = electorate.competitiveness_summary()
        meta = small_font.render(
            f"{state_abbrev} · {ev} EV · {summary} · "
            f"{electorate.likely_voters:,} likely voters",
            True,
            (150, 155, 170),
        )
        surface.blit(meta, (x, y))

        pygame.draw.line(
            surface,
            (55, 60, 75),
            (panel.x + 12, panel.y + HEADER_HEIGHT - 1),
            (panel.right - 12, panel.y + HEADER_HEIGHT - 1),
            1,
        )

    def _draw_scrollbar(self, surface: pygame.Surface, panel: pygame.Rect) -> None:
        track = pygame.Rect(panel.right - 10, self.content_top() + 4, 4, self.viewport_height() - 8)
        pygame.draw.rect(surface, (40, 42, 52), track, border_radius=2)
        max_scroll = self.max_scroll()
        if max_scroll <= 0:
            return
        ratio = self.scroll_offset / max_scroll
        thumb_h = max(24, int(track.height * self.viewport_height() / self.content_height))
        thumb_y = track.y + int((track.height - thumb_h) * ratio)
        thumb = pygame.Rect(track.x, thumb_y, track.width, thumb_h)
        pygame.draw.rect(surface, (100, 108, 130), thumb, border_radius=2)


def draw_state_detail_panel(
    surface: pygame.Surface,
    election: PresidentialElection,
    state_abbrev: str,
    *,
    panel: StateDetailPanel,
    title_font: pygame.font.Font,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    mouse_pos: tuple[int, int] | None = None,
) -> None:
    panel.draw(
        surface,
        election,
        state_abbrev,
        title_font=title_font,
        font=font,
        small_font=small_font,
        mouse_pos=mouse_pos,
    )

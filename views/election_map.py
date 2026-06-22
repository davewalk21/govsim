from __future__ import annotations

import pygame

from core.election import PresidentialElection
from core.party import BACKGROUND_COLOR, NO_DELEGATION_COLOR, PARTY_COLORS, Party, poll_gradient_color
from core.states import ELECTORAL_VOTES_TO_WIN, STATE_ABBREV_TO_NAME, TOTAL_ELECTORAL_VOTES
from views.currency_block import currency_block_rect, draw_currency_block
from views.dropdown import Dropdown
from views.election_policy import ElectionPolicyView
from views.geo import (
    load_projected_state,
    load_projected_states,
    map_viewport_for_screen,
    map_viewport_for_state_detail,
)
from views.layout import LEGEND_Y, NAV_BOTTOM, NAV_HEIGHT, PARTY_BAR_Y, VIEW_TITLE_Y
from views.party_bar import draw_party_bar, party_bar_rect
from views.policy_panel import StateDetailPanel, draw_state_detail_panel
from views.tooltip import draw_tooltip

PARTY_LEGEND_ENTRIES = (
    (PARTY_COLORS[Party.DEMOCRAT], "Democrat"),
    (PARTY_COLORS[Party.REPUBLICAN], "Republican"),
)

VIEW_OPTIONS = (
    ("Map", "map"),
    ("Policy", "policy"),
)

BACK_BUTTON_WIDTH = 110
BACK_BUTTON_HEIGHT = 32
VIEW_DROPDOWN_WIDTH = 140


def _state_fill_color(
    election: PresidentialElection,
    state_abbrev: str,
    *,
    strength: float = 0.52,
) -> pygame.Color:
    if election.resolved and election.results is not None:
        party = election.results.get(state_abbrev)
        if party in (Party.DEMOCRAT, Party.REPUBLICAN):
            return PARTY_COLORS[party]
    electorate = election.electorates[state_abbrev]
    dem, rep = electorate.map_color_pcts()
    return poll_gradient_color(dem, rep, strength=strength)


class ElectionCampaignView:
    """Presidential election: map, policy promises, state drill-down."""

    def __init__(self, screen_size: tuple[int, int], election: PresidentialElection) -> None:
        self.screen_size = screen_size
        self.election = election
        self.font = pygame.font.SysFont(None, 22)
        self.label_font = pygame.font.SysFont(None, 16)
        self.title_font = pygame.font.SysFont(None, 36)
        self.panel_title_font = pygame.font.SysFont(None, 30)
        self.result_font = pygame.font.SysFont(None, 32)
        self.button_font = pygame.font.SysFont(None, 22)
        width = screen_size[0]
        self.bar_rect = party_bar_rect(width, y=PARTY_BAR_Y)
        self.country_viewport = map_viewport_for_screen(screen_size)
        self.states = load_projected_states(self.country_viewport)
        self.selected_state: str | None = None
        self.detail_viewport = self.country_viewport
        self.detail_state = None
        self.detail_map_rect = pygame.Rect(0, 0, 0, 0)
        self.main_view = "map"
        self.view_dropdown = Dropdown(
            pygame.Rect(24, NAV_BOTTOM + 8, VIEW_DROPDOWN_WIDTH, NAV_HEIGHT),
            list(VIEW_OPTIONS),
            self.main_view,
        )
        self.policy_view = ElectionPolicyView(screen_size, election)
        self.back_rect = pygame.Rect(
            24,
            NAV_BOTTOM + 8,
            BACK_BUTTON_WIDTH,
            BACK_BUTTON_HEIGHT,
        )
        self._map_click_top = PARTY_BAR_Y + 52
        self._currency_rect = currency_block_rect(screen_size)
        self.hover_tooltip_lines: list[str] = []
        self._mouse_pos: tuple[int, int] = (0, 0)
        self.state_detail_panel = StateDetailPanel(screen_size)

    def _has_electorate(self, abbrev: str | None) -> bool:
        return bool(abbrev and abbrev in self.election.electorates)

    def update_hover(self, mouse_pos: tuple[int, int]) -> None:
        self._mouse_pos = mouse_pos
        self.hover_tooltip_lines = []
        if self.selected_state is not None or self.main_view != "map":
            return
        if mouse_pos[1] < self._map_click_top:
            return
        for state in reversed(self.states):
            if not self._has_electorate(state.abbreviation) or not state.contains(mouse_pos):
                continue
            electorate = self.election.electorates[state.abbreviation]
            dem, rep = electorate.map_color_pcts()
            ind = electorate.poll_ind_pct
            name = STATE_ABBREV_TO_NAME.get(state.abbreviation, state.abbreviation)
            self.hover_tooltip_lines = [
                name,
                electorate.competitiveness_summary(),
                f"Poll: D {dem:.1f}% · R {rep:.1f}% · I {ind:.1f}%",
                f"MOE ±{electorate.poll_margin:.1f}%",
            ]
            return

    def handle_event(self, event: pygame.event.Event) -> bool:
        if self.selected_state is not None:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.back_rect.collidepoint(event.pos):
                    self._exit_detail_view()
                    return True
            if self.state_detail_panel.handle_event(event):
                return True
            return False

        if self.view_dropdown.handle_event(event):
            self.main_view = self.view_dropdown.selected_key
            return True

        if self.main_view == "policy":
            return self.policy_view.handle_event(event)

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False

        if event.pos[1] < self._map_click_top:
            return False
        if self.bar_rect.collidepoint(event.pos):
            return False
        if self._currency_rect.collidepoint(event.pos):
            return False
        if self.view_dropdown.rect.collidepoint(event.pos) or self.view_dropdown.open:
            return False

        for state in reversed(self.states):
            if not self._has_electorate(state.abbreviation):
                continue
            if state.contains(event.pos):
                self._enter_detail_view(state.abbreviation)
                return True
        return False

    def _enter_detail_view(self, state_abbrev: str) -> None:
        self.selected_state = state_abbrev
        self.state_detail_panel.reset_scroll()
        self.detail_viewport, self.detail_map_rect = map_viewport_for_state_detail(
            state_abbrev, self.screen_size
        )
        self.detail_state = load_projected_state(self.detail_viewport, state_abbrev)

    def _exit_detail_view(self) -> None:
        self.selected_state = None
        self.detail_state = None
        self.detail_viewport = self.country_viewport

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND_COLOR)
        if self.selected_state is not None:
            self._draw_detail_view(surface)
        elif self.main_view == "policy":
            self.policy_view.draw(surface)
            self.view_dropdown.draw(surface)
        else:
            self._draw_map_view(surface)

    def _draw_map_view(self, surface: pygame.Surface) -> None:
        width, height = self.screen_size

        title = self.title_font.render("Electoral Map", True, (230, 230, 235))
        surface.blit(title, title.get_rect(midtop=(width // 2, VIEW_TITLE_Y)))

        self._draw_states(surface, self.states)

        draw_party_bar(
            surface,
            self.bar_rect,
            self.election.electoral_vote_counts(),
            self.font,
            total_label="electoral votes",
            votes_to_win=ELECTORAL_VOTES_TO_WIN,
            total_votes=TOTAL_ELECTORAL_VOTES,
        )

        self._draw_legend(surface)
        self.view_dropdown.draw(surface)

        draw_currency_block(
            surface,
            self._currency_rect,
            influence=self.election.influence,
            influence_max=self.election.influence_max,
            money=self.election.money,
            money_max=self.election.money_max,
            title_font=self.font,
            label_font=self.label_font,
        )

        if self.hover_tooltip_lines:
            draw_tooltip(surface, self._mouse_pos, self.hover_tooltip_lines, self.label_font)

        if self.election.resolved:
            message = self.election.result_message()
            banner = self.result_font.render(message, True, (240, 240, 245))
            surface.blit(banner, banner.get_rect(midbottom=(width // 2, height - 24)))
        else:
            hint = self.font.render(
                "Click a state for opinions · Next Turn to advance the campaign",
                True,
                (150, 155, 170),
            )
            surface.blit(hint, hint.get_rect(midbottom=(width // 2, height - 20)))

    def _draw_detail_view(self, surface: pygame.Surface) -> None:
        assert self.selected_state is not None and self.detail_state is not None

        self._draw_back_button(surface)

        electorate = self.election.electorates[self.selected_state]
        fill = _state_fill_color(self.election, self.selected_state, strength=0.58)
        for polygon in self.detail_state.polygons:
            pygame.draw.polygon(surface, fill, polygon)
            pygame.draw.polygon(surface, (90, 95, 110), polygon, 2)

        if self.detail_state.label_point and self.detail_state.abbreviation:
            name = STATE_ABBREV_TO_NAME.get(self.detail_state.abbreviation, self.detail_state.abbreviation)
            label = self.title_font.render(name, True, (235, 235, 240))
            surface.blit(
                label,
                label.get_rect(midtop=(self.detail_map_rect.centerx, VIEW_TITLE_Y)),
            )

        draw_state_detail_panel(
            surface,
            self.election,
            self.selected_state,
            panel=self.state_detail_panel,
            title_font=self.panel_title_font,
            font=self.font,
            small_font=self.label_font,
            mouse_pos=self._mouse_pos,
        )

    def _draw_back_button(self, surface: pygame.Surface) -> None:
        hovered = self.back_rect.collidepoint(pygame.mouse.get_pos())
        fill = (55, 62, 82) if hovered else (45, 50, 64)
        border = (140, 150, 175) if hovered else (110, 118, 140)
        pygame.draw.rect(surface, fill, self.back_rect, border_radius=6)
        pygame.draw.rect(surface, border, self.back_rect, 1, border_radius=6)
        label = self.button_font.render("← Full Map", True, (240, 240, 245))
        surface.blit(label, label.get_rect(center=self.back_rect.center))

    def _draw_states(self, surface: pygame.Surface, states) -> None:
        for state in states:
            if not state.abbreviation:
                continue
            if not self._has_electorate(state.abbreviation):
                for polygon in state.polygons:
                    pygame.draw.polygon(surface, NO_DELEGATION_COLOR, polygon)
                    pygame.draw.polygon(surface, (70, 75, 90), polygon, 1)
                continue
            fill = _state_fill_color(self.election, state.abbreviation)
            for polygon in state.polygons:
                pygame.draw.polygon(surface, fill, polygon)
                pygame.draw.polygon(surface, (70, 75, 90), polygon, 1)

            if state.label_point:
                label = self.label_font.render(state.abbreviation, True, (235, 235, 240))
                surface.blit(label, label.get_rect(center=state.label_point))

    def _draw_legend(self, surface: pygame.Surface) -> None:
        x, y = self.screen_size[0] - 170, LEGEND_Y
        if self.election.resolved:
            entries = (
                (PARTY_COLORS[Party.DEMOCRAT], "Dem won"),
                (PARTY_COLORS[Party.REPUBLICAN], "Rep won"),
            )
        else:
            entries = (
                (poll_gradient_color(100.0, 0.0), "Dem lean"),
                (poll_gradient_color(0.0, 100.0), "Rep lean"),
            )
        for color, label_text in entries:
            pygame.draw.circle(surface, color, (x, y + 8), 8)
            text = self.font.render(label_text, True, (220, 220, 225))
            surface.blit(text, (x + 16, y))
            y += 24


ElectionMapView = ElectionCampaignView

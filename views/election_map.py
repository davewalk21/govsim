from __future__ import annotations

import pygame

from core.election import PresidentialElection
from core.party import (
    BACKGROUND_COLOR,
    NO_DELEGATION_COLOR,
    PARTY_COLORS,
    Party,
    UNDECIDED_ELECTION_COLOR,
    competitiveness_map_color,
)
from core.states import (
    ELECTORAL_VOTES_BY_STATE,
    ELECTORAL_VOTES_TO_WIN,
    STATE_ABBREV_TO_NAME,
    TOTAL_ELECTORAL_VOTES,
)
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
from views.party_bar import (
    draw_competitiveness_party_bar,
    draw_party_bar,
    draw_revealing_party_bar,
    party_bar_rect,
)
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

STATE_FILTER_OPTIONS = (
    ("All States", "all"),
    ("Swing States", "swing"),
    ("Dem States", "dem"),
    ("Rep States", "rep"),
)

BACK_BUTTON_WIDTH = 110
BACK_BUTTON_HEIGHT = 32
VIEW_DROPDOWN_WIDTH = 140
DROPDOWN_GAP = 4
FILTER_DIM_STRENGTH = 0.22


def _dim_color(color: pygame.Color, strength: float = FILTER_DIM_STRENGTH) -> pygame.Color:
    bg = BACKGROUND_COLOR
    return pygame.Color(
        int(bg[0] + strength * (color.r - bg[0])),
        int(bg[1] + strength * (color.g - bg[1])),
        int(bg[2] + strength * (color.b - bg[2])),
    )


def _state_fill_color(
    election: PresidentialElection,
    state_abbrev: str,
) -> pygame.Color:
    winner = election.revealed_winner(state_abbrev)
    if election.revealing or election.resolved:
        if winner in (Party.DEMOCRAT, Party.REPUBLICAN):
            return PARTY_COLORS[winner]
        return UNDECIDED_ELECTION_COLOR
    electorate = election.electorates[state_abbrev]
    return competitiveness_map_color(electorate.competitiveness_tier())


class ElectionCampaignView:
    """Presidential election: map, policy promises, state drill-down."""

    def __init__(self, screen_size: tuple[int, int], election: PresidentialElection) -> None:
        self.screen_size = screen_size
        self.election = election
        self.font = pygame.font.SysFont(None, 22)
        self.label_font = pygame.font.SysFont(None, 16)
        self.title_font = pygame.font.SysFont(None, 36)
        self.panel_title_font = pygame.font.SysFont(None, 30)
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
        self.state_filter = "all"
        dropdown_x = 24
        dropdown_y = NAV_BOTTOM + 8
        self.view_dropdown = Dropdown(
            pygame.Rect(dropdown_x, dropdown_y, VIEW_DROPDOWN_WIDTH, NAV_HEIGHT),
            list(VIEW_OPTIONS),
            self.main_view,
        )
        self.filter_dropdown = Dropdown(
            pygame.Rect(
                dropdown_x,
                dropdown_y + NAV_HEIGHT + DROPDOWN_GAP,
                VIEW_DROPDOWN_WIDTH,
                NAV_HEIGHT,
            ),
            list(STATE_FILTER_OPTIONS),
            self.state_filter,
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

    def _ev_line(self, state_abbrev: str) -> str:
        ev = ELECTORAL_VOTES_BY_STATE[state_abbrev]
        vote_word = "vote" if ev == 1 else "votes"
        return f"{ev} electoral {vote_word}"

    def _show_state_filter(self) -> bool:
        return not self.election.revealing and not self.election.resolved

    def _filter_active(self) -> bool:
        return self._show_state_filter() and self.state_filter != "all"

    def reset_state_filter(self) -> None:
        self.state_filter = "all"
        self.filter_dropdown.set_selected("all")
        self.filter_dropdown.open = False

    def _state_matches_filter(self, state_abbrev: str) -> bool:
        if not self._filter_active():
            return True
        from core.electorate import tier_matches_filter

        electorate = self.election.electorates[state_abbrev]
        return tier_matches_filter(electorate.competitiveness_tier(), self.state_filter)

    def _dropdown_blocks_point(self, pos: tuple[int, int]) -> bool:
        if self.view_dropdown.rect.collidepoint(pos) or self.view_dropdown.open:
            return True
        if self._show_state_filter() and (
            self.filter_dropdown.rect.collidepoint(pos) or self.filter_dropdown.open
        ):
            return True
        return False

    def _draw_dropdowns(self, surface: pygame.Surface) -> None:
        if not self._show_state_filter():
            self.filter_dropdown.open = False
            self.view_dropdown.draw(surface)
            return

        self.filter_dropdown.draw_button(surface)
        self.view_dropdown.draw_button(surface)
        self.filter_dropdown.draw_menu(surface)
        self.view_dropdown.draw_menu(surface)

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
            name = STATE_ABBREV_TO_NAME.get(state.abbreviation, state.abbreviation)
            ev_line = self._ev_line(state.abbreviation)
            winner = self.election.revealed_winner(state.abbreviation)
            if self.election.revealing and winner is None:
                self.hover_tooltip_lines = [name, ev_line, "Awaiting results"]
                return
            if winner in (Party.DEMOCRAT, Party.REPUBLICAN):
                self.hover_tooltip_lines = [
                    name,
                    ev_line,
                    f"Called for {winner.value.title()}",
                ]
                return
            dem, rep = electorate.map_color_pcts()
            ind = electorate.poll_ind_pct
            self.hover_tooltip_lines = [
                name,
                ev_line,
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

        if self.main_view == "map" and self._show_state_filter() and self.filter_dropdown.handle_event(event):
            self.state_filter = self.filter_dropdown.selected_key
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
        if self._dropdown_blocks_point(event.pos):
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

        self._draw_map_header(surface)

        self._draw_states(surface, self.states)

        counts = self.election.electoral_vote_counts()
        if self.election.revealing:
            draw_revealing_party_bar(
                surface,
                self.bar_rect,
                counts[Party.DEMOCRAT],
                counts[Party.REPUBLICAN],
                self.font,
                total_votes=TOTAL_ELECTORAL_VOTES,
                votes_to_win=ELECTORAL_VOTES_TO_WIN,
            )
        elif self.election.resolved:
            draw_party_bar(
                surface,
                self.bar_rect,
                counts,
                self.font,
                total_label="electoral votes",
                votes_to_win=ELECTORAL_VOTES_TO_WIN,
                total_votes=TOTAL_ELECTORAL_VOTES,
            )
        else:
            draw_competitiveness_party_bar(
                surface,
                self.bar_rect,
                self.election.competitiveness_electoral_votes(),
                self.font,
                total_votes=TOTAL_ELECTORAL_VOTES,
                votes_to_win=ELECTORAL_VOTES_TO_WIN,
            )

        self._draw_legend(surface)
        self._draw_dropdowns(surface)

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
            self._draw_player_outcome_banner(surface)
        elif not self.election.revealing:
            hint = self.font.render(
                "Click a state for opinions · Next Turn to advance the campaign",
                True,
                (150, 155, 170),
            )
            surface.blit(hint, hint.get_rect(midbottom=(width // 2, height - 20)))

    def _draw_map_header(self, surface: pygame.Surface) -> None:
        width = self.screen_size[0]
        election = self.election

        if election.revealing or election.resolved:
            called = election.winner if election.resolved else election.reveal_called_winner()
            if called is not None:
                name = "Democrat" if called == Party.DEMOCRAT else "Republican"
                self._draw_header_banner(
                    surface,
                    f"{name} wins!",
                    PARTY_COLORS[called],
                )
            return

        title = self.title_font.render("Electoral Map", True, (230, 230, 235))
        surface.blit(title, title.get_rect(midtop=(width // 2, VIEW_TITLE_Y)))

    def _draw_header_banner(
        self,
        surface: pygame.Surface,
        message: str,
        color: pygame.Color | None,
    ) -> None:
        width = self.screen_size[0]
        text = self.title_font.render(message, True, (240, 240, 245))
        dot_gap = 16
        dot_size = 12
        group_width = text.get_width()
        if color is not None:
            group_width += dot_gap + dot_size * 2
        x = (width - group_width) // 2
        y = VIEW_TITLE_Y + 4
        if color is not None:
            dot_x = x + dot_size
            dot_y = y + text.get_height() // 2
            pygame.draw.circle(surface, color, (dot_x, dot_y), dot_size)
            x += dot_size * 2 + dot_gap
        surface.blit(text, (x, y))

    def _draw_player_outcome_banner(self, surface: pygame.Surface) -> None:
        message = self.election.player_outcome_message()
        if not message:
            return

        width, height = self.screen_size
        outcome_font = pygame.font.SysFont(None, 28)
        text = outcome_font.render(message, True, (240, 240, 245))
        pad_x, pad_y = 20, 12
        box_w = text.get_width() + pad_x * 2
        box_h = text.get_height() + pad_y * 2
        box = pygame.Rect((width - box_w) // 2, height - box_h - 24, box_w, box_h)
        pygame.draw.rect(surface, (32, 34, 44), box, border_radius=8)
        pygame.draw.rect(surface, (70, 75, 90), box, 1, border_radius=8)
        surface.blit(text, text.get_rect(center=box.center))

    def _draw_detail_view(self, surface: pygame.Surface) -> None:
        assert self.selected_state is not None and self.detail_state is not None

        self._draw_back_button(surface)

        electorate = self.election.electorates[self.selected_state]
        fill = _state_fill_color(self.election, self.selected_state)
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
            if not self._state_matches_filter(state.abbreviation):
                fill = _dim_color(fill)
            label_color = (235, 235, 240) if self._state_matches_filter(state.abbreviation) else (100, 105, 120)
            for polygon in state.polygons:
                pygame.draw.polygon(surface, fill, polygon)
                pygame.draw.polygon(surface, (70, 75, 90), polygon, 1)

            if state.label_point:
                label = self.label_font.render(state.abbreviation, True, label_color)
                surface.blit(label, label.get_rect(center=state.label_point))

    def _draw_legend(self, surface: pygame.Surface) -> None:
        x = self.screen_size[0] - 148
        y = LEGEND_Y
        if self.election.revealing or self.election.resolved:
            entries = (
                (PARTY_COLORS[Party.DEMOCRAT], "Dem"),
                (UNDECIDED_ELECTION_COLOR, "Undecided"),
                (PARTY_COLORS[Party.REPUBLICAN], "Rep"),
            )
            for color, label_text in entries:
                pygame.draw.circle(surface, color, (x, y + 8), 8)
                text = self.label_font.render(label_text, True, (200, 205, 215))
                surface.blit(text, (x + 16, y))
                y += 24
            return

        from core.electorate import CompetitivenessTier, TIER_LABELS
        bar_w = 14
        bar_h = 9 * 14
        for tier in CompetitivenessTier:
            seg_y = y + tier.value * 14
            color = competitiveness_map_color(tier)
            pygame.draw.rect(surface, color, pygame.Rect(x, seg_y, bar_w, 14))
        pygame.draw.rect(surface, (70, 75, 90), pygame.Rect(x, y, bar_w, bar_h), 1)

        label_x = x + bar_w + 8
        for tier in (CompetitivenessTier.SAFE_DEM, CompetitivenessTier.TOSS_UP, CompetitivenessTier.SAFE_REP):
            seg_y = y + tier.value * 14
            text = self.label_font.render(TIER_LABELS[tier], True, (200, 205, 215))
            surface.blit(text, (label_x, seg_y + 1))


ElectionMapView = ElectionCampaignView

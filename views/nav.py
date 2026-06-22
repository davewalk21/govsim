from __future__ import annotations

import pygame

from core.party import Party
from views.dropdown import Dropdown
from views.home_button import HOME_BUTTON_WIDTH, draw_home_button, home_button_rect
from views.layout import NAV_BOTTOM, NAV_GAP, NAV_HEIGHT, NAV_Y

BRANCH_OPTIONS = (
    ("Senate", "senate"),
    ("House", "house"),
    ("Governors", "governors"),
    ("Court", "court"),
)

VIEW_MODE_OPTIONS = (
    ("Chamber", "chamber"),
    ("Map", "map"),
    ("Roster", "roster"),
)

COURT_VIEW_MODE_OPTIONS = (
    ("Chamber", "chamber"),
    ("Roster", "roster"),
)

PARTY_OPTIONS = (
    ("All", "all"),
    ("Democrat", "democrat"),
    ("Republican", "republican"),
    ("Independent", "independent"),
)

PARTY_BY_KEY = {
    "democrat": Party.DEMOCRAT,
    "republican": Party.REPUBLICAN,
    "independent": Party.INDEPENDENT,
}

BRANCH_WIDTH = 148
VIEW_WIDTH = 128
PARTY_WIDTH = 148


class ViewNavigator:
    """Branch → view mode → party (roster only) navigation."""

    def __init__(self) -> None:
        self.branch = "senate"
        self.view_mode = "chamber"
        self.party_key = "all"
        x = 24
        self.branch_dropdown = Dropdown(
            pygame.Rect(x, NAV_Y, BRANCH_WIDTH, NAV_HEIGHT),
            list(BRANCH_OPTIONS),
            self.branch,
        )
        x += BRANCH_WIDTH + NAV_GAP
        self.view_dropdown = Dropdown(
            pygame.Rect(x, NAV_Y, VIEW_WIDTH, NAV_HEIGHT),
            list(VIEW_MODE_OPTIONS),
            self.view_mode,
        )
        x += VIEW_WIDTH + NAV_GAP
        self.party_dropdown = Dropdown(
            pygame.Rect(x, NAV_Y, PARTY_WIDTH, NAV_HEIGHT),
            list(PARTY_OPTIONS),
            self.party_key,
        )
        self.home_rect = home_button_rect(1280)
        self.pending_home = False
        self._button_font = pygame.font.SysFont(None, 22)

    def set_screen_width(self, width: int) -> None:
        self.home_rect = home_button_rect(width)

    @property
    def party(self) -> Party | None:
        if self.party_key == "all":
            return None
        return PARTY_BY_KEY[self.party_key]

    @property
    def show_party_dropdown(self) -> bool:
        return self.view_mode == "roster"

    @property
    def active_view_key(self) -> str:
        if self.view_mode == "roster":
            return f"{self.branch}_roster"
        return f"{self.branch}_{self.view_mode}"

    @property
    def is_menu_open(self) -> bool:
        if self.branch_dropdown.open or self.view_dropdown.open:
            return True
        return self.show_party_dropdown and self.party_dropdown.open

    def _sync_view_options(self) -> None:
        options = (
            list(COURT_VIEW_MODE_OPTIONS)
            if self.branch == "court"
            else list(VIEW_MODE_OPTIONS)
        )
        self.view_dropdown.options = options
        valid_keys = {key for _, key in options}
        if self.view_dropdown.selected_key not in valid_keys:
            self.view_mode = options[0][1]
            self.view_dropdown.set_selected(self.view_mode)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Return True if the event was consumed by navigation."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.home_rect.collidepoint(event.pos):
                self.pending_home = True
                return True

        if self.branch_dropdown.handle_event(event):
            if not self.branch_dropdown.open:
                self.branch = self.branch_dropdown.selected_key
                self._sync_view_options()
            return True

        if self.view_dropdown.handle_event(event):
            if not self.view_dropdown.open:
                self.view_mode = self.view_dropdown.selected_key
                if not self.show_party_dropdown:
                    self.party_dropdown.open = False
            return True

        if self.show_party_dropdown and self.party_dropdown.handle_event(event):
            if not self.party_dropdown.open:
                self.party_key = self.party_dropdown.selected_key
            return True

        return self.is_menu_open

    def draw(self, surface: pygame.Surface) -> None:
        width = surface.get_width()
        pygame.draw.rect(surface, (22, 24, 32), pygame.Rect(0, 0, width, NAV_BOTTOM))
        pygame.draw.line(surface, (55, 60, 75), (0, NAV_BOTTOM - 1), (width, NAV_BOTTOM - 1))

        self.branch_dropdown.draw(surface)
        self.view_dropdown.draw(surface)
        if self.show_party_dropdown:
            self.party_dropdown.draw(surface)
        draw_home_button(surface, self.home_rect, self._button_font)

    def consume_home(self) -> bool:
        if self.pending_home:
            self.pending_home = False
            return True
        return False

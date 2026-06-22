from __future__ import annotations

import pygame

from core.party import BACKGROUND_COLOR, PARTY_COLORS, Party
from core.politician import Office, Politician
from core.rosters import Roster
from views.layout import VIEW_TITLE_Y

ROW_HEIGHT = 26
HEADER_HEIGHT = 28
LIST_TOP = 118
FOOTER_HEIGHT = 28
PARTY_DOT_RADIUS = 6
PARTY_LABELS = {
    Party.DEMOCRAT: "Dem",
    Party.REPUBLICAN: "Rep",
    Party.INDEPENDENT: "Ind",
}

COLUMNS = (
    ("Name", 196),
    ("Role", 96),
    ("Party", 56),
    ("State", 52),
    ("Dist", 44),
    ("Seat", 44),
    ("Age", 44),
    ("Gender", 48),
    ("Policy", 100),
    ("Government", 100),
)


class RosterView:
    """Scrollable roster for one branch, filtered by party."""

    def __init__(
        self,
        screen_size: tuple[int, int],
        roster: Roster,
        branch_label: str,
    ) -> None:
        self.screen_size = screen_size
        self.roster = roster
        self.branch_label = branch_label
        self.party: Party | None = None
        self.scroll_offset = 0
        self.font = pygame.font.SysFont(None, 20)
        self.header_font = pygame.font.SysFont(None, 20)
        self.title_font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 18)

    def set_party(self, party: Party | None) -> None:
        if party != self.party:
            self.party = party
            self.scroll_offset = 0

    def _filtered_members(self) -> list[Politician]:
        members = self.roster.members
        if self.party is not None:
            members = [politician for politician in members if politician.party == self.party]
        return sorted(
            members,
            key=lambda politician: (
                0 if politician.office == Office.COURT else 1,
                politician.seat or 0,
                politician.state or "",
                politician.district or 0,
                politician.name,
            ),
        )

    def _list_rect(self) -> pygame.Rect:
        width, height = self.screen_size
        bottom = height - FOOTER_HEIGHT - 8
        return pygame.Rect(24, LIST_TOP, width - 48, bottom - LIST_TOP)

    def _max_scroll(self) -> int:
        members = self._filtered_members()
        list_height = self._list_rect().height
        content_height = len(members) * ROW_HEIGHT
        return max(0, content_height - list_height)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_offset = max(
                0,
                min(self._max_scroll(), self.scroll_offset - event.y * ROW_HEIGHT * 3),
            )

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND_COLOR)
        width, height = self.screen_size

        title = self.title_font.render(f"{self.branch_label} Roster", True, (230, 230, 235))
        surface.blit(title, title.get_rect(midtop=(width // 2, VIEW_TITLE_Y)))

        self._draw_table_chrome(surface)
        self._draw_column_headers(surface)
        self._draw_rows(surface)

        members = self._filtered_members()
        party_label = "All parties" if self.party is None else self.party.value.title()
        hint = self.small_font.render(
            f"{len(members)} {party_label} — scroll to browse",
            True,
            (150, 155, 170),
        )
        surface.blit(hint, (24, height - FOOTER_HEIGHT))

    def _draw_table_chrome(self, surface: pygame.Surface) -> None:
        list_rect = self._list_rect()
        header_rect = pygame.Rect(
            list_rect.x,
            list_rect.y - HEADER_HEIGHT,
            list_rect.width,
            HEADER_HEIGHT,
        )
        pygame.draw.rect(surface, (32, 36, 48), header_rect, border_top_left_radius=6, border_top_right_radius=6)
        pygame.draw.rect(surface, (55, 60, 75), list_rect, 1, border_radius=6)
        pygame.draw.line(
            surface,
            (55, 60, 75),
            (list_rect.x, list_rect.y),
            (list_rect.right, list_rect.y),
        )

    def _draw_column_headers(self, surface: pygame.Surface) -> None:
        list_rect = self._list_rect()
        x = list_rect.x + 12
        y = list_rect.y - HEADER_HEIGHT + 6
        for label, column_width in COLUMNS:
            text = self.header_font.render(label, True, (170, 175, 190))
            surface.blit(text, (x, y))
            x += column_width

    def _draw_rows(self, surface: pygame.Surface) -> None:
        list_rect = self._list_rect()
        surface.set_clip(list_rect)
        members = self._filtered_members()
        y = list_rect.y + 4 - self.scroll_offset

        for index, politician in enumerate(members):
            if y + ROW_HEIGHT >= list_rect.y and y <= list_rect.bottom:
                if index % 2 == 0:
                    row_rect = pygame.Rect(list_rect.x + 1, y, list_rect.width - 2, ROW_HEIGHT)
                    pygame.draw.rect(surface, (24, 27, 36), row_rect)
                self._draw_row(surface, politician, list_rect.x + 12, y)
            y += ROW_HEIGHT
            if y > list_rect.bottom:
                break

        surface.set_clip(None)

        if self._max_scroll() > 0:
            self._draw_scrollbar(surface, list_rect)

    def _draw_row(
        self, surface: pygame.Surface, politician: Politician, x: int, y: int
    ) -> None:
        column_x = x
        for label, column_width in COLUMNS:
            if label == "Party":
                dot_x = column_x + PARTY_DOT_RADIUS + 2
                dot_y = y + ROW_HEIGHT // 2
                pygame.draw.circle(
                    surface, PARTY_COLORS[politician.party], (dot_x, dot_y), PARTY_DOT_RADIUS
                )
                party_label = PARTY_LABELS[politician.party]
                text = self.font.render(party_label, True, (225, 228, 235))
                text_x = column_x + PARTY_DOT_RADIUS * 2 + 8
                clip = pygame.Rect(column_x, y, column_width, ROW_HEIGHT)
                prev_clip = surface.get_clip()
                surface.set_clip(clip)
                surface.blit(text, (text_x, y + 5))
                surface.set_clip(prev_clip)
            else:
                value = self._cell_value(politician, label)
                text = self.font.render(value, True, (225, 228, 235))
                surface.blit(text, (column_x, y + 5))
            column_x += column_width

    def _cell_value(self, politician: Politician, column: str) -> str:
        if column == "Name":
            return politician.name
        if column == "Role":
            return politician.role
        if column == "State":
            return politician.state or "—"
        if column == "Dist":
            return self._district_display(politician)
        if column == "Seat":
            return self._seat_display(politician)
        if column == "Age":
            return str(politician.age)
        if column == "Gender":
            return politician.gender.value
        if column == "Policy":
            return politician.policy.value.title()
        if column == "Government":
            return politician.government.value.title()
        return ""

    def _district_display(self, politician: Politician) -> str:
        if politician.office != Office.HOUSE or politician.district is None:
            return "—"
        return str(politician.district)

    def _seat_display(self, politician: Politician) -> str:
        if politician.seat is None:
            return "—"
        if politician.office in (Office.SENATE, Office.COURT):
            return str(politician.seat)
        return "—"

    def _draw_scrollbar(self, surface: pygame.Surface, list_rect: pygame.Rect) -> None:
        track = pygame.Rect(list_rect.right - 10, list_rect.y + 4, 6, list_rect.height - 8)
        pygame.draw.rect(surface, (40, 44, 56), track, border_radius=3)

        max_scroll = self._max_scroll()
        if max_scroll <= 0:
            return

        members = self._filtered_members()
        thumb_ratio = list_rect.height / max(len(members) * ROW_HEIGHT, 1)
        thumb_height = max(24, int(list_rect.height * thumb_ratio))
        scroll_ratio = self.scroll_offset / max_scroll
        thumb_y = list_rect.y + 4 + int((list_rect.height - 8 - thumb_height) * scroll_ratio)
        thumb = pygame.Rect(track.x, thumb_y, track.width, thumb_height)
        pygame.draw.rect(surface, (110, 118, 140), thumb, border_radius=3)

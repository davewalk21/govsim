from __future__ import annotations

import pygame

from core.election import PresidentialElection
from core.party import Party
from core.policies import POLICIES
from views.layout import NAV_BOTTOM, VIEW_TITLE_Y
from views.policy_spectrum import PolicySlider, draw_policy_row

COLUMN_TOP = NAV_BOTTOM + 48
HEADER_BLOCK_HEIGHT = 52
ROW_GAP_AFTER = 22


class ElectionPolicyView:
    """Campaign policy screen: player sliders left, opponent read-only right."""

    def __init__(self, screen_size: tuple[int, int], election: PresidentialElection) -> None:
        self.screen_size = screen_size
        self.election = election
        self.font = pygame.font.SysFont(None, 22)
        self.title_font = pygame.font.SysFont(None, 36)
        self.section_font = pygame.font.SysFont(None, 28)
        self.label_font = pygame.font.SysFont(None, 16)
        self.sliders: list[PolicySlider] = []

    def _player_column(self) -> pygame.Rect:
        half = self.screen_size[0] // 2
        return pygame.Rect(24, COLUMN_TOP, half - 36, self.screen_size[1])

    def _rows_start_y(self) -> int:
        return COLUMN_TOP + HEADER_BLOCK_HEIGHT

    def _bar_width(self) -> int:
        return self._player_column().width - 32

    def _sync_sliders(self) -> None:
        column = self._player_column()
        x = column.x + 16
        y = self._rows_start_y()
        bar_width = self._bar_width()
        sliders: list[PolicySlider] = []
        for policy in POLICIES:
            title_h = self.font.get_height()
            bar_rect = pygame.Rect(x, y + title_h + 6, bar_width, 14)
            policy_id = policy.id
            sliders.append(
                PolicySlider(
                    policy_id,
                    bar_rect,
                    lambda pid=policy_id: self.election.player_promises[pid],
                    lambda value, pid=policy_id: self._set_promise(pid, value),
                )
            )
            y += title_h + 6 + 14 + 6 + self.label_font.get_height() + ROW_GAP_AFTER
        self.sliders = sliders

    def _set_promise(self, policy_id: str, value: float) -> None:
        self.election.player_promises[policy_id] = value

    def handle_event(self, event: pygame.event.Event) -> bool:
        self._sync_sliders()
        for slider in self.sliders:
            if slider.handle_event(event):
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        self._sync_sliders()
        width, _ = self.screen_size
        half = width // 2

        title = self.title_font.render("Campaign Policies", True, (230, 230, 235))
        surface.blit(title, title.get_rect(midtop=(width // 2, VIEW_TITLE_Y)))

        pygame.draw.line(
            surface,
            (55, 60, 75),
            (half, COLUMN_TOP),
            (half, self.screen_size[1] - 24),
            1,
        )

        self._draw_column(
            surface,
            self._player_column(),
            "Your Promises",
            self.election.player_party.value.title(),
            self.election.player_promises,
            interactive=True,
        )
        self._draw_column(
            surface,
            pygame.Rect(half + 12, COLUMN_TOP, half - 36, self.screen_size[1]),
            "Opponent",
            self.election.opponent_party.value.title(),
            self.election.opponent_promises,
            interactive=False,
        )

    def _draw_column(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        heading: str,
        party_label: str,
        promises: dict[str, float],
        *,
        interactive: bool,
    ) -> None:
        x = rect.x + 16
        y = rect.y + 8
        header = self.section_font.render(heading, True, (210, 215, 225))
        surface.blit(header, (x, y))
        y += header.get_height() + 4
        sub = self.label_font.render(party_label, True, (150, 155, 170))
        surface.blit(sub, (x, y))

        bar_width = rect.width - 32
        slider_by_id = {slider.policy_id: slider for slider in self.sliders}
        y = self._rows_start_y()
        for policy in POLICIES:
            dragging = interactive and slider_by_id[policy.id].dragging
            y, bar_rect = draw_policy_row(
                surface,
                x,
                y,
                bar_width,
                policy.title,
                policy.left_label,
                policy.right_label,
                promises[policy.id],
                self.font,
                self.label_font,
                interactive=interactive,
                dragging=dragging,
            )
            if interactive:
                slider_by_id[policy.id].bar_rect = bar_rect

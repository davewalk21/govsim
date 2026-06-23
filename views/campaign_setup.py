from __future__ import annotations

import pygame

from core.party import BACKGROUND_COLOR, PARTY_COLORS, Party
from core.policies import POLICIES, generate_campaign_platforms
from views.layout import VIEW_TITLE_Y
from views.policy_spectrum import draw_policy_row

SETUP_TOP = 108
PARTY_ROW_Y = 158
COLUMN_TOP = 218
HEADER_BLOCK_HEIGHT = 52
BUTTON_WIDTH = 160
BUTTON_HEIGHT = 44
PARTY_BUTTON_WIDTH = 140
ELECTION_CHIP_WIDTH = 200


class CampaignSetupScreen:
    """Campaign creation: election type, party choice, platform comparison."""

    def __init__(self, screen_size: tuple[int, int]) -> None:
        self.screen_size = screen_size
        self.title_font = pygame.font.SysFont(None, 44)
        self.section_font = pygame.font.SysFont(None, 26)
        self.font = pygame.font.SysFont(None, 22)
        self.label_font = pygame.font.SysFont(None, 16)
        self.button_font = pygame.font.SysFont(None, 24)
        self.player_party = Party.DEMOCRAT
        self.dem_platform: dict[str, float] = {}
        self.rep_platform: dict[str, float] = {}
        self.pending_back = False
        self.pending_start = False
        self._build_controls()
        self.reset()

    def reset(self) -> None:
        self.dem_platform, self.rep_platform = generate_campaign_platforms()
        self.player_party = Party.DEMOCRAT
        self.pending_back = False
        self.pending_start = False

    def _build_controls(self) -> None:
        width, height = self.screen_size
        center_x = width // 2
        self.dem_party_rect = pygame.Rect(
            center_x - PARTY_BUTTON_WIDTH - 12,
            PARTY_ROW_Y,
            PARTY_BUTTON_WIDTH,
            BUTTON_HEIGHT,
        )
        self.rep_party_rect = pygame.Rect(
            center_x + 12,
            PARTY_ROW_Y,
            PARTY_BUTTON_WIDTH,
            BUTTON_HEIGHT,
        )
        self.back_rect = pygame.Rect(48, height - 72, BUTTON_WIDTH, BUTTON_HEIGHT)
        self.start_rect = pygame.Rect(
            width - 48 - BUTTON_WIDTH,
            height - 72,
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        if self.dem_party_rect.collidepoint(event.pos):
            self.player_party = Party.DEMOCRAT
            return
        if self.rep_party_rect.collidepoint(event.pos):
            self.player_party = Party.REPUBLICAN
            return
        if self.back_rect.collidepoint(event.pos):
            self.pending_back = True
            return
        if self.start_rect.collidepoint(event.pos):
            self.pending_start = True

    def consume_back(self) -> bool:
        if self.pending_back:
            self.pending_back = False
            return True
        return False

    def consume_start(self) -> tuple[Party, dict[str, float], dict[str, float]] | None:
        if not self.pending_start:
            return None
        self.pending_start = False
        return self.player_party, dict(self.dem_platform), dict(self.rep_platform)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND_COLOR)
        width, _ = self.screen_size
        half = width // 2

        title = self.title_font.render("Campaign Setup", True, (230, 230, 235))
        surface.blit(title, title.get_rect(midtop=(width // 2, VIEW_TITLE_Y)))

        election_label = self.section_font.render("Election", True, (170, 175, 190))
        surface.blit(election_label, (48, SETUP_TOP))
        chip = pygame.Rect(48, SETUP_TOP + election_label.get_height() + 8, ELECTION_CHIP_WIDTH, 36)
        pygame.draw.rect(surface, (45, 50, 64), chip, border_radius=6)
        pygame.draw.rect(surface, (90, 120, 180), chip, 1, border_radius=6)
        chip_text = self.font.render("Presidential", True, (240, 240, 245))
        surface.blit(chip_text, (chip.x + 14, chip.y + 8))

        party_heading = self.section_font.render("Your Party", True, (170, 175, 190))
        surface.blit(party_heading, party_heading.get_rect(midtop=(width // 2, SETUP_TOP - 4)))
        self._draw_party_button(surface, self.dem_party_rect, Party.DEMOCRAT)
        self._draw_party_button(surface, self.rep_party_rect, Party.REPUBLICAN)

        pygame.draw.line(
            surface,
            (55, 60, 75),
            (half, COLUMN_TOP),
            (half, self.screen_size[1] - 96),
            1,
        )

        self._draw_platform_column(
            surface,
            pygame.Rect(24, COLUMN_TOP, half - 36, self.screen_size[1]),
            "Democrat Platform",
            Party.DEMOCRAT,
            self.dem_platform,
            selected=self.player_party == Party.DEMOCRAT,
        )
        self._draw_platform_column(
            surface,
            pygame.Rect(half + 12, COLUMN_TOP, half - 36, self.screen_size[1]),
            "Republican Platform",
            Party.REPUBLICAN,
            self.rep_platform,
            selected=self.player_party == Party.REPUBLICAN,
        )

        self._draw_action_button(surface, self.back_rect, "Back", secondary=True)
        self._draw_action_button(surface, self.start_rect, "Start Campaign")

    def _draw_party_button(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        party: Party,
    ) -> None:
        selected = self.player_party == party
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        base = PARTY_COLORS[party]
        if selected:
            fill = (int(base.r * 0.55), int(base.g * 0.55), int(base.b * 0.55))
            border = base
        elif hovered:
            fill = (55, 62, 82)
            border = (140, 150, 175)
        else:
            fill = (45, 50, 64)
            border = (110, 118, 140)
        pygame.draw.rect(surface, fill, rect, border_radius=8)
        pygame.draw.rect(surface, border, rect, 2 if selected else 1, border_radius=8)
        label = self.button_font.render(party.value.title(), True, (240, 240, 245))
        surface.blit(label, label.get_rect(center=rect.center))

    def _draw_platform_column(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        heading: str,
        party: Party,
        platform: dict[str, float],
        *,
        selected: bool,
    ) -> None:
        if selected:
            highlight = rect.inflate(8, 8)
            pygame.draw.rect(surface, PARTY_COLORS[party], highlight, 2, border_radius=8)

        x = rect.x + 16
        y = rect.y + 8
        header = self.section_font.render(heading, True, (210, 215, 225))
        surface.blit(header, (x, y))
        y += header.get_height() + 4
        if selected:
            sub = self.label_font.render("Your campaign", True, PARTY_COLORS[party])
        else:
            sub = self.label_font.render("Opponent baseline", True, (150, 155, 170))
        surface.blit(sub, (x, y))

        bar_width = rect.width - 32
        y = rect.y + HEADER_BLOCK_HEIGHT
        for policy in POLICIES:
            y, _ = draw_policy_row(
                surface,
                x,
                y,
                bar_width,
                policy.title,
                policy.left_label,
                policy.right_label,
                platform[policy.id],
                self.font,
                self.label_font,
            )

    def _draw_action_button(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        *,
        secondary: bool = False,
    ) -> None:
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        if secondary:
            fill = (55, 62, 82) if hovered else (45, 50, 64)
            border = (140, 150, 175) if hovered else (110, 118, 140)
        else:
            fill = (55, 90, 150) if hovered else (45, 75, 130)
            border = (120, 160, 220) if hovered else (90, 120, 180)
        pygame.draw.rect(surface, fill, rect, border_radius=8)
        pygame.draw.rect(surface, border, rect, 1, border_radius=8)
        text = self.button_font.render(label, True, (240, 240, 245))
        surface.blit(text, text.get_rect(center=rect.center))

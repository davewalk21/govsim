from __future__ import annotations

import pygame

from views.home_button import HOME_BUTTON_WIDTH, draw_home_button
from views.layout import NAV_BOTTOM, NAV_HEIGHT, NAV_Y

NEXT_TURN_WIDTH = 120
NEXT_TURN_HEIGHT = NAV_HEIGHT
HOME_GAP = 8


class ElectionGameBar:
    """Top bar for presidential election: countdown + Next Turn + Home."""

    def __init__(self, screen_size: tuple[int, int]) -> None:
        self.screen_size = screen_size
        self.font = pygame.font.SysFont(None, 24)
        self.button_font = pygame.font.SysFont(None, 22)
        width = screen_size[0]
        self.next_turn_rect = pygame.Rect(
            width - 24 - NEXT_TURN_WIDTH,
            NAV_Y,
            NEXT_TURN_WIDTH,
            NEXT_TURN_HEIGHT,
        )
        self.home_rect = pygame.Rect(
            self.next_turn_rect.x - HOME_GAP - HOME_BUTTON_WIDTH,
            NAV_Y,
            HOME_BUTTON_WIDTH,
            NEXT_TURN_HEIGHT,
        )
        self.countdown_text = ""
        self.button_enabled = True
        self.pending_next_turn = False
        self.pending_home = False

    def set_countdown(self, text: str, *, button_enabled: bool = True) -> None:
        self.countdown_text = text
        self.button_enabled = button_enabled

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        if self.home_rect.collidepoint(event.pos):
            self.pending_home = True
            return True
        if not self.button_enabled:
            return False
        if self.next_turn_rect.collidepoint(event.pos):
            self.pending_next_turn = True
            return True
        return False

    def consume_next_turn(self) -> bool:
        if self.pending_next_turn:
            self.pending_next_turn = False
            return True
        return False

    def consume_home(self) -> bool:
        if self.pending_home:
            self.pending_home = False
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        width = surface.get_width()
        pygame.draw.rect(surface, (22, 24, 32), pygame.Rect(0, 0, width, NAV_BOTTOM))
        pygame.draw.line(surface, (55, 60, 75), (0, NAV_BOTTOM - 1), (width, NAV_BOTTOM - 1))

        title = self.font.render("Presidential Election", True, (210, 215, 225))
        surface.blit(title, (24, NAV_Y + 6))

        countdown = self.font.render(self.countdown_text, True, (170, 175, 190))
        countdown_x = self.home_rect.x - countdown.get_width() - 20
        surface.blit(countdown, (countdown_x, NAV_Y + 6))

        draw_home_button(surface, self.home_rect, self.button_font)

        hovered = self.next_turn_rect.collidepoint(pygame.mouse.get_pos())
        if self.button_enabled:
            fill = (55, 90, 150) if hovered else (45, 75, 130)
            border = (120, 160, 220) if hovered else (90, 120, 180)
        else:
            fill = (40, 42, 50)
            border = (70, 75, 90)
        pygame.draw.rect(surface, fill, self.next_turn_rect, border_radius=6)
        pygame.draw.rect(surface, border, self.next_turn_rect, 1, border_radius=6)
        label = self.button_font.render("Next Turn", True, (240, 240, 245))
        surface.blit(label, label.get_rect(center=self.next_turn_rect.center))

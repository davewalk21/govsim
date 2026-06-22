from __future__ import annotations

import pygame

from core.party import BACKGROUND_COLOR

BUTTON_WIDTH = 280
BUTTON_HEIGHT = 48
BUTTON_GAP = 16


class HomeScreen:
    """Main menu: New Game, Dev Mode, Exit."""

    def __init__(self, screen_size: tuple[int, int]) -> None:
        self.screen_size = screen_size
        self.title_font = pygame.font.SysFont(None, 56)
        self.font = pygame.font.SysFont(None, 28)
        self.buttons = self._build_buttons()
        self.pending_action: str | None = None

    def _build_buttons(self) -> list[tuple[pygame.Rect, str, str]]:
        width, height = self.screen_size
        labels = (
            ("New Game", "new_game"),
            ("Dev Mode", "dev_mode"),
            ("Exit", "exit"),
        )
        total_height = len(labels) * BUTTON_HEIGHT + (len(labels) - 1) * BUTTON_GAP
        start_y = height // 2 - total_height // 2 + 40
        buttons: list[tuple[pygame.Rect, str, str]] = []
        for index, (label, action) in enumerate(labels):
            rect = pygame.Rect(
                (width - BUTTON_WIDTH) // 2,
                start_y + index * (BUTTON_HEIGHT + BUTTON_GAP),
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
            )
            buttons.append((rect, label, action))
        return buttons

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        for rect, _, action in self.buttons:
            if rect.collidepoint(event.pos):
                self.pending_action = action
                return

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND_COLOR)
        width, _ = self.screen_size

        title = self.title_font.render("GovSim", True, (230, 230, 235))
        surface.blit(title, title.get_rect(midtop=(width // 2, 120)))

        subtitle = self.font.render("Government Simulator", True, (150, 155, 170))
        surface.blit(subtitle, subtitle.get_rect(midtop=(width // 2, 185)))

        mouse_pos = pygame.mouse.get_pos()
        for rect, label, _ in self.buttons:
            hovered = rect.collidepoint(mouse_pos)
            fill = (55, 62, 82) if hovered else (45, 50, 64)
            border = (140, 150, 175) if hovered else (110, 118, 140)
            pygame.draw.rect(surface, fill, rect, border_radius=8)
            pygame.draw.rect(surface, border, rect, 1, border_radius=8)
            text = self.font.render(label, True, (240, 240, 245))
            surface.blit(text, text.get_rect(center=rect.center))

from __future__ import annotations

import pygame


class Dropdown:
    """Simple click-to-open menu for switching views."""

    def __init__(
        self,
        rect: pygame.Rect,
        options: list[tuple[str, str]],
        selected_key: str,
    ) -> None:
        self.rect = rect
        self.options = options
        self.selected_key = selected_key
        self.open = False
        self.font = pygame.font.SysFont(None, 26)
        self.row_height = 34

    @property
    def selected_label(self) -> str:
        for label, key in self.options:
            if key == self.selected_key:
                return label
        return self.options[0][0]

    def set_selected(self, key: str) -> None:
        self.selected_key = key

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.open:
                menu_rect = self._menu_rect()
                if menu_rect.collidepoint(event.pos):
                    for index, (_, key) in enumerate(self.options):
                        row = pygame.Rect(
                            menu_rect.x,
                            menu_rect.y + index * self.row_height,
                            menu_rect.width,
                            self.row_height,
                        )
                        if row.collidepoint(event.pos):
                            self.selected_key = key
                            self.open = False
                            return True
                self.open = False
                return True

            if self.rect.collidepoint(event.pos):
                self.open = True
                return True

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.open:
                self.open = False
                return True

        return self.open

    def draw(self, surface: pygame.Surface) -> None:
        if self.open:
            menu_rect = self._menu_rect()
            pygame.draw.rect(surface, (38, 42, 54), menu_rect, border_radius=6)
            pygame.draw.rect(surface, (90, 98, 120), menu_rect, 1, border_radius=6)

            for index, (label, key) in enumerate(self.options):
                row = pygame.Rect(
                    menu_rect.x,
                    menu_rect.y + index * self.row_height,
                    menu_rect.width,
                    self.row_height,
                )
                if key == self.selected_key:
                    pygame.draw.rect(surface, (55, 62, 82), row)
                text = self.font.render(label, True, (235, 235, 240))
                surface.blit(text, (row.x + 12, row.y + 7))

        pygame.draw.rect(surface, (45, 50, 64), self.rect, border_radius=6)
        pygame.draw.rect(surface, (110, 118, 140), self.rect, 1, border_radius=6)

        label = self.font.render(self.selected_label, True, (240, 240, 245))
        surface.blit(label, (self.rect.x + 12, self.rect.y + 7))

        arrow = self.font.render("v" if not self.open else "^", True, (180, 185, 200))
        surface.blit(arrow, (self.rect.right - 22, self.rect.y + 7))

    def _menu_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.rect.x,
            self.rect.bottom + 4,
            self.rect.width,
            len(self.options) * self.row_height,
        )

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from core.party import (
    BACKGROUND_COLOR,
    PARTY_COLORS,
    Party,
    apply_half_split,
    count_parties,
    cycle_party,
)
from views.party_bar import draw_party_bar


@dataclass
class Seat:
    index: int
    party: Party
    position: pygame.Vector2
    radius: float

    def contains(self, point: tuple[int, int]) -> bool:
        return self.position.distance_to(point) <= self.radius + 2


class ChamberView:
    """Semicircle seating chart shared by Senate (100) and House (435)."""

    def __init__(
        self,
        title: str,
        seat_count: int,
        rows: int,
        screen_size: tuple[int, int],
    ) -> None:
        self.title = title
        self.seat_count = seat_count
        self.rows = rows
        self.screen_size = screen_size
        self.seats = self._build_seats()
        apply_half_split(self.seats, lambda seat, party: setattr(seat, "party", party))
        self.font = pygame.font.SysFont(None, 22)
        self.title_font = pygame.font.SysFont(None, 36)
        self.bar_rect = pygame.Rect(250, 98, screen_size[0] - 430, 32)

    def _build_seats(self) -> list[Seat]:
        width, height = self.screen_size
        base = min(width, height)
        size_factor = min(math.sqrt(435 / self.seat_count), 2.25)

        inner_radius = base * 0.10 * size_factor
        row_spacing = base * 0.042 * size_factor
        outer_radius = inner_radius + (self.rows - 1) * row_spacing
        max_allowed = min(width * 0.44, height * 0.52)
        if outer_radius > max_allowed:
            shrink = max_allowed / outer_radius
            inner_radius *= shrink
            row_spacing *= shrink

        center = pygame.Vector2(width * 0.5, height * 0.84)
        center_gap = math.radians(12 + 4 * (435 / max(self.seat_count, 1)))
        row_counts = _distribute_seats(self.seat_count, self.rows)
        seat_radius = max(6.0, min(22.0, base * 0.016 * size_factor))
        label_size = max(14, min(24, int(seat_radius * 1.25)))
        self.seat_font = pygame.font.SysFont(None, label_size)

        seats: list[Seat] = []
        seat_index = 1
        for row, count in enumerate(row_counts):
            row_radius = inner_radius + row * row_spacing
            left_count = count // 2
            right_count = count - left_count
            left_start = math.pi
            left_end = math.pi / 2 + center_gap / 2
            right_start = math.pi / 2 - center_gap / 2
            right_end = 0.0

            for side_count, start_angle, end_angle in (
                (left_count, left_start, left_end),
                (right_count, right_start, right_end),
            ):
                if side_count <= 0:
                    continue
                if side_count == 1:
                    angles = [(start_angle + end_angle) / 2]
                else:
                    step = (start_angle - end_angle) / (side_count - 1)
                    angles = [start_angle - step * i for i in range(side_count)]

                for angle in angles:
                    position = center + pygame.Vector2(
                        math.cos(angle) * row_radius,
                        -math.sin(angle) * row_radius,
                    )
                    seats.append(
                        Seat(
                            index=seat_index,
                            party=Party.DEMOCRAT,
                            position=position,
                            radius=seat_radius,
                        )
                    )
                    seat_index += 1

        return seats

    def party_counts(self) -> dict[Party, int]:
        return count_parties(self.seats, lambda seat: seat.party)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        point = event.pos
        for seat in reversed(self.seats):
            if seat.contains(point):
                seat.party = cycle_party(seat.party)
                break

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND_COLOR)
        width, height = self.screen_size

        title = self.title_font.render(self.title, True, (230, 230, 235))
        surface.blit(title, title.get_rect(midtop=(width // 2, 12)))

        dais = pygame.Rect(width // 2 - 90, 52, 180, 36)
        pygame.draw.rect(surface, (55, 58, 70), dais, border_radius=4)
        dais_label = self.font.render("Dais", True, (210, 210, 215))
        surface.blit(dais_label, dais_label.get_rect(center=dais.center))

        draw_party_bar(surface, self.bar_rect, self.party_counts(), self.font)

        hint = self.font.render(
            "Click a seat to cycle blue → red → yellow", True, (150, 155, 170)
        )
        surface.blit(hint, (24, height - 28))

        for seat in self.seats:
            color = PARTY_COLORS[seat.party]
            pygame.draw.circle(
                surface, color, seat.position, int(seat.radius)
            )
            if self.seat_count <= 100:
                label = self.seat_font.render(str(seat.index), True, (245, 245, 245))
                surface.blit(
                    label,
                    label.get_rect(center=(int(seat.position.x), int(seat.position.y))),
                )

        self._draw_legend(surface)

    def _draw_legend(self, surface: pygame.Surface) -> None:
        x, y = self.screen_size[0] - 170, 16
        for party in (Party.DEMOCRAT, Party.REPUBLICAN, Party.INDEPENDENT):
            pygame.draw.circle(surface, PARTY_COLORS[party], (x, y + 8), 8)
            text = self.font.render(party.value.title(), True, (220, 220, 225))
            surface.blit(text, (x + 16, y))
            y += 24


def _distribute_seats(total: int, rows: int) -> list[int]:
    weights = [index + 1 for index in range(rows)]
    weight_sum = sum(weights)
    counts = [max(1, round(total * weight / weight_sum)) for weight in weights]

    while sum(counts) > total:
        max_index = counts.index(max(counts))
        counts[max_index] -= 1
    while sum(counts) < total:
        counts[-1] += 1
    return counts

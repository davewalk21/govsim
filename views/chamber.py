from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from core.party import BACKGROUND_COLOR, PARTY_COLORS, Party
from core.politician import Politician
from core.rosters import Roster
from views.party_bar import draw_party_bar, party_bar_rect

SEAT_PADDING = 3


@dataclass
class Seat:
    index: int
    politician_id: str
    position: pygame.Vector2
    radius: float

    def contains(self, point: tuple[int, int]) -> bool:
        return self.position.distance_to(point) <= self.radius + 2


class ChamberView:
    """Semicircle seating chart driven by a politician roster."""

    def __init__(
        self,
        title: str,
        roster: Roster,
        rows: int,
        screen_size: tuple[int, int],
    ) -> None:
        self.title = title
        self.roster = roster
        self.seat_count = len(roster.members)
        self.rows = rows
        self.screen_size = screen_size
        self.font = pygame.font.SysFont(None, 22)
        self.title_font = pygame.font.SysFont(None, 36)
        width = screen_size[0]
        self.bar_rect = party_bar_rect(width)
        self.seats: list[Seat] = []
        self.seat_font = pygame.font.SysFont(None, 14)
        self._refresh_seats()

    def _refresh_seats(self) -> None:
        self.seats, self.seat_font = self._build_seats()

    def _build_seats(self) -> tuple[list[Seat], pygame.font.Font]:
        width, height = self.screen_size
        base = min(width, height)
        center = pygame.Vector2(width * 0.5, height * 0.84)
        max_arc_radius = min(width * 0.44, height * 0.50)

        row_counts = _distribute_seats(self.seat_count, self.rows)
        ordered = _order_for_chamber(self.roster.members)

        size_factor = min(math.sqrt(435 / self.seat_count), 2.25)
        seat_radius = max(6.0, min(22.0, base * 0.016 * size_factor))

        inner_radius, row_spacing = _fit_semicircle_layout(
            row_counts, seat_radius, max_arc_radius
        )

        label_size = max(10, min(18, int(seat_radius * 1.1)))
        seat_font = pygame.font.SysFont(None, label_size)

        slots = _build_slot_geometry(
            center, row_counts, inner_radius, row_spacing
        )

        seats: list[Seat] = []
        for index, (position, politician) in enumerate(zip(slots, ordered)):
            seats.append(
                Seat(
                    index=index + 1,
                    politician_id=politician.id,
                    position=position,
                    radius=seat_radius,
                )
            )

        return seats, seat_font

    def party_counts(self) -> dict[Party, int]:
        return self.roster.party_counts()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        point = event.pos
        for seat in reversed(self.seats):
            if seat.contains(point):
                self.roster.cycle_member(seat.politician_id)
                self._refresh_seats()
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
            politician = self.roster.get(seat.politician_id)
            color = PARTY_COLORS[politician.party]
            pygame.draw.circle(surface, color, seat.position, int(seat.radius))
            label = self.seat_font.render(politician.title, True, (245, 245, 245))
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


def _party_queues(
    members: list[Politician],
) -> tuple[list[Politician], list[Politician], list[Politician]]:
    """Democrats, independents, republicans — each grouped by state."""

    def group_by_state(party_members: list[Politician]) -> list[Politician]:
        by_state: dict[str, list[Politician]] = {}
        for member in party_members:
            key = member.state or ""
            by_state.setdefault(key, []).append(member)
        ordered: list[Politician] = []
        for state in sorted(by_state.keys()):
            group = sorted(
                by_state[state],
                key=lambda member: (member.seat or 0, member.district or 0, member.id),
            )
            ordered.extend(group)
        return ordered

    democrats = group_by_state([m for m in members if m.party == Party.DEMOCRAT])
    independents = group_by_state([m for m in members if m.party == Party.INDEPENDENT])
    republicans = group_by_state([m for m in members if m.party == Party.REPUBLICAN])
    return democrats, independents, republicans


def _order_for_chamber(members: list[Politician]) -> list[Politician]:
    """Left to right: Democrats, independents, Republicans (state-grouped within each)."""
    dems, independents, reps = _party_queues(members)
    return dems + independents + reps


def _build_slot_geometry(
    center: pygame.Vector2,
    row_counts: list[int],
    inner_radius: float,
    row_spacing: float,
) -> list[pygame.Vector2]:
    """Fixed semicircle slots sorted left-to-right (angle), inner-to-outer (radius)."""
    slots: list[tuple[float, float, pygame.Vector2]] = []

    for row, count in enumerate(row_counts):
        row_radius = inner_radius + row * row_spacing
        for angle in _row_angles(count):
            position = center + pygame.Vector2(
                math.cos(angle) * row_radius,
                -math.sin(angle) * row_radius,
            )
            slots.append((angle, row_radius, position))

    slots.sort(key=lambda slot: (-slot[0], slot[1]))
    return [position for _, _, position in slots]


def _row_angles(count: int) -> list[float]:
    if count <= 1:
        return [math.pi / 2]
    step = math.pi / (count - 1)
    return [math.pi - step * index for index in range(count)]


def _min_radius_for_row(count: int, seat_radius: float) -> float:
    if count <= 1:
        return 0.0
    return 2 * (seat_radius + SEAT_PADDING) * (count - 1) / math.pi


def _fit_semicircle_layout(
    row_counts: list[int],
    seat_radius: float,
    max_arc_radius: float,
) -> tuple[float, float]:
    radial_gap = 2 * seat_radius + SEAT_PADDING
    inner_radius = max(_min_radius_for_row(row_counts[0], seat_radius), seat_radius + 4)
    row_spacing = radial_gap

    for _ in range(24):
        outer_radius = inner_radius + (len(row_counts) - 1) * row_spacing
        arc_ok = all(
            _min_radius_for_row(count, seat_radius) <= inner_radius + row * row_spacing
            for row, count in enumerate(row_counts)
        )
        if outer_radius <= max_arc_radius and arc_ok:
            return inner_radius, row_spacing

        if outer_radius > max_arc_radius:
            row_spacing *= 0.94
            inner_radius *= 0.96
        elif not arc_ok:
            inner_radius += 4
            row_spacing += 1
        else:
            break

    return inner_radius, row_spacing


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

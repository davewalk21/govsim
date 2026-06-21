from __future__ import annotations

from enum import Enum
from typing import Callable, Iterable, TypeVar

import pygame

T = TypeVar("T")

BACKGROUND_COLOR = (18, 20, 28)


class Party(Enum):
    DEMOCRAT = "democrat"
    REPUBLICAN = "republican"
    INDEPENDENT = "independent"


PARTY_COLORS: dict[Party, pygame.Color] = {
    Party.DEMOCRAT: pygame.Color(48, 99, 191),
    Party.REPUBLICAN: pygame.Color(212, 64, 64),
    Party.INDEPENDENT: pygame.Color(240, 190, 50),
}

SPLIT_STATE_COLOR = pygame.Color(140, 80, 180)
NO_DELEGATION_COLOR = pygame.Color(55, 58, 70)


def color_for_senate_delegation(parties: list[Party]) -> pygame.Color:
    if not parties:
        return NO_DELEGATION_COLOR
    if len(set(parties)) == 1:
        return PARTY_COLORS[parties[0]]
    return SPLIT_STATE_COLOR


def color_for_weighted_parties(parties: list[Party]) -> pygame.Color:
    """Blend party colors by seat count (e.g. 2D + 1I + 5R → mostly red with hints of blue/yellow)."""
    if not parties:
        return NO_DELEGATION_COLOR
    total = len(parties)
    red = sum(PARTY_COLORS[party].r for party in parties) / total
    green = sum(PARTY_COLORS[party].g for party in parties) / total
    blue = sum(PARTY_COLORS[party].b for party in parties) / total
    return pygame.Color(int(red), int(green), int(blue))


def cycle_party(party: Party) -> Party:
    order = (Party.DEMOCRAT, Party.REPUBLICAN, Party.INDEPENDENT)
    index = order.index(party)
    return order[(index + 1) % len(order)]


def swap_major_party(party: Party) -> Party:
    """Toggle Democrat ↔ Republican. Independents become Democrat."""
    if party == Party.DEMOCRAT:
        return Party.REPUBLICAN
    if party == Party.REPUBLICAN:
        return Party.DEMOCRAT
    return Party.DEMOCRAT


def senate_major_party(party: Party) -> Party:
    """Senate map cycling treats independents as Republican."""
    if party == Party.DEMOCRAT:
        return Party.DEMOCRAT
    return Party.REPUBLICAN


def cycle_senate_delegation(senators: list) -> None:
    """Cycle R,R → D,R → D,D → R,D → R,R (flip seat 1, then seat 2)."""
    if len(senators) != 2:
        return
    ordered = sorted(senators, key=lambda member: member.seat or 0)
    first = senate_major_party(ordered[0].party)
    second = senate_major_party(ordered[1].party)
    if first == Party.REPUBLICAN and second == Party.REPUBLICAN:
        ordered[0].party = Party.DEMOCRAT
    elif first == Party.DEMOCRAT and second == Party.REPUBLICAN:
        ordered[1].party = Party.DEMOCRAT
    elif first == Party.DEMOCRAT and second == Party.DEMOCRAT:
        ordered[0].party = Party.REPUBLICAN
    else:
        ordered[1].party = Party.REPUBLICAN


def default_party_for_index(index: int, total: int) -> Party:
    """First half Democrat, second half Republican."""
    if index < total // 2:
        return Party.DEMOCRAT
    return Party.REPUBLICAN


def apply_half_split(items: list[T], party_setter: Callable[[T, Party], None]) -> None:
    total = len(items)
    for index, item in enumerate(items):
        party_setter(item, default_party_for_index(index, total))


def count_parties(items: Iterable[T], party_getter: Callable[[T], Party]) -> dict[Party, int]:
    counts = {party: 0 for party in Party}
    for item in items:
        counts[party_getter(item)] += 1
    return counts

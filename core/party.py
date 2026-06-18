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


def cycle_party(party: Party) -> Party:
    order = (Party.DEMOCRAT, Party.REPUBLICAN, Party.INDEPENDENT)
    index = order.index(party)
    return order[(index + 1) % len(order)]


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

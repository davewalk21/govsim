from __future__ import annotations

from dataclasses import dataclass

from core.politician import Politician
from core.rosters import Roster, create_court, create_governors, create_house, create_senate


@dataclass
class Government:
    """Top-level game state. All views read and write politician data through here."""

    senate: Roster
    house: Roster
    governors: Roster
    court: Roster

    @classmethod
    def create_default(cls) -> Government:
        return cls(
            senate=create_senate(),
            house=create_house(),
            governors=create_governors(),
            court=create_court(),
        )

    def all_politicians(self) -> list[Politician]:
        return (
            self.senate.members
            + self.house.members
            + self.governors.members
            + self.court.members
        )

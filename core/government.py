from __future__ import annotations

from dataclasses import dataclass

from core.rosters import Roster, create_governors, create_house, create_senate


@dataclass
class Government:
    """Top-level game state. All views read and write politician data through here."""

    senate: Roster
    house: Roster
    governors: Roster

    @classmethod
    def create_default(cls) -> Government:
        return cls(
            senate=create_senate(),
            house=create_house(),
            governors=create_governors(),
        )

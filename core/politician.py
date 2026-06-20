from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.party import Party


class Office(Enum):
    SENATE = "senate"
    HOUSE = "house"
    GOVERNOR = "governor"


def build_title(office: Office, state: str, *, district: int | None = None, seat: int | None = None) -> str:
    if office == Office.GOVERNOR:
        return f"{state}-G"
    if office == Office.SENATE:
        return f"{state}-{seat}"
    if office == Office.HOUSE:
        return f"{state}-{district}"
    raise ValueError(f"Unknown office: {office}")


@dataclass
class Politician:
    """A single office-holder. Source-of-truth record for party and identity."""

    id: str
    name: str
    title: str
    party: Party
    office: Office
    state: str | None = None
    district: int | None = None
    seat: int | None = None

    def cycle_party(self) -> None:
        from core.party import cycle_party

        self.party = cycle_party(self.party)

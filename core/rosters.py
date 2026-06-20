from __future__ import annotations

from dataclasses import dataclass, field

from core.party import Party, count_parties, default_party_for_index
from core.politician import Office, Politician, build_title
from core.states import HOUSE_SEATS_BY_STATE, STATE_ABBREV_TO_NAME, US_STATE_ABBREVS

SENATE_SEATS = 100
HOUSE_SEATS = 435
GOVERNOR_SEATS = len(US_STATE_ABBREVS)


@dataclass
class Roster:
    """Ordered list of politicians for one office type."""

    office: Office
    members: list[Politician] = field(default_factory=list)
    _by_id: dict[str, Politician] = field(default_factory=dict, init=False, repr=False)
    _by_state: dict[str, Politician] = field(default_factory=dict, init=False, repr=False)
    _senators_by_state: dict[str, list[Politician]] = field(
        default_factory=dict, init=False, repr=False
    )
    _house_by_state: dict[str, list[Politician]] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        self._reindex()

    def _reindex(self) -> None:
        self._by_id = {member.id: member for member in self.members}
        self._by_state = {
            member.state: member
            for member in self.members
            if member.state is not None and member.office == Office.GOVERNOR
        }
        self._senators_by_state = {}
        for member in self.members:
            if member.office == Office.SENATE and member.state is not None:
                self._senators_by_state.setdefault(member.state, []).append(member)
        for senators in self._senators_by_state.values():
            senators.sort(key=lambda member: member.seat or 0)
        self._house_by_state = {}
        for member in self.members:
            if member.office == Office.HOUSE and member.state is not None:
                self._house_by_state.setdefault(member.state, []).append(member)
        for representatives in self._house_by_state.values():
            representatives.sort(key=lambda member: member.district or 0)

    def get(self, member_id: str) -> Politician:
        return self._by_id[member_id]

    def member_at(self, index: int) -> Politician:
        return self.members[index]

    def governor_for_state(self, state_abbrev: str) -> Politician | None:
        return self._by_state.get(state_abbrev)

    def senators_for_state(self, state_abbrev: str) -> list[Politician]:
        return list(self._senators_by_state.get(state_abbrev, []))

    def representatives_for_state(self, state_abbrev: str) -> list[Politician]:
        return list(self._house_by_state.get(state_abbrev, []))

    def party_counts(self) -> dict[Party, int]:
        return count_parties(self.members, lambda member: member.party)

    def cycle_member(self, member_id: str) -> None:
        self.get(member_id).cycle_party()


def create_senate() -> Roster:
    members: list[Politician] = []
    for state in US_STATE_ABBREVS:
        for seat in (1, 2):
            index = len(members)
            title = build_title(Office.SENATE, state, seat=seat)
            members.append(
                Politician(
                    id=f"senate-{state}-{seat}",
                    name=f"Placeholder ({title})",
                    title=title,
                    party=default_party_for_index(index, SENATE_SEATS),
                    office=Office.SENATE,
                    state=state,
                    seat=seat,
                )
            )
    return Roster(office=Office.SENATE, members=members)


def create_house() -> Roster:
    members: list[Politician] = []
    for state in US_STATE_ABBREVS:
        for district in range(1, HOUSE_SEATS_BY_STATE[state] + 1):
            index = len(members)
            title = build_title(Office.HOUSE, state, district=district)
            members.append(
                Politician(
                    id=f"house-{state}-{district}",
                    name=f"Placeholder ({title})",
                    title=title,
                    party=default_party_for_index(index, HOUSE_SEATS),
                    office=Office.HOUSE,
                    state=state,
                    district=district,
                )
            )
    return Roster(office=Office.HOUSE, members=members)


def create_governors() -> Roster:
    members: list[Politician] = []
    for index, state in enumerate(US_STATE_ABBREVS):
        full_name = STATE_ABBREV_TO_NAME.get(state, state)
        title = build_title(Office.GOVERNOR, state)
        members.append(
            Politician(
                id=f"governor-{state}",
                name=f"Placeholder ({full_name})",
                title=title,
                party=default_party_for_index(index, GOVERNOR_SEATS),
                office=Office.GOVERNOR,
                state=state,
            )
        )
    return Roster(office=Office.GOVERNOR, members=members)

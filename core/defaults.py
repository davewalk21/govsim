"""Load starting party defaults from data/default_parties.py."""

from __future__ import annotations

import importlib
from typing import Iterable

from core.party import Party
from core.states import HOUSE_SEATS_BY_STATE, US_STATE_ABBREVS

_PARTY_CODES = {
    "D": Party.DEMOCRAT,
    "R": Party.REPUBLICAN,
    "I": Party.INDEPENDENT,
}


def _parse_party(code: str) -> Party:
    try:
        return _PARTY_CODES[code.upper()]
    except KeyError as exc:
        raise ValueError(f"Invalid party code {code!r}; use D, R, or I") from exc


def _load_defaults_module():
    return importlib.import_module("data.default_parties")


def state_lean(state: str) -> Party:
    module = _load_defaults_module()
    code = module.STATE_LEAN[state]
    return _parse_party(code)


def all_state_leans() -> dict[str, Party]:
    return {state: state_lean(state) for state in US_STATE_ABBREVS}


def senate_seat_parties(state: str) -> tuple[Party, Party]:
    module = _load_defaults_module()
    if state in module.SENATE:
        seat1, seat2 = module.SENATE[state]
        return _parse_party(seat1), _parse_party(seat2)
    lean = state_lean(state)
    return lean, lean


def house_district_parties(state: str) -> tuple[Party, ...]:
    module = _load_defaults_module()
    seat_count = HOUSE_SEATS_BY_STATE[state]
    if state in module.HOUSE:
        codes: Iterable[str] = module.HOUSE[state]
        parties = tuple(_parse_party(code) for code in codes)
        if len(parties) != seat_count:
            raise ValueError(
                f"HOUSE[{state}] has {len(parties)} entries; expected {seat_count}"
            )
        return parties
    lean = state_lean(state)
    return tuple(lean for _ in range(seat_count))


def court_seat_party(seat: int) -> Party:
    module = _load_defaults_module()
    codes = module.COURT
    if seat < 1 or seat > len(codes):
        raise ValueError(f"Court seat {seat} out of range for COURT defaults")
    return _parse_party(codes[seat - 1])

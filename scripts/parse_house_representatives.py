"""Parse house.gov representatives markdown export into HOUSE defaults."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.states import HOUSE_SEATS_BY_STATE, STATE_ABBREV_TO_NAME, US_STATE_ABBREVS

SOURCE = ROOT / "data" / "house_representatives.md"
PER_LINE = 8

NAME_TO_ABBREV = {name: abbrev for abbrev, name in STATE_ABBREV_TO_NAME.items()}

DISTRICT_RE = re.compile(r"^(\d+)(?:st|nd|rd|th)$", re.I)
STATE_HEADER_RE = re.compile(r"^__(.+?)__$")
ROW_RE = re.compile(r"^\| ([^|]+?) \| .+? \| ([DRI]) ")


def parse_district(label: str) -> int | None:
    label = label.strip()
    if label.lower() == "at large":
        return 1
    if label.lower() == "delegate":
        return None
    match = DISTRICT_RE.match(label)
    if match:
        return int(match.group(1))
    return None


def parse_representatives(path: Path) -> dict[str, dict[int, str]]:
    by_state: dict[str, dict[int, str]] = {}
    current_state: str | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        state_match = STATE_HEADER_RE.match(line)
        if state_match:
            state_name = state_match.group(1)
            current_state = NAME_TO_ABBREV.get(state_name)
            if current_state and current_state not in by_state:
                by_state[current_state] = {}
            continue

        if current_state is None:
            continue

        row_match = ROW_RE.match(line)
        if not row_match:
            continue

        district_label, party = row_match.group(1), row_match.group(2)
        district = parse_district(district_label)
        if district is None:
            continue

        by_state[current_state][district] = party

    return by_state


def format_state(state: str, parties: tuple[str, ...]) -> str:
    n = len(parties)
    if n == 1:
        return f'    "{state}": ("{parties[0]}",),'
    if n <= PER_LINE:
        inner = ", ".join(f'"{p}"' for p in parties)
        return f'    "{state}": ({inner}),'
    lines = [f'    "{state}": (']
    for i in range(0, n, PER_LINE):
        chunk = parties[i : i + PER_LINE]
        inner = ", ".join(f'"{p}"' for p in chunk)
        if i + PER_LINE < n:
            lines.append(f"        {inner},")
        else:
            lines.append(f"        {inner},")
    lines.append("    ),")
    return "\n".join(lines)


def main() -> None:
    parsed = parse_representatives(SOURCE)
    missing_states = [s for s in US_STATE_ABBREVS if s not in parsed]
    if missing_states:
        raise SystemExit(f"Missing states: {missing_states}")

    house: dict[str, tuple[str, ...]] = {}
    for state in US_STATE_ABBREVS:
        expected = HOUSE_SEATS_BY_STATE[state]
        districts = parsed[state]
        parties = []
        for district in range(1, expected + 1):
            if district not in districts:
                raise SystemExit(f"{state} missing district {district}")
            parties.append(districts[district])
        if len(districts) != expected:
            extra = set(districts) - set(range(1, expected + 1))
            if extra:
                raise SystemExit(f"{state} unexpected districts: {sorted(extra)}")
        house[state] = tuple(parties)

    total = sum(len(v) for v in house.values())
    print(f"# {total} districts from {SOURCE.name}")
    print("HOUSE = {")
    for state in US_STATE_ABBREVS:
        print(format_state(state, house[state]))
    print("}")

    counts = {"D": 0, "R": 0, "I": 0}
    for parties in house.values():
        for p in parties:
            counts[p] += 1
    print(f"# D={counts['D']} R={counts['R']} I={counts['I']}", file=sys.stderr)


if __name__ == "__main__":
    main()

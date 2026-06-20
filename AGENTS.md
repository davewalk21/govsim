# GovSim — Agent Instructions

Government simulator game in Python + Pygame. UI-first phase: three interactive views with live party totals.

## Project layout

```
govsim/
├── main.py              # Game loop, view switching, dropdown
├── core/
│   ├── party.py         # Party enum, colors, counting helpers
│   ├── politician.py    # Politician record + Office enum
│   ├── rosters.py       # Roster + create_senate/house/governors()
│   ├── government.py    # Government — source of truth for all office-holders
│   └── states.py        # US state abbreviations
├── views/
│   ├── chamber.py       # Senate & House semicircles (read from Roster)
│   ├── map_view.py      # Governors map (read from governors Roster)
│   ├── party_bar.py     # Shared D | I | R totals bar
│   └── dropdown.py      # View switcher (top-left)
├── data/
│   └── us_states.json   # State boundaries (do not commit huge replacements)
└── requirements.txt     # pygame
```

## Source of truth

All party affiliation lives on `Politician` objects inside `Government`:

- `government.senate` — 100 senators (2 per state)
- `government.house` — 435 representatives
- `government.governors` — 50 governors (1 per state)

Views are display layers only. Clicking a seat or state calls `roster.cycle_member(id)`.

## Run & test

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

Controls: dropdown (top-left) or keys **1** Senate, **2** House, **3** Map. Click seats/states to cycle party: Democrat → Republican → Independent.

## Architecture conventions

- **Shared party logic** lives in `core/party.py` — colors, `cycle_party()`, `apply_half_split()`, `count_parties()`.
- **Views** own drawing and click handling; each exposes `draw()`, `handle_event()`, and `party_counts()` where applicable.
- **Senate and House** share `ChamberView` with different `seat_count` / `rows`.
- **Party bar** is drawn via `views/party_bar.draw_party_bar()` — order is always Dem (left), Independent (center), Rep (right).
- **Background color** is `BACKGROUND_COLOR` in `core/party.py` — use it for all views (dark theme).

## Defaults

- Senate, House, and Map start **50/50 Democrat/Republican** via `apply_half_split()`.
- Independents start at 0; users add them by clicking.

## Coding guidelines

- **Python 3.8+** compatible (venv may be 3.8). Use `from __future__ import annotations` for modern type hints.
- **Keep changes focused** — match existing style; don't over-abstract.
- **File encoding: UTF-8 only.** On Windows, `.py` files must be saved as UTF-8 (not UTF-16). Check Cursor status bar before saving. Project has `.editorconfig` and `.vscode/settings.json` enforcing this.
- When writing files programmatically on Windows, verify encoding (UTF-8 bytes should start with ASCII like `69 6D 70 6F 72 74` for `import`, not `69 00 6D 00`).
- Do not commit `.venv/`.

## Common tasks

| Task | Where to change |
|------|-----------------|
| Add a new view | New class in `views/`, register in `main.py` + dropdown options |
| Change party colors | `PARTY_COLORS` in `core/party.py` |
| Change starting affiliation | `default_party_for_index()` or `apply_half_split()` in `core/party.py` |
| Tune seat layout / dot size | `ChamberView._build_seats()` in `views/chamber.py` |
| Map appearance / projection | `GovernorMapView`, `SenateMapView`, `HouseMapView` in `views/map_view.py` |

## Out of scope (for now)

- Game loop / simulation mechanics (elections, votes, AI) — not implemented yet
- Real congressional rosters or state lean data — seats/states use generic defaults
- Tests — add only when requested or for non-trivial logic

## Git

- Do not commit unless the user asks.
- Do not force-push to `main`.

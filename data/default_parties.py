"""Starting party defaults — edit this file to customize new games and dev mode.

Party codes: "D" (Democrat), "R" (Republican), "I" (Independent)

Used by:
  - Presidential election (STATE_LEAN)
  - Governors (STATE_LEAN)
  - Senate (SENATE — two seats per state, seat 1 then seat 2)
  - House (HOUSE — one entry per district; sourced from house.gov/representatives)
  - Supreme Court (COURT — seats 1–9 left to right on the bench)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# State lean — also used for governors and house districts unless overridden
# ---------------------------------------------------------------------------
STATE_LEAN = {
    "AL": "R", "AK": "R", "AZ": "R", "AR": "R", "CA": "D", "CO": "D", "CT": "D",
    "DE": "D", "FL": "R", "GA": "R", "HI": "D", "ID": "R", "IL": "D", "IN": "R",
    "IA": "R", "KS": "R", "KY": "R", "LA": "R", "ME": "D", "MD": "D", "MA": "D",
    "MI": "D", "MN": "D", "MS": "R", "MO": "R", "MT": "R", "NE": "R", "NV": "D",
    "NH": "D", "NJ": "D", "NM": "D", "NY": "D", "NC": "R", "ND": "R", "OH": "R",
    "OK": "R", "OR": "D", "PA": "D", "RI": "D", "SC": "R", "SD": "R", "TN": "R",
    "TX": "R", "UT": "R", "VT": "D", "VA": "D", "WA": "D", "WV": "R", "WI": "D",
    "WY": "R",
}

# ---------------------------------------------------------------------------
# Senate — (seat 1, seat 2). Omit a state to default both seats to STATE_LEAN.
# ---------------------------------------------------------------------------
SENATE = {
    "AL": ("R", "R"), "AK": ("R", "R"), "AZ": ("D", "R"), "AR": ("R", "R"),
    "CA": ("D", "D"), "CO": ("D", "D"), "CT": ("D", "D"), "DE": ("D", "D"),
    "FL": ("R", "R"), "GA": ("D", "R"), "HI": ("D", "D"), "ID": ("R", "R"),
    "IL": ("D", "D"), "IN": ("R", "R"), "IA": ("R", "R"), "KS": ("R", "R"),
    "KY": ("R", "R"), "LA": ("R", "R"), "ME": ("R", "D"), "MD": ("D", "D"),
    "MA": ("D", "D"), "MI": ("D", "D"), "MN": ("D", "D"), "MS": ("R", "R"),
    "MO": ("R", "R"), "MT": ("R", "R"), "NE": ("R", "R"), "NV": ("D", "D"),
    "NH": ("D", "D"), "NJ": ("D", "D"), "NM": ("D", "D"), "NY": ("D", "D"),
    "NC": ("R", "R"), "ND": ("R", "R"), "OH": ("D", "R"), "OK": ("R", "R"),
    "OR": ("D", "D"), "PA": ("D", "R"), "RI": ("D", "D"), "SC": ("R", "R"),
    "SD": ("R", "R"), "TN": ("R", "R"), "TX": ("R", "R"), "UT": ("R", "R"),
    "VT": ("D", "I"), "VA": ("D", "D"), "WA": ("D", "D"), "WV": ("R", "R"),
    "WI": ("D", "R"), "WY": ("R", "R"),
}

# ---------------------------------------------------------------------------
# House — one entry per district (district 1, district 2, …). 435 total.
# Sourced from https://www.house.gov/representatives (119th Congress roster).
# Re-run scripts/parse_house_representatives.py after updating the export.
# ---------------------------------------------------------------------------
HOUSE = {
    "AL": ("R", "D", "R", "R", "R", "R", "D"),
    "AK": ("R",),
    "AZ": (
        "R", "R", "D", "D", "R", "R", "D", "R",
        "R",
    ),
    "AR": ("R", "R", "R", "R"),
    "CA": (
        "R", "D", "I", "D", "R", "D", "D", "D",
        "D", "D", "D", "D", "D", "D", "D", "D",
        "D", "D", "D", "R", "D", "R", "R", "D",
        "D", "D", "D", "D", "D", "D", "D", "D",
        "D", "D", "D", "D", "D", "D", "D", "R",
        "R", "D", "D", "D", "D", "D", "D", "R",
        "D", "D", "D", "D",
    ),
    "CO": ("D", "D", "R", "R", "R", "D", "D", "R"),
    "CT": ("D", "D", "D", "D", "D"),
    "DE": ("D",),
    "FL": (
        "R", "R", "R", "R", "R", "R", "R", "R",
        "D", "D", "R", "R", "R", "D", "R", "R",
        "R", "R", "R", "D", "R", "D", "D", "D",
        "D", "R", "R", "R",
    ),
    "GA": (
        "R", "D", "R", "D", "D", "D", "R", "R",
        "R", "R", "R", "R", "D", "R",
    ),
    "HI": ("D", "D"),
    "ID": ("R", "R"),
    "IL": (
        "D", "D", "D", "D", "D", "D", "D", "D",
        "D", "D", "D", "R", "D", "D", "R", "R",
        "D",
    ),
    "IN": (
        "D", "R", "R", "R", "R", "R", "D", "R",
        "R",
    ),
    "IA": ("R", "R", "R", "R"),
    "KS": ("R", "R", "D", "R"),
    "KY": ("R", "R", "D", "R", "R", "R"),
    "LA": ("R", "D", "R", "R", "R", "D"),
    "ME": ("D", "D"),
    "MD": ("R", "D", "D", "D", "D", "D", "D", "D"),
    "MA": (
        "D", "D", "D", "D", "D", "D", "D", "D",
        "D",
    ),
    "MI": (
        "R", "R", "D", "R", "R", "D", "R", "D",
        "R", "R", "D", "D", "D",
    ),
    "MN": ("R", "D", "D", "D", "D", "R", "R", "R"),
    "MS": ("R", "D", "R", "R"),
    "MO": ("D", "R", "R", "R", "D", "R", "R", "R"),
    "MT": ("R", "R"),
    "NE": ("R", "R", "R"),
    "NV": ("D", "R", "D", "D"),
    "NH": ("D", "D"),
    "NJ": (
        "D", "R", "D", "R", "D", "D", "R", "D",
        "D", "D", "D", "D",
    ),
    "NM": ("D", "D", "D"),
    "NY": (
        "R", "R", "D", "D", "D", "D", "D", "D",
        "D", "D", "R", "D", "D", "D", "D", "D",
        "R", "D", "D", "D", "R", "D", "R", "R",
        "D", "D",
    ),
    "NC": (
        "D", "D", "R", "D", "R", "R", "R", "R",
        "R", "R", "R", "D", "R", "R",
    ),
    "ND": ("R",),
    "OH": (
        "D", "R", "D", "R", "R", "R", "R", "R",
        "D", "R", "D", "R", "D", "R", "R",
    ),
    "OK": ("R", "R", "R", "R", "R"),
    "OR": ("D", "R", "D", "D", "D", "D"),
    "PA": (
        "R", "D", "D", "D", "D", "D", "R", "R",
        "R", "R", "R", "D", "R", "R", "R", "R",
        "D",
    ),
    "RI": ("D", "D"),
    "SC": ("R", "R", "R", "R", "R", "D", "R"),
    "SD": ("R",),
    "TN": (
        "R", "R", "R", "R", "R", "R", "R", "R",
        "D",
    ),
    "TX": (
        "R", "R", "R", "R", "R", "R", "D", "R",
        "D", "R", "R", "R", "R", "R", "R", "D",
        "R", "D", "R", "D", "R", "R", "R", "R",
        "R", "R", "R", "D", "D", "D", "R", "D",
        "D", "D", "D", "R", "D", "R",
    ),
    "UT": ("R", "R", "R", "R"),
    "VT": ("D",),
    "VA": (
        "R", "R", "D", "D", "R", "R", "D", "D",
        "R", "D", "D",
    ),
    "WA": (
        "D", "D", "D", "R", "R", "D", "D", "D",
        "D", "D",
    ),
    "WV": ("R", "R"),
    "WI": ("R", "D", "R", "D", "R", "R", "R", "R"),
    "WY": ("R",),
}
# ---------------------------------------------------------------------------
# Supreme Court — seats 1–9 (bench order, left to right)
# ---------------------------------------------------------------------------
COURT = ("R", "R", "R", "R", "R", "R", "D", "D", "D")

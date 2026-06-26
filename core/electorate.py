"""Per-state electorate model, polls, and election-day vote simulation.

Tunable defaults for poll ranges live in the constants below.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import IntEnum

from core.party import Party
from core.states import STATE_POPULATION, US_STATE_ABBREVS

# --- Tunable simulation defaults ---
ELIGIBLE_VOTER_FRACTION = 0.77
EFFICACY_RANGE = (0.52, 0.72)
IND_VOTER_FRACTION = (0.02, 0.10)
OTHER_VOTER_FRACTION = (0.005, 0.02)
TWO_PARTY_DEM_SHARE = {
    Party.DEMOCRAT: 0.54,
    Party.REPUBLICAN: 0.44,
    Party.INDEPENDENT: 0.50,
}
TWO_PARTY_SHARE_SIGMA = 0.035
POLL_MARGIN_RANGE = (3.0, 6.5)
POLL_NOISE_SIGMA = 2.0

RALLY_COST = 50_000
RALLY_POLL_SHIFT = 2.5
ADS_COST = 10_000
ADS_POLL_SHIFT = 1.0


class CompetitivenessTier(IntEnum):
    SAFE_DEM = 0
    LIKELY_DEM = 1
    LEANS_DEM = 2
    TILT_DEM = 3
    TOSS_UP = 4
    TILT_REP = 5
    LEANS_REP = 6
    LIKELY_REP = 7
    SAFE_REP = 8


TIER_LABELS: dict[CompetitivenessTier, str] = {
    CompetitivenessTier.SAFE_DEM: "Safe Dem",
    CompetitivenessTier.LIKELY_DEM: "Likely Dem",
    CompetitivenessTier.LEANS_DEM: "Leans Dem",
    CompetitivenessTier.TILT_DEM: "Tilt Dem",
    CompetitivenessTier.TOSS_UP: "Toss-up",
    CompetitivenessTier.TILT_REP: "Tilt Rep",
    CompetitivenessTier.LEANS_REP: "Leans Rep",
    CompetitivenessTier.LIKELY_REP: "Likely Rep",
    CompetitivenessTier.SAFE_REP: "Safe Rep",
}

DEM_TIERS = frozenset(
    {
        CompetitivenessTier.SAFE_DEM,
        CompetitivenessTier.LIKELY_DEM,
        CompetitivenessTier.LEANS_DEM,
        CompetitivenessTier.TILT_DEM,
    }
)
REP_TIERS = frozenset(
    {
        CompetitivenessTier.SAFE_REP,
        CompetitivenessTier.LIKELY_REP,
        CompetitivenessTier.LEANS_REP,
        CompetitivenessTier.TILT_REP,
    }
)


def tier_matches_filter(tier: CompetitivenessTier, filter_key: str) -> bool:
    if filter_key == "all":
        return True
    if filter_key == "swing":
        return tier == CompetitivenessTier.TOSS_UP
    if filter_key == "dem":
        return tier in DEM_TIERS
    if filter_key == "rep":
        return tier in REP_TIERS
    return True


def tier_from_margin(leader: Party, margin: float) -> CompetitivenessTier:
    if margin < 2.0:
        return CompetitivenessTier.TOSS_UP
    if leader == Party.DEMOCRAT:
        if margin >= 10.0:
            return CompetitivenessTier.SAFE_DEM
        if margin >= 7.0:
            return CompetitivenessTier.LIKELY_DEM
        if margin >= 4.0:
            return CompetitivenessTier.LEANS_DEM
        return CompetitivenessTier.TILT_DEM
    if margin >= 10.0:
        return CompetitivenessTier.SAFE_REP
    if margin >= 7.0:
        return CompetitivenessTier.LIKELY_REP
    if margin >= 4.0:
        return CompetitivenessTier.LEANS_REP
    return CompetitivenessTier.TILT_REP


@dataclass
class StateElectorate:
    state: str
    population: int
    eligible_voters: int
    efficacy: float
    dem_voters: int
    rep_voters: int
    ind_voters: int
    other_voters: int
    poll_dem_pct: float
    poll_rep_pct: float
    poll_ind_pct: float
    poll_margin: float
    actual_turnout: float | None = None
    result_dem_votes: int | None = None
    result_rep_votes: int | None = None
    result_ind_votes: int | None = None
    result_other_votes: int | None = None

    @property
    def likely_voters(self) -> int:
        """Eligible voters expected to turn out (eligible × efficacy)."""
        return int(round(self.eligible_voters * self.efficacy))

    def affiliation_shares(self) -> dict[str, float]:
        total = max(self.eligible_voters, 1)
        return {
            "dem": self.dem_voters / total,
            "rep": self.rep_voters / total,
            "ind": self.ind_voters / total,
            "other": self.other_voters / total,
        }

    def poll_shares(self) -> dict[str, float]:
        return {
            "dem": self.poll_dem_pct,
            "rep": self.poll_rep_pct,
            "ind": self.poll_ind_pct,
        }

    def projected_winner(self) -> Party:
        if self.result_dem_votes is not None and self.result_rep_votes is not None:
            return (
                Party.DEMOCRAT
                if self.result_dem_votes >= self.result_rep_votes
                else Party.REPUBLICAN
            )
        return (
            Party.DEMOCRAT
            if self.poll_dem_pct >= self.poll_rep_pct
            else Party.REPUBLICAN
        )

    def map_color_pcts(self) -> tuple[float, float]:
        """Dem/Rep percentages used for map gradient coloring."""
        if (
            self.result_dem_votes is not None
            and self.result_rep_votes is not None
            and self.result_dem_votes + self.result_rep_votes > 0
        ):
            total = self.result_dem_votes + self.result_rep_votes
            dem = 100.0 * self.result_dem_votes / total
            rep = 100.0 * self.result_rep_votes / total
            return dem, rep
        return self.poll_dem_pct, self.poll_rep_pct

    def two_party_margin(self) -> tuple[Party, float]:
        """Leading major party and absolute two-party margin in percentage points."""
        dem, rep = self.map_color_pcts()
        leader = Party.DEMOCRAT if dem >= rep else Party.REPUBLICAN
        return leader, abs(dem - rep)

    def competitiveness_tier(self) -> CompetitivenessTier:
        leader, margin = self.two_party_margin()
        return tier_from_margin(leader, margin)

    def competitiveness_summary(self) -> str:
        return TIER_LABELS[self.competitiveness_tier()]


@dataclass
class StateElectionResult:
    party: Party
    actual_turnout: float
    dem_votes: int
    rep_votes: int
    ind_votes: int
    other_votes: int


def apply_state_election_result(
    electorate: StateElectorate, result: StateElectionResult
) -> None:
    electorate.actual_turnout = result.actual_turnout
    electorate.result_dem_votes = result.dem_votes
    electorate.result_rep_votes = result.rep_votes
    electorate.result_ind_votes = result.ind_votes
    electorate.result_other_votes = result.other_votes


def _renormalize_polls(electorate: StateElectorate) -> None:
    total = electorate.poll_dem_pct + electorate.poll_rep_pct + electorate.poll_ind_pct
    if total <= 0:
        return
    scale = 100.0 / total
    electorate.poll_dem_pct *= scale
    electorate.poll_rep_pct *= scale
    electorate.poll_ind_pct *= scale


def apply_rally(electorate: StateElectorate, player_party: Party) -> None:
    """Shift state polls toward the player's party after a campaign rally."""
    shift = RALLY_POLL_SHIFT
    if player_party == Party.DEMOCRAT:
        electorate.poll_dem_pct += shift
        electorate.poll_rep_pct = max(0.0, electorate.poll_rep_pct - shift * 0.6)
    else:
        electorate.poll_rep_pct += shift
        electorate.poll_dem_pct = max(0.0, electorate.poll_dem_pct - shift * 0.6)
    _renormalize_polls(electorate)


def apply_ads(electorate: StateElectorate, player_party: Party) -> None:
    """Smaller poll shift from TV/digital ads in a state."""
    shift = ADS_POLL_SHIFT
    if player_party == Party.DEMOCRAT:
        electorate.poll_dem_pct += shift
        electorate.poll_rep_pct = max(0.0, electorate.poll_rep_pct - shift * 0.5)
    else:
        electorate.poll_rep_pct += shift
        electorate.poll_dem_pct = max(0.0, electorate.poll_dem_pct - shift * 0.5)
    _renormalize_polls(electorate)


def _split_eligible_voters(eligible: int, lean: Party) -> tuple[int, int, int, int]:
    ind_frac = random.uniform(*IND_VOTER_FRACTION)
    other_frac = random.uniform(*OTHER_VOTER_FRACTION)
    remaining = max(0.05, 1.0 - ind_frac - other_frac)
    dem_two_party = TWO_PARTY_DEM_SHARE.get(lean, 0.5)
    dem_two_party += random.gauss(0, TWO_PARTY_SHARE_SIGMA)
    dem_two_party = max(0.25, min(0.75, dem_two_party))
    dem_frac = remaining * dem_two_party
    rep_frac = remaining * (1.0 - dem_two_party)
    ind_count = int(round(eligible * ind_frac))
    other_count = int(round(eligible * other_frac))
    dem_count = int(round(eligible * dem_frac))
    rep_count = max(0, eligible - dem_count - ind_count - other_count)
    return dem_count, rep_count, ind_count, other_count


def _intent_from_affiliation(
    dem: int, rep: int, ind: int, other: int
) -> tuple[float, float, float]:
    total = max(dem + rep + ind + other, 1)
    dem_pct = 100.0 * dem / total + random.gauss(0, POLL_NOISE_SIGMA)
    rep_pct = 100.0 * rep / total + random.gauss(0, POLL_NOISE_SIGMA)
    ind_pct = 100.0 * ind / total + random.gauss(0, POLL_NOISE_SIGMA * 0.5)
    dem_pct = max(0.0, dem_pct)
    rep_pct = max(0.0, rep_pct)
    ind_pct = max(0.0, ind_pct)
    poll_total = dem_pct + rep_pct + ind_pct
    if poll_total <= 0:
        return 33.3, 33.3, 33.4
    scale = 100.0 / poll_total
    return dem_pct * scale, rep_pct * scale, ind_pct * scale


def generate_state_electorate(state: str, lean: Party) -> StateElectorate:
    population = STATE_POPULATION[state]
    eligible = int(round(population * ELIGIBLE_VOTER_FRACTION))
    efficacy = random.uniform(*EFFICACY_RANGE)
    dem, rep, ind, other = _split_eligible_voters(eligible, lean)
    poll_dem, poll_rep, poll_ind = _intent_from_affiliation(dem, rep, ind, other)
    poll_margin = random.uniform(*POLL_MARGIN_RANGE)
    return StateElectorate(
        state=state,
        population=population,
        eligible_voters=eligible,
        efficacy=efficacy,
        dem_voters=dem,
        rep_voters=rep,
        ind_voters=ind,
        other_voters=other,
        poll_dem_pct=poll_dem,
        poll_rep_pct=poll_rep,
        poll_ind_pct=poll_ind,
        poll_margin=poll_margin,
    )


def generate_all_electorates(leans: dict[str, Party]) -> dict[str, StateElectorate]:
    return {
        state: generate_state_electorate(state, leans.get(state, Party.INDEPENDENT))
        for state in US_STATE_ABBREVS
    }


def _sample_within_margin(center: float, margin: float) -> float:
    """Bell-curve sample clamped to ±margin (MOE window)."""
    if margin <= 0:
        return center
    sigma = margin / 2.0
    for _ in range(24):
        value = random.gauss(center, sigma)
        if center - margin <= value <= center + margin:
            return value
    return max(center - margin, min(center + margin, value))


def simulate_state_election(electorate: StateElectorate) -> StateElectionResult:
    turnout_margin = electorate.efficacy * (electorate.poll_margin / 100.0)
    actual_turnout = _sample_within_margin(electorate.efficacy, turnout_margin)
    actual_turnout = max(0.35, min(0.85, actual_turnout))
    voting = int(round(electorate.eligible_voters * actual_turnout))

    margin = electorate.poll_margin
    dem_pct = _sample_within_margin(electorate.poll_dem_pct, margin)
    rep_pct = _sample_within_margin(electorate.poll_rep_pct, margin)
    ind_pct = _sample_within_margin(electorate.poll_ind_pct, margin * 0.75)
    dem_pct = max(0.0, dem_pct)
    rep_pct = max(0.0, rep_pct)
    ind_pct = max(0.0, ind_pct)
    other_pct = max(0.0, 100.0 - dem_pct - rep_pct - ind_pct)
    total_pct = dem_pct + rep_pct + ind_pct + other_pct
    if total_pct <= 0:
        dem_pct, rep_pct, ind_pct, other_pct = 45.0, 45.0, 8.0, 2.0
        total_pct = 100.0
    scale = 100.0 / total_pct
    dem_pct *= scale
    rep_pct *= scale
    ind_pct *= scale
    other_pct *= scale

    dem_votes = int(round(voting * dem_pct / 100.0))
    rep_votes = int(round(voting * rep_pct / 100.0))
    ind_votes = int(round(voting * ind_pct / 100.0))
    other_votes = max(0, voting - dem_votes - rep_votes - ind_votes)
    party = Party.DEMOCRAT if dem_votes >= rep_votes else Party.REPUBLICAN
    return StateElectionResult(
        party=party,
        actual_turnout=actual_turnout,
        dem_votes=dem_votes,
        rep_votes=rep_votes,
        ind_votes=ind_votes,
        other_votes=other_votes,
    )

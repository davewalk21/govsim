"""State-level policy opinion axes for election mode."""

from __future__ import annotations

import random
from dataclasses import dataclass

from core.party import Party
from core.states import US_STATE_ABBREVS

OPINION_SIGMA = 14.0
OPINION_MIN = 5.0
OPINION_MAX = 95.0

LEAN_CENTER = {
    Party.DEMOCRAT: 28.0,
    Party.REPUBLICAN: 72.0,
    Party.INDEPENDENT: 50.0,
}


@dataclass(frozen=True)
class PolicyDefinition:
    """One left–right issue axis (0 = left label, 100 = right label)."""

    id: str
    title: str
    left_label: str
    right_label: str


POLICIES: tuple[PolicyDefinition, ...] = (
    PolicyDefinition("immigration", "Immigration", "Pro-Immigration", "Anti-Immigration"),
    PolicyDefinition("abortion", "Abortion", "Pro-Choice", "Pro-Life"),
    PolicyDefinition("energy", "Energy & Climate", "Anti-Oil", "Pro-Oil"),
    PolicyDefinition("education", "Education", "Public", "Private"),
    PolicyDefinition("lgbt", "LGBT Rights", "Pro-LGBT", "Anti-LGBT"),
)


@dataclass
class StateOpinions:
    scores: dict[str, float]

    def score(self, policy_id: str) -> float:
        return self.scores[policy_id]


def random_opinion_score(lean: Party) -> float:
    center = LEAN_CENTER.get(lean, 50.0)
    value = random.gauss(center, OPINION_SIGMA)
    return max(OPINION_MIN, min(OPINION_MAX, value))


def generate_state_opinions(lean: Party) -> StateOpinions:
    return StateOpinions(
        scores={policy.id: random_opinion_score(lean) for policy in POLICIES}
    )


def generate_party_platform(party: Party) -> dict[str, float]:
    return {policy.id: random_opinion_score(party) for policy in POLICIES}


def generate_campaign_platforms() -> tuple[dict[str, float], dict[str, float]]:
    return generate_party_platform(Party.DEMOCRAT), generate_party_platform(Party.REPUBLICAN)


def default_player_promises() -> dict[str, float]:
    return {policy.id: 50.0 for policy in POLICIES}


def default_opponent_promises(party: Party) -> dict[str, float]:
    center = LEAN_CENTER.get(party, 50.0)
    return {policy.id: center for policy in POLICIES}


def generate_all_state_opinions(leans: dict[str, Party]) -> dict[str, StateOpinions]:
    return {
        state: generate_state_opinions(leans.get(state, Party.INDEPENDENT))
        for state in US_STATE_ABBREVS
    }

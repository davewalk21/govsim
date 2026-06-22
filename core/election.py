from __future__ import annotations

from dataclasses import dataclass, field

from core.defaults import all_state_leans
from core.electorate import StateElectorate, generate_all_electorates, simulate_state_election
from core.party import Party
from core.policies import (
    StateOpinions,
    default_opponent_promises,
    default_player_promises,
    generate_all_state_opinions,
)
from core.states import ELECTORAL_VOTES_BY_STATE, ELECTORAL_VOTES_TO_WIN

ELECTION_CAMPAIGN_DAYS = 7


@dataclass
class PresidentialElection:
    days_remaining: int = ELECTION_CAMPAIGN_DAYS
    leans: dict[str, Party] = field(default_factory=dict)
    state_opinions: dict[str, StateOpinions] = field(default_factory=dict)
    electorates: dict[str, StateElectorate] = field(default_factory=dict)
    player_party: Party = Party.DEMOCRAT
    player_promises: dict[str, float] = field(default_factory=dict)
    opponent_promises: dict[str, float] = field(default_factory=dict)
    influence: float = 100.0
    influence_max: float = 100.0
    money: float = 250.0
    money_max: float = 500.0
    results: dict[str, Party] | None = None
    winner: Party | None = None
    dem_electoral_votes: int = 0
    rep_electoral_votes: int = 0

    @classmethod
    def create_new(cls) -> PresidentialElection:
        leans = all_state_leans()
        opponent_party = Party.REPUBLICAN
        return cls(
            days_remaining=ELECTION_CAMPAIGN_DAYS,
            leans=leans,
            state_opinions=generate_all_state_opinions(leans),
            electorates=generate_all_electorates(leans),
            player_promises=default_player_promises(),
            opponent_promises=default_opponent_promises(opponent_party),
        )

    @property
    def opponent_party(self) -> Party:
        if self.player_party == Party.DEMOCRAT:
            return Party.REPUBLICAN
        if self.player_party == Party.REPUBLICAN:
            return Party.DEMOCRAT
        return Party.REPUBLICAN

    @property
    def resolved(self) -> bool:
        return self.results is not None

    def countdown_label(self) -> str:
        if self.resolved:
            return "Election complete"
        if self.days_remaining == 1:
            return "1 day until election"
        return f"{self.days_remaining} days until election"

    def display_parties_by_state(self) -> dict[str, Party]:
        if self.results is not None:
            return self.results
        return {
            state: electorate.projected_winner()
            for state, electorate in self.electorates.items()
        }

    def electoral_vote_counts(self) -> dict[Party, int]:
        counts = {party: 0 for party in Party}
        for state, party in self.display_parties_by_state().items():
            if party in (Party.DEMOCRAT, Party.REPUBLICAN):
                counts[party] += ELECTORAL_VOTES_BY_STATE[state]
        return counts

    def next_turn(self) -> None:
        if self.resolved:
            return
        if self.days_remaining > 0:
            self.days_remaining -= 1
        if self.days_remaining == 0:
            self._resolve_election()

    def _resolve_election(self) -> None:
        results: dict[str, Party] = {}
        for state, electorate in self.electorates.items():
            results[state] = simulate_state_election(electorate)

        self.results = results
        self.dem_electoral_votes = sum(
            ELECTORAL_VOTES_BY_STATE[state]
            for state, party in results.items()
            if party == Party.DEMOCRAT
        )
        self.rep_electoral_votes = sum(
            ELECTORAL_VOTES_BY_STATE[state]
            for state, party in results.items()
            if party == Party.REPUBLICAN
        )
        if self.dem_electoral_votes > self.rep_electoral_votes:
            self.winner = Party.DEMOCRAT
        elif self.rep_electoral_votes > self.dem_electoral_votes:
            self.winner = Party.REPUBLICAN
        else:
            self.winner = None

    def result_message(self) -> str:
        if not self.resolved:
            return ""
        if self.winner is None:
            return (
                f"Tie: {self.dem_electoral_votes}-{self.rep_electoral_votes} electoral votes"
            )
        name = self.winner.value.title()
        dem = self.dem_electoral_votes
        rep = self.rep_electoral_votes
        needed = ELECTORAL_VOTES_TO_WIN
        return f"{name} wins {dem}-{rep} ({needed} needed to win)"

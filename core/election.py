from __future__ import annotations

from dataclasses import dataclass, field

from core.defaults import all_state_leans
from core.electorate import (
    CompetitivenessTier,
    StateElectorate,
    StateElectionResult,
    apply_state_election_result,
    generate_all_electorates,
    simulate_state_election,
)
from core.party import Party
from core.policies import (
    StateOpinions,
    generate_all_state_opinions,
    generate_party_platform,
)
from core.states import ELECTORAL_VOTES_BY_STATE, ELECTORAL_VOTES_TO_WIN

ELECTION_CAMPAIGN_DAYS = 7
REVEAL_INTERVAL_MS = 1000


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
    revealing: bool = False
    revealed_results: dict[str, Party] = field(default_factory=dict)
    _reveal_queue: list[str] = field(default_factory=list, repr=False)
    _reveal_pending: dict[str, StateElectionResult] = field(default_factory=dict, repr=False)
    _last_reveal_ms: int = field(default=0, repr=False)

    @classmethod
    def create_new(
        cls,
        *,
        player_party: Party = Party.DEMOCRAT,
        player_promises: dict[str, float] | None = None,
        opponent_promises: dict[str, float] | None = None,
    ) -> PresidentialElection:
        leans = all_state_leans()
        opponent_party = (
            Party.REPUBLICAN if player_party == Party.DEMOCRAT else Party.DEMOCRAT
        )
        if player_promises is None:
            player_promises = generate_party_platform(player_party)
        if opponent_promises is None:
            opponent_promises = generate_party_platform(opponent_party)
        return cls(
            days_remaining=ELECTION_CAMPAIGN_DAYS,
            leans=leans,
            state_opinions=generate_all_state_opinions(leans),
            electorates=generate_all_electorates(leans),
            player_party=player_party,
            player_promises=player_promises,
            opponent_promises=opponent_promises,
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

    @property
    def on_election_day(self) -> bool:
        return self.days_remaining == 0 and not self.resolved and not self.revealing

    def button_label(self) -> str:
        if self.on_election_day:
            return "See Results"
        return "Next Turn"

    def button_enabled(self) -> bool:
        return not self.resolved and not self.revealing

    def countdown_label(self) -> str:
        if self.resolved:
            return "Election complete"
        if self.revealing:
            called = len(self.revealed_results)
            return f"Calling states… ({called}/50)"
        if self.days_remaining == 0:
            return "Election day"
        if self.days_remaining == 1:
            return "1 day until election"
        return f"{self.days_remaining} days until election"

    def revealed_winner(self, state: str) -> Party | None:
        if state in self.revealed_results:
            return self.revealed_results[state]
        if self.resolved and self.results is not None:
            return self.results.get(state)
        return None

    def display_parties_by_state(self) -> dict[str, Party]:
        if self.revealing:
            return dict(self.revealed_results)
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

    def competitiveness_electoral_votes(self) -> dict[CompetitivenessTier, int]:
        totals = {tier: 0 for tier in CompetitivenessTier}
        for state, electorate in self.electorates.items():
            totals[electorate.competitiveness_tier()] += ELECTORAL_VOTES_BY_STATE[state]
        return totals

    def reveal_called_winner(self) -> Party | None:
        """Party that has reached the electoral-vote threshold from states called so far."""
        counts = self.electoral_vote_counts()
        if counts[Party.DEMOCRAT] >= ELECTORAL_VOTES_TO_WIN:
            return Party.DEMOCRAT
        if counts[Party.REPUBLICAN] >= ELECTORAL_VOTES_TO_WIN:
            return Party.REPUBLICAN
        return None

    def player_outcome_message(self) -> str | None:
        if not self.resolved:
            return None
        if self.winner is None:
            return "Tie — no winner declared."
        if self.winner == self.player_party:
            return "Welcome to the White House!"
        return "You Lose. Better luck next time."

    def next_turn(self) -> None:
        if not self.button_enabled() or self.days_remaining <= 0:
            return
        self.days_remaining -= 1

    def start_reveal(self) -> None:
        if not self.on_election_day:
            return
        order = sorted(
            self.electorates.keys(),
            key=lambda state: abs(
                self.electorates[state].poll_dem_pct - self.electorates[state].poll_rep_pct
            ),
            reverse=True,
        )
        self._reveal_pending = {
            state: simulate_state_election(self.electorates[state])
            for state in self.electorates
        }
        self._reveal_queue = order
        self.revealed_results = {}
        self.revealing = True
        self._last_reveal_ms = 0

    def tick_reveal(self, now_ms: int) -> bool:
        if not self.revealing:
            return False
        if self._last_reveal_ms == 0:
            self._last_reveal_ms = now_ms
            return False
        if now_ms - self._last_reveal_ms < REVEAL_INTERVAL_MS:
            return False
        if not self._reveal_queue:
            return False
        state = self._reveal_queue.pop(0)
        result = self._reveal_pending[state]
        apply_state_election_result(self.electorates[state], result)
        self.revealed_results[state] = result.party
        self._last_reveal_ms = now_ms
        if not self._reveal_queue:
            self._finish_reveal()
        return True

    def _finish_reveal(self) -> None:
        self.results = {state: result.party for state, result in self._reveal_pending.items()}
        self.revealing = False
        self.dem_electoral_votes = sum(
            ELECTORAL_VOTES_BY_STATE[state]
            for state, party in self.results.items()
            if party == Party.DEMOCRAT
        )
        self.rep_electoral_votes = sum(
            ELECTORAL_VOTES_BY_STATE[state]
            for state, party in self.results.items()
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

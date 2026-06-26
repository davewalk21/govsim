from __future__ import annotations

import random
from dataclasses import dataclass, field

from core.defaults import all_state_leans
from core.electorate import (
    CompetitivenessTier,
    ADS_COST,
    RALLY_COST,
    StateElectorate,
    StateElectionResult,
    apply_ads,
    apply_rally,
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
STARTING_MONEY_RANGE = (120_000, 420_000)
STARTING_INFLUENCE_RANGE = (50.0, 95.0)
STARTING_INFLUENCE_MAX = 100.0


def generate_starting_resources() -> tuple[float, float, float, float]:
    money = round(random.uniform(*STARTING_MONEY_RANGE) / 1000) * 1000
    influence = round(random.uniform(*STARTING_INFLUENCE_RANGE), 1)
    influence_max = STARTING_INFLUENCE_MAX
    money_max = max(money * 1.25, 500_000)
    return influence, influence_max, money, money_max


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
    money: float = 250_000.0
    money_max: float = 500_000.0
    scheduled_rally_state: str | None = None
    scheduled_ad_states: list[str] = field(default_factory=list)
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
        influence: float | None = None,
        influence_max: float | None = None,
        money: float | None = None,
        money_max: float | None = None,
    ) -> PresidentialElection:
        leans = all_state_leans()
        opponent_party = (
            Party.REPUBLICAN if player_party == Party.DEMOCRAT else Party.DEMOCRAT
        )
        if player_promises is None:
            player_promises = generate_party_platform(player_party)
        if opponent_promises is None:
            opponent_promises = generate_party_platform(opponent_party)
        rolled_inf, rolled_inf_max, rolled_money, rolled_money_max = generate_starting_resources()
        if influence is None:
            influence = rolled_inf
        if influence_max is None:
            influence_max = rolled_inf_max
        if money is None:
            money = rolled_money
        if money_max is None:
            money_max = rolled_money_max
        return cls(
            days_remaining=ELECTION_CAMPAIGN_DAYS,
            leans=leans,
            state_opinions=generate_all_state_opinions(leans),
            electorates=generate_all_electorates(leans),
            player_party=player_party,
            player_promises=player_promises,
            opponent_promises=opponent_promises,
            influence=influence,
            influence_max=influence_max,
            money=money,
            money_max=money_max,
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

    def ad_cost_total(self) -> float:
        return len(self.scheduled_ad_states) * ADS_COST

    def campaign_commitment_cost(self) -> float:
        total = self.ad_cost_total()
        if self.scheduled_rally_state:
            total += RALLY_COST
        return total

    def _campaign_active(self) -> bool:
        return (
            not self.resolved
            and not self.revealing
            and self.days_remaining > 0
        )

    def can_schedule_rally(self) -> bool:
        if not self._campaign_active():
            return False
        if self.scheduled_rally_state:
            return True
        return self.money >= RALLY_COST + self.ad_cost_total()

    def schedule_rally(self, state: str) -> bool:
        if state not in self.electorates or not self.can_schedule_rally():
            return False
        self.scheduled_rally_state = state
        return True

    def clear_scheduled_rally(self) -> None:
        self.scheduled_rally_state = None

    def can_enter_ads_mode(self) -> bool:
        if not self._campaign_active():
            return False
        if self.scheduled_ad_states:
            return True
        rally_reserve = RALLY_COST if self.scheduled_rally_state else 0
        return self.money >= rally_reserve + ADS_COST

    def can_add_ad_state(self) -> bool:
        rally_reserve = RALLY_COST if self.scheduled_rally_state else 0
        return self.money >= rally_reserve + self.ad_cost_total() + ADS_COST

    def select_ad_state(self, state: str, *, multi: bool) -> None:
        if state not in self.electorates:
            return
        if multi:
            if state in self.scheduled_ad_states:
                self.scheduled_ad_states.remove(state)
            elif self.can_add_ad_state():
                self.scheduled_ad_states.append(state)
            return
        if self.scheduled_ad_states == [state]:
            self.scheduled_ad_states = []
            return
        rally_reserve = RALLY_COST if self.scheduled_rally_state else 0
        if self.money >= rally_reserve + ADS_COST:
            self.scheduled_ad_states = [state]

    def clear_scheduled_ads(self) -> None:
        self.scheduled_ad_states = []

    def next_turn(self) -> None:
        if not self.button_enabled() or self.days_remaining <= 0:
            return
        self._resolve_campaign_actions()
        self.days_remaining -= 1

    def _resolve_campaign_actions(self) -> None:
        self._resolve_scheduled_rally()
        self._resolve_scheduled_ads()

    def _resolve_scheduled_rally(self) -> None:
        state = self.scheduled_rally_state
        self.scheduled_rally_state = None
        if not state or state not in self.electorates:
            return
        if self.money < RALLY_COST:
            return
        self.money -= RALLY_COST
        apply_rally(self.electorates[state], self.player_party)

    def _resolve_scheduled_ads(self) -> None:
        states = list(self.scheduled_ad_states)
        self.scheduled_ad_states = []
        for state in states:
            if state not in self.electorates or self.money < ADS_COST:
                continue
            self.money -= ADS_COST
            apply_ads(self.electorates[state], self.player_party)

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

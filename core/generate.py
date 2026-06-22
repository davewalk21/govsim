from __future__ import annotations

import random
from typing import Sequence, TypeVar

from core.names import random_name
from core.party import Party
from core.traits import (
    GOVERNMENT_VALUES,
    POLICY_VALUES,
    Gender,
    GovernmentValue,
    PolicyValue,
)

T = TypeVar("T")

FEMALE_PROBABILITY = 0.25
AGE_MEDIAN = 60
AGE_SIGMA = 10.0
AGE_MIN = 35
AGE_MAX = 90
SCALE_CENTER_INDEX = 2
SCALE_SIGMA = 0.85

DEMOCRAT_POLICY_VALUES = (
    PolicyValue.LEFTIST,
    PolicyValue.LIBERAL,
    PolicyValue.MODERATE,
)

REPUBLICAN_POLICY_VALUES = (
    PolicyValue.MODERATE,
    PolicyValue.CONSERVATIVE,
    PolicyValue.REACTIONARY,
)


def random_gender() -> Gender:
    return Gender.FEMALE if random.random() < FEMALE_PROBABILITY else Gender.MALE


def random_age() -> int:
    return int(round(max(AGE_MIN, min(AGE_MAX, random.gauss(AGE_MEDIAN, AGE_SIGMA)))))


def _random_bell_choice(options: Sequence[T], center_index: int = SCALE_CENTER_INDEX) -> T:
    index = int(round(random.gauss(center_index, SCALE_SIGMA)))
    index = max(0, min(len(options) - 1, index))
    return options[index]


def _random_half_bell(options: Sequence[T], peak_index: int) -> T:
    """Bell curve truncated to one side, peaking at peak_index."""
    index = int(round(random.gauss(peak_index, SCALE_SIGMA)))
    index = max(0, min(len(options) - 1, index))
    return options[index]


def random_policy_value_for_party(party: Party) -> PolicyValue:
    if party == Party.DEMOCRAT:
        return _random_half_bell(DEMOCRAT_POLICY_VALUES, peak_index=2)
    if party == Party.REPUBLICAN:
        return _random_half_bell(REPUBLICAN_POLICY_VALUES, peak_index=0)
    return _random_bell_choice(POLICY_VALUES)


def random_government_value() -> GovernmentValue:
    return _random_bell_choice(GOVERNMENT_VALUES)


def random_politician_identity(party: Party) -> dict[str, object]:
    gender = random_gender()
    return {
        "gender": gender,
        "name": random_name(gender),
        "age": random_age(),
        "policy": random_policy_value_for_party(party),
        "government": random_government_value(),
    }

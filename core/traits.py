from __future__ import annotations

from enum import Enum


class Gender(Enum):
    MALE = "M"
    FEMALE = "F"


class PolicyValue(Enum):
    LEFTIST = "leftist"
    LIBERAL = "liberal"
    MODERATE = "moderate"
    CONSERVATIVE = "conservative"
    REACTIONARY = "reactionary"


class GovernmentValue(Enum):
    TOTALITARIAN = "totalitarian"
    AUTHORITARIAN = "authoritarian"
    MODERATE = "moderate"
    LIBERTARIAN = "libertarian"
    ANARCHIST = "anarchist"


POLICY_VALUES = (
    PolicyValue.LEFTIST,
    PolicyValue.LIBERAL,
    PolicyValue.MODERATE,
    PolicyValue.CONSERVATIVE,
    PolicyValue.REACTIONARY,
)

GOVERNMENT_VALUES = (
    GovernmentValue.TOTALITARIAN,
    GovernmentValue.AUTHORITARIAN,
    GovernmentValue.MODERATE,
    GovernmentValue.LIBERTARIAN,
    GovernmentValue.ANARCHIST,
)

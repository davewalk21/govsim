from __future__ import annotations

from dataclasses import dataclass

import pygame

from core.party import (
    BACKGROUND_COLOR,
    NO_DELEGATION_COLOR,
    PARTY_COLORS,
    SPLIT_STATE_COLOR,
    Party,
    color_for_senate_delegation,
    cycle_senate_delegation,
)
from core.rosters import Roster
from views.geo import (
    load_projected_districts,
    load_projected_states,
    load_projected_territories,
    map_viewport_for_screen,
    point_in_polygon,
)
from views.party_bar import draw_party_bar, party_bar_rect

PARTY_LEGEND_ENTRIES = (
    (PARTY_COLORS[Party.DEMOCRAT], "Democrat"),
    (PARTY_COLORS[Party.REPUBLICAN], "Republican"),
    (PARTY_COLORS[Party.INDEPENDENT], "Independent"),
)


def _draw_map_legend(
    surface: pygame.Surface,
    font: pygame.font.Font,
    screen_size: tuple[int, int],
    extra_entries: tuple[tuple[pygame.Color, str], ...] = (),
) -> None:
    x, y = screen_size[0] - 170, 16
    for color, label in (*PARTY_LEGEND_ENTRIES, *extra_entries):
        pygame.draw.circle(surface, color, (x, y + 8), 8)
        text = font.render(label, True, (220, 220, 225))
        surface.blit(text, (x + 16, y))
        y += 24


@dataclass
class StateRegion:
    name: str
    abbreviation: str
    governor_id: str | None
    polygons: list[list[tuple[float, float]]]
    label_point: tuple[int, int] | None = None

    def contains(self, point: tuple[int, int]) -> bool:
        return any(point_in_polygon(point, polygon) for polygon in self.polygons)


class GovernorMapView:
    def __init__(self, screen_size: tuple[int, int], governors: Roster) -> None:
        self.screen_size = screen_size
        self.governors = governors
        self.font = pygame.font.SysFont(None, 22)
        self.label_font = pygame.font.SysFont(None, 16)
        self.title_font = pygame.font.SysFont(None, 36)
        self.bar_rect = party_bar_rect(screen_size[0])
        self.states = self._load_governor_states()

    def _load_governor_states(self) -> list[StateRegion]:
        viewport = map_viewport_for_screen(self.screen_size)
        regions: list[StateRegion] = []
        for projected in load_projected_states(viewport):
            governor = self.governors.governor_for_state(projected.abbreviation)
            regions.append(
                StateRegion(
                    name=projected.name,
                    abbreviation=projected.abbreviation,
                    governor_id=governor.id if governor else None,
                    polygons=projected.polygons,
                    label_point=projected.label_point,
                )
            )
        return regions

    def _party_for_state(self, state: StateRegion) -> Party:
        if state.governor_id is None:
            return Party.INDEPENDENT
        return self.governors.get(state.governor_id).party

    def party_counts(self) -> dict[Party, int]:
        return self.governors.party_counts()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        for state in reversed(self.states):
            if state.contains(event.pos):
                if state.governor_id is not None:
                    self.governors.cycle_member(state.governor_id)
                break

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND_COLOR)
        width, height = self.screen_size

        title = self.title_font.render("Governors Map", True, (230, 230, 235))
        surface.blit(title, title.get_rect(midtop=(width // 2, 12)))

        draw_party_bar(surface, self.bar_rect, self.party_counts(), self.font)

        hint = self.font.render(
            "Click a state to cycle blue → red → yellow", True, (150, 155, 170)
        )
        surface.blit(hint, (24, height - 28))

        for state in self.states:
            party = self._party_for_state(state)
            for polygon in state.polygons:
                pygame.draw.polygon(surface, PARTY_COLORS[party], polygon)
                pygame.draw.polygon(surface, (70, 75, 90), polygon, 1)

            label_center = state.label_point
            if label_center:
                label_text = state.abbreviation or state.name[:2]
                label = self.label_font.render(label_text, True, (235, 235, 240))
                surface.blit(label, label.get_rect(center=label_center))

        self._draw_legend(surface)

    def _draw_legend(self, surface: pygame.Surface) -> None:
        _draw_map_legend(surface, self.font, self.screen_size)


class SenateMapView:
    """State map colored by each state's two senators. Purple = split delegation."""

    def __init__(self, screen_size: tuple[int, int], senate: Roster) -> None:
        self.screen_size = screen_size
        self.senate = senate
        self.font = pygame.font.SysFont(None, 22)
        self.label_font = pygame.font.SysFont(None, 16)
        self.title_font = pygame.font.SysFont(None, 36)
        self.bar_rect = party_bar_rect(screen_size[0])
        viewport = map_viewport_for_screen(screen_size)
        self.states = load_projected_states(viewport)

    def party_counts(self) -> dict[Party, int]:
        return self.senate.party_counts()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        for state in reversed(self.states):
            if not _state_contains(state, event.pos):
                continue
            senators = self.senate.senators_for_state(state.abbreviation)
            if not senators:
                return
            cycle_senate_delegation(senators)
            return

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND_COLOR)
        width, height = self.screen_size

        title = self.title_font.render("Senate Map", True, (230, 230, 235))
        surface.blit(title, title.get_rect(midtop=(width // 2, 12)))

        draw_party_bar(surface, self.bar_rect, self.party_counts(), self.font)

        hint = self.font.render(
            "Click a state to cycle its senators R → split → D → split → R",
            True,
            (150, 155, 170),
        )
        surface.blit(hint, (24, height - 28))

        for state in self.states:
            senators = self.senate.senators_for_state(state.abbreviation)
            fill_color = color_for_senate_delegation([member.party for member in senators])
            for polygon in state.polygons:
                pygame.draw.polygon(surface, fill_color, polygon)
                pygame.draw.polygon(surface, (70, 75, 90), polygon, 1)

            if state.label_point and state.abbreviation:
                label = self.label_font.render(state.abbreviation, True, (235, 235, 240))
                surface.blit(label, label.get_rect(center=state.label_point))

        self._draw_legend(surface)

    def _draw_legend(self, surface: pygame.Surface) -> None:
        _draw_map_legend(
            surface,
            self.font,
            self.screen_size,
            ((SPLIT_STATE_COLOR, "Split"),),
        )


class HouseMapView:
    """Congressional district map — one polygon per seat, colored by representative."""

    def __init__(self, screen_size: tuple[int, int], house: Roster) -> None:
        self.screen_size = screen_size
        self.house = house
        self.font = pygame.font.SysFont(None, 22)
        self.label_font = pygame.font.SysFont(None, 18)
        self.title_font = pygame.font.SysFont(None, 36)
        self.bar_rect = party_bar_rect(screen_size[0])
        self.districts = self._load_districts()
        viewport = map_viewport_for_screen(screen_size)
        self.territories = load_projected_territories(viewport, {"Puerto Rico"})

    def _load_districts(self):
        viewport = map_viewport_for_screen(self.screen_size)
        politician_ids = {
            (member.state, member.district): member.id
            for member in self.house.members
            if member.state is not None and member.district is not None
        }
        return load_projected_districts(viewport, politician_ids)

    def party_counts(self) -> dict[Party, int]:
        return self.house.party_counts()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        for district in reversed(self.districts):
            if district.contains(event.pos):
                self.house.cycle_member(district.politician_id)
                break

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND_COLOR)
        width, height = self.screen_size

        title = self.title_font.render("House Map", True, (230, 230, 235))
        surface.blit(title, title.get_rect(midtop=(width // 2, 12)))

        draw_party_bar(surface, self.bar_rect, self.party_counts(), self.font)

        hint = self.font.render(
            "Click a district to cycle blue → red → yellow", True, (150, 155, 170)
        )
        surface.blit(hint, (24, height - 28))

        for territory in self.territories:
            for polygon in territory.polygons:
                pygame.draw.polygon(surface, NO_DELEGATION_COLOR, polygon)
                pygame.draw.polygon(surface, (45, 48, 58), polygon, 1)
            if territory.label_point:
                label = self.label_font.render(
                    territory.abbreviation, True, (235, 235, 240)
                )
                surface.blit(label, label.get_rect(center=territory.label_point))

        for district in self.districts:
            politician = self.house.get(district.politician_id)
            color = PARTY_COLORS[politician.party]
            for polygon in district.polygons:
                pygame.draw.polygon(surface, color, polygon)
                pygame.draw.polygon(surface, (45, 48, 58), polygon, 1)

        self._draw_legend(surface)

    def _draw_legend(self, surface: pygame.Surface) -> None:
        _draw_map_legend(surface, self.font, self.screen_size)


def _state_contains(state, point: tuple[int, int]) -> bool:
    return any(point_in_polygon(point, polygon) for polygon in state.polygons)

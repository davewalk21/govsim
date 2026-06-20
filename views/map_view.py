from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

import pygame

from core.party import (
    BACKGROUND_COLOR,
    PARTY_COLORS,
    SPLIT_STATE_COLOR,
    Party,
    color_for_senate_delegation,
    color_for_weighted_parties,
    swap_major_party,
)
from core.rosters import Roster
from core.states import STATE_ABBREV_TO_NAME
from views.party_bar import draw_party_bar, party_bar_rect

GEOJSON_PATH = Path(__file__).resolve().parent.parent / "data" / "us_states.json"

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
class ProjectedState:
    name: str
    abbreviation: str
    polygons: list[list[tuple[float, float]]]

    def contains(self, point: tuple[int, int]) -> bool:
        return any(_point_in_polygon(point, polygon) for polygon in self.polygons)


@dataclass
class StateRegion:
    name: str
    abbreviation: str
    governor_id: str | None
    polygons: list[list[tuple[float, float]]]

    def contains(self, point: tuple[int, int]) -> bool:
        return any(_point_in_polygon(point, polygon) for polygon in self.polygons)


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
        regions: list[StateRegion] = []
        for projected in load_projected_states(self.screen_size):
            governor = self.governors.governor_for_state(projected.abbreviation)
            regions.append(
                StateRegion(
                    name=projected.name,
                    abbreviation=projected.abbreviation,
                    governor_id=governor.id if governor else None,
                    polygons=projected.polygons,
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

            centroid = _polygon_centroid(state.polygons[0])
            if centroid:
                if state.governor_id is not None:
                    label_text = self.governors.get(state.governor_id).title
                else:
                    label_text = state.abbreviation or state.name[:2]
                label = self.label_font.render(label_text, True, (235, 235, 240))
                surface.blit(label, label.get_rect(center=centroid))

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
        self.states = load_projected_states(screen_size)

    def party_counts(self) -> dict[Party, int]:
        return self.senate.party_counts()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        for state in reversed(self.states):
            if not state.contains(event.pos):
                continue
            senators = self.senate.senators_for_state(state.abbreviation)
            if not senators:
                return
            senator = random.choice(senators)
            senator.party = swap_major_party(senator.party)
            return

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND_COLOR)
        width, height = self.screen_size

        title = self.title_font.render("Senate Map", True, (230, 230, 235))
        surface.blit(title, title.get_rect(midtop=(width // 2, 12)))

        draw_party_bar(surface, self.bar_rect, self.party_counts(), self.font)

        hint = self.font.render(
            "Click a state to randomly flip one of its senators blue ↔ red",
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

            centroid = _polygon_centroid(state.polygons[0])
            if centroid and state.abbreviation:
                label = self.label_font.render(state.abbreviation, True, (235, 235, 240))
                surface.blit(label, label.get_rect(center=centroid))

        self._draw_legend(surface)

    def _draw_legend(self, surface: pygame.Surface) -> None:
        _draw_map_legend(
            surface,
            self.font,
            self.screen_size,
            ((SPLIT_STATE_COLOR, "Split"),),
        )


class HouseMapView:
    """State map colored by each state's House delegation (weighted party blend)."""

    def __init__(self, screen_size: tuple[int, int], house: Roster) -> None:
        self.screen_size = screen_size
        self.house = house
        self.font = pygame.font.SysFont(None, 22)
        self.label_font = pygame.font.SysFont(None, 16)
        self.title_font = pygame.font.SysFont(None, 36)
        self.bar_rect = party_bar_rect(screen_size[0])
        self.states = load_projected_states(screen_size)

    def party_counts(self) -> dict[Party, int]:
        return self.house.party_counts()

    def handle_event(self, event: pygame.event.Event) -> None:
        return

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND_COLOR)
        width, height = self.screen_size

        title = self.title_font.render("House Map", True, (230, 230, 235))
        surface.blit(title, title.get_rect(midtop=(width // 2, 12)))

        draw_party_bar(surface, self.bar_rect, self.party_counts(), self.font)

        for state in self.states:
            representatives = self.house.representatives_for_state(state.abbreviation)
            fill_color = color_for_weighted_parties(
                [member.party for member in representatives]
            )
            for polygon in state.polygons:
                pygame.draw.polygon(surface, fill_color, polygon)
                pygame.draw.polygon(surface, (70, 75, 90), polygon, 1)

            centroid = _polygon_centroid(state.polygons[0])
            if centroid and state.abbreviation:
                label = self.label_font.render(state.abbreviation, True, (235, 235, 240))
                surface.blit(label, label.get_rect(center=centroid))

        self._draw_legend(surface)

    def _draw_legend(self, surface: pygame.Surface) -> None:
        _draw_map_legend(
            surface,
            self.font,
            self.screen_size,
            ((SPLIT_STATE_COLOR, "Mixed"),),
        )


def load_projected_states(screen_size: tuple[int, int]) -> list[ProjectedState]:
    with GEOJSON_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)

    width, height = screen_size
    mainland = pygame.Rect(40, 145, width - 80, height - 205)
    alaska = pygame.Rect(50, height - 170, 130, 90)
    hawaii = pygame.Rect(200, height - 120, 100, 60)

    states: list[ProjectedState] = []
    for feature in data["features"]:
        name = feature["properties"]["name"]
        abbreviation = _state_abbrev(name)
        geometry = feature["geometry"]
        raw_polygons = _extract_polygons(geometry)
        projected_polygons: list[list[tuple[float, float]]] = []

        for polygon in raw_polygons:
            projected = []
            for lon, lat in polygon:
                if name == "Alaska":
                    point = _project(lon, lat, alaska, (-180.0, -129.0, 51.0, 72.0))
                elif name == "Hawaii":
                    point = _project(lon, lat, hawaii, (-161.0, -154.0, 18.5, 22.5))
                else:
                    point = _project(lon, lat, mainland, (-125.0, -66.0, 24.0, 50.0))
                projected.append(point)
            if len(projected) >= 3:
                projected_polygons.append(projected)

        if projected_polygons:
            states.append(
                ProjectedState(
                    name=name,
                    abbreviation=abbreviation,
                    polygons=projected_polygons,
                )
            )
    return states


def _extract_polygons(geometry: dict) -> list[list[tuple[float, float]]]:
    geo_type = geometry["type"]
    if geo_type == "Polygon":
        return [geometry["coordinates"][0]]
    if geo_type == "MultiPolygon":
        return [ring[0] for ring in geometry["coordinates"]]
    return []


def _project(
    lon: float,
    lat: float,
    rect: pygame.Rect,
    bounds: tuple[float, float, float, float],
) -> tuple[float, float]:
    lon_min, lon_max, lat_min, lat_max = bounds
    x = rect.left + (lon - lon_min) / (lon_max - lon_min) * rect.width
    y = rect.top + (lat_max - lat) / (lat_max - lat_min) * rect.height
    return (x, y)


def _polygon_centroid(points: list[tuple[float, float]]) -> tuple[int, int] | None:
    if not points:
        return None
    x = sum(point[0] for point in points) / len(points)
    y = sum(point[1] for point in points) / len(points)
    return (int(x), int(y))


def _point_in_polygon(point: tuple[int, int], polygon: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    previous = polygon[-1]
    for current in polygon:
        xi, yi = previous
        xj, yj = current
        intersects = (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi
        if intersects:
            inside = not inside
        previous = current
    return inside


def _state_abbrev(name: str) -> str:
    for abbrev, full_name in STATE_ABBREV_TO_NAME.items():
        if full_name == name:
            return abbrev
    return ""

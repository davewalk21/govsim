from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pygame

from core.party import (
    BACKGROUND_COLOR,
    PARTY_COLORS,
    Party,
    apply_half_split,
    count_parties,
    cycle_party,
)
from views.party_bar import draw_party_bar


@dataclass
class StateRegion:
    name: str
    abbreviation: str
    party: Party
    polygons: list[list[tuple[float, float]]]

    def contains(self, point: tuple[int, int]) -> bool:
        return any(_point_in_polygon(point, polygon) for polygon in self.polygons)


class MapView:
    GEOJSON_PATH = Path(__file__).resolve().parent.parent / "data" / "us_states.json"

    def __init__(self, screen_size: tuple[int, int]) -> None:
        self.screen_size = screen_size
        self.font = pygame.font.SysFont(None, 22)
        self.title_font = pygame.font.SysFont(None, 36)
        self.bar_rect = pygame.Rect(250, 98, screen_size[0] - 430, 32)
        self.states = self._load_states()
        apply_half_split(self.states, lambda state, party: setattr(state, "party", party))

    def _load_states(self) -> list[StateRegion]:
        with self.GEOJSON_PATH.open(encoding="utf-8") as handle:
            data = json.load(handle)

        width, height = self.screen_size
        mainland = pygame.Rect(40, 145, width - 80, height - 205)
        alaska = pygame.Rect(50, height - 170, 130, 90)
        hawaii = pygame.Rect(200, height - 120, 100, 60)

        states: list[StateRegion] = []
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
                        point = _project(
                            lon, lat, mainland, (-125.0, -66.0, 24.0, 50.0)
                        )
                    projected.append(point)
                if len(projected) >= 3:
                    projected_polygons.append(projected)

            if projected_polygons:
                states.append(
                    StateRegion(
                        name=name,
                        abbreviation=abbreviation,
                        party=Party.DEMOCRAT,
                        polygons=projected_polygons,
                    )
                )
        return states

    def party_counts(self) -> dict[Party, int]:
        return count_parties(self.states, lambda state: state.party)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        for state in reversed(self.states):
            if state.contains(event.pos):
                state.party = cycle_party(state.party)
                break

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND_COLOR)
        width, height = self.screen_size

        title = self.title_font.render("United States Map", True, (230, 230, 235))
        surface.blit(title, title.get_rect(midtop=(width // 2, 12)))

        draw_party_bar(surface, self.bar_rect, self.party_counts(), self.font)

        hint = self.font.render(
            "Click a state to cycle blue → red → yellow", True, (150, 155, 170)
        )
        surface.blit(hint, (24, height - 28))

        for state in self.states:
            for polygon in state.polygons:
                pygame.draw.polygon(surface, PARTY_COLORS[state.party], polygon)
                pygame.draw.polygon(surface, (70, 75, 90), polygon, 1)

            centroid = _polygon_centroid(state.polygons[0])
            if centroid and state.abbreviation:
                label = self.font.render(state.abbreviation, True, (235, 235, 240))
                surface.blit(label, label.get_rect(center=centroid))

        self._draw_legend(surface)

    def _draw_legend(self, surface: pygame.Surface) -> None:
        x, y = self.screen_size[0] - 170, 16
        for party in (Party.DEMOCRAT, Party.REPUBLICAN, Party.INDEPENDENT):
            pygame.draw.circle(surface, PARTY_COLORS[party], (x, y + 8), 8)
            text = self.font.render(party.value.title(), True, (220, 220, 225))
            surface.blit(text, (x + 16, y))
            y += 24


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
    mapping = {
        "Alabama": "AL",
        "Alaska": "AK",
        "Arizona": "AZ",
        "Arkansas": "AR",
        "California": "CA",
        "Colorado": "CO",
        "Connecticut": "CT",
        "Delaware": "DE",
        "District of Columbia": "DC",
        "Florida": "FL",
        "Georgia": "GA",
        "Hawaii": "HI",
        "Idaho": "ID",
        "Illinois": "IL",
        "Indiana": "IN",
        "Iowa": "IA",
        "Kansas": "KS",
        "Kentucky": "KY",
        "Louisiana": "LA",
        "Maine": "ME",
        "Maryland": "MD",
        "Massachusetts": "MA",
        "Michigan": "MI",
        "Minnesota": "MN",
        "Mississippi": "MS",
        "Missouri": "MO",
        "Montana": "MT",
        "Nebraska": "NE",
        "Nevada": "NV",
        "New Hampshire": "NH",
        "New Jersey": "NJ",
        "New Mexico": "NM",
        "New York": "NY",
        "North Carolina": "NC",
        "North Dakota": "ND",
        "Ohio": "OH",
        "Oklahoma": "OK",
        "Oregon": "OR",
        "Pennsylvania": "PA",
        "Rhode Island": "RI",
        "South Carolina": "SC",
        "South Dakota": "SD",
        "Tennessee": "TN",
        "Texas": "TX",
        "Utah": "UT",
        "Vermont": "VT",
        "Virginia": "VA",
        "Washington": "WA",
        "West Virginia": "WV",
        "Wisconsin": "WI",
        "Wyoming": "WY",
    }
    return mapping.get(name, "")

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import pygame

from core.states import STATE_ABBREV_TO_NAME, STATE_FIPS_TO_ABBREV
from views.albers_usa import (
    ALASKA,
    HAWAII,
    PUERTO_RICO_INSET,
    USA_COMPOSITE,
    USA_CONTINENTAL,
    prepare_coordinates,
)

from views.layout import PARTY_BAR_Y

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAP_TOP = PARTY_BAR_Y + 52
STATES_GEOJSON_PATH = DATA_DIR / "us_states.json"
DISTRICTS_GEOJSON_PATH = DATA_DIR / "us_cd118.geojson"

# Split rings only when consecutive projected points jump across the map (dateline artifacts).
MAX_RING_SEGMENT = 400.0
# Drop tiny polygon fragments far from a feature's main landmass.
FRAGMENT_MAX_DISTANCE = 130.0


@dataclass
class MapViewport:
    """Scale Albers composite coordinates into a pygame map rectangle."""

    left: float
    top: float
    scale: float

    def project_point(self, longitude: float, latitude: float) -> tuple[float, float]:
        x, y = USA_COMPOSITE.project_lon_lat(longitude, latitude)
        return (
            self.left + x * self.scale,
            self.top + y * self.scale,
        )

    def project_ring(
        self, ring: list[tuple[float, float]]
    ) -> list[list[tuple[float, float]]]:
        composite_points: list[tuple[float, float]] = []
        for lon, lat in ring:
            if _should_skip_coordinate(lon, lat):
                composite_points = _append_with_gap_split(composite_points, None)
                continue
            lon, lat = prepare_coordinates(lon, lat)
            if lon > 1000:
                composite_points = _append_with_gap_split(composite_points, None)
                continue
            x, y = USA_COMPOSITE.project_lon_lat(lon, lat)
            if _is_failed_projection(lon, lat, x, y):
                composite_points = _append_with_gap_split(composite_points, None)
                continue
            composite_points = _append_with_gap_split(composite_points, (x, y))

        rings: list[list[tuple[float, float]]] = []
        current: list[tuple[float, float]] = []
        for point in composite_points:
            if point is None:
                if len(current) >= 3:
                    rings.append(self._scale_ring(current))
                current = []
                continue
            current.append(point)
        if len(current) >= 3:
            rings.append(self._scale_ring(current))
        return rings

    def _scale_ring(self, ring: list[tuple[float, float]]) -> list[tuple[float, float]]:
        return [
            (self.left + x * self.scale, self.top + y * self.scale)
            for x, y in ring
        ]


@dataclass
class ProjectedState:
    name: str
    abbreviation: str
    polygons: list[list[tuple[float, float]]]
    label_point: tuple[int, int] | None = None

    def contains(self, point: tuple[int, int]) -> bool:
        return any(point_in_polygon(point, polygon) for polygon in self.polygons)


@dataclass
class ProjectedDistrict:
    state: str
    district: int
    politician_id: str
    polygons: list[list[tuple[float, float]]]

    def contains(self, point: tuple[int, int]) -> bool:
        return any(point_in_polygon(point, polygon) for polygon in self.polygons)


def map_viewport_for_screen(screen_size: tuple[int, int]) -> MapViewport:
    width, height = screen_size
    map_rect = pygame.Rect(40, MAP_TOP, width - 80, height - MAP_TOP - 48)
    return _viewport_for_composite_bounds(map_rect, _composite_extent())


def map_viewport_for_state_detail(
    state_abbrev: str, screen_size: tuple[int, int], *, panel_width: int = 380
) -> tuple[MapViewport, pygame.Rect]:
    """Fit a single state into the left portion of the screen."""
    width, height = screen_size
    map_rect = pygame.Rect(
        24,
        MAP_TOP,
        width - panel_width - 48,
        height - MAP_TOP - 40,
    )
    bounds = composite_bounds_for_state(state_abbrev)
    viewport = _viewport_for_composite_bounds(map_rect, bounds, padding=0.1)
    return viewport, map_rect


def composite_bounds_for_state(state_abbrev: str) -> tuple[float, float, float, float]:
    with STATES_GEOJSON_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    for feature in data["features"]:
        if _state_abbrev(feature["properties"]["name"]) != state_abbrev:
            continue
        return _composite_bounds_for_geometry(feature["geometry"])
    raise ValueError(f"Unknown state abbreviation: {state_abbrev}")


def load_projected_state(viewport: MapViewport, state_abbrev: str) -> ProjectedState | None:
    with STATES_GEOJSON_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    for feature in data["features"]:
        if _state_abbrev(feature["properties"]["name"]) != state_abbrev:
            continue
        return _state_from_feature(feature, viewport)
    return None


def _viewport_for_composite_bounds(
    map_rect: pygame.Rect,
    bounds: tuple[float, float, float, float],
    *,
    padding: float = 0.0,
) -> MapViewport:
    min_x, min_y, max_x, max_y = bounds
    composite_width = max(max_x - min_x, 1.0)
    composite_height = max(max_y - min_y, 1.0)
    inset = 1.0 - padding
    scale = min(map_rect.width / composite_width, map_rect.height / composite_height) * inset
    scaled_width = composite_width * scale
    scaled_height = composite_height * scale
    left = map_rect.centerx - (min_x * scale + scaled_width / 2)
    top = map_rect.centery - (min_y * scale + scaled_height / 2)
    return MapViewport(left=left, top=top, scale=scale)


def _composite_bounds_for_geometry(geometry: dict) -> tuple[float, float, float, float]:
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    for ring in _extract_rings(geometry):
        if _should_skip_ring(ring):
            continue
        for lon, lat in ring:
            if _should_skip_coordinate(lon, lat):
                continue
            lon, lat = prepare_coordinates(lon, lat)
            if lon > 1000:
                continue
            x, y = USA_COMPOSITE.project_lon_lat(lon, lat)
            if _is_failed_projection(lon, lat, x, y):
                continue
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
    if min_x == float("inf"):
        return _composite_extent()
    return min_x, min_y, max_x, max_y


def load_projected_states(viewport: MapViewport) -> list[ProjectedState]:
    return _load_features(
        STATES_GEOJSON_PATH,
        viewport,
        lambda feature: _state_from_feature(feature, viewport),
    )


def load_projected_territories(
    viewport: MapViewport, names: set[str]
) -> list[ProjectedState]:
    territories: list[ProjectedState] = []
    with STATES_GEOJSON_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    for feature in data["features"]:
        name = feature["properties"]["name"]
        if name not in names:
            continue
        state = _state_from_feature(feature, viewport)
        if state is not None:
            territories.append(state)
    return territories


def load_projected_districts(
    viewport: MapViewport,
    politician_ids: dict[tuple[str, int], str],
) -> list[ProjectedDistrict]:
    districts: list[ProjectedDistrict] = []
    with DISTRICTS_GEOJSON_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)

    for feature in data["features"]:
        props = feature["properties"]
        district_code = props.get("CD118FP", "")
        if district_code in ("ZZ",):
            continue
        state = STATE_FIPS_TO_ABBREV.get(props.get("STATEFP20", ""), "")
        if not state:
            continue
        district = 1 if district_code == "00" else int(district_code)
        politician_id = politician_ids.get((state, district))
        if politician_id is None:
            continue
        polygons = _project_geometry(feature["geometry"], viewport)
        if polygons:
            districts.append(
                ProjectedDistrict(
                    state=state,
                    district=district,
                    politician_id=politician_id,
                    polygons=polygons,
                )
            )
    return districts


def build_land_mask(
    screen_size: tuple[int, int], viewport: MapViewport
) -> pygame.Mask:
    """Mask of US state land areas — clips district fill that bleeds into lakes."""
    mask_surface = pygame.Surface(screen_size)
    mask_surface.fill((0, 0, 0))
    for state in load_projected_states(viewport):
        for polygon in state.polygons:
            pygame.draw.polygon(mask_surface, (255, 255, 255), polygon)
    return pygame.mask.from_threshold(mask_surface, (255, 255, 255), (1, 1, 1))


def apply_land_mask(
    surface: pygame.Surface,
    layer: pygame.Surface,
    land_mask: pygame.Mask,
    background: tuple[int, int, int],
) -> None:
    """Draw layer onto surface, keeping only pixels inside land_mask."""
    if isinstance(background, pygame.Color):
        background = (background.r, background.g, background.b)
    masked = layer.copy()
    mask_rgba = land_mask.to_surface(
        setcolor=(255, 255, 255, 255),
        unsetcolor=(0, 0, 0, 255),
    )
    masked.blit(mask_rgba, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(masked, (0, 0))
    outside = land_mask.copy()
    outside.invert()
    outside_rgba = outside.to_surface(
        setcolor=(*background, 255),
        unsetcolor=(0, 0, 0, 0),
    )
    surface.blit(outside_rgba, (0, 0))


def label_point_for_polygons(
    polygons: list[list[tuple[float, float]]],
) -> tuple[int, int] | None:
    if not polygons:
        return None
    largest = max(polygons, key=polygon_area)
    return polygon_centroid(largest)


def _state_from_feature(feature: dict, viewport: MapViewport) -> ProjectedState | None:
    name = feature["properties"]["name"]
    abbreviation = _state_abbrev(name)
    polygons = _project_geometry(feature["geometry"], viewport)
    if not polygons:
        return None
    return ProjectedState(
        name=name,
        abbreviation=abbreviation,
        polygons=polygons,
        label_point=label_point_for_polygons(polygons),
    )


def _load_features(path: Path, viewport: MapViewport, mapper) -> list:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    items = []
    for feature in data["features"]:
        item = mapper(feature)
        if item is not None:
            items.append(item)
    return items


def _project_geometry(
    geometry: dict, viewport: MapViewport
) -> list[list[tuple[float, float]]]:
    projected: list[list[tuple[float, float]]] = []
    for ring in _extract_rings(geometry):
        if _should_skip_ring(ring):
            continue
        for projected_ring in viewport.project_ring(ring):
            if len(projected_ring) >= 3:
                projected.append(projected_ring)
    return filter_distant_fragments(projected)


def filter_distant_fragments(
    polygons: list[list[tuple[float, float]]],
) -> list[list[tuple[float, float]]]:
    if len(polygons) <= 1:
        return polygons
    main = max(polygons, key=polygon_area)
    main_area = polygon_area(main)
    main_center = polygon_centroid(main)
    if not main_center or main_area <= 0:
        return polygons
    mx, my = main_center
    kept: list[list[tuple[float, float]]] = []
    for polygon in polygons:
        center = polygon_centroid(polygon)
        if not center:
            continue
        distance = math.hypot(center[0] - mx, center[1] - my)
        area = polygon_area(polygon)
        if distance <= FRAGMENT_MAX_DISTANCE or area >= main_area * 0.01:
            kept.append(polygon)
    return kept if kept else [main]


def _extract_rings(geometry: dict) -> list[list[tuple[float, float]]]:
    geo_type = geometry["type"]
    if geo_type == "Polygon":
        return [geometry["coordinates"][0]]
    if geo_type == "MultiPolygon":
        return [polygon[0] for polygon in geometry["coordinates"]]
    return []


def _composite_extent() -> tuple[float, float, float, float]:
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    for geo_map in (USA_CONTINENTAL, ALASKA, HAWAII):
        bounds = geo_map.geo_bounds
        for lon, lat in (
            (bounds.longitude_min, bounds.latitude_min),
            (bounds.longitude_max, bounds.latitude_min),
            (bounds.longitude_max, bounds.latitude_max),
            (bounds.longitude_min, bounds.latitude_max),
        ):
            x, y = geo_map.project_lon_lat(lon, lat)
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
    for x, y in (
        (PUERTO_RICO_INSET.x_min, PUERTO_RICO_INSET.y_min),
        (PUERTO_RICO_INSET.x_max, PUERTO_RICO_INSET.y_max),
    ):
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)
    return min_x, min_y, max_x, max_y


def _should_skip_coordinate(lon: float, lat: float) -> bool:
    prepared_lon, _ = prepare_coordinates(lon, lat)
    return prepared_lon > 1000.0


def _should_skip_ring(ring: list[tuple[float, float]]) -> bool:
    for lon, lat in ring:
        if _should_skip_coordinate(lon, lat):
            return True
    return False


def _append_with_gap_split(
    points: list[tuple[float, float] | None],
    point: tuple[float, float] | None,
) -> list[tuple[float, float] | None]:
    if point is None:
        if points and points[-1] is not None:
            points.append(None)
        return points
    if points and points[-1] is not None:
        previous = points[-1]
        dx = point[0] - previous[0]
        dy = point[1] - previous[1]
        if math.hypot(dx, dy) > MAX_RING_SEGMENT:
            points.append(None)
    points.append(point)
    return points


def _is_failed_projection(lon: float, lat: float, x: float, y: float) -> bool:
    if abs(lon) < 0.01 and abs(lat) < 0.01:
        return False
    if abs(x) < 0.01 and abs(y) < 0.01:
        return True
    # Continental projection wraps dateline points to large negative x.
    return x < 0.0


def polygon_area(points: list[tuple[float, float]]) -> float:
    if len(points) < 3:
        return 0.0
    area = 0.0
    for index, (x1, y1) in enumerate(points):
        x2, y2 = points[(index + 1) % len(points)]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def polygon_centroid(points: list[tuple[float, float]]) -> tuple[int, int] | None:
    if len(points) < 3:
        return None
    area = 0.0
    centroid_x = 0.0
    centroid_y = 0.0
    for index, (x1, y1) in enumerate(points):
        x2, y2 = points[(index + 1) % len(points)]
        cross = x1 * y2 - x2 * y1
        area += cross
        centroid_x += (x1 + x2) * cross
        centroid_y += (y1 + y2) * cross
    if abs(area) < 1e-6:
        x = sum(point[0] for point in points) / len(points)
        y = sum(point[1] for point in points) / len(points)
        return (int(x), int(y))
    area *= 0.5
    centroid_x /= 6.0 * area
    centroid_y /= 6.0 * area
    return (int(centroid_x), int(centroid_y))


def point_in_polygon(point: tuple[int, int], polygon: list[tuple[float, float]]) -> bool:
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
    if name == "Puerto Rico":
        return "PR"
    if name == "District of Columbia":
        return "DC"
    for abbrev, full_name in STATE_ABBREV_TO_NAME.items():
        if full_name == name:
            return abbrev
    return ""

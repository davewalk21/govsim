"""Albers USA composite projection (continental US + Alaska + Hawaii + PR inset).

Ported from https://github.com/cassandra/geo_maps (Apache 2.0) calibration values.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

EARTH_RADIUS_MILES = 6378.137 * 0.621371


@dataclass
class AlbersMapProjection:
    reference_longitude_deg: float
    reference_latitude_deg: float
    standard_parallel_1_deg: float
    standard_parallel_2_deg: float
    radius_miles: float = EARTH_RADIUS_MILES

    def __post_init__(self) -> None:
        phi1 = math.radians(self.standard_parallel_1_deg)
        phi2 = math.radians(self.standard_parallel_2_deg)
        phi0 = math.radians(self.reference_latitude_deg)
        self.n = 0.5 * (math.sin(phi1) + math.sin(phi2))
        self.c = math.cos(phi1) ** 2 + 2 * self.n * math.sin(phi1)
        self.rho_0 = (self.radius_miles / self.n) * math.sqrt(
            self.c - 2 * self.n * math.sin(phi0)
        )

    def project(self, longitude_deg: float, latitude_deg: float) -> tuple[float, float]:
        longitude = math.radians(longitude_deg)
        latitude = math.radians(latitude_deg)
        theta = self.n * (longitude - math.radians(self.reference_longitude_deg))
        rho_basis = self.c - 2 * self.n * math.sin(latitude)
        if rho_basis < 0.0:
            return (0.0, 0.0)
        rho = (self.radius_miles / self.n) * math.sqrt(rho_basis)
        x = rho * math.sin(theta)
        y = self.rho_0 - rho * math.cos(theta)
        return (x, y)


@dataclass
class GeoBounds:
    longitude_min: float = 999999.0
    longitude_max: float = -999999.0
    latitude_min: float = 999999.0
    latitude_max: float = -999999.0

    def contains_point(self, longitude_deg: float, latitude_deg: float) -> bool:
        return (
            self.longitude_min <= longitude_deg <= self.longitude_max
            and self.latitude_min <= latitude_deg <= self.latitude_max
        )


@dataclass
class GeoMap:
    projection: AlbersMapProjection
    geo_bounds: GeoBounds
    display_x_scale: float
    display_y_scale: float
    display_x_offset: float
    display_y_offset: float
    rotation_angle_deg: float = 0.0

    def __post_init__(self) -> None:
        if self.rotation_angle_deg:
            radians = math.radians(self.rotation_angle_deg)
            self._sin_angle = math.sin(radians)
            self._cos_angle = math.cos(radians)
        else:
            self._sin_angle = 0.0
            self._cos_angle = 1.0

    def project_lon_lat(self, longitude_deg: float, latitude_deg: float) -> tuple[float, float]:
        projected_x, projected_y = self.projection.project(longitude_deg, latitude_deg)
        if self.rotation_angle_deg:
            rotated_x = (projected_x * self._cos_angle) - (projected_y * self._sin_angle)
            rotated_y = (projected_x * self._sin_angle) + (projected_y * self._cos_angle)
            scaled_x = rotated_x * self.display_x_scale
            scaled_y = rotated_y * self.display_y_scale
        else:
            scaled_x = projected_x * self.display_x_scale
            scaled_y = projected_y * self.display_y_scale
        x = scaled_x + self.display_x_offset
        y = self.display_y_offset - scaled_y
        return (x, y)


@dataclass
class TerritoryInset:
    """Linear lon/lat → composite-space rectangle (for Puerto Rico, etc.)."""

    geo_bounds: GeoBounds
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def contains_point(self, longitude_deg: float, latitude_deg: float) -> bool:
        return self.geo_bounds.contains_point(longitude_deg, latitude_deg)

    def project_lon_lat(self, longitude_deg: float, latitude_deg: float) -> tuple[float, float]:
        bounds = self.geo_bounds
        lon_span = bounds.longitude_max - bounds.longitude_min
        lat_span = bounds.latitude_max - bounds.latitude_min
        t_x = (longitude_deg - bounds.longitude_min) / lon_span
        t_y = (bounds.latitude_max - latitude_deg) / lat_span
        x = self.x_min + t_x * (self.x_max - self.x_min)
        y = self.y_min + t_y * (self.y_max - self.y_min)
        return (x, y)


class CompositeGeoMap:
    def __init__(
        self,
        geo_maps: list[GeoMap],
        territories: list[TerritoryInset] | None = None,
    ) -> None:
        assert geo_maps
        self._geo_maps = geo_maps
        self._default = geo_maps[0]
        self._alaska = geo_maps[1]
        self._territories = territories or []

    def project_lon_lat(self, longitude_deg: float, latitude_deg: float) -> tuple[float, float]:
        longitude_deg, latitude_deg = prepare_coordinates(longitude_deg, latitude_deg)
        for territory in self._territories:
            if territory.contains_point(longitude_deg, latitude_deg):
                return territory.project_lon_lat(longitude_deg, latitude_deg)
        geo_map = self._geo_map_for_point(longitude_deg, latitude_deg)
        return geo_map.project_lon_lat(longitude_deg, latitude_deg)

    def _geo_map_for_point(self, longitude_deg: float, latitude_deg: float) -> GeoMap:
        if _in_alaska_bounds(longitude_deg, latitude_deg):
            return self._alaska
        for geo_map in self._geo_maps:
            if geo_map.geo_bounds.contains_point(longitude_deg, latitude_deg):
                return geo_map
        return self._default


def normalize_longitude(longitude_deg: float) -> float:
    longitude = ((longitude_deg + 180.0) % 360.0) - 180.0
    if longitude == -180.0 and longitude_deg > 0:
        return 180.0
    return longitude


def prepare_coordinates(longitude_deg: float, latitude_deg: float) -> tuple[float, float]:
    """Normalize lon/lat and convert Aleutian +179°E style coords to western hemisphere."""
    if longitude_deg < -180.0 or longitude_deg > 180.0:
        return (9999.0, latitude_deg)
    longitude = normalize_longitude(longitude_deg)
    if 50.5 <= latitude_deg <= 71.5232 and longitude > 160.0:
        longitude -= 360.0
    return (max(-180.0, min(180.0, longitude)), latitude_deg)


def _in_alaska_bounds(longitude_deg: float, latitude_deg: float) -> bool:
    longitude, latitude = prepare_coordinates(longitude_deg, latitude_deg)
    if longitude > 1000.0:
        return False
    return ALASKA.geo_bounds.contains_point(longitude, latitude)


USA_CONTINENTAL = GeoMap(
    projection=AlbersMapProjection(-96.0, 37.5, 29.5, 45.5),
    geo_bounds=GeoBounds(-124.8679, -66.8628, 24.3959, 49.3877),
    display_x_scale=0.3332,
    display_y_scale=0.3318,
    display_x_offset=491.0249,
    display_y_offset=323.6935,
)

ALASKA = GeoMap(
    projection=AlbersMapProjection(-154.0, 50.0, 55.0, 65.0),
    geo_bounds=GeoBounds(-180.0, -129.97, 50.5, 71.5232),
    display_x_scale=0.1301,
    display_y_scale=0.1311,
    display_x_offset=132.4555,
    display_y_offset=638.5017,
    rotation_angle_deg=-11.0,
)

HAWAII = GeoMap(
    projection=AlbersMapProjection(-157.0, 13.0, 8.0, 18.0),
    geo_bounds=GeoBounds(-160.3922, -154.6271, 18.71, 22.3386),
    display_x_scale=0.3279,
    display_y_scale=0.3371,
    display_x_offset=325.5313,
    display_y_offset=729.5,
    rotation_angle_deg=-0.5,
)

PUERTO_RICO_INSET = TerritoryInset(
    geo_bounds=GeoBounds(-67.98, -65.18, 17.88, 18.52),
    x_min=855.0,
    y_min=655.0,
    x_max=945.0,
    y_max=715.0,
)

USA_COMPOSITE = CompositeGeoMap(
    [USA_CONTINENTAL, ALASKA, HAWAII],
    territories=[PUERTO_RICO_INSET],
)

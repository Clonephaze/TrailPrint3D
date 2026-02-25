"""Coordinate conversion, distance calculations, and geo-math helpers."""

import math

import bpy  # type: ignore

# 1 degree of latitude ≈ 111.32 km  (used in older code paths, kept for reference)
LAT_LON_TO_METERS = 111.32


# ── Mercator projection helpers ────────────────────────────────────────

def calculate_scale(map_size: float, coordinates, scale_mode: str = "FACTOR",
                    path_scale: float = 0.8, generation_type: int = 0) -> float:
    """Compute the horizontal scale factor that maps real-world coordinates
    onto a Blender object of *map_size* mm.
    """
    min_lat = min(p[0] for p in coordinates)
    max_lat = max(p[0] for p in coordinates)
    min_lon = min(p[1] for p in coordinates)
    max_lon = max(p[1] for p in coordinates)

    R = 6371  # Earth radius km
    x1 = R * math.radians(min_lon)
    y1 = R * math.log(math.tan(math.pi / 4 + math.radians(min_lat) / 2))
    x2 = R * math.radians(max_lon)
    y2 = R * math.log(math.tan(math.pi / 4 + math.radians(max_lat) / 2))

    width = abs(x2 - x1)
    height = abs(y2 - y1)
    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    # For "SCALE" mode — accurate Mercator factor (currently mf = 1)
    mf = 1
    if scale_mode == "SCALE":
        mx1 = R * math.radians(min_lon) * math.cos(math.radians(min_lat))
        mx2 = R * math.radians(max_lon) * math.cos(math.radians(max_lat))
        mwidth = abs(mx1 - mx2)
        mf = 1 / width * mwidth if width else 1
        mf = 1  # currently overridden

    if scale_mode in ("COORDINATES", "SCALE"):
        distance = 0

    maxer = max(width, height, distance)

    if maxer == 0:
        return 1.0

    if scale_mode == "COORDINATES" or generation_type in (2, 3):
        scale = map_size / maxer
    elif scale_mode == "FACTOR":
        scale = (map_size * path_scale) / maxer
    elif scale_mode == "SCALE":
        scale = path_scale * mf
    else:
        scale = map_size / maxer

    return scale


def convert_to_blender_coordinates(lat: float, lon: float, elevation: float,
                                    timestamp=None, *,
                                    scale_hor: float | None = None,
                                    elevation_offset: float = 0.0,
                                    scale_elevation: float = 1.0,
                                    auto_scale: float = 1.0):
    """Convert GPS lat/lon/elevation to Blender XYZ using Web-Mercator.

    If *scale_hor* is ``None`` the value is read from
    ``bpy.context.scene.tp3d.sScaleHor`` (legacy codepath for standalone
    operators that don't have a GenerationContext).
    """
    if scale_hor is None:
        scale_hor = bpy.context.scene.tp3d.sScaleHor

    R = 6371
    x = R * math.radians(lon) * scale_hor
    y = R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * scale_hor
    z = (elevation - elevation_offset) / 1000 * scale_elevation * auto_scale

    return (x, y, z)


def convert_to_geo(x: float, y: float, scale_hor: float | None = None):
    """Convert Blender XY back to latitude/longitude."""
    if scale_hor is None:
        scale_hor = bpy.context.scene.tp3d.sScaleHor

    R = 6371
    longitude = math.degrees(x / (R * scale_hor))
    latitude = math.degrees(2 * math.atan(math.exp(y / (R * scale_hor))) - math.pi / 2)
    return latitude, longitude


# ── Distance / statistics ──────────────────────────────────────────────

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in **kilometres**."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)

    a = (math.sin(d_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def calculate_total_length(points) -> float:
    """Total path length in km from a list of ``(lat, lon, ele, time)`` tuples."""
    total = 0.0
    for i in range(1, len(points)):
        lon1, lat1 = points[i - 1][0], points[i - 1][1]
        lon2, lat2 = points[i][0], points[i][1]
        total += haversine(lon1, lat1, lon2, lat2)
    return total


def calculate_total_elevation(points) -> float:
    """Cumulative elevation gain in metres."""
    total = 0.0
    for i in range(1, len(points)):
        elev1 = points[i - 1][2]
        elev2 = points[i][2]
        if elev2 > elev1:
            total += elev2 - elev1
    return total


def calculate_total_time(points) -> float:
    """Total time between first and last point in **hours**."""
    if len(points) < 2:
        return 0.0
    start_time = points[0][3]
    end_time = points[-1][3]
    if start_time is not None and end_time is not None:
        diff = end_time - start_time
        return diff.total_seconds() / 3600
    return 0.0


# ── Misc geo helpers ───────────────────────────────────────────────────

def midpoint_spherical(lat1: float, lon1: float, lat2: float, lon2: float):
    """Spherical midpoint between two lat/lon pairs. Returns ``(lat, lon)``."""
    lat1r, lon1r = math.radians(lat1), math.radians(lon1)
    lat2r, lon2r = math.radians(lat2), math.radians(lon2)

    x1 = math.cos(lat1r) * math.cos(lon1r)
    y1 = math.cos(lat1r) * math.sin(lon1r)
    z1 = math.sin(lat1r)
    x2 = math.cos(lat2r) * math.cos(lon2r)
    y2 = math.cos(lat2r) * math.sin(lon2r)
    z2 = math.sin(lat2r)

    x, y, z = (x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2
    lon_mid = math.atan2(y, x)
    lat_mid = math.atan2(z, math.sqrt(x * x + y * y))
    return math.degrees(lat_mid), math.degrees(lon_mid)


def move_coordinates(lat: float, lon: float, distance_km: float, direction: str):
    """Move a coordinate by *distance_km* in a cardinal direction (n/s/e/w)."""
    R = 6371.0
    direction = direction.lower()
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)

    if direction == "n":
        lat_rad += distance_km / R
    elif direction == "s":
        lat_rad -= distance_km / R
    elif direction == "e":
        lon_rad += distance_km / (R * math.cos(lat_rad))
    elif direction == "w":
        lon_rad -= distance_km / (R * math.cos(lat_rad))
    else:
        raise ValueError("Direction must be 'n', 's', 'e', or 'w'")

    return math.degrees(lat_rad), math.degrees(lon_rad)


def separate_duplicate_xy(coordinates, offset: float = 0.05):
    """Nudge duplicate XYZ points slightly to prevent curve clipping."""
    seen_xy = set()
    for i, point in enumerate(coordinates):
        if isinstance(point, tuple):
            point = list(point)
            coordinates[i] = point
        xy_key = (point[0], point[1], point[2])
        if xy_key in seen_xy:
            point[2] += offset
            point[1] += offset
        else:
            seen_xy.add(xy_key)
    return coordinates

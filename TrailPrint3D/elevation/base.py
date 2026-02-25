"""Base elevation helpers — single-point lookup and tile-based mesh elevation.

Provides both a main-thread convenience wrapper (``get_tile_elevation``) and
thread-safe building blocks (``extract_world_verts`` + ``fetch_tile_elevations``)
that the modal operator uses for background fetching.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np  # type: ignore
import bpy  # type: ignore
import requests  # type: ignore

from ..coordinates import convert_to_geo, haversine
from .cache import save_elevation_cache
from .opentopodata import get_elevation_openTopoData
from .open_elevation import get_elevation_openElevation
from .terrain_tiles import get_elevation_TerrainTiles


def _batch_convert_to_geo(world_verts, scale_hor):
    """Vectorised Blender XY → (lat, lon) conversion using numpy."""
    arr = np.array(world_verts, dtype=np.float64)
    xs = arr[:, 0]
    ys = arr[:, 1]
    R = 6371.0
    longitudes = np.degrees(xs / (R * scale_hor))
    latitudes = np.degrees(2.0 * np.arctan(np.exp(ys / (R * scale_hor))) - math.pi / 2.0)
    return list(zip(latitudes.tolist(), longitudes.tolist()))


# ── Result container ──────────────────────────────────────────────────────


@dataclass
class ElevationResult:
    """Values returned by an elevation fetch — fully thread-safe, no bpy refs."""

    elevations: list
    diff: float
    lowest: float
    highest: float
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    map_distance_km: float
    vertex_count: int


# ── Single-point helper ──────────────────────────────────────────────────


def get_elevation_single(lat: float, lon: float, dataset: str = "srtm30m") -> float:
    """Fetch elevation for a single point via OpenTopoData."""
    url = f"https://api.opentopodata.org/v1/{dataset}?locations={lat},{lon}"
    response = requests.get(url).json()
    return response["results"][0]["elevation"] if "results" in response else 0


# ── World-vert extraction (main thread only) ─────────────────────────────


def extract_world_verts(obj) -> list[tuple[float, float, float]]:
    """Return world-space vertex positions as plain ``(x, y, z)`` tuples.

    Uses numpy for fast bulk matrix transformation.
    Must be called on the main thread (accesses bpy mesh data).
    The resulting list is safe to pass to a background thread.
    """
    mesh = obj.data
    n = len(mesh.vertices)
    # Read all vertex coords at once (flat array)
    coords = np.empty(n * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", coords)
    coords = coords.reshape(n, 3)

    # Apply world matrix via numpy
    mat = np.array(obj.matrix_world, dtype=np.float64)[:3, :3]
    loc = np.array(obj.matrix_world.translation, dtype=np.float64)
    world = coords @ mat.T + loc

    return [tuple(row) for row in world.tolist()]


# ── Thread-safe elevation fetch ──────────────────────────────────────────


def fetch_tile_elevations(
    world_verts: list[tuple[float, float, float]],
    *,
    api: int = 2,
    dataset: str = "aster30m",
    opentopoAddress: str = "https://api.opentopodata.org/v1/",
    num_subdivisions: int = 8,
    scale_hor: float | None = None,
    progress_callback=None,
    cancel_event=None,
) -> ElevationResult:
    """Fetch elevations for pre-extracted vertex positions.

    **Thread-safe** — no ``bpy`` access.  Progress is reported via the
    optional *progress_callback(percent, message)*.  If *cancel_event* is
    a ``threading.Event`` that gets set, the function returns early with
    zeroed elevations.

    *scale_hor* **must** be provided when calling from a background thread
    (it is passed through to ``convert_to_geo`` so it does not need to
    touch ``bpy.context``).

    Returns an :class:`ElevationResult`.
    """
    n_verts = len(world_verts)

    if api in (0, 1):
        chunk_size = 100_000
    elif api == 2:
        chunk_size = 50_000_000
    else:
        chunk_size = 100_000

    # Compute geographic bounds (vectorised) ---------------------------------
    arr = np.array(world_verts, dtype=np.float64)
    min_x, min_y = arr[:, 0].min(), arr[:, 1].min()
    max_x, max_y = arr[:, 0].max(), arr[:, 1].max()

    minl = convert_to_geo(min_x, min_y, scale_hor)
    maxl = convert_to_geo(max_x, max_y, scale_hor)
    min_lat, max_lat = minl[0], maxl[0]
    min_lon, max_lon = minl[1], maxl[1]

    realdist1 = haversine(min_lat, min_lon, min_lat, max_lon)
    realdist2 = haversine(max_lat, min_lon, max_lat, max_lon)
    map_distance_km = max(realdist1, realdist2)

    # Fetch elevations per chunk -----------------------------------------------
    elevations: list[float] = []

    for i in range(0, n_verts, chunk_size):
        if cancel_event and cancel_event.is_set():
            return ElevationResult(
                elevations=[0.0] * n_verts, diff=0, lowest=0, highest=0,
                min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon,
                map_distance_km=map_distance_km, vertex_count=n_verts,
            )

        chunk = world_verts[i : i + chunk_size]
        coords = _batch_convert_to_geo(chunk, scale_hor)

        if api == 0:
            chunk_elev = get_elevation_openTopoData(
                coords, n_verts, i,
                dataset=dataset, opentopoAddress=opentopoAddress, api=api,
                progress_callback=progress_callback, cancel_event=cancel_event,
            )
        elif api == 1:
            chunk_elev = get_elevation_openElevation(
                coords, n_verts, i, api=api,
                progress_callback=progress_callback, cancel_event=cancel_event,
            )
        elif api == 2:
            chunk_elev = get_elevation_TerrainTiles(
                coords, n_verts, i,
                minLat=min_lat, maxLat=max_lat,
                minLon=min_lon, maxLon=max_lon,
                num_subdivisions=num_subdivisions,
                progress_callback=progress_callback, cancel_event=cancel_event,
            )
        else:
            chunk_elev = [0.0] * len(chunk)

        elevations.extend(chunk_elev)
        del chunk_elev

    save_elevation_cache()

    lowest = min(elevations) if elevations else 0
    highest = max(elevations) if elevations else 0
    diff = highest - lowest

    return ElevationResult(
        elevations=elevations,
        diff=diff,
        lowest=lowest,
        highest=highest,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        map_distance_km=map_distance_km,
        vertex_count=n_verts,
    )


# ── Convenience wrapper (main-thread, legacy) ────────────────────────────


def get_tile_elevation(obj, api=2, dataset="aster30m",
                       opentopoAddress="https://api.opentopodata.org/v1/",
                       num_subdivisions=8):
    """Main-thread convenience wrapper: extract verts, fetch, write scene props.

    Returns ``(elevations, diff, lowestZ, highestZ,
               minLat, maxLat, minLon, maxLon)``.
    """
    world_verts = extract_world_verts(obj)

    # Read scale_hor from scene (safe — we're on the main thread)
    scale_hor = bpy.context.scene.tp3d.get("sScaleHor", None)

    result = fetch_tile_elevations(
        world_verts,
        api=api,
        dataset=dataset,
        opentopoAddress=opentopoAddress,
        num_subdivisions=num_subdivisions,
        scale_hor=scale_hor,
    )

    # Write scene properties (main thread only)
    bpy.context.scene.tp3d["sMapInKm"] = result.map_distance_km
    bpy.context.scene.tp3d["o_verticesMap"] = str(result.vertex_count)

    return (
        result.elevations, result.diff,
        result.lowest, result.highest,
        result.min_lat, result.max_lat,
        result.min_lon, result.max_lon,
    )

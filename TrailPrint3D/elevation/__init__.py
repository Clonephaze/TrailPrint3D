"""Elevation data package — caching, API counter, and provider implementations."""

from .cache import load_elevation_cache, save_elevation_cache, get_cached_elevation, cache_elevation
from .counter import load_counter, save_counter, update_request_counter, send_api_request
from .opentopodata import get_elevation_openTopoData, get_elevation_path_openTopoData
from .open_elevation import get_elevation_openElevation, get_elevation_path_openElevation
from .terrain_tiles import get_elevation_TerrainTiles
from .base import (
    get_elevation_single, get_tile_elevation,
    ElevationResult, extract_world_verts, fetch_tile_elevations,
)

__all__ = [
    "load_elevation_cache", "save_elevation_cache", "get_cached_elevation", "cache_elevation",
    "load_counter", "save_counter", "update_request_counter", "send_api_request",
    "get_elevation_openTopoData", "get_elevation_path_openTopoData",
    "get_elevation_openElevation", "get_elevation_path_openElevation",
    "get_elevation_TerrainTiles",
    "get_elevation_single", "get_tile_elevation",
    "ElevationResult", "extract_world_verts", "fetch_tile_elevations",
]

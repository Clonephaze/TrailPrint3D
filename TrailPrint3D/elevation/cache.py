"""Disk-backed elevation cache — JSON file with size limit."""

import json
import os

import bpy  # type: ignore

# Paths
elevation_cache_file = os.path.join(bpy.utils.user_resource('CONFIG'), "elevation_cache.json")

# In-memory cache dict
_elevation_cache: dict = {}

DEFAULT_CACHE_SIZE = 100000


def load_elevation_cache():
    """Load the elevation cache from disk into *_elevation_cache*."""
    global _elevation_cache
    if os.path.exists(elevation_cache_file):
        try:
            with open(elevation_cache_file, "r") as f:
                _elevation_cache = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Error loading elevation cache: {e}")
            _elevation_cache = {}
    else:
        _elevation_cache = {}


def save_elevation_cache(cache_size: int = DEFAULT_CACHE_SIZE):
    """Save *_elevation_cache* to disk, trimming to *cache_size* entries."""
    print(f"Currently cached: {len(_elevation_cache)}")
    if len(_elevation_cache) > cache_size:
        keys = list(_elevation_cache.keys())
        for key in keys[:-cache_size]:
            del _elevation_cache[key]
    try:
        with open(elevation_cache_file, "w") as f:
            json.dump(_elevation_cache, f)
    except OSError as e:
        print(f"Error saving elevation cache: {e}")


def get_cached_elevation(lat: float, lon: float, api_type: str = "opentopodata"):
    """Return cached elevation or ``None``."""
    key = f"{lat:.5f}_{lon:.5f}_{api_type}"
    return _elevation_cache.get(key)


def cache_elevation(lat: float, lon: float, elevation: float, api_type: str = "opentopodata"):
    """Store an elevation value in cache."""
    key = f"{lat:.5f}_{lon:.5f}_{api_type}"
    _elevation_cache[key] = elevation

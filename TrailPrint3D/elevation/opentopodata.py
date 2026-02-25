"""OpenTopoData elevation provider — batch requests with caching and rate-limiting."""

import time

import bpy  # type: ignore
import requests  # type: ignore

from .cache import (
    load_elevation_cache,
    get_cached_elevation,
    cache_elevation,
    _elevation_cache,
)
from .counter import send_api_request


def get_elevation_openTopoData(coords, lenv=0, pointsDone=0,
                               dataset="aster30m",
                               opentopoAddress="https://api.opentopodata.org/v1/",
                               api=0,
                               progress_callback=None, cancel_event=None):
    """Fetch elevations with batch requests (100 per batch), using cache when available."""
    disableCache = bpy.context.scene.tp3d.get("disableCache", 0)

    if not _elevation_cache:
        load_elevation_cache()

    coords_to_fetch = []
    coords_indices = []
    elevations = [0] * len(coords)

    for i, (lat, lon) in enumerate(coords):
        cached = get_cached_elevation(lat, lon)
        if cached is not None and disableCache == 0:
            elevations[i] = cached
        else:
            elevations[i] = -5
            coords_to_fetch.append((lat, lon))
            coords_indices.append(i)

    if len(coords) - len(coords_to_fetch) > 0:
        print(f"Using: {len(coords) - len(coords_to_fetch)} cached Coordinates")

    if not coords_to_fetch:
        return elevations

    batch_size = 100
    total_batches = (len(coords_to_fetch) + batch_size - 1) // batch_size
    for i in range(0, len(coords_to_fetch), batch_size):
        if cancel_event and cancel_event.is_set():
            return elevations
        batch_idx = i // batch_size + 1
        if progress_callback:
            progress_callback(batch_idx / total_batches, f"Batch {batch_idx}/{total_batches}")
        batch = coords_to_fetch[i:i + batch_size]
        query = "|".join(f"{c[0]},{c[1]}" for c in batch)
        url = f"{opentopoAddress}{dataset}?locations={query}"
        last_request_time = time.monotonic()
        response = requests.get(url)

        nr = i + len(batch) + pointsDone
        addition = f" {nr}/{int(lenv)}"
        send_api_request(addition, api=api, dataset=dataset)
        response.raise_for_status()

        data = response.json()
        for o, result in enumerate(data['results']):
            elevation = result.get('elevation') or 0
            cache_elevation(batch[o][0], batch[o][1], elevation)
            ind = coords_indices[i + o]
            elevations[ind] = elevation

        now = time.monotonic()
        elapsed = now - last_request_time
        if i + batch_size < len(coords_to_fetch) and elapsed < 1.3:
            time.sleep(1.3 - elapsed)

    return elevations


def get_elevation_path_openTopoData(vertices,
                                     dataset="aster30m",
                                     opentopoAddress="https://api.opentopodata.org/v1/",
                                     api=0):
    """Fetch path elevations and return updated coordinate tuples."""
    coords = [(v[0], v[1], v[2], v[3]) for v in vertices]
    elevations = []
    batch_size = 100

    for i in range(0, len(coords), batch_size):
        batch = coords[i:i + batch_size]
        query = "|".join(f"{c[0]},{c[1]}" for c in batch)
        url = f"{opentopoAddress}{dataset}?locations={query}"
        last_request_time = time.monotonic()
        response = requests.get(url).json()

        addition = f"(overwrite path) {i + len(batch)}/{len(coords)}"
        send_api_request(addition, api=api, dataset=dataset)

        elevations.extend(r.get('elevation') or 0 for r in response['results'])

        now = time.monotonic()
        elapsed = now - last_request_time
        if i + batch_size < len(coords) and elapsed < 1.4:
            time.sleep(1.4 - elapsed)

    result = []
    for i in range(len(vertices)):
        result.append((coords[i][0], coords[i][1], elevations[i], coords[i][3]))
    return result

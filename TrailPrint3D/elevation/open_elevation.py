"""Open-Elevation provider — POST-based batch requests with rate-limiting."""

import time

import requests  # type: ignore

from .counter import send_api_request


def get_elevation_openElevation(coords, lenv=0, pointsDone=0, api=1,
                                progress_callback=None, cancel_event=None):
    """Fetch elevations via Open-Elevation POST endpoint (1000 per batch)."""
    elevations = []
    batch_size = 1000
    total_batches = (len(coords) + batch_size - 1) // batch_size

    for i in range(0, len(coords), batch_size):
        if cancel_event and cancel_event.is_set():
            return elevations
        batch_idx = i // batch_size + 1
        if progress_callback:
            progress_callback(batch_idx / total_batches, f"Batch {batch_idx}/{total_batches}")
        batch = coords[i:i + batch_size]
        payload = {"locations": [{"latitude": c[0], "longitude": c[1]} for c in batch]}
        url = "https://api.open-elevation.com/api/v1/lookup"
        headers = {"Content-Type": "application/json"}
        last_request_time = time.monotonic()

        nr = i + len(batch) + pointsDone
        addition = f" {nr}/{int(lenv)}"
        send_api_request(addition, api=api)

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        for result in data['results']:
            elevation = result.get('elevation') or 0
            elevations.append(elevation)

        now = time.monotonic()
        elapsed = now - last_request_time
        if elapsed < 2:
            time.sleep(2 - elapsed)

    return elevations


def get_elevation_path_openElevation(vertices, api=1):
    """Fetch path elevations → list of updated (lat, lon, ele, ts) tuples."""
    coords = [(v[0], v[1], v[2], v[3]) for v in vertices]
    elevations = []
    batch_size = 1000

    for i in range(0, len(coords), batch_size):
        batch = coords[i:i + batch_size]
        payload = {"locations": [{"latitude": c[0], "longitude": c[1]} for c in batch]}
        url = "https://api.open-elevation.com/api/v1/lookup"
        headers = {"Content-Type": "application/json"}
        last_request_time = time.monotonic()

        addition = f"(overwrite path) {i + len(batch)}/{len(coords)}"
        send_api_request(addition, api=api)

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        elevations.extend(r['elevation'] for r in data['results'])

        now = time.monotonic()
        elapsed = now - last_request_time
        if i + batch_size < len(coords) and elapsed < 1.4:
            time.sleep(1.4 - elapsed)

    result = []
    for i in range(len(vertices)):
        result.append((coords[i][0], coords[i][1], elevations[i], coords[i][3]))
    return result

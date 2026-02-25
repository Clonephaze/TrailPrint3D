"""Terrain-Tiles (AWS Terrarium) elevation provider — PNG tile parsing with local cache.

Performance notes
-----------------
* PNG scanline reconstruction uses **numpy** vectorised operations instead of
  per-byte Python loops (≈30× faster for a 256×256 tile).
* Tiles that are not yet cached are downloaded via a
  ``concurrent.futures.ThreadPoolExecutor`` (up to 8 parallel HTTP requests),
  then parsed in parallel on a second pass.
"""

import math
import os
import struct
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np  # type: ignore
import bpy  # type: ignore
import requests  # type: ignore

from ..coordinates import haversine

# Tile cache dir
terrarium_cache_dir = os.path.join(bpy.utils.user_resource('CONFIG'), "terrarium_cache")
if not os.path.exists(terrarium_cache_dir):
    os.makedirs(terrarium_cache_dir)

# Reusable HTTP session (connection keep-alive)
_http_session: requests.Session | None = None


def _get_session() -> requests.Session:
    global _http_session
    if _http_session is None:
        _http_session = requests.Session()
    return _http_session


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def lonlat_to_tilexy(lon, lat, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


def lonlat_to_pixelxy(lon, lat, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = (lon + 180.0) / 360.0 * n * 256
    y = (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n * 256
    return int(x % 256), int(y % 256)


def _fetch_tile_to_disk(zoom, xtile, ytile):
    """Download a tile to disk cache if missing.  Returns the cache path."""
    tile_path = os.path.join(terrarium_cache_dir, f"{zoom}_{xtile}_{ytile}.png")
    if not os.path.exists(tile_path):
        url = f"https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{zoom}/{xtile}/{ytile}.png"
        resp = _get_session().get(url, timeout=30)
        resp.raise_for_status()
        with open(tile_path, "wb") as f:
            f.write(resp.content)
    return tile_path


def _read_tile_bytes(tile_path: str) -> bytes:
    with open(tile_path, "rb") as f:
        return f.read()


# ── Numpy-accelerated PNG RGB parser ─────────────────────────────────────

def _paeth_vec(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Vectorised Paeth predictor for full scanlines."""
    p = a.astype(np.int16) + b.astype(np.int16) - c.astype(np.int16)
    pa = np.abs(p - a.astype(np.int16))
    pb = np.abs(p - b.astype(np.int16))
    pc = np.abs(p - c.astype(np.int16))
    out = np.where((pa <= pb) & (pa <= pc), a,
          np.where(pb <= pc, b, c))
    return out


def parse_png_to_elevation(png_bytes: bytes) -> np.ndarray:
    """Parse an 8-bit RGB PNG and return a 256×256 float32 elevation array.

    Combines scanline reconstruction and Terrarium decoding in one pass,
    avoiding the creation of a large Python list-of-tuples intermediate.
    """
    assert png_bytes[:8] == b'\x89PNG\r\n\x1a\n', "Not a valid PNG file"
    offset = 8
    width = height = 0
    idat_chunks: list[bytes] = []

    while offset < len(png_bytes):
        length = struct.unpack(">I", png_bytes[offset:offset + 4])[0]
        chunk_type = png_bytes[offset + 4:offset + 8]
        data = png_bytes[offset + 8:offset + 8 + length]
        offset += 12 + length

        if chunk_type == b'IHDR':
            width, height = struct.unpack(">II", data[:8])
        elif chunk_type == b'IDAT':
            idat_chunks.append(data)
        elif chunk_type == b'IEND':
            break

    raw = zlib.decompress(b''.join(idat_chunks))
    stride = 3 * width

    # Reshape raw bytes into (height, stride+1) — filter byte + pixel bytes
    raw_arr = np.frombuffer(raw, dtype=np.uint8).reshape(height, stride + 1)
    filters = raw_arr[:, 0]
    scanlines = raw_arr[:, 1:].copy()  # mutable

    # Reconstruct scanlines in-place (row-by-row, but with numpy vectorised ops per row)
    prev_row = np.zeros(stride, dtype=np.uint8)

    for y in range(height):
        ft = filters[y]
        row = scanlines[y]

        if ft == 0:
            pass  # None — already correct
        elif ft == 1:  # Sub — each byte adds the byte 3 positions left
            for j in range(3, stride):
                row[j] = (int(row[j]) + int(row[j - 3])) & 0xFF
        elif ft == 2:  # Up
            row[:] = (row.astype(np.int16) + prev_row.astype(np.int16)) % 256
        elif ft == 3:  # Average
            left = np.zeros(stride, dtype=np.int16)
            left[3:] = row[:-3]
            # First pass: accumulate left dependency sequentially
            for j in range(3, stride):
                left[j] = row[j - 3]
                row[j] = (row[j] + (left[j] + prev_row[j]) // 2) % 256
            # First 3 bytes only depend on prev_row
            row[:3] = (row[:3].astype(np.int16) + prev_row[:3].astype(np.int16) // 2) % 256
        elif ft == 4:  # Paeth — sequential due to left-dependency
            for j in range(stride):
                a = int(row[j - 3]) if j >= 3 else 0
                b = int(prev_row[j])
                c = int(prev_row[j - 3]) if j >= 3 else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                if pa <= pb and pa <= pc:
                    pred = a
                elif pb <= pc:
                    pred = b
                else:
                    pred = c
                row[j] = (row[j] + pred) % 256

        prev_row = row.copy()
        scanlines[y] = row

    # Reshape to (height, width, 3) and compute elevation in one vectorised step
    rgb = scanlines.reshape(height, width, 3).astype(np.float32)
    elevation = rgb[:, :, 0] * 256.0 + rgb[:, :, 1] + rgb[:, :, 2] / 256.0 - 32768.0
    return elevation


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_elevation_TerrainTiles(coords, lenv=0, pointsDone=0, zoom=10,
                               minLat=0, maxLat=0, minLon=0, maxLon=0,
                               num_subdivisions=8,
                               progress_callback=None, cancel_event=None):
    """Fetch elevations for *coords* using AWS Terrarium tiles.

    Downloads tiles in parallel (up to 8 concurrent) and parses them with
    numpy-accelerated PNG reconstruction.
    """
    # Calculate optimal zoom from real distances
    realdist1 = haversine(minLat, minLon, minLat, maxLon) * 1000
    realdist2 = haversine(maxLat, minLon, maxLat, maxLon) * 1000

    horVerts = 1 + 2 ** (num_subdivisions + 1)
    vertdist = max(realdist1, realdist2) / horVerts if horVerts else 1

    zoom = 2
    strt = 156543  # m/pixel at zoom 0
    while strt > vertdist:
        zoom += 1
        strt /= 2
    zoom = min(zoom, 15)
    print(f"Zoom Level for API: {zoom}, Start fetching Data...")

    # Group coords by tile
    tile_dict: dict = {}
    for idx, (lat, lon) in enumerate(coords):
        xtile, ytile = lonlat_to_tilexy(lon, lat, zoom)
        tile_dict.setdefault((xtile, ytile), []).append((idx, lat, lon))

    total_tiles = len(tile_dict)
    elevations = [0.0] * len(coords)
    tile_keys = list(tile_dict.keys())

    # Phase 1: download all tiles in parallel ─────────────────────────────
    tile_paths: dict[tuple[int, int], str] = {}
    failed_tiles: set[tuple[int, int]] = set()

    if progress_callback:
        progress_callback(0.0, f"Downloading {total_tiles} tiles...")

    def _download(key):
        xt, yt = key
        return key, _fetch_tile_to_disk(zoom, xt, yt)

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(_download, k): k for k in tile_keys}
        done_count = 0
        for fut in as_completed(futures):
            if cancel_event and cancel_event.is_set():
                return elevations
            try:
                key, path = fut.result()
                tile_paths[key] = path
            except Exception as e:
                key = futures[fut]
                print(f"Failed to download tile {zoom}/{key[0]}/{key[1]}: {e}")
                failed_tiles.add(key)
            done_count += 1
            if progress_callback:
                progress_callback(done_count / total_tiles * 0.7,
                                  f"Downloaded {done_count}/{total_tiles} tiles")

    # Phase 2: parse tiles and sample elevations ──────────────────────────
    tile_elevation_cache: dict[tuple[int, int], np.ndarray] = {}

    for i, key in enumerate(tile_keys):
        if cancel_event and cancel_event.is_set():
            return elevations
        if key in failed_tiles:
            continue
        try:
            png_bytes = _read_tile_bytes(tile_paths[key])
            tile_elevation_cache[key] = parse_png_to_elevation(png_bytes)
        except Exception as e:
            print(f"Failed to parse tile {zoom}/{key[0]}/{key[1]}: {e}")
            failed_tiles.add(key)
        if progress_callback:
            progress_callback(0.7 + (i + 1) / total_tiles * 0.3,
                              f"Parsed {i + 1}/{total_tiles} tiles")

    # Phase 3: sample elevations from parsed numpy arrays ─────────────────
    for key, idx_lat_lon_list in tile_dict.items():
        if key in failed_tiles:
            continue
        elev_arr = tile_elevation_cache[key]
        for idx, lat, lon in idx_lat_lon_list:
            px, py = lonlat_to_pixelxy(lon, lat, zoom)
            px = min(max(px, 0), 255)
            py = min(max(py, 0), 255)
            elevations[idx] = float(elev_arr[py, px])

    return elevations

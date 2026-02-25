"""GPS data loading, stat calculation, and coordinate preparation."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

import bpy  # type: ignore

from ..coordinates import (
    calculate_total_length,
    calculate_total_elevation,
    calculate_total_time,
    convert_to_blender_coordinates,
    move_coordinates,
    separate_duplicate_xy,
)
from ..gps import read_gpx_file, read_gpx_directory
from ..geometry.curves import simplify_curve
from ..utils import show_message_box

if TYPE_CHECKING:
    from ..context import GenerationContext


def load_gps_data(ctx: GenerationContext, gen_type: int) -> bool:
    """Populate *ctx* with GPS coordinates and trail statistics.

    Returns *True* on success, *False* on error.
    """
    separate_paths: list[list] = []
    coordinates2: list = []

    try:
        if gen_type == 0:
            separate_paths = read_gpx_file(ctx.gpx_file_path)
        elif gen_type == 1:
            separate_paths = read_gpx_directory(ctx.gpx_chain_path)
        elif gen_type in (2, 4):
            for d in ("e", "s", "w", "n"):
                nlat, nlon = move_coordinates(ctx.jMapLat, ctx.jMapLon, ctx.jMapRadius, d)
                separate_paths.append([(nlat, nlon, 0, 0)])
            if gen_type == 4:
                temp = read_gpx_file(ctx.gpx_file_path)
                coordinates2 = [item for sublist in temp for item in sublist]
        elif gen_type == 3:
            separate_paths.append([(ctx.jMapLat1, ctx.jMapLon1, 0, 0)])
            separate_paths.append([(ctx.jMapLat2, ctx.jMapLon2, 0, 0)])
    except (OSError, ValueError, ET.ParseError) as e:
        show_message_box(f"Error reading GPS file (type {gen_type}): {e}")
        return False

    coordinates = [item for sublist in separate_paths for item in sublist]

    # Trail stats
    if gen_type in (0, 1):
        ctx.total_length = calculate_total_length(coordinates)
        ctx.total_elevation = calculate_total_elevation(coordinates)
        total_time = calculate_total_time(coordinates)
    else:
        total_time = 0

    hours = int(total_time)
    minutes = int((total_time - hours) * 60)
    ctx.time_str = f"{hours}h {minutes}m"

    # Up-sample sparse data
    while len(coordinates) < 300 and len(coordinates) > 1 and gen_type != 2:
        i = 0
        while i < len(coordinates) - 1:
            p1, p2 = coordinates[i], coordinates[i + 1]
            mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, (p1[2] + p2[2]) / 2, p1[3])
            coordinates.insert(i + 1, mid)
            i += 2

    # Store on context
    ctx.coordinates = coordinates
    ctx.separate_paths = separate_paths
    ctx.coordinates2 = coordinates2

    return True


def prepare_blender_coords(ctx: GenerationContext, gen_type: int) -> None:
    """Convert geo-coordinates to Blender units and compute center / scale.

    The scale factor MUST be computed and written to the scene BEFORE
    ``convert_to_blender_coordinates`` is called, because that function
    reads ``sScaleHor`` from the scene property.  This matches the order
    in the original monolith.
    """
    from ..coordinates import calculate_scale

    coords = ctx.coordinates

    # 1) Compute horizontal scale FIRST (matches original monolith order)
    scalecoords = coords
    if ctx.scalemode == "COORDINATES" and gen_type in (0, 1):
        scalecoords = ((ctx.scaleLon1, ctx.scaleLat1), (ctx.scaleLon2, ctx.scaleLat2))
    ctx.scaleHor = calculate_scale(ctx.size, scalecoords)
    bpy.context.scene.tp3d["sScaleHor"] = ctx.scaleHor

    # 2) Now convert coordinates — uses the newly-set sScaleHor
    blender_coords = [convert_to_blender_coordinates(lat, lon, ele, ts) for lat, lon, ele, ts in coords]

    if gen_type == 1 or len(ctx.separate_paths) > 1:
        ctx.blender_coords_separate = [
            [convert_to_blender_coordinates(lat, lon, ele, ts) for lat, lon, ele, ts in path]
            for path in ctx.separate_paths
        ]

    # 3) Compute center from correctly-scaled blender coords
    min_x = min(p[0] for p in blender_coords)
    max_x = max(p[0] for p in blender_coords)
    min_y = min(p[1] for p in blender_coords)
    max_y = max(p[1] for p in blender_coords)

    ctx.centerx = (max_x - min_x) / 2 + min_x
    ctx.centery = (max_y - min_y) / 2 + min_y

    bpy.context.scene.tp3d["o_centerx"] = ctx.centerx
    bpy.context.scene.tp3d["o_centery"] = ctx.centery

    ctx.blender_coords = blender_coords


def reproject_after_elevation(ctx: GenerationContext, gen_type: int) -> None:
    """Re-convert coordinates after autoScale is set and simplify / dedupe.

    This is the second coordinate conversion — it uses the now-known
    ``autoScale``, ``elevationOffset`` and ``scaleElevation`` so that
    trail Z values are in the same scale space as the terrain mesh.
    """
    coords = ctx.coordinates
    kw = dict(
        elevation_offset=ctx.elevationOffset,
        scale_elevation=ctx.scaleElevation,
        auto_scale=ctx.autoScale,
    )
    bc = [convert_to_blender_coordinates(lat, lon, ele, ts, **kw) for lat, lon, ele, ts in coords]
    bc = simplify_curve(bc, 0.12)
    bc = separate_duplicate_xy(bc, 0.05)
    ctx.blender_coords = bc

    if (gen_type == 1 or len(ctx.separate_paths) > 1) and gen_type != 4:
        ctx.blender_coords_separate = [
            [convert_to_blender_coordinates(lat, lon, ele, ts, **kw) for lat, lon, ele, ts in path]
            for path in ctx.separate_paths
        ]

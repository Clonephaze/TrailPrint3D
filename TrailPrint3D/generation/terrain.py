"""Terrain creation — shape, elevation fetch, mesh deformation.

Split into two public functions for the modal operator:

* ``create_terrain_mesh(ctx, gen_type)`` — builds the shape on the main thread.
* ``apply_terrain_elevation(ctx, elev_result)`` — applies elevation data and
  extrudes the base (main thread).

The synchronous orchestrator can still call both in sequence with an elevation
fetch in between.
"""

from __future__ import annotations

import time as _time
from typing import TYPE_CHECKING

import bpy  # type: ignore
from mathutils import Vector  # type: ignore

from ..coordinates import convert_to_blender_coordinates, midpoint_spherical, haversine
from ..elevation.base import ElevationResult
from ..geometry.shapes import create_hexagon, create_rectangle, create_circle
from ..geometry.mesh_utils import (
    recalculateNormals,
    transform_MapObject,
    fix_mesh_anomalies,
)
from ..materials import setup_materials
from ..utils import show_message_box

import numpy as np  # type: ignore

if TYPE_CHECKING:
    from ..context import GenerationContext


# Map shape name → creation callable + size transform
_SHAPE_CREATORS = {
    "HEXAGON":            lambda s, n, ns: create_hexagon(s / 2, n, ns),
    "SQUARE":             lambda s, n, ns: create_rectangle(s, s, n, ns),
    "HEXAGON INNER TEXT":  lambda s, n, ns: create_hexagon(s / 2, n, ns),
    "HEXAGON OUTER TEXT":  lambda s, n, ns: create_hexagon(s / 2, n, ns),
    "HEXAGON FRONT TEXT":  lambda s, n, ns: create_hexagon(s / 2, n, ns),
    "CIRCLE":             lambda s, n, ns: create_circle(s / 2, n, ns),
}


# ── Phase 1: create terrain mesh (main thread) ──────────────────────────


def create_terrain_mesh(ctx: GenerationContext, gen_type: int) -> bool:
    """Create the base terrain shape and position it.

    Sets ``ctx.MapObject``.  Returns *True* on success.
    """
    setup_materials()

    # Delete overlapping objects at the centre
    target_2d = Vector((ctx.centerx, ctx.centery))
    for obs in list(bpy.data.objects):
        d = Vector((obs.location.x, obs.location.y)) - target_2d
        if d.length <= 0.1:
            bpy.data.objects.remove(obs, do_unlink=True)

    bpy.ops.object.select_all(action='DESELECT')

    # Create shape
    _t0 = _time.perf_counter()
    creator = _SHAPE_CREATORS.get(ctx.shape, _SHAPE_CREATORS["HEXAGON"])
    MapObject = creator(ctx.size, ctx.name, ctx.num_subdivisions)
    print(f"[TIMING] shape creation (subdiv={ctx.num_subdivisions}): {_time.perf_counter() - _t0:.2f}s, verts={len(MapObject.data.vertices)}")
    ctx.MapObject = MapObject

    recalculateNormals(MapObject)

    # Apply shape rotation
    import math
    MapObject.rotation_euler[2] += math.radians(ctx.shapeRotation)
    MapObject.select_set(True)
    bpy.context.view_layer.objects.active = MapObject
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    # Position
    targetx = ctx.centerx + ctx.xTerrainOffset
    targety = ctx.centery + ctx.yTerrainOffset
    if ctx.scalemode == "COORDINATES" and gen_type == 1:
        midLat, midLon = midpoint_spherical(ctx.scaleLat1, ctx.scaleLon1, ctx.scaleLat2, ctx.scaleLon2)
        targetx, targety, _ = convert_to_blender_coordinates(midLat, midLon, 0, 0)
    transform_MapObject(MapObject, targetx, targety)

    if gen_type == 4:
        ctx.coordinates = ctx.coordinates2

    # Apply final transforms so vertex positions are in world space
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    return True


# ── Phase 2: apply elevation data (main thread) ─────────────────────────


def apply_terrain_elevation(ctx: GenerationContext, result: ElevationResult) -> bool:
    """Apply fetched elevation data to the terrain mesh and extrude the base.

    Expects ``ctx.MapObject`` to already exist.  Returns *True* on success.
    """
    MapObject = ctx.MapObject
    tileVerts = result.elevations
    diff = result.diff

    # Store geographic bounds on context
    ctx.minLat = result.min_lat
    ctx.maxLat = result.max_lat
    ctx.minLon = result.min_lon
    ctx.maxLon = result.max_lon

    # Write scene properties (main thread)
    bpy.context.scene.tp3d["sMapInKm"] = result.map_distance_km
    bpy.context.scene.tp3d["o_verticesMap"] = str(result.vertex_count)

    if len(tileVerts) < 2000:
        show_message_box(
            f"Mesh only has {len(tileVerts)} points. Increase subdivisions for higher resolution",
            "INFO", "Info",
        )

    # Compute autoScale
    if ctx.fixedElevationScale:
        # Fixed mode: terrain relief always spans 10 Blender units (before scaleElevation)
        ctx.autoScale = 10 / (diff / 1000) if diff > 0 else 10
    else:
        # Proportional mode: use horizontal scale so hills keep their real
        # geographic proportions (matches original behaviour).
        ctx.autoScale = ctx.scaleHor if ctx.scaleHor else 1.0
    bpy.context.scene.tp3d["sAutoScale"] = ctx.autoScale

    if not ctx.fixedElevationScale:
        if diff == 0:
            show_message_box("Terrain appears very flat. Area may lack elevation data.", "INFO", "Info")
        elif (diff / 1000) * ctx.autoScale * ctx.scaleElevation < 2:
            show_message_box("Terrain appears fairly flat. Increasing elevation scale may help", "INFO", "Info")

    # Apply elevation to vertices (numpy-vectorised) -------------------------
    mesh = MapObject.data
    n_verts = len(mesh.vertices)
    n_elev = len(tileVerts)

    # Build elevation array, clamping index range
    elev_arr = np.array(tileVerts[:n_verts], dtype=np.float64)
    if n_verts > n_elev:
        elev_arr = np.pad(elev_arr, (0, n_verts - n_elev),
                          mode='edge')  # repeat last value

    z_arr = (elev_arr - ctx.elevationOffset) / 1000.0 * ctx.scaleElevation * ctx.autoScale

    highestZ = float(z_arr.max())

    # Robust "floor" — 2nd percentile so outlier pits don't set the base level
    robust_floor = float(np.percentile(z_arr, 2))

    # Clamp vertices below the robust floor (fill pits so they don't
    # punch through the base plate)
    np.clip(z_arr, robust_floor, None, out=z_arr)

    # Write Z values back into mesh (read all coords, overwrite Z, write back)
    coords_flat = np.empty(n_verts * 3, dtype=np.float64)
    mesh.vertices.foreach_get("co", coords_flat)
    coords_flat[2::3] = z_arr
    mesh.vertices.foreach_set("co", coords_flat)
    mesh.update()

    # Base gap: terrain floor sits ~2 mm above the plate top surface.
    # For shapes with a back-plate, the plate gets pushed up by
    # plateInsertValue (so the map seats into a groove).  The terrain
    # base must be thick enough to clear that raised plate.
    BASE_GAP_MM = 2.0
    plate_shapes = {"HEXAGON OUTER TEXT", "OCTAGON OUTER TEXT", "HEXAGON FRONT TEXT"}
    insert_allowance = ctx.plateInsertValue if ctx.shape in plate_shapes else 0.0
    effective_thickness = BASE_GAP_MM + insert_allowance

    ctx.lowestZ = robust_floor
    ctx.highestZ = highestZ
    ctx.additionalExtrusion = robust_floor
    bpy.context.scene.tp3d["sAdditionalExtrusion"] = ctx.additionalExtrusion
    ctx.effectiveThickness = effective_thickness

    _t0 = _time.perf_counter()
    fix_mesh_anomalies(MapObject, threshold=0.1)
    print(f"[TIMING] fix_mesh_anomalies: {_time.perf_counter() - _t0:.2f}s")

    # Extrude base + shift to z=0 + dissolve — single EDIT session ──────────
    _t0 = _time.perf_counter()
    bpy.context.view_layer.objects.active = MapObject
    bpy.ops.object.mode_set(mode='EDIT')

    # 1) Extrude the bottom face
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move()
    bpy.ops.mesh.dissolve_faces()
    bpy.ops.transform.translate(value=(0, 0, -1))
    bpy.ops.object.mode_set(mode='OBJECT')

    # 2) Position the extruded base face
    obj = bpy.context.object
    mesh = obj.data
    for face in mesh.polygons:
        if face.select:
            for vi in face.vertices:
                mesh.vertices[vi].co.z = ctx.additionalExtrusion - effective_thickness

    # 3) Shift everything so bottom == 0, dissolve flat areas — back to EDIT once
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.translate(value=(0, 0, -ctx.additionalExtrusion + effective_thickness))

    # Dissolve coplanar faces while still in edit mode — reduces poly count
    # on flat areas but creates large faces that hurt per-face paint (OSM
    # overlays, multi-colour 3MF).  Disabled for now; can be re-enabled
    # behind a property toggle if needed.
    # import math as _math
    # bpy.ops.mesh.dissolve_limited(angle_limit=_math.radians(0.5))
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.context.scene.cursor.location = obj.location
    recalculateNormals(obj)
    print(f"[TIMING] extrude+shift+dissolve+normals: {_time.perf_counter() - _t0:.2f}s")

    # Compute map scale for display
    coords = ctx.coordinates
    lat1, lon1 = coords[0][0], coords[0][1]
    lat2, lon2 = coords[-1][0], coords[-1][1]
    mscale = (haversine(lat1, lon1, lat2, lon2) / ctx.size) * 1_000_000
    bpy.context.scene.tp3d["o_mapScale"] = f"{mscale:.0f}"

    return True


# ── Convenience: combined (used by synchronous orchestrator) ─────────────


def create_terrain(ctx: GenerationContext, gen_type: int) -> bool:
    """All-in-one: create shape → fetch elevation → apply.  Blocks on network."""
    from ..elevation.base import get_tile_elevation

    if not create_terrain_mesh(ctx, gen_type):
        return False

    tileVerts, diff, rawLow, rawHigh, minLat, maxLat, minLon, maxLon = get_tile_elevation(
        ctx.MapObject,
        api=ctx.api_index,
        dataset=ctx.dataset,
        opentopoAddress=ctx.opentopoAddress,
        num_subdivisions=ctx.num_subdivisions,
    )

    result = ElevationResult(
        elevations=tileVerts, diff=diff, lowest=rawLow, highest=rawHigh,
        min_lat=minLat, max_lat=maxLat, min_lon=minLon, max_lon=maxLon,
        map_distance_km=bpy.context.scene.tp3d.get("sMapInKm", 0),
        vertex_count=len(ctx.MapObject.data.vertices),
    )
    return apply_terrain_elevation(ctx, result)

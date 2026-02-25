"""Top-level orchestrator — synchronous fallback for batch generation.

The modal operator in ``operators/generation.py`` is the primary entry
point for single-file generation (with progress overlay and threaded
elevation fetch).  This module remains as a simpler synchronous path
used by ``MY_OT_BatchGeneration``.
"""

from __future__ import annotations

import os
import time

import bpy  # type: ignore

from ..context import GenerationContext
from .validation import validate_inputs
from .loading import load_gps_data, prepare_blender_coords, reproject_after_elevation
from .terrain import create_terrain
from .trail import create_trail
from .decorations import apply_decorations
from .finalize import finalize


def run_generation(gen_type: int = 0) -> None:
    """Synchronous entry point — blocks until generation is complete.

    Parameters
    ----------
    gen_type : int
        0 = single GPX, 1 = batch, 2 = center-point map, 3 = two-point map,
        4 = center-point + path.
    """
    start_time = time.time()

    # Build context from scene properties
    ctx = GenerationContext.from_scene(gen_type)

    # Resolve default export path
    if not ctx.exportPath and ctx.gpx_file_path:
        gpx_dir = os.path.dirname(ctx.gpx_file_path)
        gpx_base = os.path.splitext(os.path.basename(ctx.gpx_file_path))[0]
        ctx.exportPath = os.path.join(gpx_dir, gpx_base)

    ctx.exportPath = bpy.path.abspath(ctx.exportPath) if ctx.exportPath else ""
    if ctx.gpx_file_path:
        ctx.gpx_file_path = bpy.path.abspath(ctx.gpx_file_path)
    if ctx.gpx_chain_path:
        ctx.gpx_chain_path = bpy.path.abspath(ctx.gpx_chain_path)

    # Self-hosted OpenTopo
    ctx.opentopoAddress = "https://api.opentopodata.org/v1/"
    if ctx.selfHosted and ctx.api_index == 1:
        ctx.opentopoAddress = ctx.selfHosted

    # Validate
    if not validate_inputs(ctx, gen_type):
        return

    # Auto-name
    if not ctx.name:
        if gen_type in (0, 4) and ctx.gpx_file_path:
            ctx.name = os.path.splitext(os.path.basename(ctx.gpx_file_path))[0]
        elif gen_type == 1 and ctx.gpx_chain_path:
            ctx.name = os.path.splitext(os.path.basename(os.path.normpath(ctx.gpx_chain_path)))[0]
        else:
            ctx.name = "Terrain"

    # Console hints
    if ctx.singleColorMode:
        ctx.overwritePathElevation = False

    # Ensure we're in object mode
    if bpy.context.object and bpy.context.object.mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.scene.tool_settings.use_mesh_automerge = False

    # Phase 1 — Load GPS
    if not load_gps_data(ctx, gen_type):
        return

    # Pick up elevation offset computed by GPS parsers
    ctx.elevationOffset = bpy.context.scene.tp3d.get("sElevationOffset", 0.0)

    # Phase 2 — Coordinate prep
    prepare_blender_coords(ctx, gen_type)

    # Phase 3 — Terrain (blocks during elevation fetch)
    if not create_terrain(ctx, gen_type):
        return

    # Re-project blender coords with autoScale
    reproject_after_elevation(ctx, gen_type)

    # Phase 4 — Trail
    if gen_type not in (2, 3):
        if not create_trail(ctx, gen_type):
            return

    # Phase 5 — Decorations
    apply_decorations(ctx)

    # Phase 6 — Finalize
    finalize(ctx, gen_type, start_time)

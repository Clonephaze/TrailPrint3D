"""Final export, material assignment, metadata, and cleanup."""

from __future__ import annotations

import time
import time as _time
from typing import TYPE_CHECKING

import bpy  # type: ignore

from ..elevation.counter import load_counter
from ..export import export_object
from ..metadata import write_metadata
from ..osm.coloring import coloring_main
from ..utils import zoom_camera_to_selected

if TYPE_CHECKING:
    from ..context import GenerationContext


def finalize(ctx: GenerationContext, gen_type: int, start_time: float) -> None:
    """Assign materials, export STL, write metadata, display stats."""
    obj = ctx.MapObject
    curveObj = ctx.curveObj

    # Zoom viewport
    zoom_camera_to_selected(obj)
    bpy.ops.object.select_all(action='DESELECT')

    # Material assignment
    mat_base = bpy.data.materials.get("BASE")
    obj.data.materials.clear()
    obj.data.materials.append(mat_base)

    if curveObj:
        mat_trail = bpy.data.materials.get("TRAIL")
        curveObj.data.materials.clear()
        curveObj.data.materials.append(mat_trail)

    # Switch viewport to material preview
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'

    # OSM colour overlays
    _t0 = _time.perf_counter()
    tp = bpy.context.scene.tp3d
    if tp.col_wActive:
        coloring_main(obj, "WATER",
                       minLat=ctx.minLat, maxLat=ctx.maxLat,
                       minLon=ctx.minLon, maxLon=ctx.maxLon)
    if tp.col_fActive:
        coloring_main(obj, "FOREST",
                       minLat=ctx.minLat, maxLat=ctx.maxLat,
                       minLon=ctx.minLon, maxLon=ctx.maxLon)
    if tp.col_cActive:
        coloring_main(obj, "CITY",
                       minLat=ctx.minLat, maxLat=ctx.maxLat,
                       minLon=ctx.minLon, maxLon=ctx.maxLon)
    osm_t = _time.perf_counter() - _t0
    if osm_t > 0.5:
        print(f"[TIMING] OSM coloring: {osm_t:.2f}s")

    # Export (only if auto-export is enabled)
    auto_export = getattr(bpy.context.scene.tp3d, 'autoExport', False)
    export_path = ctx.exportPath if auto_export else None
    if export_path and curveObj:
        export_object(curveObj, export_path)
    if export_path:
        export_object(obj, export_path)

    shape = ctx.shape
    if shape in ("HEXAGON INNER TEXT", "HEXAGON OUTER TEXT", "OCTAGON OUTER TEXT", "HEXAGON FRONT TEXT"):
        tobj = ctx.textobj
        if tobj:
            mat_name = "TRAIL" if shape == "HEXAGON INNER TEXT" else "WHITE"
            mat = bpy.data.materials.get(mat_name)
            tobj.data.materials.clear()
            tobj.data.materials.append(mat)
            if export_path:
                export_object(tobj, export_path)

    if shape in ("HEXAGON OUTER TEXT", "OCTAGON OUTER TEXT", "HEXAGON FRONT TEXT"):
        plobj = ctx.plateobj
        if plobj:
            mat = bpy.data.materials.get("BLACK")
            plobj.data.materials.clear()
            plobj.data.materials.append(mat)
            write_metadata(plobj, type="PLATE")
            if export_path:
                export_object(plobj, export_path)

    # Timing
    duration = time.time() - start_time
    bpy.context.scene.tp3d["o_time"] = f"Script ran for {duration:.0f} seconds"

    # Metadata
    write_metadata(obj)
    if gen_type != 2 and curveObj:
        write_metadata(curveObj, type="TRAIL")

    # API counter display
    cnt_otd, _, cnt_oe, _ = load_counter()
    if cnt_otd < 1000:
        bpy.context.scene.tp3d["o_apiCounter_OpenTopoData"] = f"API Limit: {cnt_otd:.0f}/1000 daily"
    else:
        bpy.context.scene.tp3d["o_apiCounter_OpenTopoData"] = f"API Limit: {cnt_otd:.0f}/1000 (daily limit reached)"

    if cnt_oe < 1000:
        bpy.context.scene.tp3d["o_apiCounter_OpenElevation"] = f"API Limit: {cnt_oe:.0f}/1000 Monthly"
    else:
        bpy.context.scene.tp3d["o_apiCounter_OpenElevation"] = f"API Limit: {cnt_oe:.0f}/1000 (Monthly limit reached)"

    print("Finished")

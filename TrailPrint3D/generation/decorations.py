"""Decorations — text shapes, plate-insert, single-color, flags."""

from __future__ import annotations

import time as _time
from typing import TYPE_CHECKING

import bpy  # type: ignore

from ..export import export_object
from ..flags import create_flag, find_path_endpoints
from ..geometry.boolean_ops import plateInsert, single_color_mode
from ..text.layouts import HexagonInnerText, HexagonOuterText, HexagonFrontText, OctagonOuterText

if TYPE_CHECKING:
    from ..context import GenerationContext


def apply_decorations(ctx: GenerationContext) -> None:
    """Run all post-terrain decoration steps (text, plates, flags)."""
    _t0 = _time.perf_counter()
    obj = ctx.MapObject
    curveObj = ctx.curveObj
    shape = ctx.shape

    # Text layouts
    _t1 = _time.perf_counter()
    if shape == "HEXAGON INNER TEXT":
        HexagonInnerText(ctx)
    elif shape == "HEXAGON OUTER TEXT":
        HexagonOuterText(ctx)
        obj.location.z += ctx.plateThickness
        if curveObj:
            curveObj.location.z += ctx.plateThickness
    elif shape == "OCTAGON OUTER TEXT":
        OctagonOuterText(ctx)
        obj.location.z += ctx.plateThickness
        if curveObj:
            curveObj.location.z += ctx.plateThickness
    elif shape == "HEXAGON FRONT TEXT":
        HexagonFrontText(ctx)
        obj.location.z += ctx.plateThickness
        if curveObj:
            curveObj.location.z += ctx.plateThickness
    print(f"[TIMING]   text layout: {_time.perf_counter() - _t1:.2f}s")

    # Plate insert (before single-color so path doesn't affect plate)
    _t1 = _time.perf_counter()
    dist = bpy.context.scene.tp3d.plateInsertValue
    if dist > 0 and shape in ("HEXAGON OUTER TEXT", "OCTAGON OUTER TEXT", "HEXAGON FRONT TEXT"):
        plate = bpy.data.objects.get(ctx.name + "_Plate")
        if plate:
            plateInsert(plate, obj, ctx.size)
            text = bpy.data.objects.get(ctx.name + "_Text")
            if text:
                text.location.z += dist
    print(f"[TIMING]   plate insert: {_time.perf_counter() - _t1:.2f}s")

    # Single-color mode (after plate so path merge doesn't affect plate)
    _t1 = _time.perf_counter()
    if ctx.singleColorMode and curveObj:
        single_color_mode(curveObj, obj.name, ctx.pathThickness)
    if ctx.singleColorMode:
        print(f"[TIMING]   single-color: {_time.perf_counter() - _t1:.2f}s")

    # Flags
    auto_export = getattr(bpy.context.scene.tp3d, 'autoExport', False)
    addFlags = bpy.context.scene.tp3d.get("addFlags", False)
    if addFlags and curveObj:
        flagHeight = bpy.context.scene.tp3d.get("flagHeight", 5.0)
        flagWidth = bpy.context.scene.tp3d.get("flagWidth", 3.0)
        try:
            start_pt, end_pt = find_path_endpoints(curveObj)
            if start_pt and end_pt:
                sf = create_flag(ctx.name + "_StartFlag", start_pt, "START", flagHeight, flagWidth)
                if sf and auto_export:
                    export_object(sf)
                ff = create_flag(ctx.name + "_FinishFlag", end_pt, "FINISH", flagHeight, flagWidth)
                if ff and auto_export:
                    export_object(ff)
        except (RuntimeError, ValueError, TypeError) as e:
            print(f"Warning: Flag creation failed: {e}")

    print(f"[TIMING] decorations: {_time.perf_counter() - _t0:.2f}s")

"""Trail / path curve creation and projection onto terrain."""

from __future__ import annotations

from typing import TYPE_CHECKING

import bpy  # type: ignore

from ..geometry.curves import create_curve_from_coordinates, RaycastCurveToMesh
from ..utils import show_message_box

if TYPE_CHECKING:
    from ..context import GenerationContext


def create_trail(ctx: GenerationContext, gen_type: int) -> bool:
    """Create the GPS trail curve.  Project it onto the terrain if requested.

    Returns *True* on success.
    """
    curveObj = None

    try:
        bc = ctx.blender_coords
        bcs = getattr(ctx, "blender_coords_separate", None)

        if gen_type == 0 or (bcs and len(bcs) == 1) or gen_type == 4:
            create_curve_from_coordinates(bc, ctx.name + "_Trail", ctx.pathThickness)
            curveObj = bpy.context.view_layer.objects.active
        elif (gen_type == 1 or (bcs and len(bcs) > 1)) and gen_type != 4:
            for crds in bcs:
                create_curve_from_coordinates(crds, ctx.name + "_Trail", ctx.pathThickness)
            bpy.ops.object.join()
            curveObj = bpy.context.view_layer.objects.active
    except (RuntimeError, ValueError, TypeError) as e:
        show_message_box(f"Error creating curve: {e}")
        return False

    ctx.curveObj = curveObj
    bpy.ops.object.select_all(action='DESELECT')

    if curveObj is None:
        return True  # type 2/3 may have no trail — that's OK

    # Snap trail onto terrain surface, or keep raw GPS elevation
    if ctx.overwritePathElevation:
        # Raycast projects the curve onto the already-shifted terrain mesh,
        # so the trail ends up at the correct final Z — no extra shift needed.
        RaycastCurveToMesh(curveObj, ctx.MapObject)
    else:
        # Raw GPS Z values are in the pre-shift coordinate system;
        # apply the same Z translation that was applied to the terrain.
        effective_thickness = getattr(ctx, 'effectiveThickness', ctx.minThickness)
        bpy.context.view_layer.objects.active = curveObj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.transform.translate(value=(0, 0, -ctx.additionalExtrusion + effective_thickness))
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.context.view_layer.objects.active = curveObj
    curveObj.select_set(True)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")

    return True

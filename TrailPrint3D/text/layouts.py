"""Text layout functions for different shape types.

Each layout creates text objects (name, elevation, length, duration),
positions them on the shape, scales to mm sizes, converts to mesh,
joins, and returns (textobj, plateobj) where applicable.

All layouts accept a ``ctx`` (:class:`~TrailPrint3D.context.GenerationContext`)
so they no longer read globals.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import bpy  # type: ignore

from .base import create_text, update_text_object, convert_text_to_mesh
from ..geometry.mesh_utils import transform_MapObject

if TYPE_CHECKING:
    from ..context import GenerationContext


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _get_text_sizes():
    """Return (textSize, textSize2) from scene properties."""
    tp = bpy.context.scene.tp3d
    ts = tp.textSize
    ts2 = tp.textSizeTitle
    if ts2 == 0:
        ts2 = ts
    return ts, ts2


def _scale_text_objects(tName, tElevation, tLength, tDuration, textSize, textSize2):
    """Uniformly scale the four text objects to their target mm sizes."""
    bpy.context.view_layer.update()
    current = tName.dimensions.y
    if current == 0:
        current = tElevation.dimensions.y
    if current == 0:
        current = tLength.dimensions.y
    if current == 0:
        current = 5

    sf_title = textSize2 / current
    tName.scale.x *= sf_title
    tName.scale.y *= sf_title

    sf = textSize / current
    for obj in (tElevation, tLength, tDuration):
        obj.scale.x *= sf
        obj.scale.y *= sf


def _overwrite_stats(ctx: GenerationContext):
    """Apply user overrides for length / height / time strings."""
    if ctx.overwriteLength:
        update_text_object("t_length", ctx.overwriteLength)
    if ctx.overwriteHeight:
        update_text_object("t_elevation", ctx.overwriteHeight)
    if ctx.overwriteTime:
        update_text_object("t_duration", ctx.overwriteTime)


def _join_text_objects(*objs):
    """Select, join, and origin-set the given objects. Returns the active (joined) object."""
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    return objs[0]


def _apply_shape_rotation(obj, shapeRotation: float):
    """Rotate *obj* around Z by *shapeRotation* degrees and apply."""
    obj.rotation_euler[2] += math.radians(shapeRotation)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')


def _create_outer_plate(plate_name: str, outersize: float, thickness: float,
                        centerx: float, centery: float,
                        num_sides: int = 6, angle_offset: float = 0.0):
    """Create an extruded polygon plate and position it."""
    verts, faces = [], []
    for i in range(num_sides):
        angle = math.radians(360 / num_sides * i + angle_offset)
        x = outersize / 2 * math.cos(angle)
        y = outersize / 2 * math.sin(angle)
        verts.append((x, y, 0))
    verts.append((0, 0, 0))
    faces = [[i, (i + 1) % num_sides, num_sides] for i in range(num_sides)]

    mesh = bpy.data.meshes.new(plate_name)
    obj = bpy.data.objects.new(plate_name, mesh)
    bpy.context.collection.objects.link(obj)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj.name = plate_name
    obj.data.name = plate_name

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move()
    bpy.ops.transform.translate(value=(0, 0, -8))
    bpy.ops.object.mode_set(mode='OBJECT')

    for face in obj.data.polygons:
        if face.select:
            for vi in face.vertices:
                obj.data.vertices[vi].co.z = -thickness

    transform_MapObject(obj, centerx, centery)
    return obj


# ---------------------------------------------------------------------------
# Layout functions
# ---------------------------------------------------------------------------

def HexagonInnerText(ctx: GenerationContext):
    """Text inside the hexagon map area (no plate)."""
    textSize, textSize2 = _get_text_sizes()
    dist = ctx.size / 2 - ctx.size / 2 * (1 - ctx.pathScale) / 2
    temp_y = math.sin(math.radians(90)) * (dist * math.cos(math.radians(30)))

    tName = create_text("t_name", "Name", (0, temp_y, 0.1), 1)

    for text_name, angle in zip(
        ["t_length", "t_elevation", "t_duration"], [210, 270, 330]
    ):
        angle_centered = angle + 90
        x = math.cos(math.radians(angle)) * (dist * math.cos(math.radians(30)))
        y = math.sin(math.radians(angle)) * (dist * math.cos(math.radians(30)))
        rot_z = math.radians(angle_centered)
        create_text(text_name, text_name.split("_")[1].capitalize(), (x, y, 0.1), 1, (0, 0, rot_z), 100)

    tElevation = bpy.data.objects.get("t_elevation")
    tLength = bpy.data.objects.get("t_length")
    tDuration = bpy.data.objects.get("t_duration")

    for o in (tName, tElevation, tLength, tDuration):
        transform_MapObject(o, ctx.centerx, ctx.centery)

    update_text_object("t_name", ctx.name)
    update_text_object("t_elevation", f"{ctx.total_elevation:.2f} hm")
    update_text_object("t_length", f"{ctx.total_length:.2f} km")
    update_text_object("t_duration", ctx.time_str)
    _overwrite_stats(ctx)

    _scale_text_objects(tName, tElevation, tLength, tDuration, textSize, textSize2)

    map_name = ctx.MapObject.name
    convert_text_to_mesh("t_name", map_name)
    convert_text_to_mesh("t_elevation", map_name)
    convert_text_to_mesh("t_length", map_name)
    convert_text_to_mesh("t_duration", map_name)

    _join_text_objects(tName, tElevation, tLength, tDuration)
    tName.name = ctx.name + "_Text"
    _apply_shape_rotation(tName, ctx.shapeRotation)

    ctx.textobj = tName


def HexagonOuterText(ctx: GenerationContext):
    """Text on a hexagonal outer-plate border."""
    textSize, textSize2 = _get_text_sizes()
    outersize = ctx.size * (1 + ctx.outerBorderSize / 100)

    outerHex = _create_outer_plate(
        ctx.name, outersize, ctx.plateThickness,
        ctx.centerx, ctx.centery, num_sides=6,
    )

    dist = (outersize - ctx.size) / 4 + ctx.size / 2
    ap = ctx.text_angle_preset

    for i, (text_name, angle) in enumerate(zip(
        ["t_name", "t_length", "t_elevation", "t_duration"],
        [90 + ap, 210 + ap, 270 + ap, 330 + ap],
    )):
        angle_centered = angle + 90
        x = math.cos(math.radians(angle)) * (dist * math.cos(math.radians(30)))
        y = math.sin(math.radians(angle)) * (dist * math.cos(math.radians(30)))
        rot_z = math.radians(angle_centered)
        if i == 0:
            rot_z += math.radians(180)
        create_text(text_name, text_name.split("_")[1].capitalize(), (x, y, 1.4), 1, (0, 0, rot_z), 0.4)

    tName = bpy.data.objects.get("t_name")
    tElevation = bpy.data.objects.get("t_elevation")
    tLength = bpy.data.objects.get("t_length")
    tDuration = bpy.data.objects.get("t_duration")

    for o in (tName, tElevation, tLength, tDuration):
        transform_MapObject(o, ctx.centerx, ctx.centery)

    update_text_object("t_name", ctx.name)
    update_text_object("t_elevation", f"{ctx.total_elevation:.2f} hm")
    update_text_object("t_length", f"{ctx.total_length:.2f} km")
    update_text_object("t_duration", ctx.time_str)
    _overwrite_stats(ctx)

    _scale_text_objects(tName, tElevation, tLength, tDuration, textSize, textSize2)

    hex_name = outerHex.name
    convert_text_to_mesh("t_name", hex_name, False)
    convert_text_to_mesh("t_elevation", hex_name, False)
    convert_text_to_mesh("t_length", hex_name, False)
    convert_text_to_mesh("t_duration", hex_name, False)

    _join_text_objects(tName, tElevation, tLength, tDuration)
    tName.name = ctx.name + "_Text"
    outerHex.name = ctx.name + "_Plate"

    tName.location.z += ctx.plateThickness
    outerHex.location.z += ctx.plateThickness

    _apply_shape_rotation(outerHex, ctx.shapeRotation)
    _apply_shape_rotation(tName, ctx.shapeRotation)

    ctx.plateobj = outerHex
    ctx.textobj = tName


def HexagonFrontText(ctx: GenerationContext):
    """Text on the front face of a hexagonal outer-plate."""
    textSize, textSize2 = _get_text_sizes()
    outersize = ctx.size * (1 + ctx.outerBorderSize / 100)

    outerHex = _create_outer_plate(
        ctx.name, outersize, ctx.plateThickness,
        ctx.centerx, ctx.centery, num_sides=6,
    )

    dist = outersize / 2
    ap = ctx.text_angle_preset

    for i, (text_name, angle) in enumerate(zip(
        ["t_name", "t_length", "t_elevation", "t_duration"],
        [90 + ap, 210 + ap, 270 + ap, 330 + ap],
    )):
        angle_centered = angle + 90
        x = math.cos(math.radians(angle)) * (dist * math.cos(math.radians(30)))
        y = math.sin(math.radians(angle)) * (dist * math.cos(math.radians(30)))
        rot_z = math.radians(angle_centered)
        create_text(
            text_name, text_name.split("_")[1].capitalize(),
            (x, y, ctx.minThickness / 2 - ctx.plateThickness / 2), 1,
            (math.radians(90), 0, rot_z), 0.4,
        )

    tName = bpy.data.objects.get("t_name")
    tElevation = bpy.data.objects.get("t_elevation")
    tLength = bpy.data.objects.get("t_length")
    tDuration = bpy.data.objects.get("t_duration")

    for o in (tName, tElevation, tLength, tDuration):
        transform_MapObject(o, ctx.centerx, ctx.centery)

    update_text_object("t_name", ctx.name)
    update_text_object("t_elevation", f"{ctx.total_elevation:.2f} hm")
    update_text_object("t_length", f"{ctx.total_length:.2f} km")
    update_text_object("t_duration", ctx.time_str)
    _overwrite_stats(ctx)

    _scale_text_objects(tName, tElevation, tLength, tDuration, textSize, textSize2)

    hex_name = outerHex.name
    convert_text_to_mesh("t_name", hex_name, False)
    convert_text_to_mesh("t_elevation", hex_name, False)
    convert_text_to_mesh("t_length", hex_name, False)
    convert_text_to_mesh("t_duration", hex_name, False)

    _join_text_objects(tName, tElevation, tLength, tDuration)
    tName.name = ctx.name + "_Text"
    outerHex.name = ctx.name + "_Plate"

    tName.location.z += ctx.plateThickness
    outerHex.location.z += ctx.plateThickness

    _apply_shape_rotation(outerHex, ctx.shapeRotation)
    _apply_shape_rotation(tName, ctx.shapeRotation)

    ctx.plateobj = outerHex
    ctx.textobj = tName


def OctagonOuterText(ctx: GenerationContext):
    """Text on an octagonal outer-plate border."""
    textSize, textSize2 = _get_text_sizes()
    outersize = ctx.size * (1 + ctx.outerBorderSize / 100)

    outerOct = _create_outer_plate(
        ctx.name, outersize, ctx.plateThickness,
        ctx.centerx, ctx.centery,
        num_sides=8, angle_offset=22.5,
    )

    dist = (outersize - ctx.size) / 4 + ctx.size / 2
    ap = ctx.text_angle_preset

    for i, (text_name, angle) in enumerate(zip(
        ["t_name", "t_length", "t_elevation", "t_duration"],
        [90 + ap, 225 + ap, 270 + ap, 315 + ap],
    )):
        angle_centered = angle + 90
        x = math.cos(math.radians(angle)) * (dist * math.cos(math.radians(22.5)))
        y = math.sin(math.radians(angle)) * (dist * math.cos(math.radians(22.5)))
        rot_z = math.radians(angle_centered)
        if i == 0:
            rot_z += math.radians(180)
        create_text(text_name, text_name.split("_")[1].capitalize(), (x, y, 1.4), 1, (0, 0, rot_z), 0.4)

    tName = bpy.data.objects.get("t_name")
    tElevation = bpy.data.objects.get("t_elevation")
    tLength = bpy.data.objects.get("t_length")
    tDuration = bpy.data.objects.get("t_duration")

    for o in (tName, tElevation, tLength, tDuration):
        transform_MapObject(o, ctx.centerx, ctx.centery)

    update_text_object("t_name", ctx.name)
    update_text_object("t_elevation", f"{ctx.total_elevation:.2f} hm")
    update_text_object("t_length", f"{ctx.total_length:.2f} km")
    update_text_object("t_duration", ctx.time_str)
    _overwrite_stats(ctx)

    _scale_text_objects(tName, tElevation, tLength, tDuration, textSize, textSize2)

    oct_name = outerOct.name
    convert_text_to_mesh("t_name", oct_name, False)
    convert_text_to_mesh("t_elevation", oct_name, False)
    convert_text_to_mesh("t_length", oct_name, False)
    convert_text_to_mesh("t_duration", oct_name, False)

    _join_text_objects(tName, tElevation, tLength, tDuration)
    tName.name = ctx.name + "_Text"
    outerOct.name = ctx.name + "_Plate"

    tName.location.z += ctx.plateThickness
    outerOct.location.z += ctx.plateThickness

    _apply_shape_rotation(outerOct, ctx.shapeRotation)
    _apply_shape_rotation(tName, ctx.shapeRotation)

    ctx.plateobj = outerOct
    ctx.textobj = tName

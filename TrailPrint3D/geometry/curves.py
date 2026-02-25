"""Curve creation, simplification, and raycasting onto meshes."""

import bpy  # type: ignore
from mathutils import Vector  # type: ignore


def create_curve_from_coordinates(coordinates, name="Trail", pathThickness=1.2):
    """Create a bevel-depth curve from *(x, y, z)* points and add a Remesh modifier."""
    curve_data = bpy.data.curves.new('GPX_Curve', type='CURVE')
    curve_data.dimensions = '3D'
    polyline = curve_data.splines.new('POLY')
    polyline.points.add(count=len(coordinates) - 1)

    for i, coord in enumerate(coordinates):
        polyline.points[i].co = (coord[0], coord[1], coord[2], 1)

    curve_object = bpy.data.objects.new('GPX_Curve_Object', curve_data)
    bpy.context.collection.objects.link(curve_object)
    curve_object.data.bevel_depth = pathThickness / 2
    curve_object.data.bevel_resolution = 4

    mod = curve_object.modifiers.new(name="Remesh", type="REMESH")
    mod.mode = "VOXEL"
    mod.voxel_size = 0.05 * pathThickness * 10 / 2
    mod.adaptivity = 0.0
    curve_object.data.use_fill_caps = True

    curve_object.data.name = name + "_Trail"
    curve_object.name = name + "_Trail"

    curve_object.select_set(True)
    bpy.context.view_layer.objects.active = curve_object

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


def simplify_curve(points_with_extra, min_distance=0.1):
    """Remove points closer than *min_distance* to keep only significant changes."""
    if not points_with_extra:
        return []

    simplified = [points_with_extra[0]]
    last_xyz = Vector(points_with_extra[0][:3])
    skipped = 0

    for pt in points_with_extra[1:]:
        current_xyz = Vector(pt[:3])
        if (current_xyz - last_xyz).length >= min_distance:
            simplified.append(pt)
            last_xyz = current_xyz
        else:
            skipped += 1

    print(f"Smooth curve: Removed {skipped} vertices")
    return simplified


def RaycastCurveToMesh(curve_obj, mesh_obj):
    """Project every curve point downward (−Z) onto *mesh_obj* surface."""
    offset = Vector((0, 0, 100))
    for spline in curve_obj.data.splines:
        if spline.type == 'BEZIER':
            for p in spline.bezier_points:
                p.co += offset
                p.handle_left += offset
                p.handle_right += offset
        else:
            for p in spline.points:
                p.co = (p.co.x, p.co.y, p.co.z + offset.z, p.co.w)

    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_mesh_obj = mesh_obj.evaluated_get(depsgraph)

    curve_world = curve_obj.matrix_world
    curve_world_inv = curve_world.inverted()
    mesh_world = eval_mesh_obj.matrix_world
    mesh_world_inv = mesh_world.inverted()

    direction_world = Vector((0, 0, -1))
    direction_local = (mesh_world_inv.to_3x3() @ direction_world).normalized()

    for spline in curve_obj.data.splines:
        points = spline.bezier_points if spline.type == 'BEZIER' else spline.points

        for point in points:
            co_world = (
                curve_world @ point.co
                if spline.type == 'BEZIER'
                else curve_world @ point.co.xyz
            )
            co_local = mesh_world_inv @ co_world
            success, hit_loc, normal, face_index = eval_mesh_obj.ray_cast(co_local, direction_local)

            if success:
                hit_world = mesh_world @ hit_loc
                local_hit = curve_world_inv @ hit_world
                if spline.type == 'BEZIER':
                    point.co = local_hit
                    point.handle_left_type = point.handle_right_type = 'AUTO'
                else:
                    point.co = (local_hit.x, local_hit.y, local_hit.z, 1.0)

    bpy.context.view_layer.objects.active = curve_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.curve.smooth()
    bpy.ops.object.mode_set(mode='OBJECT')

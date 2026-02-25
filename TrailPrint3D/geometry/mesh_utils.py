"""Mesh utilities — normals, face selection, anomaly fixing, transforms."""

import bmesh  # type: ignore
import bpy  # type: ignore


def recalculateNormals(obj):
    """Recalculate outward-facing normals for *obj*."""
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def selectBottomFaces(obj):
    """Select faces whose normal points downward (z < −0.99)."""
    if obj is None or obj.type != 'MESH':
        raise Exception("Please select a mesh object.")
    bpy.ops.object.mode_set(mode='EDIT')
    mesh = bmesh.from_edit_mesh(obj.data)
    bmesh.ops.recalc_face_normals(mesh, faces=mesh.faces)
    for f in mesh.faces:
        f.select = f.normal.normalized().z < -0.99
    bmesh.update_edit_mesh(obj.data, loop_triangles=False)


def selectTopFaces(obj):
    """Select faces whose normal points upward (z > 0.99)."""
    if obj is None or obj.type != 'MESH':
        raise Exception("Please select a mesh object.")
    bpy.ops.object.mode_set(mode='EDIT')
    mesh = bmesh.from_edit_mesh(obj.data)
    bmesh.ops.recalc_face_normals(mesh, faces=mesh.faces)
    for f in mesh.faces:
        f.select = f.normal.normalized().z > 0.99
    bmesh.update_edit_mesh(obj.data, loop_triangles=False)


def transform_MapObject(obj, newX, newY):
    """Translate *obj* by *(newX, newY)* in the XY plane."""
    obj.location.x += newX
    obj.location.y += newY


def fix_mesh_anomalies(obj, threshold=0.1):
    """Remove doubles and smooth the terrain surface.

    The Z-spike detection loop has been removed — outlier pits are already
    handled by the robust-floor clamp in ``apply_terrain_elevation``.
    Uses bmesh for all operations to avoid expensive modifier-apply cycles.
    """
    if obj.type != 'MESH':
        return

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)

    # Remove doubles (fast)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=threshold * 0.01)

    # Light smooth pass — bmesh-native (avoids modifier apply overhead)
    bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.5,
                          use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.5,
                          use_axis_x=True, use_axis_y=True, use_axis_z=True)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.update_edit_mesh(obj.data)
    bm.free()
    bpy.ops.object.mode_set(mode='OBJECT')


def delete_non_manifold(obj):
    """Select and delete non-manifold vertices."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_non_manifold()
    bm = bmesh.from_edit_mesh(obj.data)
    bm.normal_update()
    bmesh.update_edit_mesh(obj.data, loop_triangles=True)
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.object.mode_set(mode='OBJECT')

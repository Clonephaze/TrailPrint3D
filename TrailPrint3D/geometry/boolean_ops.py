"""Boolean operations — plate insert, merge, trail intersection, single-color mode."""

import time as _time

import bmesh  # type: ignore
import bpy  # type: ignore
from mathutils import Vector  # type: ignore

from .mesh_utils import recalculateNormals
from ..metadata import write_metadata


def plateInsert(plate, map_obj, size=100, tolerance=0.2, dist=2.0):
    """Subtract an enlarged map copy from *plate* to create an inset groove."""
    map_copy = map_obj.copy()
    map_copy.data = map_obj.data.copy()
    bpy.context.collection.objects.link(map_copy)
    map_copy.scale *= (size + tolerance) / size

    plate.location.z += dist

    bpy.ops.object.select_all(action="DESELECT")
    plate.select_set(True)
    bpy.context.view_layer.objects.active = plate

    mod = plate.modifiers.new(name="Boolean", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.solver = "MANIFOLD"
    mod.object = map_copy
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

    bpy.data.objects.remove(map_copy, do_unlink=True)


def single_color_mode(crv, mapName, pathThickness=1.2, tolerance=0.2):
    """Embed the path curve into the map for single-color 3D printing.

    1. Convert curve to mesh + intersect with map
    2. Create thicker copy → subtract from map → groove
    3. Place original path flush in groove

    Uses a decimated copy of the map for INTERSECT operations (only need
    approximate shape), and the full-res map only for the final DIFFERENCE
    that actually modifies map geometry.
    """
    _t0 = _time.perf_counter()
    map_obj = bpy.data.objects.get(mapName)

    # Compute a tight extrude height — just enough to pass through the terrain
    import numpy as np
    n_verts = len(map_obj.data.vertices)
    co_arr = np.empty(n_verts * 3, dtype=np.float32)
    map_obj.data.vertices.foreach_get("co", co_arr)
    z_vals = co_arr[2::3]
    extrude_height = float(z_vals.max() - z_vals.min()) + 10  # terrain relief + margin

    crv_data = crv.data
    crv_data.dimensions = "2D"
    crv_data.dimensions = "3D"
    crv_data.extrude = extrude_height

    # Slightly reduce curve resolution — enough for clean edges, fewer polys
    for spline in crv_data.splines:
        spline.resolution_u = max(4, (spline.resolution_u * 2) // 3)

    bpy.ops.object.select_all(action='DESELECT')
    crv.select_set(True)
    bpy.context.view_layer.objects.active = crv

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.curve.smooth()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Thicker duplicate (make before converting crv to mesh)
    crv_thick = crv.copy()
    crv_thick.data = crv.data.copy()
    crv_thick.data.bevel_depth = pathThickness / 2 + tolerance
    bpy.context.collection.objects.link(crv_thick)

    # Convert crv to mesh (only crv is selected)
    bpy.ops.object.select_all(action='DESELECT')
    crv.select_set(True)
    bpy.context.view_layer.objects.active = crv
    bpy.ops.object.convert(target='MESH')
    recalculateNormals(crv)
    _t1 = _time.perf_counter()
    crv_verts = len(crv.data.vertices)
    print(f"[TIMING]     single-color prep: {_t1-_t0:.2f}s (extrude={extrude_height:.0f}, crv verts={crv_verts})")

    # --- Create decimated map copy for INTERSECT operations ---
    map_lo = map_obj.copy()
    map_lo.data = map_obj.data.copy()
    bpy.context.collection.objects.link(map_lo)
    map_verts = len(map_lo.data.vertices)
    if map_verts > 5000:
        dec = map_lo.modifiers.new(name="_dec", type='DECIMATE')
        dec.ratio = 5000 / map_verts
        bpy.ops.object.select_all(action='DESELECT')
        map_lo.select_set(True)
        bpy.context.view_layer.objects.active = map_lo
        bpy.ops.object.modifier_apply(modifier=dec.name)
    print(f"[TIMING]     decimate map {map_verts}→{len(map_lo.data.vertices)} verts: {_time.perf_counter()-_t1:.2f}s")

    # Re-select crv for boolean operations
    bpy.ops.object.select_all(action='DESELECT')
    crv.select_set(True)
    bpy.context.view_layer.objects.active = crv

    # 1st intersect — clip to map (using decimated copy)
    _t1 = _time.perf_counter()
    bool_mod = crv.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_mod.object = map_lo
    bool_mod.operation = 'INTERSECT'
    bool_mod.solver = 'MANIFOLD'
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    print(f"[TIMING]     bool 1 intersect crv: {_time.perf_counter()-_t1:.2f}s")

    for v in crv.data.vertices:
        v.co += Vector((0, 0, 1))
    recalculateNormals(crv)

    # 2nd intersect — flush with terrain (using decimated copy)
    _t1 = _time.perf_counter()
    bool_mod = crv.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_mod.object = map_lo
    bool_mod.operation = 'INTERSECT'
    bool_mod.solver = 'MANIFOLD'
    recalculateNormals(crv)
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    print(f"[TIMING]     bool 2 intersect crv flush: {_time.perf_counter()-_t1:.2f}s")

    # Convert thick copy to mesh
    bpy.ops.object.select_all(action='DESELECT')
    crv_thick.select_set(True)
    bpy.context.view_layer.objects.active = crv_thick
    bpy.ops.object.convert(target='MESH')

    _t1 = _time.perf_counter()
    bool_mod = crv_thick.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_mod.object = map_lo
    bool_mod.operation = 'INTERSECT'
    bool_mod.solver = 'MANIFOLD'
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    crv_thick.location.z += 1
    print(f"[TIMING]     bool 3 intersect thick: {_time.perf_counter()-_t1:.2f}s")

    # Remove decimated copy — no longer needed
    bpy.data.objects.remove(map_lo, do_unlink=True)

    # Subtract groove from map (uses full-res map — this modifies actual geometry)
    _t1 = _time.perf_counter()
    bpy.ops.object.select_all(action='DESELECT')
    map_obj.select_set(True)
    bpy.context.view_layer.objects.active = map_obj

    bool_mod = map_obj.modifiers.new(name="Boolean", type="BOOLEAN")
    bool_mod.object = crv_thick
    bool_mod.operation = "DIFFERENCE"
    bool_mod.solver = "MANIFOLD"
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    print(f"[TIMING]     bool 4 difference groove: {_time.perf_counter()-_t1:.2f}s")

    bpy.data.objects.remove(crv_thick, do_unlink=True)
    print(f"[TIMING]     single-color total: {_time.perf_counter()-_t0:.2f}s")


def intersect_trails_with_existing_box(cutobject):
    """Find visible *_Trail* objects inside *cutobject* bounds and boolean-intersect them."""
    cutobject.scale.z = 1000
    bpy.context.view_layer.objects.active = cutobject
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    cube_bb = [cutobject.matrix_world @ Vector(corner) for corner in cutobject.bound_box]

    def _inside(point, bb):
        mn = Vector((min(v[0] for v in bb), min(v[1] for v in bb), min(v[2] for v in bb)))
        mx = Vector((max(v[0] for v in bb), max(v[1] for v in bb), max(v[2] for v in bb)))
        return all(mn[i] <= point[i] <= mx[i] for i in range(3))

    done = False
    bool_objects = []

    for robj in bpy.data.objects:
        if "_Trail" not in robj.name or robj.type not in {'CURVE', 'MESH'}:
            continue
        if robj.hide_get():
            continue

        if robj.type == 'CURVE':
            bpy.context.view_layer.objects.active = robj
            bpy.ops.object.select_all(action='DESELECT')
            robj.select_set(True)
            bpy.ops.object.convert(target='MESH')

        if robj.type == 'MESH' and len(robj.data.vertices) > 0:
            for v in robj.data.vertices:
                gc = robj.matrix_world @ v.co
                if _inside(gc, cube_bb):
                    if robj not in bool_objects:
                        bool_objects.append(robj)
                    done = True
                    break

    if not done:
        bpy.data.objects.remove(cutobject, do_unlink=True)
        return

    # Copy + merge + boolean
    copies = []
    for obj in bool_objects:
        oc = obj.copy()
        oc.data = obj.data.copy()
        bpy.context.collection.objects.link(oc)
        copies.append(oc)

    bpy.ops.object.select_all(action='DESELECT')
    for oc in copies:
        oc.select_set(True)
    bpy.context.view_layer.objects.active = copies[0]
    bpy.ops.object.join()
    merged = bpy.context.active_object

    bool_mod = cutobject.modifiers.new(name="Intersect", type='BOOLEAN')
    bool_mod.operation = 'INTERSECT'
    bool_mod.object = merged
    bpy.context.view_layer.objects.active = cutobject
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    bpy.data.objects.remove(merged, do_unlink=True)

    write_metadata(cutobject, type="TRAIL")


def merge_with_map(mapobject, mergeobject):
    """Intersect *mergeobject* with *mapobject* (extrude + boolean + trim bottom)."""
    bpy.ops.object.select_all(action="DESELECT")

    if mergeobject.type in ("FONT", "CURVE"):
        mergeobject.select_set(True)
        bpy.context.view_layer.objects.active = mergeobject
        bpy.ops.object.convert(target='MESH')

    bpy.context.view_layer.objects.active = mergeobject
    mergeobject.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move()
    bpy.ops.transform.translate(value=(0, 0, 200))
    bpy.ops.object.mode_set(mode='OBJECT')
    mergeobject.location.z = -1

    recalculateNormals(mergeobject)

    bool_mod = mergeobject.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_mod.object = mapobject
    bool_mod.operation = 'INTERSECT'
    bool_mod.solver = 'MANIFOLD'
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)

    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(mergeobject.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    try:
        min_z = min(v.co.z for v in bm.verts)
    except ValueError:
        bpy.ops.object.mode_set(mode='OBJECT')
        return

    tol = 0.1
    for v in bm.verts:
        v.select = abs(v.co.z - min_z) < tol

    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    bmesh.ops.delete(
        bm,
        geom=[e for e in bm.verts[:] + bm.edges[:] + bm.faces[:] if e.select],
        context='VERTS',
    )

    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_region_move()
    bpy.ops.transform.translate(value=(0, 0, -1))

    bmesh.update_edit_mesh(mergeobject.data)
    bpy.ops.object.mode_set(mode="OBJECT")

    mergeobject.location.z += 0.05

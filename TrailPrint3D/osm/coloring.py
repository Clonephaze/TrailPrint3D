"""Terrain coloring — OSM overlay on map meshes."""

from __future__ import annotations

import math
import time

import bmesh  # type: ignore
import bpy  # type: ignore
from mathutils import Vector  # type: ignore
from mathutils.bvhtree import BVHTree as bvhtree  # type: ignore

from ..coordinates import convert_to_blender_coordinates
from ..export import export_object
from ..geometry.mesh_utils import recalculateNormals
from ..metadata import write_metadata
from ..utils import show_message_box
from .fetch import fetch_osm_data, build_osm_nodes, extract_multipolygon_bodies


# ---------------------------------------------------------------------------
# Mesh creation helpers
# ---------------------------------------------------------------------------

def col_create_line_mesh(name: str, coords: list):
    """Create an edge-only mesh object from a coordinate list."""
    mesh = bpy.data.meshes.new(name)
    tobj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(tobj)

    bm = bmesh.new()
    verts = [bm.verts.new(c) for c in coords]
    for i in range(len(verts) - 1):
        bm.edges.new((verts[i], verts[i + 1]))
    bm.to_mesh(mesh)
    bm.free()
    return tobj


def col_create_face_mesh(name: str, coords: list):
    """Create a single-face mesh from a coordinate list (≥3 points)."""
    if len(coords) < 3:
        return None

    mesh = bpy.data.meshes.new(name)
    tobj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(tobj)

    bm = bmesh.new()
    verts = [bm.verts.new(c) for c in coords]
    try:
        bm.faces.new(verts)
    except ValueError:
        pass
    bm.to_mesh(mesh)
    bm.free()
    return tobj


def calculate_polygon_area_2d(coords: list) -> float:
    """Shoelace formula for polygon area (ignores Z)."""
    area = 0.0
    n = len(coords)
    if n < 3:
        return 0.0
    for i in range(n):
        x0, y0, *_ = coords[i]
        x1, y1, *_ = coords[(i + 1) % n]
        area += x0 * y1 - x1 * y0
    return abs(area) * 0.5


# ---------------------------------------------------------------------------
# Core coloring
# ---------------------------------------------------------------------------

def color_map_faces_by_terrain(map_obj, terrain_obj, up_threshold: float = 0.5):
    """Raycast upward from *map_obj* faces to detect *terrain_obj* above.

    Faces with terrain overhead get painted with the terrain material.
    """
    if map_obj.type != 'MESH' or terrain_obj.type != 'MESH':
        return

    map_mesh = map_obj.data
    terrain_mesh = terrain_obj.data

    bm = bmesh.new()
    bm.from_mesh(map_mesh)
    bm.faces.ensure_lookup_table()

    verts = [v.co for v in terrain_mesh.vertices]
    polys = [p.vertices for p in terrain_mesh.polygons]
    bvh = bvhtree.FromPolygons(verts, polys)

    mat = terrain_obj.active_material or bpy.data.materials.new(name="TerrainColor")
    if mat.name not in [m.name for m in map_mesh.materials]:
        map_mesh.materials.append(mat)
    mat_index = map_mesh.materials.find(mat.name)

    up = Vector((0, 0, 1))
    colored = 0

    for f in bm.faces:
        if f.normal.normalized().dot(up) > up_threshold:
            center = f.calc_center_median()
            loc, _norm, _idx, dist = bvh.ray_cast(center, up)
            if loc is not None and dist > 0:
                f.material_index = mat_index
                colored += 1

    bm.to_mesh(map_mesh)
    bm.free()


def coloring_main(
    map_obj,
    kind: str = "WATER",
    *,
    minLat: float,
    maxLat: float,
    minLon: float,
    maxLon: float,
):
    """Fetch OSM features and overlay them on *map_obj*.

    Parameters
    ----------
    map_obj : bpy.types.Object
        The terrain mesh to colour.
    kind : str
        ``"WATER"``, ``"FOREST"``, or ``"CITY"``.
    minLat, maxLat, minLon, maxLon : float
        Geographic bounding box.
    """
    tp = bpy.context.scene.tp3d
    col_PaintMap = tp.col_PaintMap
    col_area_map = {"WATER": tp.col_wArea, "FOREST": tp.col_fArea, "CITY": tp.col_cArea}
    col_Area = col_area_map.get(kind, tp.col_wArea)

    bpy.context.preferences.edit.use_global_undo = False

    name = map_obj.name
    lat_step = min(2, maxLat - minLat)
    lon_step = min(2, maxLon - minLon)

    lats = math.ceil((maxLat - minLat) / lat_step)
    lons = math.ceil((maxLon - minLon) / lon_step)

    created_objects: list = []

    if lats * lons >= 20:
        print("Region too large for OSM fetch")
        bpy.context.preferences.edit.use_global_undo = True
        return

    for k in range(lats):
        for lon_idx in range(lons):
            south = minLat + k * lat_step
            north = south + lat_step
            west = minLon + lon_idx * lon_step
            east = west + lon_step
            bbox = (south, west, north, east)

            try:
                resp = fetch_osm_data(bbox, kind)
                if resp is None or resp.status_code != 200:
                    continue
            except (OSError, ValueError) as e:
                show_message_box(f"Error fetching OSM data: {e}")
                continue

            data = resp.json()
            nodes = build_osm_nodes(data)
            bodies = extract_multipolygon_bodies(data['elements'], nodes)

            for i, coords in enumerate(bodies):
                bc = [convert_to_blender_coordinates(lat, lon, ele, 0) for lat, lon, ele in coords]
                if calculate_polygon_area_2d(bc) > col_Area:
                    tobj = col_create_face_mesh(f"LakeRelation_{i}", bc)
                    created_objects.append(tobj)

            for i, element in enumerate(data['elements']):
                if element['type'] != 'way':
                    continue
                coords = []
                for nid in element.get('nodes', []):
                    if nid in nodes:
                        nd = nodes[nid]
                        coords.append(convert_to_blender_coordinates(nd['lat'], nd['lon'], 0, 0))
                if len(coords) < 2 or calculate_polygon_area_2d(coords) < col_Area:
                    continue
                if coords[0] == coords[-1]:
                    tobj = col_create_face_mesh(f"Lake_{i}", coords)
                else:
                    tobj = col_create_line_mesh(f"OpenWater_{i}", coords)
                created_objects.append(tobj)

            time.sleep(5)

    # Merge all created meshes -------------------------------------------------
    if created_objects:
        bpy.ops.object.select_all(action='DESELECT')
        biggest = 0.0
        for tobj in list(created_objects):
            bm = bmesh.new()
            bm.from_mesh(tobj.data)
            area = sum(f.calc_area() for f in bm.faces)
            bm.free()
            if area > biggest:
                biggest = area
            if area >= col_Area:
                tobj.select_set(True)
                bpy.context.view_layer.objects.active = tobj
            else:
                md = tobj.data
                bpy.data.objects.remove(tobj, do_unlink=True)
                bpy.data.meshes.remove(md)

        if biggest == 0:
            bpy.context.preferences.edit.use_global_undo = True
            return

        bpy.ops.object.join()
        merged = bpy.context.view_layer.objects.active
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

        # Extrude up + boolean intersect
        bpy.context.view_layer.objects.active = merged
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.extrude_region_move()
        bpy.ops.transform.translate(value=(0, 0, 200))
        bpy.ops.object.mode_set(mode='OBJECT')
        merged.location.z -= 1

        recalculateNormals(merged)

        bool_mod = merged.modifiers.new(name="Boolean", type='BOOLEAN')
        bool_mod.object = map_obj
        bool_mod.operation = 'INTERSECT'
        bool_mod.solver = 'MANIFOLD'
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        # Trim bottom verts
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(merged.data)
        bm.verts.ensure_lookup_table()

        try:
            min_z = min(v.co.z for v in bm.verts)
        except ValueError:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.preferences.edit.use_global_undo = True
            return

        for v in bm.verts:
            v.select = abs(v.co.z - min_z) < 0.1

        bpy.context.tool_settings.mesh_select_mode = (True, False, False)
        bmesh.ops.delete(
            bm,
            geom=[e for e in bm.verts[:] + bm.edges[:] + bm.faces[:] if e.select],
            context='VERTS',
        )

        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.extrude_region_move()
        bpy.ops.transform.translate(value=(0, 0, -1))
        bmesh.update_edit_mesh(merged.data)
        bpy.ops.object.mode_set(mode='OBJECT')

        recalculateNormals(merged)
        merged.name = name + "_" + kind

        bpy.context.view_layer.objects.active = merged
        merged.select_set(True)
        for v in merged.data.vertices:
            v.co.z -= 0.9
        merged.location.z = 0

        write_metadata(merged, type=kind)
        mat = bpy.data.materials.get(kind)
        merged.data.materials.clear()
        merged.data.materials.append(mat)

        if not col_PaintMap:
            auto_export = getattr(bpy.context.scene.tp3d, 'autoExport', False)
            if auto_export:
                export_object(merged)
        else:
            color_map_faces_by_terrain(map_obj, merged)
            md = merged.data
            bpy.data.objects.remove(merged, do_unlink=True)
            bpy.data.meshes.remove(md)

    bpy.context.preferences.edit.use_global_undo = True

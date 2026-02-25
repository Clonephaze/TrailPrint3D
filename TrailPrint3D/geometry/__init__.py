"""Geometry package — shapes, curves, mesh utilities, and boolean operations."""

from .shapes import create_hexagon, create_rectangle, create_circle
from .curves import create_curve_from_coordinates, simplify_curve, RaycastCurveToMesh
from .mesh_utils import (
    fix_mesh_anomalies, recalculateNormals,
    selectBottomFaces, selectTopFaces,
    transform_MapObject, delete_non_manifold,
)
from .boolean_ops import plateInsert, merge_with_map, intersect_trails_with_existing_box, single_color_mode

__all__ = [
    "create_hexagon", "create_rectangle", "create_circle",
    "create_curve_from_coordinates", "simplify_curve", "RaycastCurveToMesh",
    "fix_mesh_anomalies", "recalculateNormals",
    "selectBottomFaces", "selectTopFaces",
    "transform_MapObject", "delete_non_manifold",
    "plateInsert", "merge_with_map", "intersect_trails_with_existing_box", "single_color_mode",
]

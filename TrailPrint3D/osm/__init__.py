"""OpenStreetMap data fetching and terrain coloring."""

from .fetch import fetch_osm_data, build_osm_nodes, extract_multipolygon_bodies
from .coloring import (
    coloring_main,
    color_map_faces_by_terrain,
    col_create_face_mesh,
    col_create_line_mesh,
    calculate_polygon_area_2d,
)

__all__ = [
    "fetch_osm_data",
    "build_osm_nodes",
    "extract_multipolygon_bodies",
    "coloring_main",
    "color_map_faces_by_terrain",
    "col_create_face_mesh",
    "col_create_line_mesh",
    "calculate_polygon_area_2d",
]

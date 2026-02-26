"""Shared helpers for post-processing operators."""

import bpy  # type: ignore

# Object types written by the generation pipeline (see metadata.py)
_MAP_TYPES = {"MAP"}
_PLATE_TYPES = {"PLATE"}
_GENERATION_TYPES = {"MAP", "TRAIL", "WATER", "FOREST", "CITY", "LINES", "TEXT", "PLATE"}


def find_map_objects() -> list:
    """Return all MAP-type mesh objects in the scene.

    If the user has MAP objects selected, only those are returned.
    Otherwise, all MAP objects in the active scene are gathered
    automatically so operators don't require manual selection.
    """
    # Prefer user selection if it contains MAP objects
    selected_maps = [
        o for o in bpy.context.selected_objects
        if o.type == 'MESH' and o.get("Object type") in _MAP_TYPES
    ]
    if selected_maps:
        return selected_maps

    # Fall back to all MAP objects in the scene
    return [
        o for o in bpy.context.scene.objects
        if o.type == 'MESH' and o.get("Object type") in _MAP_TYPES
    ]


def find_plate_objects() -> list:
    """Return PLATE objects for base-related ops (magnets, dovetail, bottom mark).

    Prefers selected PLATE objects.  Falls back to all PLATEs in the scene.
    If no PLATE exists (plain shapes without text-plate), falls back to MAP
    objects so the operator still works on simple shapes.
    """
    selected_plates = [
        o for o in bpy.context.selected_objects
        if o.type == 'MESH' and o.get("Object type") in _PLATE_TYPES
    ]
    if selected_plates:
        return selected_plates

    scene_plates = [
        o for o in bpy.context.scene.objects
        if o.type == 'MESH' and o.get("Object type") in _PLATE_TYPES
    ]
    if scene_plates:
        return scene_plates

    # No plate exists — fall back to MAP (e.g. plain hexagon without text)
    return find_map_objects()


def find_generation_objects() -> list:
    """Return all generation-pipeline objects (MAP, TRAIL, overlays, etc.).

    Same preference logic as :func:`find_map_objects` — if any
    generation objects are selected, only those are returned.
    """
    selected_gen = [
        o for o in bpy.context.selected_objects
        if o.get("Object type") in _GENERATION_TYPES
    ]
    if selected_gen:
        return selected_gen

    return [
        o for o in bpy.context.scene.objects
        if o.get("Object type") in _GENERATION_TYPES
    ]

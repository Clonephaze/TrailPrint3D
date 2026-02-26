"""3MF export integration via the ThreeMF_io addon.

Detects whether ``io_mesh_3mf`` is installed and provides:

* ``is_3mf_available()`` — live check (works even if installed after TP3D)
* ``export_as_3mf(parts, filepath, name)`` — duplicates parts, centres them
  at the origin, exports via the OrcaExporter (auto-selected because the
  objects have materials) which writes Orca-style colorgroups for each
  object and groups them on one plate via model_settings.config.
"""

from __future__ import annotations

import os
from typing import List

import bpy  # type: ignore


def is_3mf_available() -> bool:
    """Return *True* if the ThreeMF_io addon is active and usable.

    Works across Blender 4.x legacy addons and 5.0 extensions by checking
    whether the 3MF export operator is registered.
    """
    try:
        return hasattr(bpy.ops.export_mesh, "threemf")
    except Exception:
        return False


def _import_3mf_api():
    """Import and return the ``io_mesh_3mf.api`` module, or *None*.

    Handles both legacy addon installs (``import io_mesh_3mf.api``) and
    Blender 4.2+ extension installs where the module lives under
    ``bl_ext.<repo>.ThreeMF_io``.
    """
    import importlib
    import sys

    # 1. Direct import — works for legacy addons or if already on sys.path
    try:
        return importlib.import_module("io_mesh_3mf.api")
    except (ImportError, ModuleNotFoundError):
        pass

    # 2. Extension-style: find the ThreeMF_io package in sys.modules and
    #    dynamically import .api from its root.
    for key in list(sys.modules.keys()):
        parts = key.split(".")
        if "ThreeMF_io" in parts:
            idx = parts.index("ThreeMF_io")
            base_pkg = ".".join(parts[: idx + 1])
            try:
                return importlib.import_module(base_pkg + ".api")
            except (ImportError, ModuleNotFoundError):
                continue

    return None


def export_as_3mf(
    parts: List[bpy.types.Object],
    filepath: str,
    assembly_name: str = "TrailPrint3D",
) -> bool:
    """Export *parts* as a 3MF file with per-object colors, grouped as one assembly.

    To avoid touching the original scene objects, this function:

    1. Duplicates each part (object + mesh data).
    2. Centres the duplicates around the world origin (relative positions
       kept intact so text stays on the plate, trail on the terrain, etc.).
    3. Parents duplicates under a temporary Empty so Orca treats them as
       one grouped project.
    4. Exports via the ThreeMF_io API.  The OrcaExporter is auto-selected
       (objects have materials) and writes each child mesh as its own model
       file with the correct extruder assignment per part.
    5. Deletes all temporaries and restores original names.

    Returns *True* on success, *False* on failure.
    """
    if not is_3mf_available():
        print("[3MF] ThreeMF_io addon not found — skipping 3MF export")
        return False

    api = _import_3mf_api()
    if api is None:
        print("[3MF] Could not import io_mesh_3mf.api — is the addon enabled?")
        return False

    # Filter to only valid mesh objects still in the scene
    valid_parts = [p for p in parts if p and p.name in bpy.data.objects]
    if not valid_parts:
        print("[3MF] No valid objects to export")
        return False

    # Ensure filepath has .3mf extension
    if not filepath.lower().endswith(".3mf"):
        filepath += ".3mf"

    # Ensure directory exists
    dirpath = os.path.dirname(filepath)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)

    # --- Work on duplicates so originals are untouched ---
    from mathutils import Vector  # type: ignore
    import bmesh  # type: ignore

    # TrailPrint3D treats 1 Blender unit as 1 mm, but Blender's default
    # scene unit is meters (scale_length = 1.0).  The 3MF exporter
    # auto-converts metres → mm (×1000) via export_unit_scale().
    # We compute the inverse of that conversion so the raw vertex values
    # (already in "mm") are written as-is into the 3MF file.
    scene_scale = bpy.context.scene.unit_settings.scale_length or 1.0
    mm_correction = 0.001 / scene_scale  # e.g. 0.001/1.0 = 0.001 for metre scene

    # Compute the centre of all parts (average of bounding-box centres)
    # and the lowest Z across the entire group so we can sit the model
    # on the bed (Z=0) instead of burying it halfway in.
    centres = []
    min_z = float("inf")
    for p in valid_parts:
        bb = [p.matrix_world @ Vector(c) for c in p.bound_box]
        centres.append(sum(bb, Vector()) / 8)
        for v in bb:
            if v.z < min_z:
                min_z = v.z
    group_centre = sum(centres, Vector()) / len(centres)
    # Only centre XY; shift Z so the bottom sits on the bed
    group_centre.z = min_z

    # Deselect everything
    bpy.ops.object.select_all(action='DESELECT')

    temp_objects: list[bpy.types.Object] = []
    orig_names: list[str] = []

    for orig in valid_parts:
        # Duplicate object + mesh data so we don't touch the original
        new_mesh = orig.data.copy()
        dup = orig.copy()
        dup.data = new_mesh
        bpy.context.collection.objects.link(dup)

        # Bake the full world transform (location + rotation + scale)
        # into the mesh vertices, then re-centre around the group origin.
        # This is critical for text and other objects whose size lives in
        # the object-level scale rather than the raw vertex positions.
        bm = bmesh.new()
        bm.from_mesh(new_mesh)
        bm.transform(orig.matrix_world)               # local → world
        bmesh.ops.translate(bm, verts=bm.verts,
                            vec=-group_centre)         # centre on group
        bmesh.ops.scale(bm, verts=bm.verts,
                        vec=(mm_correction,
                             mm_correction,
                             mm_correction))            # BU → mm
        bm.to_mesh(new_mesh)
        bm.free()

        # All geometry is now baked — reset object transform to identity
        dup.location = Vector((0, 0, 0))
        dup.rotation_euler = (0, 0, 0)
        dup.scale = (1, 1, 1)

        temp_objects.append(dup)
        orig_names.append(str(orig.name))

    # Create assembly Empty and parent all duplicates under it
    assembly = bpy.data.objects.new(assembly_name, None)
    bpy.context.collection.objects.link(assembly)
    for dup in temp_objects:
        dup.parent = assembly
        dup.matrix_parent_inverse.identity()

    # Temporarily hide originals so we can give duplicates clean names
    hidden_originals = []
    for orig in valid_parts:
        orig_name = str(orig.name)
        orig.name = orig_name + "_tp3d_hide"
        hidden_originals.append((orig, orig_name))

    # Rename duplicates to the clean original names
    for dup, clean_name in zip(temp_objects, orig_names):
        dup.name = clean_name

    bpy.context.view_layer.update()

    # Export via the API — assembly Empty groups everything as one project
    try:
        result = api.export_3mf(
            filepath,
            objects=[assembly],
            use_orca_format="STANDARD",
            use_mesh_modifiers=True,
            use_components=False,
            thumbnail_mode="AUTO",
            thumbnail_resolution=256,
        )

        if result.status == "FINISHED":
            print(f"[3MF] Exported {result.num_written} objects to {filepath}")
            success = True
        else:
            print(f"[3MF] Export finished with status: {result.status}")
            if hasattr(result, 'warnings') and result.warnings:
                print(f"[3MF] Warnings: {result.warnings}")
            success = False

    except Exception as e:
        print(f"[3MF] Export error: {e}")
        success = False

    # --- Cleanup: remove assembly Empty + all temp objects, restore names ---
    bpy.ops.object.select_all(action='DESELECT')
    for dup in temp_objects:
        bpy.data.meshes.remove(dup.data, do_unlink=True)
    bpy.data.objects.remove(assembly, do_unlink=True)

    # Restore original names
    for orig, orig_name in hidden_originals:
        orig.name = orig_name

    return success

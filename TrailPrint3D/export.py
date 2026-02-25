"""Object export — STL for geometry-only objects, OBJ for objects with materials.

Fixes the path-concatenation bug in the original code by using ``os.path.join``.
Unifies ``export_to_STL`` and ``export_selected_to_STL`` into two focused helpers.
"""

import os

import bpy  # type: ignore

from .utils import show_message_box


def export_object(obj, export_path: str | None = None):
    """Export a single Blender object as STL or OBJ (if it has materials).

    Parameters:
        obj: Blender object to export.
        export_path: Directory to write the file into.
                     If *None*, reads from ``bpy.context.scene.tp3d.export_path``.
    """
    if export_path is None:
        export_path = bpy.context.scene.tp3d.get("export_path", "")
    if not export_path:
        return
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    if obj.material_slots:
        filepath = os.path.join(export_path, obj.name + ".obj")
        bpy.ops.wm.obj_export(
            filepath=filepath,
            export_selected_objects=True,
            export_triangulated_mesh=True,
            apply_modifiers=True,
            export_materials=True,
            forward_axis="Y",
            up_axis="Z",
        )
    else:
        filepath = os.path.join(export_path, obj.name + ".stl")
        bpy.ops.wm.stl_export(
            filepath=filepath,
            export_selected_objects=True,
        )

    obj.select_set(False)


def export_selected(export_path: str):
    """Export every currently-selected object individually.

    Each object is exported as STL or OBJ depending on whether it has materials.
    """
    selected_objects = list(bpy.context.selected_objects)
    active_obj = bpy.context.active_object

    if not selected_objects:
        show_message_box("No object selected")
        return

    for obj in selected_objects:
        export_object(obj, export_path)
        show_message_box("File Exported to your selected directory", "INFO", "File Exported")

    # Restore selection state
    bpy.ops.object.select_all(action='DESELECT')
    for obj in selected_objects:
        obj.select_set(True)
    if active_obj:
        bpy.context.view_layer.objects.active = active_obj

"""Export operator."""

import os

import bpy  # type: ignore

from ..export import export_selected
from ..utils import show_message_box


class MY_OT_ExportSTL(bpy.types.Operator):
    bl_idname = "wm.run_my_script5"
    bl_label = "Export STL/OBJ"
    bl_description = "Export selected objects as separate STL files (OBJ if object has materials)"

    def execute(self, context):
        export_path = bpy.context.scene.tp3d.get('export_path', None)

        if not export_path:
            show_message_box("Export path is empty. Please select a directory for completed files")
            return {'FINISHED'}

        export_path = bpy.path.abspath(export_path)

        if not export_path:
            show_message_box("Export path is empty! Please select a valid folder.")
            return {'FINISHED'}
        if not os.path.isdir(export_path):
            show_message_box(f"Invalid export directory: {export_path}. Please select a valid directory.")
            return {'FINISHED'}

        if not bpy.context.selected_objects:
            show_message_box("Please select objects to export")
            return {'FINISHED'}

        export_selected()
        return {'FINISHED'}

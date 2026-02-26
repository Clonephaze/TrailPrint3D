"""Export operator — STL/OBJ or 3MF."""

import os

import bpy  # type: ignore

from ..export import export_selected
from ..export_3mf import is_3mf_available, export_as_3mf
from ..utils import show_message_box


def _find_generated_objects() -> list:
    """Return the objects created by the last generation, based on trail name.

    Matches: ``{name}``, ``{name}_Trail*``, ``{name}_Plate``, ``{name}_Text``,
    ``{name}_*Flag``, ``{name}_Assembly``.
    """
    props = bpy.context.scene.tp3d
    name = props.get("trailName", "")
    if not name:
        # Fallback: try to derive from file_path
        fp = props.get("file_path", "")
        if fp:
            name = os.path.splitext(os.path.basename(bpy.path.abspath(fp)))[0]
    if not name:
        return []

    found = []
    for obj in bpy.data.objects:
        n = obj.name
        if n == name or n.startswith(name + "_"):
            found.append(obj)
    return found


class MY_OT_ExportSTL(bpy.types.Operator):
    bl_idname = "wm.run_my_script5"
    bl_label = "Export"
    bl_description = "Export generated objects (auto-selects if nothing is selected)"

    def execute(self, context):
        props = context.scene.tp3d
        export_path = props.get('export_path', None)

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

        export_fmt = props.export_format  # 'STL_OBJ' or '3MF'

        # Auto-detect objects if nothing is selected
        selected = list(bpy.context.selected_objects)
        auto_selected = False
        if not selected:
            selected = _find_generated_objects()
            if not selected:
                show_message_box("No objects selected and no generated objects found. "
                                 "Please select objects to export.", "ERROR", "Nothing to export")
                return {'FINISHED'}
            auto_selected = True
            # Select them so export functions work
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected:
                obj.select_set(True)

        # --- 3MF export ---
        if export_fmt == '3MF':
            if not is_3mf_available():
                show_message_box("ThreeMF_io addon is not installed. "
                                 "Install it to enable 3MF export.", "ERROR", "3MF Not Available")
                return {'FINISHED'}

            # Derive a name for the 3MF file
            name = props.get("trailName", "")
            if not name:
                fp = props.get("file_path", "")
                if fp:
                    name = os.path.splitext(os.path.basename(bpy.path.abspath(fp)))[0]
            if not name:
                name = "TrailPrint3D"

            filepath = os.path.join(export_path, name + ".3mf")
            ok = export_as_3mf(selected, filepath, assembly_name=name)
            if ok:
                show_message_box(f"3MF exported to {filepath}", "INFO", "Export Complete")
            else:
                show_message_box("3MF export failed — check console for details",
                                 "ERROR", "Export Failed")
            return {'FINISHED'}

        # --- STL/OBJ export ---
        export_selected(export_path)
        return {'FINISHED'}

"""Export panel — top-level, separate from generation."""

import bpy  # type: ignore

from ..export_3mf import is_3mf_available


class TP3D_PT_export(bpy.types.Panel):
    bl_label = "Export"
    bl_idname = "TP3D_PT_export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_options = set()
    bl_order = 1

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        layout.prop(props, "export_path")

        layout.prop(props, "export_format")
        if props.export_format == '3MF' and not is_3mf_available():
            layout.label(text="Install ThreeMF_io addon for 3MF", icon='ERROR')

        layout.separator()

        row = layout.row(align=True)
        row.prop(props, "autoExport")
        if is_3mf_available():
            row.prop(props, "auto3mfExport")

        layout.separator()

        layout.operator("tp3d.export", icon='EXPORT')
        layout.label(text="Auto-selects generated objects if nothing is selected", icon='INFO')

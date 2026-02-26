"""Generate sub-panel — GPX input, shape, and generate button."""

import bpy  # type: ignore


class TP3D_PT_generate(bpy.types.Panel):
    bl_label = "Generate"
    bl_idname = "TP3D_PT_generate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_parent_id = "TP3D_PT_main"
    bl_options = set()

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        layout.prop(props, "file_path")
        layout.prop(props, "trailName")
        layout.prop(props, "shape")

        layout.separator()

        from ..export_3mf import is_3mf_available
        row = layout.row(align=True)
        row.prop(props, "autoExport")
        if is_3mf_available():
            row.prop(props, "auto3mfExport")

        layout.operator("tp3d.generate", icon='PLAY')

        if props.o_time:
            layout.label(text=props.o_time)

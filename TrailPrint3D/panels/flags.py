"""Flag markers sub-panel."""

import bpy  # type: ignore


class TP3D_PT_flags(bpy.types.Panel):
    bl_label = "Flags"
    bl_idname = "TP3D_PT_flags"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_parent_id = "TP3D_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        layout.prop(props, "addFlags")

        if props.addFlags:
            col = layout.column(align=True)
            col.prop(props, "flagHeight")
            col.prop(props, "flagWidth")

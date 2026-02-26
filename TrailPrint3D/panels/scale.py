"""Scale mode sub-panel."""

import bpy  # type: ignore


class TP3D_PT_scale(bpy.types.Panel):
    bl_label = "Scale"
    bl_idname = "TP3D_PT_scale"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_parent_id = "TP3D_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        layout.prop(props, "scalemode")

        if props.scalemode == "FACTOR":
            layout.prop(props, "pathScale")
        elif props.scalemode == "COORDINATES":
            row = layout.row(align=True)
            row.prop(props, "scaleLat1")
            row.prop(props, "scaleLon1")
            row = layout.row(align=True)
            row.prop(props, "scaleLat2")
            row.prop(props, "scaleLon2")
        elif props.scalemode == "SCALE":
            layout.prop(props, "pathScale")

"""Terrain settings sub-panel."""

import bpy  # type: ignore


class TP3D_PT_terrain(bpy.types.Panel):
    bl_label = "Terrain"
    bl_idname = "TP3D_PT_terrain"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_parent_id = "TP3D_PT_main"
    bl_options = set()

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        col = layout.column(align=True)
        col.prop(props, "objSize")
        col.prop(props, "num_subdivisions")

        layout.separator()

        col = layout.column(align=True)
        col.prop(props, "scaleElevation")
        col.prop(props, "fixedElevationScale")
        col.prop(props, "minThickness")

        layout.separator()

        col = layout.column(align=True)
        col.prop(props, "pathThickness")
        col.prop(props, "overwritePathElevation")
        col.prop(props, "singleColorMode")

        if props.singleColorMode:
            layout.prop(props, "tolerance")

        layout.separator()

        row = layout.row(align=True)
        row.prop(props, "xTerrainOffset")
        row.prop(props, "yTerrainOffset")

        layout.prop(props, "shapeRotation")

"""OSM overlay elements sub-panel."""

import bpy  # type: ignore


class TP3D_PT_osm(bpy.types.Panel):
    bl_label = "Overlays"
    bl_idname = "TP3D_PT_osm"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_parent_id = "TP3D_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        # Water
        box = layout.box()
        row = box.row()
        row.prop(props, "col_wActive")
        if props.col_wActive:
            row.prop(props, "col_wArea", text="Min Size")

        # Forest
        box = layout.box()
        row = box.row()
        row.prop(props, "col_fActive")
        if props.col_fActive:
            row.prop(props, "col_fArea", text="Min Size")

        # City
        box = layout.box()
        row = box.row()
        row.prop(props, "col_cActive")
        if props.col_cActive:
            row.prop(props, "col_cArea", text="Min Size")

        layout.separator()
        layout.prop(props, "col_PaintMap")

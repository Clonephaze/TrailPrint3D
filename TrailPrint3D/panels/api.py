"""Elevation API settings sub-panel."""

import bpy  # type: ignore


class TP3D_PT_api(bpy.types.Panel):
    bl_label = "Elevation API"
    bl_idname = "TP3D_PT_api"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_parent_id = "TP3D_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        layout.prop(props, "api")

        if props.api == "OPENTOPODATA":
            layout.prop(props, "dataset")
            layout.separator()
            layout.label(text="Self-hosted Opentopodata server:")
            layout.prop(props, "selfHosted")

        layout.separator()
        layout.prop(props, "disableCache")

        if not props.disableCache:
            layout.prop(props, "ccacheSize")

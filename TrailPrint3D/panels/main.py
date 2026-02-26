"""Header-only parent panel — all sub-panels attach to this."""

import bpy  # type: ignore


class TP3D_PT_main(bpy.types.Panel):
    bl_label = "TrailPrint3D"
    bl_idname = "TP3D_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"

    def draw(self, context):
        pass  # Header only — content is in sub-panels

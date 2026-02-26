"""Shape-specific settings panel (text layout options)."""

import bpy  # type: ignore


class MY_PT_Shapes(bpy.types.Panel):
    bl_label = "Additional Shape Settings"
    bl_idname = "TP3D_PT_ShapeSettings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TrailPrint3D"

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        text_shapes = {
            "HEXAGON INNER TEXT",
            "HEXAGON OUTER TEXT",
            "OCTAGON OUTER TEXT",
            "HEXAGON FRONT TEXT",
        }

        if props.shape in text_shapes:
            layout.prop(props, "textFont")
            layout.prop(props, "textSize")
            layout.prop(props, "textSizeTitle")
            layout.separator()
            layout.label(text="Custom Text Content:")
            layout.prop(props, "overwriteLength")
            layout.prop(props, "overwriteHeight")
            layout.prop(props, "overwriteTime")
            layout.prop(props, "plateThickness")
            layout.prop(props, "outerBorderSize")
            layout.prop(props, "plateInsertValue")
            layout.prop(props, "text_angle_preset")

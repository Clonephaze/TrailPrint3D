"""Text & plate settings sub-panel — only visible for text-based shapes."""

import bpy  # type: ignore

# Shapes that include text layout
_TEXT_SHAPES = {
    "HEXAGON INNER TEXT",
    "HEXAGON OUTER TEXT",
    "OCTAGON OUTER TEXT",
    "HEXAGON FRONT TEXT",
}


class TP3D_PT_text(bpy.types.Panel):
    bl_label = "Text & Plate"
    bl_idname = "TP3D_PT_text"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_parent_id = "TP3D_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        props = context.scene.tp3d
        return props.shape in _TEXT_SHAPES

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        col = layout.column(align=True)
        col.prop(props, "textFont")
        col.prop(props, "textSize")
        col.prop(props, "textSizeTitle")

        layout.separator()
        layout.label(text="Custom Text:")

        col = layout.column(align=True)
        col.prop(props, "overwriteLength")
        col.prop(props, "overwriteHeight")
        col.prop(props, "overwriteTime")

        layout.separator()
        layout.label(text="Plate:")

        col = layout.column(align=True)
        col.prop(props, "plateThickness")
        col.prop(props, "outerBorderSize")
        col.prop(props, "plateInsertValue")
        col.prop(props, "text_angle_preset")

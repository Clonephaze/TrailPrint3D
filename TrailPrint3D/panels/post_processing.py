"""Post-processing panel — top-level, operates on already-generated objects."""

import bpy  # type: ignore


class TP3D_PT_post_processing(bpy.types.Panel):
    bl_label = "Post Processing"
    bl_idname = "TP3D_PT_post_processing"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        # Mountain coloring
        box = layout.box()
        box.label(text="Mountain Coloring", icon='COLORSET_01_VEC')
        box.prop(props, "mountain_treshold")
        box.operator("tp3d.color_mountain", icon='BRUSH_DATA')

        # Contour lines
        box = layout.box()
        box.label(text="Contour Lines", icon='IPO_LINEAR')
        col = box.column(align=True)
        col.prop(props, "cl_thickness")
        col.prop(props, "cl_distance")
        col.prop(props, "cl_offset")
        box.operator("tp3d.contour_lines")

        # Rescale elevation
        box = layout.box()
        box.label(text="Rescale Elevation", icon='EMPTY_SINGLE_ARROW')
        row = box.row(align=True)
        row.prop(props, "rescaleMultiplier")
        row.operator("tp3d.rescale", text="Scale")

        # Extrude terrain
        box = layout.box()
        box.label(text="Extrude Terrain", icon='MOD_SOLIDIFY')
        row = box.row(align=True)
        row.prop(props, "thickenValue")
        row.operator("tp3d.thicken", text="Extrude")

        # Magnet holes
        box = layout.box()
        box.label(text="Magnet Holes", icon='SNAP_FACE_CENTER')
        row = box.row(align=True)
        row.prop(props, "magnetHeight")
        row.prop(props, "magnetDiameter")
        box.operator("tp3d.magnet_holes")

        # Dovetail + Bottom Mark
        layout.separator()
        layout.operator("tp3d.dovetail", icon='MOD_BOOLEAN')
        layout.operator("tp3d.bottom_mark", icon='FONT_DATA')

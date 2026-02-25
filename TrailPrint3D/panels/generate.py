"""Main generation panel."""

import bpy  # type: ignore


class MY_PT_Generate(bpy.types.Panel):
    bl_label = "Create"
    bl_idname = "PT_EmGi_3DPath+"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        layout.separator()
        layout.label(text="Create File")
        layout.operator("wm.run_my_script")

        box = layout.box()
        box.prop(props, "file_path")
        box.prop(props, "export_path")
        box.prop(props, "autoExport")
        box.prop(props, "trailName")
        box.prop(props, "shape")
        box.separator()
        box.prop(props, "objSize")
        box.prop(props, "num_subdivisions")
        box.prop(props, "scaleElevation")
        box.prop(props, "pathThickness")
        box.prop(props, "scalemode")

        if props.scalemode == "FACTOR":
            box.prop(props, "pathScale")
        elif props.scalemode == "COORDINATES":
            row = box.row()
            row.prop(props, "scaleLat1")
            row.prop(props, "scaleLon1")
            row = box.row()
            row.prop(props, "scaleLat2")
            row.prop(props, "scaleLon2")
        elif props.scalemode == "SCALE":
            box.prop(props, "pathScale")

        box.prop(props, "overwritePathElevation")
        layout.label(text=props.o_time)
        layout.label(text="------------------------------")

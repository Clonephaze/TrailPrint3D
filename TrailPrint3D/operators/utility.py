"""Utility operators — pins, website links, properties popup."""

import webbrowser

import bpy  # type: ignore

from ..coordinates import convert_to_blender_coordinates


class TP3D_OT_PinCoords(bpy.types.Operator):
    bl_idname = "tp3d.pin_coords"
    bl_label = "Add Coordinate Pin"
    bl_description = "Place a pin marker at specified coordinates"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        tp = bpy.context.scene.tp3d
        minThickness = tp.get("minThickness", 7)
        lat = float(tp.get("pinLat", 0))
        lon = float(tp.get("pinLon", 0))

        xp, yp, zp = convert_to_blender_coordinates(lat, lon, 0, 0)
        name = f"Pin_{round(lat, 2)}.{round(lon, 2)}"

        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

        bpy.ops.mesh.primitive_cone_add(
            vertices=16, radius1=0.4, radius2=0.8, depth=4,
            location=(xp, yp, minThickness + 2),
        )
        pin = bpy.context.active_object
        pin.name = name
        return {'FINISHED'}


class TP3D_OT_OpenWebsite(bpy.types.Operator):
    bl_idname = "tp3d.open_website"
    bl_label = "Visit Project Homepage"
    bl_description = "Visit TrailPrint3D project homepage for more info and support"

    def execute(self, context):
        webbrowser.open("https://github.com/EmGi3D/TrailPrint3D")
        return {'FINISHED'}


class TP3D_OT_JoinDiscord(bpy.types.Operator):
    bl_idname = "tp3d.join_discord"
    bl_label = "Join Discord"
    bl_description = "TrailPrint3D Discord community!"

    def execute(self, context):
        webbrowser.open("https://discord.gg/C67H9EJFbz")
        return {'FINISHED'}


class TP3D_OT_ShowProps(bpy.types.Operator):
    bl_idname = "tp3d.show_props"
    bl_label = "Generation Parameters"
    bl_description = "Show settings used to generate this object (select map object)"
    bl_options = {'REGISTER'}

    MAX_PER_COLUMN = 25
    NORMAL_WIDTH = 400
    DOUBLE_WIDTH = 800

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        if not obj:
            layout.label(text="No active object selected.", icon="ERROR")
            return

        props = [k for k in obj.keys() if not k.startswith("_")]

        if not props:
            layout.label(text="No custom properties found. Please select a map object", icon="INFO")
            return

        if len(props) > self.MAX_PER_COLUMN:
            split = layout.split(factor=0.5)
            col1, col2 = split.column(align=True), split.column(align=True)
            mid = (len(props) + 1) // 2
            for col, chunk in ((col1, props[:mid]), (col2, props[mid:])):
                for key in chunk:
                    row = col.row()
                    row.label(text=key + ":", icon='DOT')
                    row.label(text=str(obj[key]))
        else:
            col = layout.column(align=True)
            for key in props:
                row = col.row()
                row.label(text=key + ":", icon='DOT')
                row.label(text=str(obj[key]))

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        obj = context.active_object
        props = [k for k in obj.keys() if not k.startswith("_")] if obj else []
        w = self.DOUBLE_WIDTH if len(props) > self.MAX_PER_COLUMN else self.NORMAL_WIDTH
        return context.window_manager.invoke_props_dialog(self, width=w)

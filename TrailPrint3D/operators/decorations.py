"""Decoration operators — bottom mark, mountain coloring, contour lines."""

import bmesh  # type: ignore
import bpy  # type: ignore

from ..metadata import write_metadata
from ..text.base import BottomText
from ..utils import show_message_box


class TP3D_OT_BottomMark(bpy.types.Operator):
    bl_idname = "tp3d.bottom_mark"
    bl_label = "Bottom Mark"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = context.selected_objects
        if not selected:
            show_message_box("No object selected")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')
        for o in selected:
            o.select_set(False)

        generated = False
        for zobj in selected:
            if zobj.type == 'MESH' and "objSize" in zobj:
                zobj.select_set(True)
                bpy.context.view_layer.objects.active = zobj
                BottomText(zobj)
                generated = True
                bpy.ops.object.select_all(action='DESELECT')
                zobj.select_set(False)

        if not generated:
            show_message_box("No map object found in selection")

        bpy.context.view_layer.objects.active = selected[0]
        for o in selected:
            o.select_set(True)
        return {'FINISHED'}


class TP3D_OT_ColorMountain(bpy.types.Operator):
    bl_idname = "tp3d.color_mountain"
    bl_label = "Color Mountains"
    bl_description = "Add color to mountain areas above specified threshold height"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = bpy.context.selected_objects
        min_treshold = bpy.context.scene.tp3d.mountain_treshold

        if not selected:
            show_message_box("No Object Selected. Please select a Map first")
            return {'CANCELLED'}

        min_z = max_z = minThickness = None
        for obj in selected:
            if "lowestZ" in obj and "highestZ" in obj and obj["highestZ"] != 0:
                low, high = obj["lowestZ"], obj["highestZ"]
                minThickness = obj["minThickness"]
                min_z = low if min_z is None else min(min_z, low)
                max_z = high if max_z is None else max(max_z, high)

        mat = bpy.data.materials.get("MOUNTAIN")

        for obj in selected:
            if obj.type != 'MESH' or obj.get("Object type") != "MAP" or max_z is None or max_z == 0:
                continue

            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(obj.data)

            matG_index = obj.data.materials.find("BASE")
            mat_index = obj.data.materials.find("MOUNTAIN")
            if mat_index == -1:
                obj.data.materials.append(mat)
                mat_index = len(obj.data.materials) - 1

            tres = (max_z - min_z) / 100 * min_treshold + minThickness
            for face in bm.faces:
                if abs(face.normal.z) < 0.02:
                    continue
                avg_z = sum(v.co.z for v in face.verts) / len(face.verts)
                if avg_z > tres and face.material_index == matG_index:
                    face.material_index = mat_index
                elif avg_z < tres and face.material_index == mat_index:
                    face.material_index = matG_index

            bmesh.update_edit_mesh(obj.data)
            bpy.ops.object.mode_set(mode='OBJECT')

        return {'FINISHED'}


class TP3D_OT_ContourLines(bpy.types.Operator):
    bl_idname = "tp3d.contour_lines"
    bl_label = "Contour Lines"
    bl_description = "Generate contour lines on the map"

    def execute(self, context):
        selected = bpy.context.selected_objects
        tp = bpy.context.scene.tp3d
        cl_thickness = tp.cl_thickness
        cl_distance = tp.cl_distance
        cl_offset = tp.cl_offset
        size = tp.objSize

        if not selected:
            show_message_box("No object selected. Please select a map object first")
            return {'CANCELLED'}

        for obj in selected:
            if "Object type" not in obj or obj["Object type"] != "MAP":
                continue

            # Delete existing contour lines owned by this map
            for o in list(bpy.context.scene.objects):
                if o.get("Object type") == "LINES" and o.get("PARENT") == obj:
                    bpy.data.objects.remove(o, do_unlink=True)

            bpy.ops.object.select_all(action='DESELECT')

            bpy.ops.mesh.primitive_plane_add(
                size=size + 10, enter_editmode=False, align='WORLD',
                location=bpy.context.scene.cursor.location,
            )
            plane = bpy.context.active_object
            plane.name = "CuttingPlane"
            plane.location.z += cl_offset

            arr = plane.modifiers.new(name="ArrayZ", type='ARRAY')
            arr.relative_offset_displace = (0, 0, 0)
            arr.constant_offset_displace = (0, 0, cl_distance)
            arr.use_relative_offset = False
            arr.use_constant_offset = True
            arr.count = 100

            sol = plane.modifiers.new(name="Solidify", type='SOLIDIFY')
            sol.thickness = cl_thickness

            bpy.context.view_layer.objects.active = plane
            bpy.ops.object.modifier_apply(modifier=arr.name)
            bpy.ops.object.modifier_apply(modifier=sol.name)

            bmod = plane.modifiers.new(name="Boolean", type='BOOLEAN')
            bmod.operation = 'INTERSECT'
            bmod.solver = 'MANIFOLD'
            bmod.use_hole_tolerant = True
            bmod.object = obj

            plane.name = obj.name + "_LINES"
            mat = bpy.data.materials.get("WHITE")
            plane.data.materials.clear()
            plane.data.materials.append(mat)
            write_metadata(plane, type="LINES")
            plane["PARENT"] = obj

            bpy.context.view_layer.objects.active = plane
            bpy.ops.object.modifier_apply(modifier=bmod.name)

        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = selected[0]
        return {'FINISHED'}


class TP3D_OT_Dummy(bpy.types.Operator):
    bl_idname = "tp3d.dummy"
    bl_label = "Placeholder Operator"
    bl_description = "This feature is now fully unlocked"

    def execute(self, context):
        show_message_box("All features are now fully unlocked!")
        return {'FINISHED'}

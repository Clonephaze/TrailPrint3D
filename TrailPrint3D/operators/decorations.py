"""Decoration operators — bottom mark, mountain coloring, contour lines."""

import bmesh  # type: ignore
import bpy  # type: ignore

from ..metadata import write_metadata
from ..text.base import BottomText
from ..utils import show_message_box
from .helpers import find_map_objects, find_plate_objects


class TP3D_OT_BottomMark(bpy.types.Operator):
    bl_idname = "tp3d.bottom_mark"
    bl_label = "Bottom Mark"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        targets = find_plate_objects()
        if not targets:
            show_message_box("No map or plate object found. Generate a terrain first.")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')

        for zobj in targets:
            zobj.select_set(True)
            bpy.context.view_layer.objects.active = zobj
            BottomText(zobj)
            bpy.ops.object.select_all(action='DESELECT')

        bpy.context.view_layer.objects.active = targets[0]
        for o in targets:
            o.select_set(True)
        return {'FINISHED'}


class TP3D_OT_ColorMountain(bpy.types.Operator):
    bl_idname = "tp3d.color_mountain"
    bl_label = "Color Mountains"
    bl_description = "Add color to mountain areas above specified threshold height"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import numpy as np

        map_objs = find_map_objects()
        threshold_pct = bpy.context.scene.tp3d.mountain_treshold

        if not map_objs:
            show_message_box("No map object found. Generate a terrain first.")
            return {'CANCELLED'}

        # Ensure MOUNTAIN material exists
        from ..materials import create_material, MATERIAL_COLORS
        mat = bpy.data.materials.get("MOUNTAIN")
        if mat is None:
            mat = create_material("MOUNTAIN", MATERIAL_COLORS["MOUNTAIN"])

        colored_any = False
        for obj in map_objs:

            mesh = obj.data

            # Compute Z bounds from actual vertex positions (post-shift)
            n_verts = len(mesh.vertices)
            co_arr = np.empty(n_verts * 3, dtype=np.float64)
            mesh.vertices.foreach_get("co", co_arr)
            z_vals = co_arr[2::3]
            min_z = float(z_vals.min())
            max_z = float(z_vals.max())

            if max_z <= min_z:
                continue

            tres = min_z + (max_z - min_z) * threshold_pct / 100.0

            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(mesh)

            base_idx = mesh.materials.find("BASE")
            mtn_idx = mesh.materials.find("MOUNTAIN")
            if mtn_idx == -1:
                mesh.materials.append(mat)
                mtn_idx = len(mesh.materials) - 1

            for face in bm.faces:
                if abs(face.normal.z) < 0.02:
                    continue
                avg_z = sum(v.co.z for v in face.verts) / len(face.verts)
                if avg_z > tres and face.material_index == base_idx:
                    face.material_index = mtn_idx
                elif avg_z <= tres and face.material_index == mtn_idx:
                    face.material_index = base_idx

            bmesh.update_edit_mesh(mesh)
            bpy.ops.object.mode_set(mode='OBJECT')
            colored_any = True

        return {'FINISHED'}


class TP3D_OT_ContourLines(bpy.types.Operator):
    bl_idname = "tp3d.contour_lines"
    bl_label = "Contour Lines"
    bl_description = "Generate contour lines on the map"

    def execute(self, context):
        map_objs = find_map_objects()
        tp = bpy.context.scene.tp3d
        cl_thickness = tp.cl_thickness
        cl_distance = tp.cl_distance
        cl_offset = tp.cl_offset
        size = tp.objSize

        if not map_objs:
            show_message_box("No map object found. Generate a terrain first.")
            return {'CANCELLED'}

        # Small Z lift so contour geometry doesn't overlap the terrain surface
        CONTOUR_Z_OFFSET = 0.05

        for obj in map_objs:

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
            from ..materials import create_material, MATERIAL_COLORS
            mat = bpy.data.materials.get("WHITE")
            if mat is None:
                mat = create_material("WHITE", MATERIAL_COLORS["WHITE"])
            plane.data.materials.clear()
            plane.data.materials.append(mat)
            write_metadata(plane, type="LINES")
            plane["PARENT"] = obj

            bpy.context.view_layer.objects.active = plane
            bpy.ops.object.modifier_apply(modifier=bmod.name)

            # Lift contour lines slightly above terrain to prevent Z-fighting
            plane.location.z += CONTOUR_Z_OFFSET

        bpy.ops.object.select_all(action='DESELECT')
        for obj in map_objs:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = map_objs[0]
        return {'FINISHED'}


class TP3D_OT_Dummy(bpy.types.Operator):
    bl_idname = "tp3d.dummy"
    bl_label = "Placeholder Operator"
    bl_description = "This feature is now fully unlocked"

    def execute(self, context):
        show_message_box("All features are now fully unlocked!")
        return {'FINISHED'}

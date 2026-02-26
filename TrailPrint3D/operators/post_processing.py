"""Post-processing operators — rescale, thicken, magnet holes, dovetail."""

import math

import bmesh  # type: ignore
import bpy  # type: ignore
from mathutils import Euler, Vector  # type: ignore

from ..geometry.mesh_utils import selectBottomFaces, selectTopFaces
from ..utils import show_message_box
from .helpers import find_map_objects, find_generation_objects, find_plate_objects


class TP3D_OT_Rescale(bpy.types.Operator):
    bl_idname = "tp3d.rescale"
    bl_label = "Scale Z Height"
    bl_description = "Rescale elevation height of currently selected object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        multiZ = bpy.context.scene.tp3d.get('rescaleMultiplier', 1)
        selected = find_generation_objects()
        if not selected:
            show_message_box("No map objects found. Generate a terrain first.")
            return {'CANCELLED'}
        lowestZ = 1000

        for obj in selected:
            if obj.type == 'MESH':
                for v in obj.data.vertices:
                    if 0.1 < v.co.z < lowestZ:
                        lowestZ = v.co.z
            elif obj.type == 'CURVE' and lowestZ == 1000:
                for spline in obj.data.splines:
                    for pt in spline.bezier_points:
                        if 0.1 < pt.co.z < lowestZ:
                            lowestZ = pt.co.z

        for obj in selected:
            if lowestZ != 1000 and obj.type == 'MESH':
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                bm = bmesh.from_edit_mesh(obj.data)
                for v in bm.verts:
                    if v.co.z > 0.1:
                        v.co.z = (v.co.z - lowestZ) * multiZ + lowestZ
                bmesh.update_edit_mesh(obj.data)
                bpy.ops.object.mode_set(mode='OBJECT')

            if lowestZ != 1000 and obj.type == 'CURVE':
                for spline in obj.data.splines:
                    for pt in spline.bezier_points:
                        if pt.co.z > -0.5:
                            pt.co.z = (pt.co.z - lowestZ) * multiZ + lowestZ
                    for pt in spline.points:
                        if pt.co.z > -0.5:
                            pt.co.z = (pt.co.z - lowestZ) * multiZ + lowestZ

            bpy.ops.object.mode_set(mode='OBJECT')
            if "Elevation Scale" in obj:
                obj["Elevation Scale"] *= multiZ

        return {'FINISHED'}


class TP3D_OT_Thicken(bpy.types.Operator):
    bl_idname = "tp3d.thicken"
    bl_label = "Thicken Map"
    bl_description = "Increase thickness of selected map"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        all_objs = find_generation_objects()
        map_objs = [o for o in all_objs if o.get("Object type") == "MAP"]
        val = bpy.context.scene.tp3d.thickenValue

        if not map_objs:
            show_message_box("No map object found. Generate a terrain first.")
            return {'CANCELLED'}

        bpy.context.tool_settings.mesh_select_mode = (False, False, True)
        bpy.ops.object.select_all(action='DESELECT')

        for zobj in all_objs:
            ot = zobj.get("Object type")
            if ot in ("TRAIL", "WATER", "FOREST", "CITY"):
                zobj.location.z += val
            elif ot == "MAP":
                zobj.select_set(True)
                bpy.context.view_layer.objects.active = zobj
                selectBottomFaces(zobj)
                bpy.ops.mesh.select_more()
                bpy.ops.mesh.select_all(action='INVERT')
                bm = bmesh.from_edit_mesh(zobj.data)
                verts_to_move = set()
                for f in bm.faces:
                    if f.select:
                        verts_to_move.update(f.verts)
                for v in verts_to_move:
                    v.co.z += val
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')
                zobj.select_set(False)
                zobj["minThickness"] += val

        bpy.context.view_layer.objects.active = map_objs[0]
        for o in all_objs:
            o.select_set(True)
        return {'FINISHED'}


class TP3D_OT_MagnetHoles(bpy.types.Operator):
    bl_idname = "tp3d.magnet_holes"
    bl_label = "Magnet Holes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        targets = find_plate_objects()
        if not targets:
            show_message_box("No map or plate object found. Generate a terrain first.")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')

        for zobj in targets:
            if zobj.type != 'MESH':
                continue

            zobj.select_set(True)
            bpy.context.view_layer.objects.active = zobj
            obj_size = zobj.get("objSize", bpy.context.scene.tp3d.objSize)

            magnetDiameter = bpy.context.scene.tp3d.magnetDiameter
            magnetHeight = bpy.context.scene.tp3d.magnetHeight

            selectBottomFaces(zobj)

            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(zobj.data)
            wm = zobj.matrix_world
            z_values = [(wm @ f.calc_center_median()).z for f in bm.faces if f.select]
            zValue = min(z_values) if z_values else 0
            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.context.scene.cursor.location = zobj.location

            radius = obj_size / 3
            cyls = []
            for i in range(4):
                angle = i * math.radians(90)
                pos = zobj.location + Vector((math.cos(angle) * radius, math.sin(angle) * radius, zValue))
                bpy.ops.mesh.primitive_cylinder_add(radius=magnetDiameter / 2, depth=magnetHeight, location=pos)
                cyls.append(bpy.context.active_object)

            bpy.ops.object.select_all(action='DESELECT')
            for c in cyls:
                c.select_set(True)
            bpy.context.view_layer.objects.active = cyls[0]
            bpy.ops.object.join()
            merged = bpy.context.active_object

            bpy.ops.object.select_all(action='DESELECT')
            zobj.select_set(True)
            bpy.context.view_layer.objects.active = zobj
            mod = zobj.modifiers.new(name="MagnetCutout", type='BOOLEAN')
            mod.operation = 'DIFFERENCE'
            mod.object = merged
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(merged, do_unlink=True)
            zobj["MagnetHoles"] = True

            bpy.ops.object.select_all(action='DESELECT')

        bpy.context.view_layer.objects.active = targets[0]
        for o in targets:
            o.select_set(True)
        return {'FINISHED'}


class TP3D_OT_Dovetail(bpy.types.Operator):
    bl_idname = "tp3d.dovetail"
    bl_label = "Dovetail Joints"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        targets = find_plate_objects()
        if not targets:
            show_message_box("No map or plate object found. Generate a terrain first.")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')

        for zobj in targets:
            if zobj.type != 'MESH':
                continue
            obj_size = zobj.get("objSize")
            if obj_size is None:
                continue

            zobj.select_set(True)
            bpy.context.view_layer.objects.active = zobj

            dovetailSize = 15
            if obj_size <= 50:
                dovetailSize = 5
            elif obj_size <= 75:
                dovetailSize = 10
            dovetailHeight = 3

            selectBottomFaces(zobj)
            bm = bmesh.from_edit_mesh(zobj.data)
            wm = zobj.matrix_world
            z_values = [(wm @ f.calc_center_median()).z for f in bm.faces if f.select]
            zValue = min(z_values) if z_values else 0
            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.context.scene.cursor.location = zobj.location

            radius = obj_size / 2 * 0.866 - dovetailSize / 2
            cyls = []
            for i in range(6):
                angle = i * math.radians(60) + math.radians(30)
                pos = zobj.location + Vector((
                    math.cos(angle) * radius,
                    math.sin(angle) * radius,
                    zValue + dovetailHeight / 2,
                ))
                rot = Euler((0, 0, angle - math.radians(90)), 'XYZ')
                bpy.ops.mesh.primitive_cylinder_add(
                    vertices=3, radius=dovetailSize, depth=dovetailHeight,
                    location=pos, rotation=rot,
                )
                cyls.append(bpy.context.active_object)

            bpy.ops.object.select_all(action='DESELECT')
            for c in cyls:
                c.select_set(True)
            bpy.context.view_layer.objects.active = cyls[0]
            bpy.ops.object.join()
            merged = bpy.context.active_object

            selectTopFaces(merged)
            bm = bmesh.from_edit_mesh(merged.data)
            for f in bm.faces:
                if f.select:
                    center = f.calc_center_median()
                    for v in f.verts:
                        v.co = center + (v.co - center) * 1.05
            bmesh.update_edit_mesh(merged.data, loop_triangles=False)
            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.object.select_all(action='DESELECT')
            zobj.select_set(True)
            bpy.context.view_layer.objects.active = zobj
            mod = zobj.modifiers.new(name="DovetailCutout", type='BOOLEAN')
            mod.operation = 'DIFFERENCE'
            mod.object = merged
            zobj["Dovetail"] = True
            bpy.ops.object.modifier_apply(modifier=mod.name)
            bpy.data.objects.remove(merged, do_unlink=True)

            bpy.ops.object.select_all(action='DESELECT')

        bpy.context.view_layer.objects.active = targets[0]
        for o in targets:
            o.select_set(True)
        return {'FINISHED'}

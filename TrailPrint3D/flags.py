"""Flag markers — start/finish flags placed at trail endpoints."""

import math

import bpy  # type: ignore


def create_flag(name: str, position, flag_type: str = "START",
                height: float = 5.0, flag_width: float = 3.0):
    """Create a 3-D flag marker (pole + triangular flag + base insert).

    Parameters:
        name: Blender object name.
        position: ``(x, y, z)`` location.
        flag_type: ``"START"`` (green) or ``"FINISH"`` (red).
        height: Pole height in mm.
        flag_width: Flag banner width in mm.

    Returns:
        The joined flag object.
    """
    pole_radius = 0.4
    insert_depth = 2.0
    base_radius = 0.8
    base_height = 0.5

    # 1. Pole
    bpy.ops.mesh.primitive_cylinder_add(
        radius=pole_radius, depth=height,
        location=(position[0], position[1], position[2] + height / 2),
    )
    pole = bpy.context.active_object
    pole.name = f"{name}_Pole"

    # 2. Insert part (below surface)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=pole_radius * 0.9, depth=insert_depth,
        location=(position[0], position[1], position[2] - insert_depth / 2),
    )
    insert_part = bpy.context.active_object
    insert_part.name = f"{name}_Insert"

    # 3. Base
    bpy.ops.mesh.primitive_cylinder_add(
        radius=base_radius, depth=base_height,
        location=(position[0], position[1], position[2] + base_height / 2),
    )
    base = bpy.context.active_object
    base.name = f"{name}_Base"

    # 4. Triangular flag
    flag_height = flag_width * 0.6
    verts = [
        (0, 0, 0),
        (flag_width, flag_height / 2, 0),
        (0, flag_height, 0),
    ]
    faces = [(0, 1, 2)]
    mesh = bpy.data.meshes.new(f"{name}_Flag_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    flag = bpy.data.objects.new(f"{name}_Flag", mesh)
    bpy.context.collection.objects.link(flag)
    flag.location = (
        position[0] + pole_radius,
        position[1],
        position[2] + height - flag_height / 2,
    )
    flag.rotation_euler = (math.radians(90), 0, 0)

    # Materials
    if flag_type == "START":
        color = (0.0, 0.8, 0.0, 1.0)
        mat_name = "FLAG_START"
    else:
        color = (0.9, 0.0, 0.0, 1.0)
        mat_name = "FLAG_FINISH"

    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = color
            bsdf.inputs["Metallic"].default_value = 0.0
            bsdf.inputs["Roughness"].default_value = 0.5
        mat.diffuse_color = color

    if flag.data.materials:
        flag.data.materials[0] = mat
    else:
        flag.data.materials.append(mat)

    pole_mat = bpy.data.materials.get("FLAG_POLE")
    if pole_mat is None:
        pole_mat = bpy.data.materials.new(name="FLAG_POLE")
        pole_mat.use_nodes = True
        bsdf = pole_mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.3, 0.3, 0.3, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.8
            bsdf.inputs["Roughness"].default_value = 0.2
        pole_mat.diffuse_color = (0.3, 0.3, 0.3, 1.0)

    for part in (pole, insert_part, base):
        if part.data.materials:
            part.data.materials[0] = pole_mat
        else:
            part.data.materials.append(pole_mat)

    # Join all parts
    bpy.ops.object.select_all(action='DESELECT')
    for part in (pole, insert_part, base, flag):
        part.select_set(True)
    bpy.context.view_layer.objects.active = pole
    bpy.ops.object.join()

    combined = bpy.context.active_object
    combined.name = name
    combined["Object type"] = "FLAG"
    combined["Flag Type"] = flag_type
    combined["Addon"] = "TrailPrint3D"

    print(f"Created {flag_type} flag at position: "
          f"({position[0]:.2f}, {position[1]:.2f}, {position[2]:.2f})")
    return combined


def find_elevation_extremes(obj):
    """Return ``(min_point, max_point)`` as world-space ``(x,y,z)`` tuples."""
    if obj.type != 'MESH':
        return None, None

    matrix = obj.matrix_world
    min_z, max_z = float('inf'), float('-inf')
    min_pt = max_pt = None

    for vert in obj.data.vertices:
        wc = matrix @ vert.co
        if wc.z < min_z:
            min_z = wc.z
            min_pt = (wc.x, wc.y, wc.z)
        if wc.z > max_z:
            max_z = wc.z
            max_pt = (wc.x, wc.y, wc.z)

    print(f"Terrain analysis: Lowest={min_z:.2f}mm, Highest={max_z:.2f}mm, "
          f"Diff={max_z - min_z:.2f}mm")
    return min_pt, max_pt


def find_path_endpoints(curve_obj):
    """Return ``(start_point, end_point)`` as world-space ``(x,y,z)`` tuples."""
    if curve_obj is None or curve_obj.type != 'CURVE':
        print("Error: Provided object is not a valid curve object")
        return None, None

    curve_data = curve_obj.data
    mtx = curve_obj.matrix_world

    if len(curve_data.splines) == 0:
        print("Error: Curve has no splines")
        return None, None

    spline = curve_data.splines[0]

    from mathutils import Vector  # type: ignore

    if len(spline.points) > 0:
        start_local = spline.points[0].co[:3]
        end_local = spline.points[-1].co[:3]
    elif len(spline.bezier_points) > 0:
        start_local = spline.bezier_points[0].co
        end_local = spline.bezier_points[-1].co
    else:
        print("Error: Spline has no points")
        return None, None

    sw = mtx @ Vector(start_local)
    ew = mtx @ Vector(end_local)

    start_point = (sw.x, sw.y, sw.z)
    end_point = (ew.x, ew.y, ew.z)

    print(f"Path analysis: Start=({sw.x:.2f}, {sw.y:.2f}, {sw.z:.2f})")
    print(f"Path analysis: End=({ew.x:.2f}, {ew.y:.2f}, {ew.z:.2f})")
    return start_point, end_point

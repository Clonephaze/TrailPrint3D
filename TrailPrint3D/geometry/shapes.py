"""Primitive shape creation — hexagon, rectangle, circle with subdivision."""

import math

import bpy  # type: ignore


def create_hexagon(radius, name="Hexagon", num_subdivisions=8):
    """Create a flat hexagon at origin, subdivide, and return the object."""
    verts = []
    for i in range(6):
        angle = math.radians(60 * i)
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        verts.append((x, y, 0))
    verts.append((0, 0, 0))  # center
    faces = [[i, (i + 1) % 6, 6] for i in range(6)]

    mesh = bpy.data.meshes.new("Hexagon")
    obj = bpy.data.objects.new("Hexagon", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    # Single-pass subdivision: equivalent to num_subdivisions rounds of
    # subdivide(number_cuts=1), each of which doubles edge segments.
    # One call with (2^n − 1) cuts produces the same segment count.
    cuts = (2 ** num_subdivisions) - 1
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=cuts)
    bpy.ops.object.mode_set(mode='OBJECT')

    obj.name = name
    obj.data.name = name
    return obj


def create_rectangle(width, height, name="Rectangle", num_subdivisions=8):
    """Create a flat rectangle at origin, subdivide, and return the object."""
    verts = [
        (-width / 2, -height / 2, 0),
        (width / 2, -height / 2, 0),
        (width / 2, height / 2, 0),
        (-width / 2, height / 2, 0),
    ]
    faces = [[0, 1, 2, 3]]

    mesh = bpy.data.meshes.new("Rectangle")
    obj = bpy.data.objects.new("Rectangle", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    cuts = (2 ** num_subdivisions) - 1
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=cuts)
    bpy.ops.object.mode_set(mode='OBJECT')

    obj.name = name
    obj.data.name = name
    return obj


def create_circle(radius, name="Circle", num_subdivisions=8, num_segments=64):
    """Create a filled circle at origin, subdivide, and return the object."""
    try:
        bpy.ops.object.mode_set(mode='OBJECT')
    except RuntimeError:
        pass  # Already in OBJECT mode or no active object

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    verts = []
    for i in range(num_segments):
        angle = math.radians(360 * i / num_segments)
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        verts.append((x, y, 0))

    edges = [(i, (i + 1) % num_segments) for i in range(num_segments)]
    mesh.from_pydata(verts, edges, [])
    mesh.update()

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.fill_grid()
    cuts = (2 ** num_subdivisions) - 1
    bpy.ops.mesh.subdivide(number_cuts=cuts)
    bpy.ops.object.mode_set(mode='OBJECT')

    return obj

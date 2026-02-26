"""Material management — setup, creation, and the canonical colour palette.

Replaces 8 identical 28-line blocks in the original ``setupColors()`` with a
compact dict + single helper loop (~30 lines instead of ~280).
"""

import bpy  # type: ignore

# Canonical material name → RGBA base colour mapping
MATERIAL_COLORS: dict[str, tuple[float, float, float, float]] = {
    "BASE":     (0.05, 0.70, 0.05, 1.0),   # green — terrain
    "FOREST":   (0.05, 0.25, 0.05, 1.0),   # dark green
    "MOUNTAIN": (0.50, 0.50, 0.50, 1.0),   # grey
    "WATER":    (0.00, 0.00, 0.80, 1.0),   # blue
    "TRAIL":    (1.00, 0.00, 0.00, 1.0),   # red
    "CITY":     (0.70, 0.70, 0.10, 1.0),   # yellow
    "BLACK":    (0.00, 0.00, 0.00, 1.0),   # black
    "WHITE":    (1.00, 1.00, 1.00, 1.0),   # white
}


def create_material(name: str, color: tuple[float, float, float, float]) -> bpy.types.Material:
    """Get or create a Principled-BSDF material with the given *color*.

    If the material already exists it is reused (its base colour is updated).
    """
    if name in bpy.data.materials:
        mat = bpy.data.materials[name]
    else:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Ensure a Principled BSDF exists
    bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf:
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)

    # Ensure a Material Output exists
    output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if not output:
        output = nodes.new(type="ShaderNodeOutputMaterial")
        output.location = (300, 0)

    # Wire BSDF → Output if not already connected
    if not bsdf.outputs["BSDF"].is_linked:
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    bsdf.inputs["Base Color"].default_value = color

    # Set viewport display colour so Solid mode shows the right tint
    mat.diffuse_color = color
    return mat


def setup_materials():
    """Ensure every material in :data:`MATERIAL_COLORS` exists in the blend file."""
    for mat_name, color in MATERIAL_COLORS.items():
        create_material(mat_name, color)

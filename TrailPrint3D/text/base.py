"""Core text creation, update, and mesh-conversion helpers."""

import platform
import time as _time

import bpy  # type: ignore

from ..utils import get_chinese_font
from ..geometry.mesh_utils import recalculateNormals, transform_MapObject


# ---------------------------------------------------------------------------
# Module-level font cache — resolved once per session
# ---------------------------------------------------------------------------
_resolved_font: str | None = None


def _resolve_font(font_path: str = "") -> str:
    """Return a usable font path, caching the result."""
    global _resolved_font
    if _resolved_font is not None:
        return _resolved_font

    if font_path:
        _resolved_font = font_path
        return _resolved_font

    _resolved_font = get_chinese_font()
    if _resolved_font:
        return _resolved_font

    # Platform defaults
    if platform.system() == "Windows":
        _resolved_font = "C:/WINDOWS/FONTS/ariblk.ttf"
    elif platform.system() == "Darwin":
        _resolved_font = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
    else:
        _resolved_font = ""

    return _resolved_font


# ---------------------------------------------------------------------------
# Text primitives
# ---------------------------------------------------------------------------

def create_text(
    name: str,
    text: str,
    position: tuple,
    scale_multiplier: float = 1.0,
    rotation: tuple = (0, 0, 0),
    extrude: float = 20,
    font_path: str = "",
) -> bpy.types.Object:
    """Create a FONT object with *text* at *position*.

    Parameters
    ----------
    name : str
        Blender object / data-block name.
    text : str
        Body text to display.
    position : tuple
        (x, y, z) location.
    scale_multiplier : float
        Uniform X/Y scale.
    rotation : tuple
        Euler rotation (radians).
    extrude : float
        Extrusion depth.
    font_path : str, optional
        Override font file path.  If empty, auto-resolved.

    Returns
    -------
    bpy.types.Object
        The newly created text object.
    """
    txt_data = bpy.data.curves.new(name=name, type='FONT')
    txt_obj = bpy.data.objects.new(name=name, object_data=txt_data)
    bpy.context.collection.objects.link(txt_obj)

    txt_data.body = text
    txt_data.extrude = extrude

    font = _resolve_font(font_path)
    try:
        if font:
            txt_data.font = bpy.data.fonts.load(font)
    except (OSError, RuntimeError):
        pass  # Fall back to Blender built-in font

    txt_data.align_x = 'CENTER'
    txt_data.align_y = 'CENTER'

    txt_obj.scale = (scale_multiplier, scale_multiplier, 1)
    txt_obj.location = position
    txt_obj.rotation_euler = rotation
    txt_obj.location.z -= 1

    return txt_obj


def update_text_object(obj_name: str, new_text: str) -> None:
    """Replace the body text of a FONT object."""
    text_obj = bpy.data.objects.get(obj_name)
    if text_obj and text_obj.type == 'FONT':
        text_obj.data.body = new_text


def convert_text_to_mesh(
    text_obj_name: str,
    mesh_obj_name: str,
    merge: bool = True,
) -> None:
    """Convert a FONT object to MESH and optionally boolean-intersect with *mesh_obj_name*."""
    text_obj = bpy.data.objects.get(text_obj_name)
    mesh_obj = bpy.data.objects.get(mesh_obj_name)

    if not text_obj or not mesh_obj:
        return

    _t0 = _time.perf_counter()
    bpy.ops.object.select_all(action='DESELECT')
    text_obj.select_set(True)
    bpy.context.view_layer.objects.active = text_obj

    bpy.ops.object.convert(target='MESH')
    _t1 = _time.perf_counter()

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.002)
    bpy.ops.object.mode_set(mode='OBJECT')
    _t2 = _time.perf_counter()

    recalculateNormals(text_obj)

    # Nudge Z up/down (original automerge workaround)
    text_obj.location.z += 1
    text_obj.location.z -= 1

    bpy.context.tool_settings.use_mesh_automerge = False

    if merge:
        bool_mod = text_obj.modifiers.new(name="Boolean", type='BOOLEAN')
        bool_mod.object = mesh_obj
        bool_mod.operation = 'INTERSECT'
        bool_mod.solver = 'MANIFOLD'

        bpy.ops.object.select_all(action='DESELECT')
        text_obj.select_set(True)
        bpy.context.view_layer.objects.active = text_obj
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        text_obj.location.z += 0.4

    _t3 = _time.perf_counter()
    print(f"[TIMING]     convert_text '{text_obj_name}': font→mesh={_t1-_t0:.2f}s, remDoubles={_t2-_t1:.2f}s, boolean={_t3-_t2:.2f}s, total={_t3-_t0:.2f}s")


def BottomText(obj) -> None:
    """Place a name label on the bottom of *obj* (for bottom-mark operator)."""
    obj_name = obj.name
    obj_size = obj.get("objSize")
    if obj_size is None:
        return

    cx = obj.location.x
    cy = obj.location.y

    tName = create_text("t_name", "Name", (0, 0, 1.1), obj_size / 10)
    transform_MapObject(tName, cx, cy)
    tName.data.extrude = 0.1
    tName.scale.x *= -1

    update_text_object("t_name", obj_name)
    convert_text_to_mesh("t_name", obj.name, False)

    tName.name = obj_name + "_Mark"

    bpy.ops.object.select_all(action='DESELECT')
    tName.select_set(True)
    bpy.context.view_layer.objects.active = tName

    mat = bpy.data.materials.get("TRAIL")
    tName.data.materials.clear()
    tName.data.materials.append(mat)

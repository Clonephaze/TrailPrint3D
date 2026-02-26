"""Input validation — version check, file existence, export path."""

import os

import bpy  # type: ignore

from ..context import GenerationContext
from ..utils import show_message_box, toggle_console


REQUIRED_VERSION = (4, 5, 0)


def validate_inputs(ctx: GenerationContext, gen_type: int) -> bool:
    """Return *True* if all inputs are valid, else show an error and return *False*.

    Parameters
    ----------
    ctx : GenerationContext
        Populated context (paths, settings, etc.).
    gen_type : int
        0 = single GPX, 1 = batch, 2 = center-point map, 3 = two-point map,
        4 = center-point map with path.
    """
    # Blender version gate
    if bpy.app.version < REQUIRED_VERSION:
        v = REQUIRED_VERSION
        show_message_box(
            f"This plugin requires Blender {v[0]}.{v[1]} or higher. "
            f"(You are using {bpy.app.version_string})."
        )
        return False

    # GPX / IGC file for single-file and center+path modes
    if gen_type in (0, 4):
        if not ctx.gpx_file_path:
            show_message_box("File path is empty! Please select a valid file.")
            toggle_console()
            return False
        if not os.path.isfile(ctx.gpx_file_path):
            show_message_box(f"Invalid file path: {ctx.gpx_file_path}. Please select a valid file.")
            toggle_console()
            return False
        ext = os.path.splitext(ctx.gpx_file_path)[1].lower()
        if ext not in ('.gpx', '.igc'):
            show_message_box("Invalid file format. Please use .GPX or .IGC files")
            toggle_console()
            return False

    # Chain directory for batch mode
    if gen_type == 1:
        if not ctx.gpx_chain_path:
            show_message_box("Chain path is empty! Please select a valid folder.")
            toggle_console()
            return False

    # Export path — only required when auto-export is enabled
    auto_export = getattr(bpy.context.scene.tp3d, 'autoExport', False)
    auto_3mf = getattr(bpy.context.scene.tp3d, 'auto3mfExport', False)
    if auto_export or auto_3mf:
        if not ctx.exportPath:
            show_message_box("Auto-export is enabled but export path is empty. "
                             "Please set an export directory or disable auto-export.")
            toggle_console()
            return False
        if not os.path.isdir(ctx.exportPath):
            show_message_box(f"Invalid export directory: {ctx.exportPath}. "
                             "Please select a valid directory.")
            toggle_console()
            return False

    return True

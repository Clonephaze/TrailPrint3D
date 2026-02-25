"""UI helper utilities — message boxes, console toggle, font detection, camera zoom."""

import os
import platform

import bpy  # type: ignore


def show_message_box(message: str, ic: str = "ERROR", ti: str = "ERROR"):
    """Show a popup message in the Blender UI.

    Parameters:
        message: Text to display.
        ic: Icon type — ``"ERROR"``, ``"INFO"``, ``"WARNING"``.
        ti: Popup window title.
    """
    def draw(self, context):
        self.layout.label(text=message)

    print(message)
    bpy.context.window_manager.popup_menu(draw, title=ti, icon=ic)


def toggle_console():
    """Toggle the Blender system console (Windows only)."""
    try:
        if platform.system() == "Windows":
            bpy.ops.wm.console_toggle()
    except RuntimeError as e:
        print(f"Cannot toggle console: {e}")


def get_chinese_font() -> str:
    """Find a CJK-capable system font and return its path, or ``""`` if none found.

    Checks common font locations for macOS, Windows, and Linux.
    """
    if platform.system() == "Darwin":
        possible_fonts = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Supplemental/Songti.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        ]
    elif platform.system() == "Windows":
        possible_fonts = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/simkai.ttf",
        ]
    else:
        possible_fonts = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        ]

    for font_path in possible_fonts:
        if os.path.exists(font_path):
            print(f"Found available font: {font_path}")
            return font_path

    print("Warning: No system font found, text may not display correctly")
    return ""


def resolve_font(font_path: str = "") -> str:
    """Return *font_path* if non-empty, otherwise auto-detect a system font.

    Falls back to platform-specific defaults as a last resort.
    """
    if font_path:
        return font_path

    found = get_chinese_font()
    if found:
        return found

    # Absolute last resort
    if platform.system() == "Windows":
        return "C:/WINDOWS/FONTS/ariblk.ttf"
    elif platform.system() == "Darwin":
        return "/System/Library/Fonts/Supplemental/Arial Black.ttf"
    return ""


def zoom_camera_to_selected(obj):
    """Frame the 3-D viewport on *obj*."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)

    area = next((a for a in bpy.context.screen.areas if a.type == "VIEW_3D"), None)
    if area is None:
        return
    region = area.regions[-1]

    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.view3d.view_selected(use_all_regions=False)

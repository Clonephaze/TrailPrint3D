"""UI Panel classes — sub-panel architecture.

Registration order matters: parent panels must be registered before children.
"""

from .main import TP3D_PT_main
from .generate import TP3D_PT_generate
from .terrain import TP3D_PT_terrain
from .scale import TP3D_PT_scale
from .osm import TP3D_PT_osm
from .flags import TP3D_PT_flags
from .text import TP3D_PT_text
from .api import TP3D_PT_api
from .export import TP3D_PT_export
from .post_processing import TP3D_PT_post_processing
from .tools import TP3D_PT_tools, TP3D_PT_pins, TP3D_PT_custom_map, TP3D_PT_batch, TP3D_PT_special
from .info import TP3D_PT_info, TP3D_PT_statistics, TP3D_PT_attribution

# Parent panels MUST come before their children
PANEL_CLASSES = [
    # Main panel (parent for generation sub-panels)
    TP3D_PT_main,
    TP3D_PT_generate,
    TP3D_PT_terrain,
    TP3D_PT_scale,
    TP3D_PT_osm,
    TP3D_PT_flags,
    TP3D_PT_text,
    TP3D_PT_api,

    # Export (own top-level)
    TP3D_PT_export,

    # Post Processing (own top-level)
    TP3D_PT_post_processing,

    # Tools (parent + children)
    TP3D_PT_tools,
    TP3D_PT_pins,
    TP3D_PT_custom_map,
    TP3D_PT_batch,
    TP3D_PT_special,

    # Info (parent + children)
    TP3D_PT_info,
    TP3D_PT_statistics,
    TP3D_PT_attribution,
]

__all__ = [cls.__name__ for cls in PANEL_CLASSES] + ["PANEL_CLASSES"]

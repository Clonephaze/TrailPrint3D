"""
TrailPrint3D — Blender addon for converting GPS tracks to 3D printable terrain.

This is the **modular rewrite** (v3.0).  The original monolithic script
(``TrailPrint3D.py``, ~6 300 lines) has been split into focused sub-packages.

Package layout::

    TrailPrint3D/
    ├── __init__.py          ← you are here
    ├── context.py           ← GenerationContext dataclass
    ├── coordinates.py       ← GPS ↔ Blender coordinate conversions
    ├── export.py            ← STL / OBJ export helpers
    ├── flags.py             ← Start / finish flag markers
    ├── materials.py         ← Material colour definitions
    ├── metadata.py          ← Per-object metadata writing
    ├── properties.py        ← MyProperties PropertyGroup
    ├── utils.py             ← Small utilities (fonts, messages, console)
    ├── elevation/           ← Elevation API wrappers + cache
    ├── generation/          ← runGeneration() split into phases
    ├── geometry/            ← Shape creation, curves, booleans
    ├── gps/                 ← GPX / IGC file parsing
    ├── operators/           ← All bpy.types.Operator classes
    ├── osm/                 ← OpenStreetMap fetch & terrain colouring
    ├── panels/              ← All bpy.types.Panel classes
    └── text/                ← Text creation and layout helpers
"""

bl_info = {
    "name": "TrailPrint3D",
    "blender": (4, 5, 2),
    "category": "Object",
    "version": (3, 1, 0),
    "description": "Create 3D printable terrain models from GPS tracks",
    "warning": "",
    "doc_url": "https://github.com/badriram/TrailPrint3D",
    "tracker_url": "https://github.com/badriram/TrailPrint3D/issues",
    "support": "COMMUNITY",
}

import bpy  # type: ignore  # noqa: E402

from .properties import MyProperties  # noqa: E402
from .operators import OPERATOR_CLASSES  # noqa: E402
from .panels import PANEL_CLASSES  # noqa: E402


# All classes that need bpy.utils.register_class / unregister_class
_CLASSES = [MyProperties] + OPERATOR_CLASSES + PANEL_CLASSES


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Scene.tp3d = bpy.props.PointerProperty(type=MyProperties)


def unregister():
    del bpy.types.Scene.tp3d

    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)

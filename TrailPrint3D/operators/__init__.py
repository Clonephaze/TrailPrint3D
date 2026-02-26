"""Operator classes, split by domain."""

from .generation import TP3D_OT_Generate, TP3D_OT_BatchGenerate
from .export import TP3D_OT_Export
from .post_processing import (
    TP3D_OT_Rescale,
    TP3D_OT_Thicken,
    TP3D_OT_MagnetHoles,
    TP3D_OT_Dovetail,
)
from .decorations import (
    TP3D_OT_BottomMark,
    TP3D_OT_ColorMountain,
    TP3D_OT_ContourLines,
    TP3D_OT_Dummy,
)
from .utility import (
    TP3D_OT_PinCoords,
    TP3D_OT_OpenWebsite,
    TP3D_OT_JoinDiscord,
    TP3D_OT_ShowProps,
)

# Ordered list of all operator classes for register / unregister
OPERATOR_CLASSES = [
    TP3D_OT_Generate,
    TP3D_OT_BatchGenerate,
    TP3D_OT_Export,
    TP3D_OT_Rescale,
    TP3D_OT_Thicken,
    TP3D_OT_MagnetHoles,
    TP3D_OT_Dovetail,
    TP3D_OT_BottomMark,
    TP3D_OT_ColorMountain,
    TP3D_OT_ContourLines,
    TP3D_OT_Dummy,
    TP3D_OT_PinCoords,
    TP3D_OT_OpenWebsite,
    TP3D_OT_JoinDiscord,
    TP3D_OT_ShowProps,
]

__all__ = [cls.__name__ for cls in OPERATOR_CLASSES] + ["OPERATOR_CLASSES"]

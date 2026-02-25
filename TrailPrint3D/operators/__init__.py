"""Operator classes, split by domain."""

from .generation import MY_OT_runGeneration, MY_OT_BatchGeneration
from .export import MY_OT_ExportSTL
from .post_processing import (
    MY_OT_Rescale,
    MY_OT_thicken,
    MY_OT_MagnetHoles,
    MY_OT_Dovetail,
)
from .decorations import (
    MY_OT_BottomMark,
    MY_OT_ColorMountain,
    MY_OT_ContourLines,
    MY_OT_TerrainDummy,
)
from .utility import (
    MY_OT_PinCoords,
    MY_OT_OpenWebsite,
    MY_OT_JoinDiscord,
    OBJECT_OT_ShowCustomPropsPopup,
)

# Ordered list of all operator classes for register / unregister
OPERATOR_CLASSES = [
    MY_OT_runGeneration,
    MY_OT_BatchGeneration,
    MY_OT_ExportSTL,
    MY_OT_Rescale,
    MY_OT_thicken,
    MY_OT_MagnetHoles,
    MY_OT_Dovetail,
    MY_OT_BottomMark,
    MY_OT_ColorMountain,
    MY_OT_ContourLines,
    MY_OT_TerrainDummy,
    MY_OT_PinCoords,
    MY_OT_OpenWebsite,
    MY_OT_JoinDiscord,
    OBJECT_OT_ShowCustomPropsPopup,
]

__all__ = [cls.__name__ for cls in OPERATOR_CLASSES] + ["OPERATOR_CLASSES"]

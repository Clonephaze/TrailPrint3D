"""UI Panel classes."""

from .generate import MY_PT_Generate
from .advanced import MY_PT_Advanced
from .shapes import MY_PT_Shapes

PANEL_CLASSES = [
    MY_PT_Generate,
    MY_PT_Advanced,
    MY_PT_Shapes,
]

__all__ = [cls.__name__ for cls in PANEL_CLASSES] + ["PANEL_CLASSES"]

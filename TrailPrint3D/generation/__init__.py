"""Generation pipeline — splits the monolithic runGeneration() into phases."""

from .orchestrator import run_generation
from .progress import ProgressOverlay
from .validation import validate_inputs
from .loading import load_gps_data
from .terrain import create_terrain, create_terrain_mesh, apply_terrain_elevation
from .trail import create_trail
from .decorations import apply_decorations
from .finalize import finalize

__all__ = [
    "run_generation",
    "ProgressOverlay",
    "validate_inputs",
    "load_gps_data",
    "create_terrain",
    "create_terrain_mesh",
    "apply_terrain_elevation",
    "create_trail",
    "apply_decorations",
    "finalize",
]

"""GenerationContext — central state for a single map generation run.

Replaces ~50 mutable globals with a single explicit dataclass object.
Created once in the generation operator's execute(), populated from
bpy.context.scene.tp3d, then threaded through every helper via ``ctx``.
"""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class GenerationContext:
    """All state required for a complete terrain generation pass.

    Field names intentionally match the original camelCase globals so that
    consumer code (generation/, text/, etc.) can use ``ctx.scaleElevation``
    without translation.  The ``from_scene()`` constructor maps UI property
    names → these fields.
    """

    # ── Input parameters (from UI / scene properties) ──────────────────

    # File paths
    gpx_file_path: str = ""
    exportPath: str = ""
    gpx_chain_path: str = ""

    # Map parameters
    shape: str = "HEXAGON"
    name: str = ""
    size: int = 100
    num_subdivisions: int = 8
    shapeRotation: int = 0

    # Elevation
    scaleElevation: float = 2.0
    dataset: str = "aster30m"
    api_index: int = 2          # 0=OpenTopoData, 1=OpenElevation, 2=TerrainTiles
    selfHosted: str = ""
    fixedElevationScale: bool = False

    # Path
    pathThickness: float = 1.2
    pathScale: float = 0.8
    overwritePathElevation: bool = True

    # Scale
    scalemode: str = "FACTOR"
    scaleLon1: float = 0.0
    scaleLat1: float = 0.0
    scaleLon2: float = 0.0
    scaleLat2: float = 0.0

    # Text / shape settings
    textFont: str = ""
    textSize: int = 5
    textSizeTitle: int = 0
    overwriteLength: str = ""
    overwriteHeight: str = ""
    overwriteTime: str = ""
    outerBorderSize: int = 20
    text_angle_preset: int = 0
    plateThickness: float = 5.0
    plateInsertValue: float = 2.0

    # Map generation mode settings
    minThickness: int = 7
    xTerrainOffset: float = 0.0
    yTerrainOffset: float = 0.0
    singleColorMode: bool = True
    tolerance: float = 0.2
    disableCache: bool = False
    cacheSize: int = 50000

    # Flag settings
    addFlags: bool = False
    flagHeight: float = 5.0
    flagWidth: float = 3.0

    # Center-point generation
    jMapLat: float = 49.0
    jMapLon: float = 9.0
    jMapRadius: float = 200.0
    jMapLat1: float = 48.0
    jMapLon1: float = 8.0
    jMapLat2: float = 49.0
    jMapLon2: float = 9.0

    # Coloring toggles
    col_wActive: bool = False
    col_fActive: bool = False
    col_cActive: bool = False

    # ── Computed during generation ─────────────────────────────────────

    generation_type: int = 0    # 0=single, 1=batch, 2=center, 3=two-point, 4=center+trail
    autoScale: float = 1.0
    scaleHor: float = 0.0
    centerx: float = 0.0
    centery: float = 0.0
    lowestZ: float = 0.0
    highestZ: float = 0.0
    elevationOffset: float = 0.0
    additionalExtrusion: float = 0.0
    total_length: float = 0.0
    total_elevation: float = 0.0
    total_time: float = 0.0
    time_str: str = ""
    minLat: float = 0.0
    maxLat: float = 0.0
    minLon: float = 0.0
    maxLon: float = 0.0
    opentopoAddress: str = "https://api.opentopodata.org/v1/"
    gpx_sections: int = 0
    duration: float = 0.0

    # GPS data (populated by loading phase)
    coordinates: list = field(default_factory=list)
    coordinates2: list = field(default_factory=list)
    separate_paths: list = field(default_factory=list)
    blender_coords: list = field(default_factory=list)
    blender_coords_separate: list = field(default_factory=list)

    # Blender object references (set during generation)
    MapObject: Optional[Any] = None
    plateobj: Optional[Any] = None
    textobj: Optional[Any] = None
    curveObj: Optional[Any] = None

    # ── Factory / helpers ──────────────────────────────────────────────

    @classmethod
    def from_scene(cls, generation_type: int = 0) -> "GenerationContext":
        """Create a GenerationContext populated from ``bpy.context.scene.tp3d``."""
        import bpy
        props = bpy.context.scene.tp3d

        # Map api enum string to integer index
        api_map = {"OPENTOPODATA": 0, "OPEN-ELEVATION": 1, "TERRAIN-TILES": 2}
        api_str = props.get("api", "TERRAIN-TILES")
        api_index = api_map.get(api_str, 2)

        ctx = cls(
            gpx_file_path=props.get("file_path", ""),
            exportPath=props.get("export_path", ""),
            gpx_chain_path=props.get("chain_path", ""),
            shape=props.shape,
            name=props.get("trailName", ""),
            size=props.get("objSize", 100),
            num_subdivisions=props.get("num_subdivisions", 8),
            shapeRotation=props.get("shapeRotation", 0),
            scaleElevation=props.get("scaleElevation", 2.0),
            dataset=props.dataset,
            api_index=api_index,
            selfHosted=props.get("selfHosted", ""),
            fixedElevationScale=props.get("fixedElevationScale", False),
            pathThickness=props.get("pathThickness", 1.2),
            pathScale=props.get("pathScale", 0.8),
            overwritePathElevation=props.get("overwritePathElevation", True),
            scalemode=props.scalemode,
            scaleLon1=props.get("scaleLon1", 0.0),
            scaleLat1=props.get("scaleLat1", 0.0),
            scaleLon2=props.get("scaleLon2", 0.0),
            scaleLat2=props.get("scaleLat2", 0.0),
            textFont=props.get("textFont", ""),
            textSize=props.get("textSize", 5),
            textSizeTitle=props.get("textSizeTitle", 0),
            overwriteLength=props.get("overwriteLength", ""),
            overwriteHeight=props.get("overwriteHeight", ""),
            overwriteTime=props.get("overwriteTime", ""),
            outerBorderSize=props.get("outerBorderSize", 20),
            text_angle_preset=int(props.text_angle_preset),
            plateThickness=props.get("plateThickness", 5.0),
            plateInsertValue=props.plateInsertValue,
            minThickness=props.get("minThickness", 7),
            xTerrainOffset=props.get("xTerrainOffset", 0.0),
            yTerrainOffset=props.get("yTerrainOffset", 0.0),
            singleColorMode=props.get("singleColorMode", True),
            tolerance=props.tolerance,
            disableCache=props.get("disableCache", False),
            cacheSize=props.get("ccacheSize", 50000),
            addFlags=props.get("addFlags", False),
            flagHeight=props.get("flagHeight", 5.0),
            flagWidth=props.get("flagWidth", 3.0),
            jMapLat=props.get("jMapLat", 49.0),
            jMapLon=props.get("jMapLon", 9.0),
            jMapRadius=props.get("jMapRadius", 200.0),
            jMapLat1=props.get("jMapLat1", 48.0),
            jMapLon1=props.get("jMapLon1", 8.0),
            jMapLat2=props.get("jMapLat2", 49.0),
            jMapLon2=props.get("jMapLon2", 9.0),
            col_wActive=props.col_wActive,
            col_fActive=props.col_fActive,
            col_cActive=props.col_cActive,
            generation_type=generation_type,
        )

        # Derive opentopo address
        if ctx.selfHosted and ctx.api_index == 0:
            ctx.opentopoAddress = ctx.selfHosted
            print(f"!!using {ctx.opentopoAddress} instead of Opentopodata!!")

        return ctx

    def sync_to_scene(self):
        """Write computed values back to scene properties for UI display."""
        import bpy
        props = bpy.context.scene.tp3d
        props["sScaleHor"] = self.scaleHor
        props["sAutoScale"] = self.autoScale
        props["sAdditionalExtrusion"] = self.additionalExtrusion
        props["sElevationOffset"] = self.elevationOffset
        props["o_centerx"] = self.centerx
        props["o_centery"] = self.centery

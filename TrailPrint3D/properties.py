"""MyProperties PropertyGroup — all UI-exposed parameters for TrailPrint3D."""

import os

import bpy  # type: ignore

# ---------------------------------------------------------------------------
# Callbacks and dynamic-item helpers
# ---------------------------------------------------------------------------

specialCollection = [("----", "----", "")]


def get_external_collections(path):
    """Return list of collection names inside a .blend file."""
    if not os.path.exists(path):
        return []
    with bpy.data.libraries.load(path, link=True) as (data_from, _):
        return list(data_from.collections)


def update_collection_items(self, context):
    """Refresh *specialCollection* global from the selected .blend file."""
    global specialCollection
    path = bpy.path.abspath(bpy.context.scene.tp3d.specialBlend_path)
    names = get_external_collections(path)
    specialCollection = [(n, n, "") for n in names]


def dynamic_specialCollection_items(self, context):
    return specialCollection


# ---------------------------------------------------------------------------
# PropertyGroup
# ---------------------------------------------------------------------------

class MyProperties(bpy.types.PropertyGroup):
    # --- File paths ---
    file_path: bpy.props.StringProperty(
        name="File Path", description="Select a file",
        default="", maxlen=1024, subtype='FILE_PATH',
    )  # type: ignore
    export_path: bpy.props.StringProperty(
        name="Export Path", description="Location to save STL files",
        default="", maxlen=1024, subtype='DIR_PATH',
    )  # type: ignore
    autoExport: bpy.props.BoolProperty(
        name="Auto Export",
        description="Automatically export STL/OBJ files after generation",
        default=False,
    )  # type: ignore
    auto3mfExport: bpy.props.BoolProperty(
        name="3MF Export",
        description="Automatically export a combined 3MF file after generation (requires ThreeMF_io addon)",
        default=False,
    )  # type: ignore
    export_format: bpy.props.EnumProperty(
        name="Format",
        description="Export file format for manual export",
        items=[
            ("STL_OBJ", "STL / OBJ", "STL for plain meshes, OBJ if materials are present"),
            ("3MF", "3MF", "3MF file with component hierarchy (requires ThreeMF_io addon)"),
        ],
        default="STL_OBJ",
    )  # type: ignore
    chain_path: bpy.props.StringProperty(
        name="Folder Path", description="Select folder containing multiple GPX files",
        default="", maxlen=1024, subtype='DIR_PATH',
    )  # type: ignore
    trailName: bpy.props.StringProperty(
        name="Name", default="", description="Leave empty to use filename",
    )  # type: ignore

    # --- Shape ---
    shape: bpy.props.EnumProperty(
        name="Shape",
        items=[
            ("HEXAGON", "Hexagon", "Hexagon map"),
            ("SQUARE", "Square", "Square map"),
            ("CIRCLE", "Circle", "Circle map"),
            ("HEXAGON INNER TEXT", "Hexagon Inner Text", "Hexagon map with inner text"),
            ("HEXAGON OUTER TEXT", "Hexagon Outer Text", "Hexagon map with backplate and text"),
            ("HEXAGON FRONT TEXT", "Hexagon Front Text", "Hexagon map with backplate and front text"),
        ],
        default="HEXAGON OUTER TEXT",
    )  # type: ignore

    # --- Elevation API ---
    api: bpy.props.EnumProperty(
        name="api",
        items=[
            ("OPENTOPODATA", "Opentopodata", "Slower but more accurate elevation"),
            ("OPEN-ELEVATION", "Open-Elevation", "Faster but some regions are low quali"),
            ("TERRAIN-TILES", "Terrain-Tiles", "Currently Fastest available set"),
        ],
        default="TERRAIN-TILES",
    )  # type: ignore

    dataset: bpy.props.EnumProperty(
        name="Dataset",
        items=[
            ("srtm30m", "srtm30m", "Latitudes -60 to 60"),
            ("aster30m", "aster30m", "global"),
            ("ned10m", "ned10m", "Continental USA, Hawaii, parts of Alaska"),
            ("mapzen", "mapzen", "global"),
            ("nzdem8m", "nzdem8m", "New Zealand 8m"),
            ("eudem25m", "eudem25m", "Europe"),
        ],
        default="aster30m",
    )  # type: ignore

    # --- Scale mode ---
    scalemode: bpy.props.EnumProperty(
        name="Scale Mode",
        items=[
            ('FACTOR', "Fit to Shape", "Scale the trail to fill a percentage of the terrain shape. 0.8 = trail fills 80%"),
            ('COORDINATES', "Match GPS Points", "Set scale so two GPS coordinates are geographically accurate on the model"),
            ('SCALE', "Fixed Scale", "Use a fixed scale factor — useful for making multiple models at the same geographic scale"),
        ],
        default='FACTOR',
    )  # type: ignore
    pathScale: bpy.props.FloatProperty(name="Scale Factor", default=0.8, min=0.01, max=200, description="In Fit to Shape mode: how much of the shape the trail fills (0.8 = 80%). In Fixed Scale mode: raw Mercator scale multiplier")  # type: ignore
    scaleLon1: bpy.props.FloatProperty(name="Longitude 1", default=0, description="Longitude of first coordinate")  # type: ignore
    scaleLat1: bpy.props.FloatProperty(name="Latitude 1", default=0, description="Latitude of first coordinate")  # type: ignore
    scaleLon2: bpy.props.FloatProperty(name="Longitude 2", default=0, description="Longitude of second coordinate")  # type: ignore
    scaleLat2: bpy.props.FloatProperty(name="Latitude 2", default=0, description="Latitude of second coordinate")  # type: ignore

    selfHosted: bpy.props.StringProperty(name="Self-hosted API URL", default="", description="Must use same API format as Opentopodata.org (https://api.opentopodata.org/v1/)")  # type: ignore

    # --- Map settings ---
    objSize: bpy.props.IntProperty(name="Map Size", default=100, min=5, max=10000, description="Size of the map in millimeters")  # type: ignore
    num_subdivisions: bpy.props.IntProperty(name="Resolution", default=8, min=1, max=10, description="(Max recommended: 8) Higher values create more detailed terrain but slower generation")  # type: ignore
    scaleElevation: bpy.props.FloatProperty(name="Elevation Scale", default=2, min=0, max=10000, description="Multiplier for elevation")  # type: ignore
    pathThickness: bpy.props.FloatProperty(name="Path Thickness", default=1.2, min=0.1, max=5, description="Thickness of the path in millimeters")  # type: ignore
    shapeRotation: bpy.props.IntProperty(name="Shape Rotation", default=0, min=-360, max=360, description="Rotation angle of the shape")  # type: ignore
    overwritePathElevation: bpy.props.BoolProperty(name="Snap Trail to Terrain", default=True, description="Project the trail onto the terrain surface via raycast. When off the trail uses raw GPS elevation")  # type: ignore

    # --- Output info strings ---
    o_verticesPath: bpy.props.StringProperty(name="Path Vertices", default="")  # type: ignore
    o_verticesMap: bpy.props.StringProperty(name="Map Vertices", default="")  # type: ignore
    o_mapScale: bpy.props.StringProperty(name="Map Scale", default="")  # type: ignore
    o_time: bpy.props.StringProperty(name="Generation Time", default="")  # type: ignore
    o_apiCounter_OpenTopoData: bpy.props.StringProperty(name="OpenTopoData Count", default="API Limit: ---/1000 per day")  # type: ignore
    o_apiCounter_OpenElevation: bpy.props.StringProperty(name="OpenElevation Count", default="API Limit: ---/1000 per month")  # type: ignore
    o_centerx: bpy.props.FloatProperty(name="Center X", default=0, description="X-axis center coordinate of the path")  # type: ignore
    o_centery: bpy.props.FloatProperty(name="Center Y", default=0, description="Y-axis center coordinate of the path")  # type: ignore

    # --- Magnet holes ---
    magnetHeight: bpy.props.FloatProperty(name="Magnet Height", default=2.5, description="Height of the magnet hole in millimeters")  # type: ignore
    magnetDiameter: bpy.props.FloatProperty(name="Magnet Diameter", default=6.3, description="Diameter of the magnet hole in millimeters")  # type: ignore

    # --- Text settings ---
    textFont: bpy.props.StringProperty(name="Font File", description="Select a font file (leave empty to auto-detect system font)", default="", maxlen=1024, subtype='FILE_PATH')  # type: ignore
    textSize: bpy.props.IntProperty(name="Text Size", default=5, min=0, max=1000, description="Size of the text in millimeters")  # type: ignore
    textSizeTitle: bpy.props.IntProperty(name="Title Text Size", default=0, min=0, max=1000, description="Set to 0 to use 'Text Size' value")  # type: ignore
    overwriteLength: bpy.props.StringProperty(name="Custom Distance Text", default="", description="Override default distance display")  # type: ignore
    overwriteHeight: bpy.props.StringProperty(name="Custom Elevation Text", default="", description="Override default elevation display")  # type: ignore
    overwriteTime: bpy.props.StringProperty(name="Custom Time Text", default="", description="Override default time display")  # type: ignore
    outerBorderSize: bpy.props.IntProperty(name="Border Size (%)", default=20, min=0, max=1000, description="Only for shapes with backplate")  # type: ignore
    text_angle_preset: bpy.props.IntProperty(name="Text Angle", description="Angle to rotate text on the shape", default=0, min=0, max=260)  # type: ignore
    plateThickness: bpy.props.FloatProperty(name="Plate Thickness", default=5, description="Thickness of the additional backplate")  # type: ignore
    plateInsertValue: bpy.props.FloatProperty(name="Plate Insert Depth", default=2, description="Depth of map cutout in the plate, 0 to ignore")  # type: ignore

    tileSpacing: bpy.props.FloatProperty(name="Tile Spacing", default=0, description="Distance between tiles when extending")  # type: ignore

    # --- Advanced map ---
    minThickness: bpy.props.IntProperty(name="Minimum Thickness", default=7, min=0, max=1000, description="Thickness added at lowest point for print strength")  # type: ignore
    xTerrainOffset: bpy.props.FloatProperty(name="X Terrain Offset", default=0, description="Offset map relative to path in X direction")  # type: ignore
    yTerrainOffset: bpy.props.FloatProperty(name="Y Terrain Offset", default=0, description="Offset map relative to path in Y direction")  # type: ignore

    rescaleMultiplier: bpy.props.FloatProperty(name="Scale Multiplier", default=1, min=0, max=10000, description="Multiplier for elevation rescaling")  # type: ignore
    thickenValue: bpy.props.FloatProperty(name="Thicken Value", default=1, description="Add specified thickness to map in millimeters")  # type: ignore
    fixedElevationScale: bpy.props.BoolProperty(name="Normalize Elevation Range", default=False, description="Normalize terrain range so that the tallest peak is 10mm(xElevationScale) above the lowest point regardless of real elevation range. Recommended for 3D printing.")  # type: ignore
    singleColorMode: bpy.props.BoolProperty(name="Cut Trail into Terrain", default=True, description="Cut the trail into the terrain as one solid object. When off, trail stays as a curve on top of the terrain.")  # type: ignore
    tolerance: bpy.props.FloatProperty(name="Cut Offset", default=0.2, description="Extra width added to the groove cut when cutting the trail into the terrain. Increase if the trail doesn't sit flush")  # type: ignore
    disableCache: bpy.props.BoolProperty(name="Disable Cache", default=False, description="Disabling cache may help if mesh has holes or anomalies")  # type: ignore
    ccacheSize: bpy.props.IntProperty(name="Cache Size", default=50000, min=0, description="Maximum entries in elevation data cache")  # type: ignore

    # --- Flags ---
    addFlags: bpy.props.BoolProperty(name="Add Flag Markers", default=False, description="Add start/finish flags at lowest/highest points to mark terrain extremes")  # type: ignore
    flagHeight: bpy.props.FloatProperty(name="Flag Height", default=5.0, min=1.0, max=30.0, description="Flag pole height in millimeters")  # type: ignore
    flagWidth: bpy.props.FloatProperty(name="Flag Width", default=3.0, min=0.5, max=10.0, description="Flag banner width in millimeters")  # type: ignore

    # --- Internal state ---
    sAdditionalExtrusion: bpy.props.FloatProperty(name="Additional Extrusion", default=0, description="Extrusion value for internal use")  # type: ignore
    sAutoScale: bpy.props.FloatProperty(name="Auto Scale", default=1, description="Automatically calculated scale factor")  # type: ignore
    sScaleHor: bpy.props.FloatProperty(name="Horizontal Scale", default=1, description="Horizontal scale factor for map")  # type: ignore
    sElevationOffset: bpy.props.FloatProperty(name="Elevation Offset", default=0, description="Base offset value for elevation")  # type: ignore
    sMapInKm: bpy.props.FloatProperty(name="Map Length (km)", default=0, description="Actual kilometers corresponding to map size")  # type: ignore

    # --- OSM coloring ---
    col_wActive: bpy.props.BoolProperty(name="Include Water", default=False, description="Include water bodies (lakes, ponds) (experimental), oceans not supported")  # type: ignore
    col_wArea: bpy.props.FloatProperty(name="Water Size Threshold", default=1, description="Lakes smaller than this threshold will be ignored")  # type: ignore
    col_fActive: bpy.props.BoolProperty(name="Include Forest", default=False, description="Include forest areas (experimental)")  # type: ignore
    col_fArea: bpy.props.FloatProperty(name="Forest Size Threshold", default=10, description="Forests smaller than this threshold will be ignored")  # type: ignore
    col_cActive: bpy.props.BoolProperty(name="Include City Boundaries", default=False, description="Include city boundaries (experimental)")  # type: ignore
    col_cArea: bpy.props.FloatProperty(name="City Size Threshold", default=1, description="Cities smaller than this threshold will be ignored")  # type: ignore
    col_KeepManifold: bpy.props.BoolProperty(name="Keep Non-manifold", default=False, description="Keep broken/non-manifold water body parts")  # type: ignore
    col_PaintMap: bpy.props.BoolProperty(name="Paint Map", default=True, description="Paint on map instead of generating separate objects (recommended for Mac)")  # type: ignore

    # --- Post-processing ---
    mountain_treshold: bpy.props.IntProperty(name="Mountain Threshold", default=60, min=0, max=100, subtype='PERCENTAGE', description="Areas above this percentage height will be colored as mountain")  # type: ignore
    cl_thickness: bpy.props.FloatProperty(name="Contour Thickness", default=0.2, description="Contour line thickness in millimeters")  # type: ignore
    cl_distance: bpy.props.FloatProperty(name="Contour Spacing", default=2, description="Distance between contour lines")  # type: ignore
    cl_offset: bpy.props.FloatProperty(name="Contour Offset", default=0.0, description="Starting offset for contour lines")  # type: ignore

    # --- Pin markers ---
    cityname: bpy.props.StringProperty(name="City Name", default="Berlin", description="Get coordinates for city")  # type: ignore
    pinLat: bpy.props.FloatProperty(name="Latitude", default=48.00, description="Latitude for pin marker")  # type: ignore
    pinLon: bpy.props.FloatProperty(name="Longitude", default=8.00, description="Longitude for pin marker")  # type: ignore

    # --- Custom map ---
    mapmode: bpy.props.EnumProperty(
        name="mapmode",
        items=[
            ('FROMPLANE', "From Plane", "Generate the Map from a Flat Plane"),
            ('FROMCENTER', "From Point", "Generate the Map from a Point coordinate and a Radius"),
            ('2POINTS', "2 Points", "Generate the Map from 2 Coordinates"),
        ],
        default='FROMPLANE',
    )  # type: ignore

    jMapLat: bpy.props.FloatProperty(name="Latitude", default=49.00)  # type: ignore
    jMapLon: bpy.props.FloatProperty(name="Longitude", default=9.00)  # type: ignore
    jMapRadius: bpy.props.FloatProperty(name="Radius (km)", default=200)  # type: ignore

    jMapLat1: bpy.props.FloatProperty(name="Latitude1", default=48.00)  # type: ignore
    jMapLat2: bpy.props.FloatProperty(name="Latitude2", default=49.00)  # type: ignore
    jMapLon1: bpy.props.FloatProperty(name="Longitude1", default=8.00)  # type: ignore
    jMapLon2: bpy.props.FloatProperty(name="Longitude2", default=9.00)  # type: ignore

    # --- Special templates ---
    specialBlend_path: bpy.props.StringProperty(
        name="Special Template Path",
        description="Select special template .blend file (TP3dSpecial.blend)",
        default="", maxlen=1024, subtype='FILE_PATH',
    )  # type: ignore
    specialCollectionName: bpy.props.EnumProperty(
        name="Special Collection",
        description="Select a collection from external .blend file",
        items=dynamic_specialCollection_items,
    )  # type: ignore

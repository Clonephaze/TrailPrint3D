"""Object metadata — write generation parameters as custom properties."""

import bpy  # type: ignore

# Plugin category identifier
ADDON_CATEGORY = "TrailPrint3D+"


def write_metadata(obj, ctx=None, type: str = "MAP"):
    """Store generation metadata on *obj* as Blender custom properties.

    When *ctx* is ``None`` the values are read directly from
    ``bpy.context.scene.tp3d`` (legacy codepath for standalone operators).
    """
    props = bpy.context.scene.tp3d

    if type == "MAP":
        obj["Object type"] = type
        obj["Addon"] = ADDON_CATEGORY
        obj["Generation Duration"] = (
            f"{ctx.duration:.0f} seconds" if ctx else str(props.get("o_time", ""))
        )
        obj["Shape"] = props.shape if ctx is None else ctx.shape
        obj["Resolution"] = props.num_subdivisions if ctx is None else ctx.num_subdivisions
        obj["Elevation Scale"] = props.scaleElevation if ctx is None else ctx.scaleElevation
        obj["objSize"] = props.objSize if ctx is None else ctx.size
        obj["pathThickness"] = round(
            props.pathThickness if ctx is None else ctx.pathThickness, 2
        )
        obj["overwritePathElevation"] = (
            props.overwritePathElevation if ctx is None else ctx.overwritePathElevation
        )
        obj["api"] = props.api if ctx is None else ctx.api_index
        obj["scalemode"] = props.scalemode if ctx is None else ctx.scalemode
        obj["fixedElevationScale"] = (
            props.fixedElevationScale if ctx is None else ctx.fixedElevationScale
        )
        obj["minThickness"] = props.minThickness if ctx is None else ctx.minThickness
        obj["xTerrainOffset"] = props.xTerrainOffset if ctx is None else ctx.xTerrainOffset
        obj["yTerrainOffset"] = props.yTerrainOffset if ctx is None else ctx.yTerrainOffset
        obj["singleColorMode"] = (
            props.singleColorMode if ctx is None else ctx.singleColorMode
        )
        obj["selfHosted"] = props.selfHosted if ctx is None else ctx.selfHosted
        obj["Horizontal Scale"] = round(props.sScaleHor, 6)
        obj["Generate Water"] = props.col_wActive
        obj["MinWaterSize"] = props.col_wArea
        obj["Keep Non-Manifold"] = props.col_KeepManifold
        obj["Map Size in Km"] = round(props.sMapInKm, 2)
        obj["Dovetail"] = False
        obj["MagnetHoles"] = False
        obj["AdditionalExtrusion"] = (
            ctx.additionalExtrusion if ctx else props.get("sAdditionalExtrusion", 0)
        )
        obj["lowestZ"] = ctx.lowestZ if ctx else 0
        obj["highestZ"] = ctx.highestZ if ctx else 0
        obj["dataset"] = props.dataset if ctx is None else ctx.dataset
        obj["name"] = props.get("trailName", "") if ctx is None else ctx.name
        obj["pathScale"] = props.pathScale if ctx is None else ctx.pathScale
        obj["scaleLon1"] = props.scaleLon1 if ctx is None else ctx.scaleLon1
        obj["scaleLat1"] = props.scaleLat1 if ctx is None else ctx.scaleLat1
        obj["scaleLon2"] = props.scaleLon2 if ctx is None else ctx.scaleLon2
        obj["scaleLat2"] = props.scaleLat2 if ctx is None else ctx.scaleLat2
        obj["shapeRotation"] = props.shapeRotation if ctx is None else ctx.shapeRotation
        obj["pathVertices"] = props.o_verticesPath
        obj["mapVertices"] = props.o_verticesMap
        obj["mapScale"] = props.o_mapScale
        obj["centerx"] = props.o_centerx
        obj["centery"] = props.o_centery
        obj["sElevationOffset"] = props.sElevationOffset
        obj["sMapInKm"] = props.sMapInKm
        obj["col_wActive"] = props.col_wActive
        obj["col_wArea"] = props.col_wArea
        obj["col_fActive"] = props.col_fActive
        obj["col_fArea"] = props.col_fArea
        obj["col_cActive"] = props.col_cActive
        obj["col_cArea"] = props.col_cArea

    elif type == "TRAIL":
        obj["Object type"] = type
        obj["Addon"] = ADDON_CATEGORY
        obj["overwritePathElevation"] = (
            props.overwritePathElevation if ctx is None else ctx.overwritePathElevation
        )

    elif type in ("CITY", "WATER", "FOREST"):
        obj["Object type"] = type
        obj["Addon"] = ADDON_CATEGORY
        obj["minThickness"] = props.minThickness if ctx is None else ctx.minThickness

    elif type == "PLATE":
        obj["Object type"] = type
        obj["Addon"] = ADDON_CATEGORY
        obj["Shape"] = props.shape if ctx is None else ctx.shape
        obj["textFont"] = props.textFont if ctx is None else ctx.textFont
        obj["textSize"] = props.textSize if ctx is None else ctx.textSize
        obj["overwriteLength"] = props.overwriteLength if ctx is None else ctx.overwriteLength
        obj["overwriteHeight"] = props.overwriteHeight if ctx is None else ctx.overwriteHeight
        obj["overwriteTime"] = props.overwriteTime if ctx is None else ctx.overwriteTime
        obj["outerBorderSize"] = (
            props.outerBorderSize if ctx is None else ctx.outerBorderSize
        )
        obj["shapeRotation"] = props.shapeRotation if ctx is None else ctx.shapeRotation
        obj["name"] = props.get("trailName", "") if ctx is None else ctx.name
        obj["plateThickness"] = props.plateThickness if ctx is None else ctx.plateThickness
        obj["plateInsertValue"] = (
            props.plateInsertValue if ctx is None else ctx.plateInsertValue
        )
        obj["textAngle"] = props.text_angle_preset if ctx is None else ctx.text_angle_preset
        border = props.outerBorderSize if ctx is None else ctx.outerBorderSize
        base_size = props.objSize if ctx is None else ctx.size
        obj["objSize"] = base_size * ((100 + border) / 100)

    elif type == "LINES":
        obj["Object type"] = type
        obj["cl_thickness"] = props.cl_thickness
        obj["cl_distance"] = props.cl_distance
        obj["cl_offset"] = props.cl_offset

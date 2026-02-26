"""Advanced options panel."""

import bpy  # type: ignore

from ..export_3mf import is_3mf_available


class MY_PT_Advanced(bpy.types.Panel):
    bl_label = "Advanced Options"
    bl_idname = "TP3D_PT_Advanced"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "TrailPrint3D"

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        # Export
        box = layout.box()
        box.label(text="Export generated objects")
        box.prop(props, "export_format")
        if props.export_format == '3MF' and not is_3mf_available():
            box.label(text="Install ThreeMF_io addon for 3MF", icon='ERROR')
        box.operator("wm.run_my_script5")
        box.label(text="Auto-selects generated objects if nothing is selected", icon='INFO')

        # --- Map Settings ---
        layout.prop(props, "show_map", icon="TRIA_DOWN" if props.show_map else "TRIA_RIGHT",
                    emboss=True, text="Map Settings")
        if props.show_map:
            box = layout.box()
            box.prop(props, "fixedElevationScale")
            box.prop(props, "minThickness")
            box.prop(props, "shapeRotation")
            box.prop(props, "xTerrainOffset")
            box.prop(props, "yTerrainOffset")
            box.prop(props, "singleColorMode")
            box.prop(props, "tolerance")
            box.prop(props, "disableCache")
            box.prop(props, "ccacheSize")
            box.separator()

            box.prop(props, "addFlags")
            if props.addFlags:
                box.prop(props, "flagHeight")
                box.prop(props, "flagWidth")

            box.separator()
            box.label(text="Custom Map")
            if bpy.context.scene.tp3d.sScaleHor is not None:
                box.prop(props, "mapmode")
                if props.mapmode == "FROMPLANE":
                    # TODO: operators not yet ported to modular package
                    # box.operator("wm.terrain", text="Create map from selected object")
                    # box.operator("wm.create_blank", text="Create blank map")
                    # box.operator("wm.extend_tile", text="Extend selected tile")
                    box.label(text="(Custom map ops not yet available)")
                    box.prop(props, "tileSpacing")
                elif props.mapmode == "FROMCENTER":
                    row = box.row()
                    row.prop(props, "jMapLat")
                    row.prop(props, "jMapLon")
                    box.prop(props, "jMapRadius")
                    box.operator("wm.fromcentergeneration", text="Create map from 1 point + radius")
                    box.operator("wm.fromcentergenerationwithtrail", text="Create map with trail from 1 point + radius")
                elif props.mapmode == "2POINTS":
                    row = box.row()
                    row.prop(props, "jMapLat1")
                    row.prop(props, "jMapLon1")
                    row = box.row()
                    row.prop(props, "jMapLat2")
                    row.prop(props, "jMapLon2")
                    box.operator("wm.2pointgeneration", text="Create map from 2 points")

                box.separator()
                # TODO: operator not yet ported to modular package
                # box.operator("wm.mergewithmap", text="Merge to map")
                box.separator()
            else:
                box.label(text="Only available after generating a map")
                box.label(text="(same session)")
                # TODO: operators not yet ported to modular package
                # box.operator("wm.terrain", text="Create map from selected object")
                # box.operator("wm.create_blank", text="Create blank map")

            layout.separator()

        # --- Batch Generation ---
        layout.prop(props, "show_chain", icon="TRIA_DOWN" if props.show_chain else "TRIA_RIGHT",
                    emboss=True, text="Batch Generation")
        if props.show_chain:
            box = layout.box()
            box.label(text="Batch Generation")
            box.label(text="Create single map from multiple GPX files in folder")
            box.prop(props, "chain_path")
            box.operator("wm.run_my_script2")
            layout.separator()

        # --- Include Elements ---
        layout.prop(props, "show_coloring", icon="TRIA_DOWN" if props.show_coloring else "TRIA_RIGHT",
                    emboss=True, text="Include Elements")
        if props.show_coloring:
            boxer = layout.box()
            box = boxer.box()
            box.label(text="Water Bodies")
            box.prop(props, "col_wActive")
            box.prop(props, "col_wArea")
            box = boxer.box()
            box.label(text="Forest")
            box.prop(props, "col_fActive")
            box.prop(props, "col_fArea")
            box = boxer.box()
            box.label(text="City Boundaries")
            box.prop(props, "col_cActive")
            box.prop(props, "col_cArea")
            boxer.prop(props, "col_PaintMap")

        # --- Pin Markers ---
        layout.prop(props, "show_pin", icon="TRIA_DOWN" if props.show_pin else "TRIA_RIGHT",
                    emboss=True, text="Pin Markers")
        if props.show_pin:
            box = layout.box()
            box.label(text="Set pin by coordinates")
            row = box.row()
            row.prop(props, "pinLat")
            row.prop(props, "pinLon")
            box.operator("wm.pincoords", text="Add pin at coordinates")
            box.separator()
            box.label(text="Set pin by city name")
            box.prop(props, "cityname")
            box.operator("wm.citycoords", text="Add pin at city")

        # --- Special Features ---
        layout.prop(props, "show_special", icon="TRIA_DOWN" if props.show_special else "TRIA_RIGHT",
                    emboss=True, text="Special Features")
        if props.show_special:
            box = layout.box()
            box.label(text="Use special handcrafted templates")
            box.label(text="For example: puzzles, sliding puzzles, etc.")
            box.separator()
            box.prop(props, "specialBlend_path")
            box.operator("wm.update_special_collection", text="Load .blend file")
            box.prop(props, "specialCollectionName", text="Collection")
            box.operator("wm.appendcollection", text="Import")

        # --- Post Processing ---
        layout.prop(props, "show_postProcess", icon="TRIA_DOWN" if props.show_postProcess else "TRIA_RIGHT",
                    emboss=True, text="Post Processing")
        if props.show_postProcess:
            box = layout.box()
            box.label(text="Manual export required after these operations")
            box.separator()

            box.label(text="Mountain Coloring")
            box.prop(props, "mountain_treshold")
            box.operator("wm.colormountain", text="Color Mountains")
            box.separator()

            box.prop(props, "cl_thickness")
            box.prop(props, "cl_distance")
            box.prop(props, "cl_offset")
            box.operator("wm.contourlines")
            box.separator()

            box.label(text="Rescale elevation height of selected object")
            row = box.row()
            row.prop(props, "rescaleMultiplier")
            row.operator("wm.rescale", text="Scale Elevation")
            box.separator()

            box.label(text="Extrude terrain of selected object by specified height")
            box.prop(props, "thickenValue")
            box.operator("wm.thicken", text="Extrude Terrain")
            box.separator()

            row = box.row()
            row.prop(props, "magnetHeight")
            row.prop(props, "magnetDiameter")
            box.operator("wm.magnetholes", text="Add Magnet Holes")
            box.separator()

            box.operator("wm.dovetail", text="Add Dovetail Joints")
            box.separator()

            box.operator("wm.bottommark", text="Add Bottom Mark")

        # --- API ---
        layout.prop(props, "show_api", icon="TRIA_DOWN" if props.show_api else "TRIA_RIGHT",
                    emboss=True, text="Elevation Data API")
        if props.show_api:
            box = layout.box()
            box.prop(props, "api")
            if props.api == "OPENTOPODATA":
                box.prop(props, "dataset")
                box.separator()
                box.label(text="If you self-host an Opentopodata server:")
                box.prop(props, "selfHosted")
                layout.separator()

        # --- Statistics ---
        layout.prop(props, "show_stats", icon="TRIA_DOWN" if props.show_stats else "TRIA_RIGHT",
                    emboss=True, text="Statistics")
        if props.show_stats:
            box = layout.box()
            box.label(text="Get generation parameters of selected map")
            box.operator("object.show_custom_props_popup")
            box = layout.box()
            box.label(text=props.o_verticesPath)
            box.label(text=props.o_verticesMap)
            box.label(text=props.o_mapScale)
            box.label(text=f"Horizontal Scale: {props.sScaleHor}")
            box.label(text=f"Map Size: {props.sMapInKm}")
            box.label(text=props.o_time)
            box.separator()
            box.label(text="Opentopodata API calls:")
            box.label(text=props.o_apiCounter_OpenTopoData)
            box.label(text="OpenElevation API calls:")
            box.label(text=props.o_apiCounter_OpenElevation)
            layout.separator()

        # --- Attribution ---
        layout.prop(props, "show_attribution", icon="TRIA_DOWN" if props.show_attribution else "TRIA_RIGHT",
                    emboss=True, text="Data Attribution")
        if props.show_attribution:
            box = layout.box()
            box.label(text="Data Attribution")
            box.label(text="Elevation data from OpenTopoData using SRTM and other datasets.")
            box.label(text="Elevation data from Open-Elevation based on NASA SRTM data.")
            box.label(text="Water, forest, city data \u00a9 OpenStreetMap contributors")
            box.label(text="Terrain data from Mapzen based on OpenStreetMap contributors, NASA SRTM and USGS.")
            layout.separator()

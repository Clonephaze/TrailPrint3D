"""Info panel — statistics and data attribution."""

import bpy  # type: ignore


class TP3D_PT_info(bpy.types.Panel):
    bl_label = "Info"
    bl_idname = "TP3D_PT_info"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 4

    def draw(self, context):
        pass  # Content is in sub-panels


# ── Statistics ───────────────────────────────────────────────────────────


class TP3D_PT_statistics(bpy.types.Panel):
    bl_label = "Statistics"
    bl_idname = "TP3D_PT_statistics"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_parent_id = "TP3D_PT_info"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        layout.operator("tp3d.show_props", icon='INFO')

        layout.separator()
        col = layout.column(align=True)
        col.label(text=props.o_verticesPath)
        col.label(text=props.o_verticesMap)
        col.label(text=props.o_mapScale)
        col.label(text=f"Horizontal Scale: {props.sScaleHor}")
        col.label(text=f"Map Size: {props.sMapInKm}")
        col.label(text=props.o_time)

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Opentopodata API calls:")
        col.label(text=props.o_apiCounter_OpenTopoData)
        col.label(text="OpenElevation API calls:")
        col.label(text=props.o_apiCounter_OpenElevation)


# ── Attribution ──────────────────────────────────────────────────────────


class TP3D_PT_attribution(bpy.types.Panel):
    bl_label = "Data Attribution"
    bl_idname = "TP3D_PT_attribution"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_parent_id = "TP3D_PT_info"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Elevation: OpenTopoData (SRTM + others)")
        col.label(text="Elevation: Open-Elevation (NASA SRTM)")
        col.label(text="OSM data \u00a9 OpenStreetMap contributors")
        col.label(text="Terrain: Mapzen (OSM, NASA SRTM, USGS)")

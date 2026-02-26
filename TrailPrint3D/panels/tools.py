"""Tools panel — pin markers, custom map, batch generation, special templates."""

import bpy  # type: ignore


class TP3D_PT_tools(bpy.types.Panel):
    bl_label = "Tools"
    bl_idname = "TP3D_PT_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 3

    def draw(self, context):
        pass  # Content is in sub-panels


# ── Pin Markers ──────────────────────────────────────────────────────────


class TP3D_PT_pins(bpy.types.Panel):
    bl_label = "Pin Markers"
    bl_idname = "TP3D_PT_pins"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_parent_id = "TP3D_PT_tools"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        layout.label(text="By Coordinates:")
        row = layout.row(align=True)
        row.prop(props, "pinLat")
        row.prop(props, "pinLon")
        layout.operator("tp3d.pin_coords", text="Add Pin", icon='EMPTY_DATA')

        layout.separator()

        layout.label(text="By City Name:")
        layout.prop(props, "cityname")
        layout.operator("tp3d.pin_city", text="Add Pin", icon='WORLD')


# ── Custom Map ───────────────────────────────────────────────────────────


class TP3D_PT_custom_map(bpy.types.Panel):
    bl_label = "Custom Map"
    bl_idname = "TP3D_PT_custom_map"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_parent_id = "TP3D_PT_tools"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        if props.sScaleHor is not None:
            layout.prop(props, "mapmode")

            if props.mapmode == "FROMPLANE":
                layout.label(text="(Custom map ops not yet available)")
                layout.prop(props, "tileSpacing")
            elif props.mapmode == "FROMCENTER":
                row = layout.row(align=True)
                row.prop(props, "jMapLat")
                row.prop(props, "jMapLon")
                layout.prop(props, "jMapRadius")
                layout.operator("tp3d.map_from_center", text="Generate Map")
                layout.operator("tp3d.map_from_center_trail", text="Generate Map + Trail")
            elif props.mapmode == "2POINTS":
                row = layout.row(align=True)
                row.prop(props, "jMapLat1")
                row.prop(props, "jMapLon1")
                row = layout.row(align=True)
                row.prop(props, "jMapLat2")
                row.prop(props, "jMapLon2")
                layout.operator("tp3d.map_from_2points", text="Generate Map")
        else:
            layout.label(text="Generate a map first", icon='INFO')


# ── Batch Generation ─────────────────────────────────────────────────────


class TP3D_PT_batch(bpy.types.Panel):
    bl_label = "Batch Generation"
    bl_idname = "TP3D_PT_batch"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_parent_id = "TP3D_PT_tools"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        layout.label(text="Create map from multiple GPX files")
        layout.prop(props, "chain_path")
        layout.operator("tp3d.batch_generate", icon='FILE_FOLDER')


# ── Special Templates ────────────────────────────────────────────────────


class TP3D_PT_special(bpy.types.Panel):
    bl_label = "Special Templates"
    bl_idname = "TP3D_PT_special"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TrailPrint3D"
    bl_parent_id = "TP3D_PT_tools"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.tp3d

        layout.label(text="Import handcrafted templates")
        layout.label(text="(puzzles, sliding puzzles, etc.)")
        layout.separator()
        layout.prop(props, "specialBlend_path")
        layout.operator("tp3d.load_special_blend", text="Load .blend", icon='FILE_BLEND')
        layout.prop(props, "specialCollectionName", text="Collection")
        layout.operator("tp3d.import_special", text="Import", icon='IMPORT')

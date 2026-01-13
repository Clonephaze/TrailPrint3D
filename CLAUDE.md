# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TrailPrint3D is a Blender plugin (Python) that converts GPS trail data (GPX/IGC files) into 3D printable terrain models (STL/OBJ). It fetches real elevation data from external APIs and creates customizable terrain maps with trails.

- **Language**: Python 3.x (runs within Blender 4.5.2+)
- **License**: CC BY-NC 4.0
- **Version**: 2.23

## Installation

No build system - install directly in Blender:
1. Edit → Preferences → Add-ons → Install
2. Select `TrailPrint3D.py`
3. Enable the add-on

## Testing

Manual testing only. Use sample GPX files in `/gpx/` directory:
- `九龙山.gpx`
- `莫干山.gpx`
- `达摩古道.gpx`

## Architecture

Single monolithic file (`TrailPrint3D.py`, ~6300 lines) organized as:

| Section | Lines | Purpose |
|---------|-------|---------|
| Metadata & Constants | 80-182 | Global config, API limits, cache paths |
| **MyProperties** | 219-421 | ~80 UI parameters (scene properties) |
| **Operators** | 425-1450 | 15 operator classes (user actions) |
| **Panels** | 1155-1450 | 3 UI panel classes |
| Registration | 1511-1554 | `register()` / `unregister()` |
| Helper Functions | 1564-5476 | Core logic (~110 functions) |
| **runGeneration()** | 5477+ | Main orchestration function |

### Key Components

**MyProperties** (lines 219-421): Central storage for all UI parameters including file paths, map settings, elevation options, text/labels, flag settings, and coloring options.

**Main Operators**:
- `MY_OT_runGeneration` - Main terrain generation
- `MY_OT_ExportSTL` - STL/OBJ export
- `MY_OT_Rescale`, `MY_OT_thicken`, `MY_OT_MagnetHoles`, `MY_OT_Dovetail` - Post-processing

**Core Function Groups**:
- File parsing: `read_gpx_1_1()`, `read_gpx_1_0()`, `read_igc()`
- Elevation APIs: `get_elevation_openTopoData()`, `get_elevation_TerrainTiles()`
- Geometry: `create_hexagon()`, `create_rectangle()`, `create_circle()`, `create_flag()`
- Coordinate transforms: `convert_to_blender_coordinates()`, `haversine()`
- OSM integration: `fetch_osm_data()`, `coloring_main()`

### Data Flow

```
GPX/IGC File → Parse GPS points → Fetch elevation data → Create terrain mesh
    → Apply styling/colors → Add text/flags → Export STL/OBJ
```

## External APIs

Rate-limited services used for elevation data:
- **Terrain-Tiles** (AWS) - Fastest, recommended
- **OpenTopoData** - 1,000 requests/day
- **Open-Elevation** - 1,000 requests/month
- **OpenStreetMap** - Water/forest/city overlay data

## Caching

User data stored in Blender config directory (`~/.config/blender/4.x/config/`):
- `api_request_counter.json` - API rate limit tracking
- `elevation_cache.json` - Up to 50,000 elevation entries
- `terrarium_cache/` - Terrain tile PNG cache

## Code Style Notes

- Comments and variable names are in Chinese
- Procedural style (not OOP for core logic)
- Heavy use of global variables
- Blender API conventions (`bpy`, `bmesh`, `mathutils`)

>[!WARNING]
>While I am in contact with the original author, the repository this fork is forked from is NOT the original work by the author of the addon found on makerworld. 

# TrailPrint3D - 3D Printable Trail Maps

[![Version](https://img.shields.io/badge/version-2.23-blue.svg)](https://github.com/xuqi2024/TrailPrint3D)
[![Blender](https://img.shields.io/badge/Blender-4.5%2B-orange.svg)](https://www.blender.org/)
[![License](https://img.shields.io/badge/license-CC%20BY--NC%204.0-green.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

## Overview

TrailPrint3D is a Blender plugin that converts your favorite GPS routes into beautiful 3D printable artwork. The plugin supports GPX and IGC file formats, using real elevation data to create customizable terrain maps.

**Latest Version v2.23 Features:**
- Complete English interface
- Automatic mesh anomaly repair
- Single color mode enabled by default
- Base plate indent defaults to 2mm
- Resolution defaults increased to 8
- **New Feature: Flag Markers** - Automatically add start/finish markers at terrain elevation extremes

### Main Features

- **Multiple Map Shapes**: Hexagon, square, circle and other base shapes
- **Real Terrain Data**: Integrated OpenTopoData, Open-Elevation and Terrain-Tiles APIs
- **Route Statistics**: Automatically calculate distance, elevation gain and duration
- **Customizable Appearance**: Adjust size, resolution, path thickness and elevation scale
- **Text Integration**: Add route name and statistics to the map
- **Flag Markers**: Automatically add visual markers at lowest and highest elevation points (v2.23)
- **Post-Processing Tools**: Magnet holes, dovetail joints, mountain coloring and more
- **Element Overlays**: Include water bodies, forests and city boundaries (experimental)
- **Batch Generation**: Support importing multiple GPX files from a folder
- **Direct Export**: One-click export to STL/OBJ format for 3D printing

## Quick Start

### System Requirements

- Blender 4.5.2 or higher
- Python 3.x (built into Blender)
- Internet connection (for elevation data)

### Installation Steps

1. **Download the Plugin**
   ```
   git clone https://github.com/xuqi2024/TrailPrint3D.git
   ```

2. **Install in Blender**
   - Open Blender
   - Edit → Preferences → Add-ons
   - Click "Install" button
   - Select `TrailPrint3D.py` file
   - Enable the "TrailPrint3D" add-on

3. **Start Using**
   - Find the "TrailPrint3D" tab in the right panel of 3D View
   - Select your GPX/IGC file
   - Configure settings and click "Generate"

## Usage Guide

### Basic Workflow

1. **Select File**: Click the "File Path" browse button to select your GPX or IGC file
2. **Configure Settings**:
   - Choose map shape (hexagon, square, circle, etc.)
   - Set object size (in millimeters)
   - Adjust resolution (6-8 recommended)
   - Set elevation scale and path thickness
3. **Generate Map**: Click the "Generate" button
4. **Export File**: Select export path and export as STL/OBJ format

### Advanced Features

#### Scale Modes
- **Map Scale**: Set scale based on map size
- **Coordinates**: Calculate scale using two coordinate points
- **Global Scale**: Set scale based on global scale (Mercator projection)

#### API Options
- **OpenTopoData**: Slower but more accurate elevation data
- **Open-Elevation**: Faster but lower quality in some regions
- **Terrain-Tiles**: Currently the fastest dataset

#### Flag Markers (v2.23 New)
- **Automatic Extreme Point Detection**: Intelligently find lowest and highest elevation points
- **Two-Color Marker System**:
  - Green start flag → Marks lowest elevation point
  - Red finish flag → Marks highest elevation point
- **Adjustable Parameters**:
  - Flag height: 1-30mm (5mm recommended)
  - Flag width: 0.5-10mm (3mm recommended)
- **Separate STL Export**: Flags export as separate files for multi-color printing

#### Post-Processing
- **Rescale Elevation**: Adjust Z-axis scale of generated objects
- **Thicken Terrain**: Add specified thickness to the map
- **Magnet Holes**: Add embedded magnet holes
- **Dovetail Joints**: Add puzzle-style cutouts
- **Mountain Coloring**: Color mountains based on elevation
- **Contour Lines**: Generate terrain contour lines

## Project Structure

```
TrailPrint3D/
├── TrailPrint3D.py          # Main plugin file
├── README.md                # Project documentation
├── gpx/                     # Sample GPX files
│   ├── jiulong_mountain.gpx
│   ├── mogan_mountain.gpx
│   └── damo_trail.gpx
└── .git/                    # Git version control
```

## Dependencies

### Python Libraries (Built into Blender)
- `bpy` - Blender Python API
- `xml.etree.ElementTree` - GPX file parsing
- `requests` - API requests
- `bmesh` - Mesh editing
- `mathutils` - Math utilities

### External APIs
- OpenTopoData API (1000 requests/day limit)
- Open-Elevation API (1000 requests/month limit)
- Terrain-Tiles (AWS Public Dataset)
- OpenStreetMap (water, forest and city data)

## Supported File Formats

- **GPX 1.0 and 1.1**: Standard GPS exchange format
- **IGC**: Paragliding and aviation sport recording format

## Customization Options

### Shape Options
- Hexagon
- Square
- Circle
- Hexagon (Inner Text)
- Hexagon (Outer Text)
- Hexagon (Front Text)

### Text Options
- Custom font support
- Adjustable text size
- Route statistics override
- Rotation and position control

### Material System
Automatically created materials:
- BASE (Green) - Base terrain
- MOUNTAIN (Gray) - High elevation areas
- WATER (Blue) - Water bodies
- FOREST (Dark Green) - Forest areas
- TRAIL (Red) - Path
- CITY (Yellow) - City boundaries

## Test Data

Sample GPX files are provided in the `/gpx/` directory for testing plugin functionality.

## Related Projects

- [Elevon](https://github.com/xuqi2024/Elevon) - Companion web system with GPX upload and 3D preview

## License

This work is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
View license: https://creativecommons.org/licenses/by-nc/4.0/

## Acknowledgments

### Data Sources
- Elevation data provided by Mapzen Terrain Tiles project
- © Mapzen. Data hosted on AWS Public Dataset Program
- Elevation data from OpenTopoData, using SRTM and other datasets
- Elevation data from Open-Elevation, based on NASA's Shuttle Radar Topography Mission (SRTM) data
- Water body data © OpenStreetMap contributors
- Terrain data from Mapzen, based on © OpenStreetMap contributors, NASA SRTM and USGS data

### Map Data
- Map data © OpenStreetMap contributors

## Author

- **EmGi** - Plugin development
- **Version**: 2.23

## Support

- [Support on Patreon](https://patreon.com/EmGi3D)
- [Join Discord Community](https://discord.gg/C67H9EJFbz)

## Version History

- **v2.23** - Current version (2024)
  - **New Feature: Flag Marker System**
    - Automatically add start/finish flags at terrain lowest and highest points
    - Green start flag, red finish flag
    - Adjustable flag height (1-30mm) and flag width (0.5-10mm)
    - Separate STL file export for multi-color printing
  - **Complete Documentation System**
    - New flag feature documentation
    - Quick start guide
    - Technical implementation documentation
    - Code modification summary
  - **Code Optimization**
    - New `create_flag()` function (152 lines)
    - New `find_elevation_extremes()` function (44 lines)
    - Comprehensive error handling and comments
  - **Interface Improvements**
    - Added flag settings panel in advanced options
    - Collapsible parameter display
    - Real-time parameter adjustment

- **v2.22** - Code optimization and localization
  - Improved API integration
  - Enhanced caching system
  - New post-processing tools
  - Bug fixes and performance optimization
  - Complete interface localization
  - Local font lookup system

## Troubleshooting

### Common Issues

1. **Random holes in mesh**
   - Disable cache option
   - Reduce cache size

2. **API request limits**
   - OpenTopoData: 1000 requests per day
   - Open-Elevation: 1000 requests per month
   - Consider using Terrain-Tiles for faster speed

3. **Slow generation**
   - Lower resolution setting
   - Use Terrain-Tiles API
   - Enable caching

4. **Export failure**
   - Ensure export path is valid
   - Check disk space
   - Verify object is mesh type

## Future Plans

- [ ] Web interface integration
- [ ] Real-time 3D preview
- [ ] More map shapes
- [ ] Improved OSM data integration
- [ ] Batch processing optimization
- [ ] Automatic chunking system
- [ ] Cloud rendering support

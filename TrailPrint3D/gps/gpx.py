"""GPX file readers — version 1.0 and 1.1 parsers, plus file/directory dispatch."""

import os
import xml.etree.ElementTree as ET
from datetime import datetime

import bpy  # type: ignore

from ..utils import show_message_box, toggle_console


def read_gpx_1_1(filepath):
    """Read a GPX 1.1 file → list of segment coordinate lists.

    Each segment is a list of ``(lat, lon, elevation, timestamp)`` tuples.
    Also writes ``elevationOffset`` into scene properties.
    """
    tree = ET.parse(filepath)
    root = tree.getroot()

    segmentlist = []
    ns = {'default': 'http://www.topografix.com/GPX/1/1'}

    segments = root.findall('.//default:trkseg', ns)
    print(f"Segments: {len(segments)}")

    if segments:
        for seg in segments:
            points = seg.findall('.//default:trkpt', ns)
            point_type = 'trkpt'
            if not points:
                points = seg.findall('.//default:rtept', ns)
                point_type = 'rtept'

            segcoords = []
            lowest_elevation = 10000

            for pt in points:
                lat = float(pt.get('lat'))
                lon = float(pt.get('lon'))
                ele = pt.find('default:ele', ns)
                elevation = float(ele.text) if ele is not None else 0.0
                time_el = pt.find('default:time', ns)
                try:
                    timestamp = (
                        datetime.fromisoformat(time_el.text.replace("Z", "+00:00"))
                        if time_el is not None else None
                    )
                except (ValueError, TypeError, AttributeError):
                    timestamp = None
                segcoords.append((lat, lon, elevation, timestamp))
                if elevation < lowest_elevation:
                    lowest_elevation = elevation

            elevation_offset = max(lowest_elevation - 50, 0)
            bpy.context.scene.tp3d["sElevationOffset"] = elevation_offset
            bpy.context.scene.tp3d["o_verticesPath"] = (
                f"{point_type.upper()}  Path vertices: {len(segcoords)}"
            )
            segmentlist.append(segcoords)

    return segmentlist


def read_gpx_1_0(filepath):
    """Read a GPX 1.0 file → list of segment coordinate lists."""
    tree = ET.parse(filepath)
    root = tree.getroot()

    segmentlist = []
    ns = {'gpx': 'http://www.topografix.com/GPX/1/0'}

    segcoords = []
    lowest_elevation = 10000

    segments = root.findall('.//gpx:trkseg', ns)
    print(f"Segments in 1.0: {len(segments)}")

    if segments:
        for seg in segments:
            for trkpt in seg.findall('.//gpx:trkpt', ns):
                lat = float(trkpt.get('lat'))
                lon = float(trkpt.get('lon'))
                ele = trkpt.find('gpx:ele', ns)
                elevation = float(ele.text) if ele is not None else 0.0
                time_el = trkpt.find('gpx:time', ns)
                timestamp = (
                    datetime.fromisoformat(time_el.text) if time_el is not None else None
                )
                segcoords.append((lat, lon, elevation, timestamp))
                if elevation < lowest_elevation:
                    lowest_elevation = elevation

            elevation_offset = max(lowest_elevation - 50, 0)
            bpy.context.scene.tp3d["sElevationOffset"] = elevation_offset
            bpy.context.scene.tp3d["o_verticesPath"] = f"Path vertices: {len(segcoords)}"
            segmentlist.append(segcoords)

    return segmentlist


def read_gpx_file(gpx_file_path: str):
    """Dispatch a single GPX/IGC file to the correct reader.

    Returns a list of segments (each a list of coordinate tuples).
    """
    from .igc import read_igc

    file_extension = os.path.splitext(gpx_file_path)[1].lower()

    if file_extension == '.gpx':
        tree = ET.parse(gpx_file_path)
        root = tree.getroot()
        version = root.get("version")

        ns = {'default': root.tag.split('}')[0].strip('{')}
        gpx_sections = len(root.findall(".//default:trkseg", ns))
        print(f"GPX Sections: {gpx_sections}")

        if version == "1.0":
            coords = read_gpx_1_0(gpx_file_path)
        elif version == "1.1":
            coords = read_gpx_1_1(gpx_file_path)
        else:
            coords = read_gpx_1_1(gpx_file_path)  # default to 1.1

    elif file_extension == '.igc':
        coords = read_igc(gpx_file_path)
    else:
        show_message_box("Unsupported file format. Please use .gpx or .igc files.")
        toggle_console()
        return []

    return coords


def read_gpx_directory(directory_path: str):
    """Read every GPX/IGC file in *directory_path* and return a list of segment lists."""
    from .igc import read_igc

    coordinates_separate = []
    lowest_elevation = 10000

    for filename in os.listdir(directory_path):
        if not filename.lower().endswith(('.gpx', '.igc')):
            continue

        filepath = os.path.join(directory_path, filename)
        file_extension = os.path.splitext(filepath)[1].lower()
        co = []

        if file_extension == '.gpx':
            tree = ET.parse(filepath)
            root = tree.getroot()
            version = root.get("version")
            print(f"File Name: {filename}, File Version: {version}")
            if version == "1.0":
                co = read_gpx_1_0(filepath)
            else:
                co = read_gpx_1_1(filepath)
        elif file_extension == '.igc':
            co = read_igc(filepath)

        if co:
            for coseg in co:
                coordinates_separate.append(coseg)
                lowest = min(coseg, key=lambda x: x[2])
                if lowest[2] < lowest_elevation:
                    lowest_elevation = lowest[2]
                    print(f"new Lowest Elevation: {lowest_elevation}")

    coordinates = [pt for sublist in coordinates_separate for pt in sublist]

    elevation_offset = max(lowest_elevation - 50, 0)
    bpy.context.scene.tp3d["sElevationOffset"] = elevation_offset
    bpy.context.scene.tp3d["o_verticesPath"] = f"Path vertices: {len(coordinates)}"

    print(f"Total GPX files processed: {len(coordinates_separate)}")
    return coordinates_separate

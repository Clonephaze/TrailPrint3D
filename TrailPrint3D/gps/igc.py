"""IGC flight-recorder file reader."""

from datetime import datetime

import bpy  # type: ignore


def read_igc(filepath: str):
    """Read an IGC file → list containing one segment of coordinate tuples.

    Each coordinate is ``(lat, lon, elevation, timestamp)``.
    Uses GPS altitude from B-records.
    """
    segmentlist = []
    coordinates = []
    lowest_elevation = 10000

    with open(filepath, 'r') as file:
        for line in file:
            # IGC B records contain position data
            if not line.startswith('B'):
                continue

            try:
                # Extract time (HHMMSS)
                time_str = line[1:7]
                hours = int(time_str[0:2])
                minutes = int(time_str[2:4])
                seconds = int(time_str[4:6])

                # Extract latitude (DDMMmmmN/S)
                lat_str = line[7:15]
                lat_deg = int(lat_str[0:2])
                lat_min = int(lat_str[2:4])
                lat_min_frac = int(lat_str[4:7]) / 1000.0
                lat = lat_deg + (lat_min + lat_min_frac) / 60.0
                if lat_str[7] == 'S':
                    lat = -lat

                # Extract longitude (DDDMMmmmE/W)
                lon_str = line[15:24]
                lon_deg = int(lon_str[0:3])
                lon_min = int(lon_str[3:5])
                lon_min_frac = int(lon_str[5:8]) / 1000.0
                lon = lon_deg + (lon_min + lon_min_frac) / 60.0
                if lon_str[8] == 'W':
                    lon = -lon

                # Pressure altitude and GPS altitude (in meters)
                # pressure_alt = int(line[25:30])  # not used
                gps_alt = int(line[30:35])

                now = datetime.now()
                timestamp = datetime(now.year, now.month, now.day, hours, minutes, seconds)

                elevation = gps_alt
                coordinates.append((lat, lon, elevation, timestamp))

                if elevation < lowest_elevation:
                    lowest_elevation = elevation

            except (ValueError, IndexError):
                print(f"Error parsing IGC line: {line.strip()}")
                continue

    elevation_offset = max(lowest_elevation - 50, 0)
    bpy.context.scene.tp3d["sElevationOffset"] = elevation_offset
    bpy.context.scene.tp3d["o_verticesPath"] = f"Path vertices: {len(coordinates)}"

    segmentlist.append(coordinates)
    return segmentlist

"""Fetch OpenStreetMap data via the Overpass API."""

import time

import requests  # type: ignore


def fetch_osm_data(bbox, kind: str = "WATER"):
    """Query the Overpass API for features of *kind* within *bbox*.

    Parameters
    ----------
    bbox : tuple
        (south, west, north, east) in degrees.
    kind : str
        One of ``"WATER"``, ``"FOREST"``, ``"CITY"``.

    Returns
    -------
    requests.Response | None
        The API response, or *None* on failure.
    """
    south, west, north, east = bbox
    overpass_url = "http://overpass-api.de/api/interpreter"

    queries = {
        "WATER": f"""
        [out:json][timeout:25];
        (
            nwr["natural"="water"]({south},{west},{north},{east});
            nwr["water"="river"]({south},{west},{north},{east});
            nwr["water"="lake"]({south},{west},{north},{east});
        );
        out body;
        >;
        out skel qt;
        """,
        "FOREST": f"""
        [out:json][timeout:25];
        (
            nwr["natural"="wood"]({south},{west},{north},{east});
            nwr["landuse"="forest"]({south},{west},{north},{east});
        );
        out body;
        >;
        out skel qt;
        """,
        "CITY": f"""
        [out:json][timeout:25];
        (
            nwr["landuse"~"residential|urban|commercial|industrial"]({south},{west},{north},{east});
        );
        out body;
        >;
        out skel qt;
        """,
    }

    query = queries.get(kind, queries["WATER"])

    for attempt in range(3):
        try:
            response = requests.post(overpass_url, data={'data': query})
            if response.status_code == 200:
                return response
            if response.status_code == 504:
                print(f"Timeout (504), retrying... {attempt + 1}/3")
        except (requests.RequestException, OSError) as e:
            print("Request failed:", e)
            time.sleep(5)

    return None


def build_osm_nodes(data: dict) -> dict:
    """Index ``node`` elements by ID from an Overpass JSON response."""
    nodes = {}
    for element in data['elements']:
        if element['type'] == 'node':
            nodes[element['id']] = element
    return nodes


def extract_multipolygon_bodies(elements, nodes) -> list:
    """Stitch outer rings of multipolygon relations into closed loops.

    Returns a list of coordinate lists, each ``[(lat, lon, elevation), ...]``.
    """
    def _way_coords(way):
        return [
            (nodes[nid]['lat'], nodes[nid]['lon'], nodes[nid].get('elevation', 0))
            for nid in way['nodes']
            if nid in nodes
        ]

    multipolygon_bodies = []
    way_dict = {el['id']: el for el in elements if el['type'] == 'way'}

    for el in elements:
        if el['type'] not in ('relation', 'way'):
            continue

        outer_ways = []
        for member in el.get('members', []):
            if member['type'] != 'way':
                continue
            way = way_dict.get(member['ref'])
            if not way:
                continue
            if member.get('role', '') == 'outer':
                outer_ways.append(way)

        def _stitch_ways(ways):
            loops = []
            ways_coords = [_way_coords(w) for w in ways]

            while ways_coords:
                current = ways_coords.pop(0)
                changed = True
                while changed:
                    changed = False
                    i = 0
                    while i < len(ways_coords):
                        w = ways_coords[i]
                        if not w:
                            i += 1
                            continue
                        if current[-1] == w[0]:
                            current.extend(w[1:])
                            ways_coords.pop(i)
                            changed = True
                        elif current[-1] == w[-1]:
                            current.extend(reversed(w[:-1]))
                            ways_coords.pop(i)
                            changed = True
                        elif current[0] == w[-1]:
                            current = w[:-1] + current
                            ways_coords.pop(i)
                            changed = True
                        elif current[0] == w[0]:
                            current = list(reversed(w[1:])) + current
                            ways_coords.pop(i)
                            changed = True
                        else:
                            i += 1
                loops.append(current)
            return loops

        for loop in _stitch_ways(outer_ways):
            multipolygon_bodies.append(loop)

    return multipolygon_bodies

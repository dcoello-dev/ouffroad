import logging
import gpxpy

logger = logging.getLogger(__name__)


def parse_kml(content: bytes) -> list[gpxpy.gpx.GPX]:
    import xml.etree.ElementTree as ET

    gpx_list = []
    try:
        root = ET.fromstring(content)
        # Define namespaces
        ns = {
            "kml": "http://www.opengis.net/kml/2.2",
            "gx": "http://www.google.com/kml/ext/2.2",
        }

        # Find all Placemarks
        # Note: iterfind with namespaces requires the namespace in the tag
        # We'll try to find all Placemarks recursively
        for placemark in root.iter():
            if placemark.tag.endswith("Placemark"):
                name_elem = placemark.find("kml:name", ns)
                if name_elem is None:
                    name_elem = placemark.find("name")  # Try without namespace

                track_name = (
                    name_elem.text if name_elem is not None else "Unnamed Track"
                )

                # Check for LineString
                line_string = placemark.find(".//kml:LineString", ns)
                if line_string is None:
                    line_string = placemark.find(".//LineString")

                # Check for gx:Track
                gx_track = placemark.find(".//gx:Track", ns)

                coordinates = []

                if line_string is not None:
                    coords_elem = line_string.find("kml:coordinates", ns)
                    if coords_elem is None:
                        coords_elem = line_string.find("coordinates")

                    if coords_elem is not None and coords_elem.text:
                        # KML coordinates are lon,lat,alt
                        for coord_str in coords_elem.text.strip().split():
                            parts = coord_str.split(",")
                            if len(parts) >= 2:
                                lon = float(parts[0])
                                lat = float(parts[1])
                                ele = float(parts[2]) if len(parts) > 2 else None
                                coordinates.append((lat, lon, ele))

                elif gx_track is not None:
                    # gx:Track has multiple gx:coord elements: lon lat alt
                    for coord_elem in gx_track.findall("gx:coord", ns):
                        if coord_elem.text:
                            parts = coord_elem.text.split()
                            if len(parts) >= 2:
                                lon = float(parts[0])
                                lat = float(parts[1])
                                ele = float(parts[2]) if len(parts) > 2 else None
                                coordinates.append((lat, lon, ele))

                if coordinates:
                    gpx = gpxpy.gpx.GPX()
                    gpx_track = gpxpy.gpx.GPXTrack(name=track_name)
                    gpx.tracks.append(gpx_track)
                    gpx_segment = gpxpy.gpx.GPXTrackSegment()
                    gpx_track.segments.append(gpx_segment)

                    for lat, lon, ele in coordinates:
                        gpx_segment.points.append(
                            gpxpy.gpx.GPXTrackPoint(lat, lon, elevation=ele)
                        )

                    gpx_list.append(gpx)
                    logger.debug(f"Extracted track from KML: {track_name}")

    except Exception as e:
        logger.error(f"Error parsing KML: {e}")

    return gpx_list


def parse_kmz(content: bytes) -> list[gpxpy.gpx.GPX]:
    import zipfile
    from io import BytesIO

    gpx_list = []
    try:
        with zipfile.ZipFile(BytesIO(content)) as z:
            # Look for .kml files
            kml_files = [f for f in z.namelist() if f.endswith(".kml")]
            for kml_file in kml_files:
                logger.debug(f"Processing KML inside KMZ: {kml_file}")
                with z.open(kml_file) as f:
                    kml_content = f.read()
                    gpx_list.extend(parse_kml(kml_content))
    except Exception as e:
        logger.error(f"Error parsing KMZ: {e}")

    return gpx_list

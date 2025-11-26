import os
import re
import logging
import pathlib
from datetime import datetime
from io import BytesIO

import gpxpy
import gpxpy.gpx

from .ITrack import ITrack
from .Formats import GPX
from ouffroad.core.exceptions import MetadataError

logger = logging.getLogger(__name__)


def extract_datetime_from_gpx_path(file_path: str) -> datetime | None:
    file_name = os.path.basename(file_path)

    pattern = r"(\d{1,2})_([a-zA-Z]{3})_(\d{4})_(\d{1,2})_(\d{1,2})"

    match = re.search(pattern, file_name, re.IGNORECASE)

    spanish_to_english = {
        "ene": "jan",
        "feb": "feb",
        "mar": "mar",
        "abr": "apr",
        "may": "may",
        "jun": "jun",
        "jul": "jul",
        "ago": "aug",
        "sep": "sep",
        "oct": "oct",
        "nov": "nov",
        "dic": "dec",
    }
    if match:
        day = match.group(1)
        month = match.group(2)
        year = match.group(3)
        hour = match.group(4)
        minute = match.group(5)

        if month.lower() in spanish_to_english:
            month = spanish_to_english[month.lower()]

        date_time_str = f"{day} {month} {year} {hour} {minute}"
        date_format = "%d %b %Y %H %M"
        try:
            logger.debug(f"Parsing date from file name: {file_name} {date_time_str}")
            date_time_obj = datetime.strptime(date_time_str, date_format)
            return date_time_obj
        except ValueError:
            logger.error(f"Error parsing date from file name: {file_name}")
            return None
    else:
        return None


class GPXTrack(ITrack):
    def __init__(self, path: pathlib.Path, content: bytes | None = None):
        super().__init__(GPX, path)
        self.content_ = content
        self.gpx_ = None

    def date(self) -> datetime | None:
        if not self.gpx_:
            return None

        try:
            if self.gpx_.time:
                logger.debug(f"Found GPX file time: {self.gpx_.time}")
                return self.gpx_.time

            for track in self.gpx_.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        if point.time:
                            logger.debug(f"Found GPX point time: {point.time}")
                            return point.time
        except Exception as e:
            logger.error(f"Error extracting GPX date: {e}")

        date = extract_datetime_from_gpx_path(self.name())
        if date:
            return date

        logger.warning("Warning: Using current date as fallback for GPX")
        return datetime.now()

    def geojson(self) -> dict:
        if not self.gpx_:
            return {"type": "FeatureCollection", "features": []}

        features = []
        for track in self.gpx_.tracks:
            for segment in track.segments:
                coordinates = []
                for point in segment.points:
                    coordinates.append(
                        [point.longitude, point.latitude, point.elevation]
                    )

                feature = {
                    "type": "Feature",
                    "properties": {
                        "name": track.name or "Unnamed Track",
                        "description": track.description,
                    },
                    "geometry": {"type": "LineString", "coordinates": coordinates},
                }
                features.append(feature)

        return {"type": "FeatureCollection", "features": features}

    def load(self) -> bool:
        try:
            if self.content_:
                self.gpx_ = gpxpy.parse(BytesIO(self.content_))
                return True

            with open(self.path_, "r", encoding="utf-8") as gpx_file:
                self.gpx_ = gpxpy.parse(gpx_file)
                return True
        except Exception as e:
            logging.error(f"Error loading GPX file {self.path_}: {e}")
            raise MetadataError(f"Fallo al cargar el fichero GPX: {self.path_}") from e

    def save(self) -> bool:
        try:
            if self.gpx_:
                xml = self.gpx_.to_xml()
                # Ensure directory exists
                self.path_.parent.mkdir(parents=True, exist_ok=True)
                with open(self.path_, "w", encoding="utf-8") as f:
                    f.write(xml)
                return True
            return False
        except Exception as e:
            logging.error(f"Error saving GPX file {self.path_}: {e}")
            return False

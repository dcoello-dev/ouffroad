import logging
import pathlib
from datetime import datetime
from io import BytesIO

from fitparse import FitFile

from .ITrack import ITrack
from .Formats import FIT
from ouffroad.core.exceptions import MetadataError

logger = logging.getLogger(__name__)


class FITTrack(ITrack):
    def __init__(self, path: pathlib.Path, content: BytesIO | None = None):
        super().__init__(FIT, path)
        self.content_ = content
        self.fitfile_ = None

    def load(self) -> bool:
        try:
            if self.content_:
                # fitparse can parse from a file-like object (BytesIO)
                self.fitfile_ = FitFile(self.content_)
            else:
                self.fitfile_ = FitFile(str(self.path_))

            # Trigger parsing to ensure file is valid
            if self.fitfile_:
                self.fitfile_.parse()
            return True
        except Exception as e:
            logger.error(f"Error loading FIT file {self.path_}: {e}")
            raise MetadataError(f"Fallo al cargar el fichero FIT: {self.path_}") from e

    def save(self) -> bool:
        try:
            # fitparse is read-only, so we can only save if we have the raw content (e.g. from upload)
            if self.content_:
                # Ensure directory exists
                self.path_.parent.mkdir(parents=True, exist_ok=True)
                with open(self.path_, "wb") as f:
                    f.write(self.content_.getvalue())
                return True

            # If loaded from file and no content in memory, we assume it's already saved/unchanged
            # Since we can't edit FIT files, this is effectively a no-op success
            return True
        except Exception as e:
            logger.error(f"Error saving FIT file {self.path_}: {e}")
            return False

    def date(self) -> datetime | None:
        if not self.fitfile_:
            return None

        try:
            # Try to get the creation time from file_id message
            for record in self.fitfile_.get_messages("file_id"):
                for data in record:
                    if data.name == "time_created" and data.value:
                        logger.debug(f"Found time_created: {data.value}")
                        return data.value

            # Try to get timestamp from first record
            for record in self.fitfile_.get_messages("record"):
                for data in record:
                    if data.name == "timestamp" and data.value:
                        logger.debug(f"Found timestamp: {data.value}")
                        return data.value

            # Try to get timestamp from session
            for record in self.fitfile_.get_messages("session"):
                for data in record:
                    if data.name in ["start_time", "timestamp"] and data.value:
                        logger.debug(f"Found session time: {data.value}")
                        return data.value

            # Try to get timestamp from activity
            for record in self.fitfile_.get_messages("activity"):
                for data in record:
                    if data.name in ["timestamp", "local_timestamp"] and data.value:
                        logger.debug(f"Found activity time: {data.value}")
                        return data.value

        except Exception as e:
            logger.error(f"Error extracting FIT date: {e}")

        logger.warning("Warning: Using current date as fallback for FIT")
        return datetime.now()

    def geojson(self) -> dict:
        if not self.fitfile_:
            return {"type": "FeatureCollection", "features": []}

        coordinates = []

        try:
            for record in self.fitfile_.get_messages("record"):
                lat = None
                lon = None
                alt = None

                for data in record:
                    if data.name == "position_lat" and data.value is not None:
                        lat = data.value * (180 / 2**31)
                    elif data.name == "position_long" and data.value is not None:
                        lon = data.value * (180 / 2**31)
                    elif data.name == "altitude" and data.value is not None:
                        alt = data.value

                if lat is not None and lon is not None:
                    if alt is not None:
                        coordinates.append([lon, lat, alt])
                    else:
                        coordinates.append([lon, lat])
        except Exception as e:
            logger.error(f"Error extracting coordinates from FIT: {e}")

        if not coordinates:
            return {"type": "FeatureCollection", "features": []}

        feature = {
            "type": "Feature",
            "properties": {"name": self.name() or "FIT Track", "description": None},
            "geometry": {"type": "LineString", "coordinates": coordinates},
        }

        return {"type": "FeatureCollection", "features": [feature]}

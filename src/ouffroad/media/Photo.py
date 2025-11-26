import pathlib
import json
import logging
from datetime import datetime
from typing import Optional
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from .IMedia import IMedia
from ouffroad.core.exceptions import MetadataError

logger = logging.getLogger(__name__)


class Photo(IMedia):
    """Photo implementation that extracts EXIF data and location."""

    def __init__(self, path: pathlib.Path, content: Optional[bytes] = None):
        super().__init__("photo", path)
        self.content_ = content

    def load(self) -> bool:
        """Load photo and extract EXIF metadata."""
        try:
            if self.content_:
                # Load from bytes
                from io import BytesIO

                img = Image.open(BytesIO(self.content_))
            else:
                # Load from file
                if not self.path_.exists():
                    return False
                img = Image.open(self.path_)

            # Extract EXIF data
            exif_data = img.getexif()
            if exif_data:
                self.metadata_ = self._parse_exif(exif_data)
            else:
                self.metadata_ = {}

            # Check for sidecar JSON
            sidecar_path = pathlib.Path(str(self.path_) + ".json")
            if sidecar_path.exists():
                with open(sidecar_path, "r") as f:
                    sidecar_data = json.load(f)
                    # Sidecar overrides EXIF
                    self.metadata_.update(sidecar_data)

            return True
        except Exception as e:  # Catch generic Exception from Pillow or file operations
            logger.exception(f"Error loading photo {self.path_}")
            raise MetadataError(
                f"Fallo al cargar la foto {self.path_}"
            ) from e  # Re-raise as custom exception

    def _parse_exif(self, exif_data: Image.Exif) -> dict:
        """Parse EXIF data to extract GPS and date information."""
        metadata = {}

        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)

            # Extract GPS data
            if tag == "GPSInfo" and isinstance(value, dict):
                try:  # New try-except block for GPS processing
                    gps_data = {}
                    for gps_tag_id in value:
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag] = value[gps_tag_id]

                    # Convert GPS to decimal degrees
                    if "GPSLatitude" in gps_data and "GPSLongitude" in gps_data:
                        lat = self._convert_to_degrees(gps_data["GPSLatitude"])
                        lon = self._convert_to_degrees(gps_data["GPSLongitude"])

                        if gps_data.get("GPSLatitudeRef") == "S":
                            lat = -lat
                        if gps_data.get("GPSLongitudeRef") == "W":
                            lon = -lon

                        metadata["latitude"] = lat
                        metadata["longitude"] = lon
                except Exception as e:
                    logger.error(
                        f"Error procesando datos GPS de la foto {self.path_}. Error: {e}"
                    )
                    raise MetadataError(
                        f"Fallo al procesar datos GPS de la foto {self.path_}"
                    ) from e

            # Extract date
            elif tag == "DateTimeOriginal" or tag == "DateTime":
                try:
                    metadata["date"] = datetime.strptime(
                        str(value), "%Y:%m:%d %H:%M:%S"
                    )
                except (ValueError, TypeError):
                    logger.warning(
                        f"Could not parse EXIF date '{value}' for photo {self.path_}"
                    )
                    pass

        return metadata

    def _convert_to_degrees(self, value):
        """Convert GPS coordinates to degrees."""
        try:
            d, m, s = value
            return float(d) + (float(m) / 60.0) + (float(s) / 3600.0)
        except (ValueError, TypeError):
            # Return 0.0 if the format is not as expected
            return 0.0

    def save(self) -> bool:
        """Save photo to disk."""
        try:
            if self.content_:
                self.path_.parent.mkdir(parents=True, exist_ok=True)
                with open(self.path_, "wb") as f:
                    f.write(self.content_)
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving photo {self.path_}: {e}")
            return False

    def geojson(self) -> dict:
        """Return GeoJSON representation."""
        location = self.location()
        if not location:
            return {}

        lat, lon = location
        date_val = self.date()
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {
                        "name": self.name(),
                        "type": "photo",
                        "date": date_val.isoformat() if date_val else None,
                    },
                }
            ],
        }

    def date(self) -> Optional[datetime]:
        """Extract date from EXIF, sidecar JSON, or fallback to file modification time."""
        if self.metadata_ and "date" in self.metadata_:
            date_val = self.metadata_["date"]

            if isinstance(date_val, datetime):
                return date_val  # Already a datetime object from EXIF parsing
            elif isinstance(date_val, str):
                try:
                    # Attempt to parse ISO format first (common for sidecar)
                    return datetime.fromisoformat(date_val)
                except (ValueError, TypeError):
                    # Fallback to EXIF format (less likely for sidecar override)
                    try:
                        return datetime.strptime(date_val, "%Y:%m:%d %H:%M:%S")
                    except (ValueError, TypeError):
                        logger.warning(
                            f"Could not parse date string '{date_val}' from metadata for photo {self.path_}"
                        )
                        pass  # Continue to fallback if all parsing fails
            else:
                logger.warning(
                    f"Unexpected date type '{type(date_val)}' in metadata for photo {self.path_}"
                )

        # Fallback to file modification time
        if self.path_.exists():
            return datetime.fromtimestamp(self.path_.stat().st_mtime)

        return datetime.now()

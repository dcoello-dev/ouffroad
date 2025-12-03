import pathlib
import json
import logging
from datetime import datetime
from typing import Optional
from .IMedia import IMedia
from ouffroad.core.exceptions import MetadataError

logger = logging.getLogger(__name__)


class Video(IMedia):
    """Video implementation that uses sidecar JSON for location data."""

    def __init__(self, path: pathlib.Path, content: Optional[bytes] = None):
        super().__init__("video", path)
        self.content_ = content

    def load(self) -> bool:
        """Load video metadata from sidecar JSON."""
        try:
            # Videos don't have embedded GPS like photos
            # We rely on sidecar JSON files
            sidecar_path = pathlib.Path(str(self.path_) + ".json")

            if sidecar_path.exists():
                with open(sidecar_path, "r") as f:
                    self.metadata_ = json.load(f)
            else:
                self.metadata_ = {}

            return True
        except Exception as e:
            logger.exception(f"Error loading video metadata for {self.path_}")
            raise MetadataError(
                f"Fallo al cargar metadatos del video {self.path_}"
            ) from e

    def save(self) -> bool:
        """Save video to disk."""
        try:
            if self.content_:
                self.path_.parent.mkdir(parents=True, exist_ok=True)
                with open(self.path_, "wb") as f:
                    f.write(self.content_)
                return True
            return False
        except Exception:
            logger.exception(f"Error saving video {self.path_}")
            return False

    def date(self) -> Optional[datetime]:
        """Extract date from metadata or fallback to file modification time."""
        if self.metadata_ and "date" in self.metadata_:
            date_str = self.metadata_["date"]
            try:
                return datetime.fromisoformat(date_str)
            except (ValueError, TypeError):
                logger.warning(
                    f"Could not parse sidecar date '{date_str}' for video {self.path_}"
                )
                # Fallback if parsing fails
                pass

        if self.path_.exists():
            return datetime.fromtimestamp(self.path_.stat().st_mtime)

        return datetime.now()

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
                        "type": "video",
                        "date": date_val.isoformat() if date_val else None,
                    },
                }
            ],
        }

import pathlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime


from ouffroad.core.IFile import IFile

logger = logging.getLogger(__name__)


class IMedia(IFile):
    """Abstract base class for media files (photos and videos)."""

    def __init__(self, format: str, path: pathlib.Path):
        super().__init__(format, path)
        self.metadata_: Dict[str, Any] | None = None

    def location(self) -> Optional[tuple[float, float]]:
        """Return (latitude, longitude) if available."""
        if (
            self.metadata_
            and "latitude" in self.metadata_
            and "longitude" in self.metadata_
        ):
            return (self.metadata_["latitude"], self.metadata_["longitude"])
        return None

    def save_metadata(self, latitude: float, longitude: float) -> bool:
        """Save location metadata to sidecar JSON."""
        try:
            sidecar_path = pathlib.Path(str(self.path_) + ".json")
            metadata = {
                "latitude": latitude,
                "longitude": longitude,
                "date": datetime.now().isoformat(),
            }

            with open(sidecar_path, "w") as f:
                json.dump(metadata, f, indent=2)

            self.metadata_ = metadata
            return True
        except Exception:
            logger.exception(f"Error saving metadata for {self.path_}")
            return False

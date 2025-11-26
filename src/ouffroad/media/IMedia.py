import pathlib
from typing import Optional, Dict, Any


from ouffroad.core.IFile import IFile


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

import pathlib
import logging
from typing import Dict, Any, Sequence
from ouffroad.core.IFile import IFile
from ouffroad.repository.ITrackRepository import ITrackRepository
from ouffroad.track.TrackFactory import TrackFactory
from ouffroad.media.MediaFactory import MediaFactory
from ouffroad.zone.ZoneFactory import ZoneFactory

logger = logging.getLogger(__name__)


class ContentManager:
    """Unified service layer for managing all file types (tracks and media)."""

    def __init__(self, repository: ITrackRepository):
        self.repo = repository

    def import_file(
        self, file_path: pathlib.Path, category: str, content: bytes | None = None
    ) -> Sequence[str]:
        """
        Import file(s) into the system.
        Handles tracks (GPX, FIT, KML, KMZ) and media (photos, videos).
        """
        # files can be of type ITrack or IMedia, IFile is the common ancestor.
        files: Sequence[IFile] = TrackFactory.create(file_path, content)

        # If not a track, try MediaFactory
        if not files:
            files = MediaFactory.create(file_path, content)

        # If not media, try ZoneFactory
        if not files:
            files = ZoneFactory.create(file_path, content)

        if not files:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        saved_paths = []
        for file in files:
            # Load to validate and extract metadata. If it fails, it will raise MetadataError.
            file.load()

            # Save using repository
            rel_path = self.repo.save(file, category)
            saved_paths.append(str(rel_path))

        return saved_paths

    def list_files(self) -> Sequence[str]:
        """List all available files (tracks and media)."""
        return self.repo.list_all()

    def get_geojson(self, rel_path: str) -> Dict[str, Any]:
        """Get the GeoJSON representation of file(s)."""
        files = self.repo.get(rel_path)
        if not files:
            raise FileNotFoundError(f"File not found: {rel_path}")

        all_features = []
        for file in files:
            # Load to validate and extract metadata. If it fails, it will raise MetadataError.
            file.load()

            geojson = file.geojson()
            if "features" in geojson:
                all_features.extend(geojson["features"])
            else:
                # Handle single geometry if not FeatureCollection
                all_features.append(geojson)

        return {"type": "FeatureCollection", "features": all_features}

    def update_media_location(
        self, rel_path: str, latitude: float, longitude: float
    ) -> bool:
        """
        Update location for a media file via sidecar JSON.
        Applicable to all media files (photos and videos).
        """
        files = self.repo.get(rel_path)
        if not files:
            raise FileNotFoundError(f"File not found: {rel_path}")

        file = files[0]  # Should only be one file

        # All IMedia instances support manual location updates via sidecar
        from ouffroad.media.IMedia import IMedia

        if isinstance(file, IMedia):
            return file.save_metadata(latitude, longitude)
        else:
            raise ValueError("Only media files support manual location updates")

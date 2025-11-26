import pathlib
from typing import Dict, Any, Sequence
from ouffroad.media.MediaFactory import MediaFactory
from ouffroad.repository.FileSystemRepository import FileSystemRepository


class MediaManager:
    """Service layer for managing media files (photos and videos)."""

    def __init__(self, repository: FileSystemRepository):
        self.repo = repository

    def import_media(
        self, file_path: pathlib.Path, category: str, content: bytes
    ) -> Sequence[str]:
        """
        Import media file(s) into the repository.

        Args:
            file_path: Path object with the filename
            category: Category to store the media in
            content: File content as bytes

        Returns:
            List of relative paths where media was saved
        """
        media_list = MediaFactory.create(file_path, content)

        if not media_list:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        saved_paths = []
        for media in media_list:
            media.load()

            rel_path = self.repo.save(media, category)
            saved_paths.append(str(rel_path))

        return saved_paths

    def list_media(self) -> Sequence[str]:
        """List all media files in the repository."""
        return self.repo.list_all()

    def get_media_geojson(self, rel_path: str) -> Dict[str, Any]:
        """Gets the GeoJSON representation of media."""
        media_list = self.repo.get(rel_path)
        if not media_list:
            raise FileNotFoundError(f"Media not found: {rel_path}")

        all_features = []
        for media in media_list:
            media.load()

            geojson = media.geojson()
            if "features" in geojson:
                all_features.extend(geojson["features"])
            else:
                # Handle single geometry if not FeatureCollection
                all_features.append(geojson)

        return {"type": "FeatureCollection", "features": all_features}

    def update_media_location(
        self, rel_path: str, latitude: float, longitude: float
    ) -> bool:
        """Update location for a video file via sidecar JSON."""
        media_list = self.repo.get(rel_path)
        if not media_list:
            raise FileNotFoundError(f"Media not found: {rel_path}")

        media = media_list[0]  # Should only be one media file

        # Only videos support manual location updates
        from ouffroad.media.Video import Video

        if isinstance(media, Video):
            return media.save_metadata(latitude, longitude)
        else:
            raise ValueError("Only videos support manual location updates")

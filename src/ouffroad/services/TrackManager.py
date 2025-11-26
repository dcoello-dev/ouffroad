import pathlib
from typing import Sequence, Dict, Any
from ouffroad.repository.ITrackRepository import ITrackRepository
from ouffroad.track.TrackFactory import TrackFactory


class TrackManager:
    def __init__(self, repository: ITrackRepository):
        self.repo = repository

    def import_track(
        self, file_path: pathlib.Path, category: str, content: bytes | None = None
    ) -> Sequence[str]:
        """
        Imports track file(s) into the system.
        Returns a list of relative paths of saved files.

        Note: Returns a list because some formats (KML/KMZ) can contain multiple tracks.
        Single track files (GPX, FIT) will return a list with one element.

        Args:
            file_path: Path to the file (used for extension detection)
            category: Category to save the track(s) under
            content: Optional file content as bytes

        Returns:
            List of relative paths where tracks were saved

        Raises:
            ValueError: If file format is unsupported or file is corrupted
        """
        # Factory handles detection and conversion (returns list)
        tracks = TrackFactory.create(file_path, content)

        if not tracks:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        saved_paths = []
        for track in tracks:
            # Load to validate and extract metadata (like date)
            track.load()

            # Save using repository
            rel_path = self.repo.save(track, category)
            saved_paths.append(str(rel_path))

        return saved_paths

    def list_tracks(self) -> Sequence[str]:
        """Lists all available tracks."""
        return self.repo.list_all()

    def get_track_geojson(self, rel_path: str) -> Dict[str, Any]:
        """Gets the GeoJSON representation of a track (or tracks)."""
        tracks = self.repo.get(rel_path)
        if not tracks:
            raise FileNotFoundError(f"Track not found: {rel_path}")

        all_features = []
        for track in tracks:
            if not track.load():
                raise ValueError(f"Could not load track file: {track.name()}")

            geojson = track.geojson()
            if "features" in geojson:
                all_features.extend(geojson["features"])
            else:
                # Handle single geometry if not FeatureCollection (though ITrack usually returns FeatureCollection)
                all_features.append(geojson)

        return {"type": "FeatureCollection", "features": all_features}

import pathlib
from typing import Sequence
from io import BytesIO

from .ITrack import ITrack
from .GPXTrack import GPXTrack
from .FITTrack import FITTrack
from ..core.Parsers import parse_kml, parse_kmz


class TrackFactory:
    @staticmethod
    def create(path: pathlib.Path, content: bytes | None = None) -> Sequence[ITrack]:
        """
        Creates ITrack instances based on file extension.
        Returns a sequence to handle aggregates (KML/KMZ can contain multiple tracks).
        Single files return a sequence with 1 element.

        Args:
            path: Path to the file (used for extension detection and naming)
            content: Optional file content as bytes

        Returns:
            Sequence of ITrack instances (empty list if unsupported format)
        """
        suffix = path.suffix.lower()

        # Single track formats
        if suffix == ".gpx":
            gpx_track = GPXTrack(path, content)
            return [gpx_track]

        elif suffix == ".fit":
            # FITTrack expects a file-like object (BytesIO) for content
            fit_content = BytesIO(content) if content else None
            fit_track = FITTrack(path, fit_content)
            return [fit_track]

        # Aggregate formats - convert to GPX
        elif suffix == ".kml":
            if content:
                return TrackFactory._import_kml(path, content)

        elif suffix == ".kmz":
            if content:
                return TrackFactory._import_kmz(path, content)

        # Unsupported format
        return []

    @staticmethod
    def _import_kml(path: pathlib.Path, content: bytes) -> Sequence[ITrack]:
        """
        Converts KML to multiple GPX tracks.
        KML files can contain multiple Placemarks, each becomes a separate GPX track.
        """
        gpx_list = parse_kml(content)
        tracks: list[ITrack] = []

        for i, gpx in enumerate(gpx_list):
            # Extract track name or use default
            track_name = (
                gpx.tracks[0].name
                if gpx.tracks and gpx.tracks[0].name
                else f"track_{i}"
            )
            # Sanitize filename
            safe_name = "".join(
                [
                    c
                    for c in track_name
                    if c.isalpha() or c.isdigit() or c in (" ", "-", "_")
                ]
            ).rstrip()
            if not safe_name:
                safe_name = f"track_{i}"

            # Create GPXTrack from converted content
            gpx_path = path.with_name(f"{safe_name}.gpx")
            gpx_content = gpx.to_xml().encode("utf-8")

            track = GPXTrack(gpx_path, gpx_content)
            tracks.append(track)

        return tracks

    @staticmethod
    def _import_kmz(path: pathlib.Path, content: bytes) -> Sequence[ITrack]:
        """
        Converts KMZ (zipped KML) to multiple GPX tracks.
        KMZ files are extracted and each KML inside is processed.
        """
        gpx_list = parse_kmz(content)
        tracks: list[ITrack] = []

        for i, gpx in enumerate(gpx_list):
            track_name = (
                gpx.tracks[0].name
                if gpx.tracks and gpx.tracks[0].name
                else f"track_{i}"
            )
            safe_name = "".join(
                [
                    c
                    for c in track_name
                    if c.isalpha() or c.isdigit() or c in (" ", "-", "_")
                ]
            ).rstrip()
            if not safe_name:
                safe_name = f"track_{i}"

            gpx_path = path.with_name(f"{safe_name}.gpx")
            gpx_content = gpx.to_xml().encode("utf-8")

            track = GPXTrack(gpx_path, gpx_content)
            tracks.append(track)

        return tracks

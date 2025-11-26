import pytest
import pathlib
from unittest.mock import Mock, patch

from ouffroad.services.TrackManager import TrackManager
from ouffroad.repository.ITrackRepository import ITrackRepository
from ouffroad.track.GPXTrack import GPXTrack
from ouffroad.core.exceptions import MetadataError  # Added import


@pytest.fixture
def mock_repository():
    """Create a mock repository for testing."""
    return Mock(spec=ITrackRepository)


@pytest.fixture
def track_manager(mock_repository):
    """Create a TrackManager with a mock repository."""
    return TrackManager(mock_repository)


@pytest.fixture
def sample_gpx_content():
    """Sample GPX content for testing."""
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="TestCreator">
  <metadata>
    <time>2023-10-27T10:00:00Z</time>
  </metadata>
  <trk>
    <name>Test Track</name>
    <trkseg>
      <trkpt lat="40.0" lon="-3.0">
        <ele>100.0</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""


def test_track_manager_initialization(mock_repository):
    """Test that TrackManager initializes with a repository."""
    manager = TrackManager(mock_repository)
    assert manager.repo == mock_repository


@patch("ouffroad.services.TrackManager.TrackFactory")
def test_import_track_success(
    mock_factory, track_manager, mock_repository, sample_gpx_content
):
    """Test successful track import (single track)."""
    # Setup mock track
    mock_track = Mock(spec=GPXTrack)
    mock_track.load.return_value = True
    mock_track.name.return_value = "test.gpx"
    # Factory now returns a LIST
    mock_factory.create.return_value = [mock_track]

    # Setup mock repository
    mock_repository.save.return_value = pathlib.Path("trail/2023/10/test.gpx")

    # Import track
    file_path = pathlib.Path("test.gpx")
    result = track_manager.import_track(file_path, "trail", sample_gpx_content)

    # Verify
    mock_factory.create.assert_called_once_with(file_path, sample_gpx_content)
    mock_track.load.assert_called_once()
    mock_repository.save.assert_called_once_with(mock_track, "trail")
    # Result is now a list
    assert isinstance(result, list)
    assert len(result) == 1
    # Normalize path separators for cross-platform compatibility
    assert result[0].replace("\\", "/") == "trail/2023/10/test.gpx"


@patch("ouffroad.services.TrackManager.TrackFactory")
def test_import_track_unsupported_format(
    mock_factory, track_manager, sample_gpx_content
):
    """Test that import_track raises ValueError for unsupported formats."""
    # Factory returns empty list for unsupported formats
    mock_factory.create.return_value = []

    file_path = pathlib.Path("test.xyz")

    with pytest.raises(ValueError, match="Unsupported file format"):
        track_manager.import_track(file_path, "trail", sample_gpx_content)


@patch("ouffroad.services.TrackManager.TrackFactory")
def test_import_track_corrupted_file(mock_factory, track_manager, sample_gpx_content):
    """Test that import_track raises MetadataError when track fails to load."""
    # Setup mock track that fails to load by raising MetadataError
    mock_track = Mock(spec=GPXTrack)
    mock_track.load.side_effect = MetadataError(
        "Mocked load failure"
    )  # Changed from return_value=False
    mock_track.name.return_value = "corrupted.gpx"
    mock_factory.create.return_value = [mock_track]

    file_path = pathlib.Path("corrupted.gpx")

    with pytest.raises(
        MetadataError, match="Mocked load failure"
    ):  # Changed from ValueError
        track_manager.import_track(file_path, "trail", sample_gpx_content)

    mock_track.load.assert_called_once()


def test_list_tracks_empty(track_manager, mock_repository):
    """Test list_tracks with empty repository."""
    mock_repository.list_all.return_value = []

    result = track_manager.list_tracks()

    assert result == []
    mock_repository.list_all.assert_called_once()


def test_list_tracks_with_content(track_manager, mock_repository):
    """Test list_tracks with tracks in repository."""
    expected_tracks = [
        "trail/2023/10/track1.gpx",
        "enduro/2023/11/track2.fit",
        "special_events/2023/12/track3.gpx",
    ]
    mock_repository.list_all.return_value = expected_tracks

    result = track_manager.list_tracks()

    assert result == expected_tracks
    mock_repository.list_all.assert_called_once()


def test_get_track_geojson_success(track_manager, mock_repository):
    """Test successful GeoJSON retrieval."""
    # Setup mock track
    mock_track = Mock(spec=GPXTrack)
    mock_track.load.return_value = True
    expected_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": [[0, 0]]},
                "properties": {"name": "Test Track"},
            }
        ],
    }
    mock_track.geojson.return_value = expected_geojson

    # Setup mock repository
    mock_repository.get.return_value = [mock_track]

    # Get GeoJSON
    result = track_manager.get_track_geojson("trail/2023/10/test.gpx")

    # Verify
    mock_repository.get.assert_called_once_with("trail/2023/10/test.gpx")
    mock_track.load.assert_called_once()
    mock_track.geojson.assert_called_once()
    assert result == expected_geojson


def test_get_track_geojson_not_found(track_manager, mock_repository):
    """Test that get_track_geojson raises FileNotFoundError for non-existent tracks."""
    mock_repository.get.return_value = None

    with pytest.raises(FileNotFoundError, match="Track not found"):
        track_manager.get_track_geojson("nonexistent/path.gpx")

    mock_repository.get.assert_called_once_with("nonexistent/path.gpx")


@patch("ouffroad.services.TrackManager.TrackFactory")
def test_import_track_without_content(mock_factory, track_manager, mock_repository):
    """Test importing track without content (from file path only)."""
    # Setup mock track
    mock_track = Mock(spec=GPXTrack)
    mock_track.load.return_value = True
    mock_track.name.return_value = "test.gpx"
    mock_factory.create.return_value = [mock_track]

    # Setup mock repository
    mock_repository.save.return_value = pathlib.Path("trail/2023/10/test.gpx")

    # Import track without content
    file_path = pathlib.Path("test.gpx")
    result = track_manager.import_track(file_path, "trail", None)

    # Verify
    mock_factory.create.assert_called_once_with(file_path, None)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].replace("\\", "/") == "trail/2023/10/test.gpx"


@patch("ouffroad.services.TrackManager.TrackFactory")
def test_import_multiple_tracks_from_kml(
    mock_factory, track_manager, mock_repository, sample_gpx_content
):
    """Test importing KML file that contains multiple tracks."""
    # Setup multiple mock tracks (simulating KML with 3 placemarks)
    mock_track1 = Mock(spec=GPXTrack)
    mock_track1.load.return_value = True
    mock_track1.name.return_value = "track1.gpx"

    mock_track2 = Mock(spec=GPXTrack)
    mock_track2.load.return_value = True
    mock_track2.name.return_value = "track2.gpx"

    mock_track3 = Mock(spec=GPXTrack)
    mock_track3.load.return_value = True
    mock_track3.name.return_value = "track3.gpx"

    # Factory returns list of 3 tracks
    mock_factory.create.return_value = [mock_track1, mock_track2, mock_track3]

    # Setup mock repository to return different paths
    mock_repository.save.side_effect = [
        pathlib.Path("trail/2023/10/track1.gpx"),
        pathlib.Path("trail/2023/10/track2.gpx"),
        pathlib.Path("trail/2023/10/track3.gpx"),
    ]

    # Import KML
    result = track_manager.import_track(
        pathlib.Path("routes.kml"), "trail", sample_gpx_content
    )

    # Verify
    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0].replace("\\", "/") == "trail/2023/10/track1.gpx"
    assert result[1].replace("\\", "/") == "trail/2023/10/track2.gpx"
    assert result[2].replace("\\", "/") == "trail/2023/10/track3.gpx"
    assert mock_repository.save.call_count == 3

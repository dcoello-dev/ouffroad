import pytest
import pathlib
import os
from datetime import datetime
from unittest.mock import Mock

from ouffroad.repository.FileSystemRepository import FileSystemRepository
from ouffroad.track.GPXTrack import GPXTrack
from ouffroad.storage.IStoragePolicy import IStoragePolicy  # Keep this import
from ouffroad.config import (
    OuffroadConfig,
    RepositoryConfig,
    CategoryConfig,
    DateBasedPolicyConfig,
    FlatPolicyConfig,
    StoragePolicyType,
)


class MockStoragePolicy(IStoragePolicy):
    """A mock storage policy for testing purposes."""

    def get_relative_path(
        self, category: str, date: datetime | None, filename: str
    ) -> pathlib.Path:
        return pathlib.Path(category) / "custom" / filename


@pytest.fixture
def base_ouffroad_config(tmp_path) -> OuffroadConfig:
    """Provides a base OuffroadConfig object with a simple repository config."""
    repo_root = tmp_path / "test_repo_root"
    repo_root.mkdir(exist_ok=True)

    # Create a simple default repository config
    repo_config = RepositoryConfig(
        categories={
            "trail": CategoryConfig(
                name="trail",
                type="track",
                extensions=[".gpx", ".fit"],
                storage_policy=DateBasedPolicyConfig(),
            ),
            "enduro": CategoryConfig(
                name="enduro",
                type="track",
                extensions=[".gpx"],
                storage_policy=DateBasedPolicyConfig(),
            ),
            "media": CategoryConfig(
                name="media",
                type="media",
                extensions=[".jpg", ".mp4"],
                storage_policy=FlatPolicyConfig(),
            ),
            "special_events": CategoryConfig(
                name="special_events",
                type="track",
                extensions=[".gpx"],
                storage_policy=DateBasedPolicyConfig(),
            ),
        }
    )

    config = OuffroadConfig(repository_path=repo_root, repository_config=repo_config)
    return config


@pytest.fixture
def temp_repo(base_ouffroad_config) -> tuple[FileSystemRepository, pathlib.Path]:
    """Create a temporary repository for testing."""
    repo = FileSystemRepository(base_ouffroad_config)
    return repo, base_ouffroad_config.repository_path


@pytest.fixture
def custom_policy_repo(
    tmp_path, monkeypatch
) -> tuple[FileSystemRepository, pathlib.Path]:
    """Create a repository with a custom policy."""
    repo_root = tmp_path / "custom_repo_root"
    repo_root.mkdir(exist_ok=True)

    # Define a custom policy config based on our mock policy
    # We'll configure a category to use a DateBasedPolicy in the config,
    # but then patch the FileSystemRepository to return our MockStoragePolicy instance.
    mock_policy_config: StoragePolicyType = DateBasedPolicyConfig(
        name="DateBasedPolicy"
    )

    # Create a category that will use our mock policy
    repo_config = RepositoryConfig(
        categories={
            "trail": CategoryConfig(
                name="trail",
                type="track",
                extensions=[".gpx"],
                storage_policy=mock_policy_config,
            ),
        }
    )

    # Create a mock IStoragePolicy for the repository to use for the "trail" category
    mock_policy_instance = Mock(spec=IStoragePolicy)
    mock_policy_instance.get_relative_path.side_effect = (
        MockStoragePolicy().get_relative_path
    )  # Use our actual mock logic

    # We need to mock the _get_storage_policy_instance method within the FileSystemRepository
    # to control what policy instance is returned for a given config.
    # This is a bit tricky, might need to patch the method directly.

    config = OuffroadConfig(repository_path=repo_root, repository_config=repo_config)
    repo = FileSystemRepository(config)

    # Patch the _get_storage_policy_instance to return our mock for the 'trail' category
    original_get_policy_instance = repo._get_storage_policy_instance

    def patched_get_policy_instance(policy_config_arg: StoragePolicyType):
        if (
            policy_config_arg.name == "DateBasedPolicy"
        ):  # This is the type we used in mock_policy_config
            return mock_policy_instance
        return original_get_policy_instance(
            policy_config_arg
        )  # Pass the argument to original

    monkeypatch.setattr(
        repo,
        "_get_storage_policy_instance",
        Mock(side_effect=patched_get_policy_instance),
    )

    return repo, repo_root


@pytest.fixture
def sample_gpx_track(tmp_path):
    """Create a sample GPX track for testing."""
    gpx_content = b"""<?xml version="1.0" encoding="UTF-8"?>
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
    track_path = tmp_path / "test_track.gpx"
    track = GPXTrack(track_path, gpx_content)
    track.load()
    return track


def test_repository_initialization(temp_repo):
    """Test that repository creates base directory on initialization."""
    repo, repo_path = temp_repo
    assert repo_path.exists()
    assert repo_path.is_dir()


def test_save_track_creates_correct_structure(temp_repo, sample_gpx_track):
    """Test that save() creates the correct directory structure."""
    repo, repo_path = temp_repo

    # Save track to 'trail' category
    rel_path = repo.save(sample_gpx_track, "trail")

    # Check that the file was saved
    saved_file = repo_path / rel_path
    assert saved_file.exists()

    # Check directory structure: trail/2023/10/
    assert "trail" in str(rel_path)
    assert "2023" in str(rel_path)
    assert "10" in str(rel_path)


def test_save_track_handles_duplicates(temp_repo, sample_gpx_track):
    """Test that save() renames duplicate files."""
    repo, repo_path = temp_repo

    # Save the same track twice
    rel_path_1 = repo.save(sample_gpx_track, "enduro")

    # Create another track with the same name
    gpx_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1"><metadata><time>2023-10-27T10:00:00Z</time></metadata><trk><name>Test</name></trk></gpx>"""
    track_path_2 = pathlib.Path("test_track.gpx")
    track_2 = GPXTrack(track_path_2, gpx_content)
    track_2.load()

    rel_path_2 = repo.save(track_2, "enduro")

    # Verify both files exist and have different names
    assert (repo_path / rel_path_1).exists()
    assert (repo_path / rel_path_2).exists()
    assert rel_path_1 != rel_path_2
    assert "test_track_1.gpx" in str(rel_path_2)


def test_get_existing_track(temp_repo, sample_gpx_track):
    """Test that get() retrieves an existing track."""
    repo, repo_path = temp_repo

    # Save a track
    rel_path = repo.save(sample_gpx_track, "trail")

    # Retrieve it - get() returns a single ITrack (or list with one element from factory)
    retrieved = repo.get(str(rel_path))

    # Factory.create() returns a list, so get() will return the first element
    assert retrieved is not None
    # If get() uses factory, it might return a list - handle both cases
    if isinstance(retrieved, list):
        retrieved_track = retrieved[0]
    else:
        retrieved_track = retrieved

    assert isinstance(retrieved_track, GPXTrack)
    # Path comparison - handle both single track and list
    if isinstance(retrieved, list):
        assert retrieved_track.path() == repo_path / rel_path
    else:
        assert retrieved.path() == repo_path / rel_path
    # tracks = repo.list_all()
    # assert tracks == []


def test_list_all_with_tracks(temp_repo, sample_gpx_track):
    """Test that list_all() returns all saved tracks."""
    repo, _ = temp_repo

    # Save multiple tracks
    rel_path_1 = repo.save(sample_gpx_track, "trail")

    # Create another track
    gpx_content_2 = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1"><metadata><time>2023-11-15T15:30:00Z</time></metadata><trk><name>Track 2</name></trk></gpx>"""
    track_2 = GPXTrack(pathlib.Path("track2.gpx"), gpx_content_2)
    track_2.load()
    rel_path_2 = repo.save(track_2, "enduro")

    # List all tracks
    tracks = repo.list_all()

    assert len(tracks) == 2
    assert str(rel_path_1).replace(os.sep, "/") in tracks
    assert str(rel_path_2).replace(os.sep, "/") in tracks


def test_exists_for_existing_track(temp_repo, sample_gpx_track):
    """Test that exists() returns True for existing tracks."""
    repo, _ = temp_repo

    rel_path = repo.save(sample_gpx_track, "trail")

    assert repo.exists(str(rel_path)) is True


def test_exists_for_nonexistent_track(temp_repo):
    """Test that exists() returns False for non-existent tracks."""
    repo, _ = temp_repo

    assert repo.exists("fake/path/file.gpx") is False


def test_save_track_without_date_uses_current_date(temp_repo, sample_gpx_track):
    """Test that save() uses current date when track has no date."""
    repo, repo_path = temp_repo

    # Create a GPX with no time metadata
    gpx_no_date = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1"><trk><trkseg></trkseg></trk></gpx>"""

    track = GPXTrack(repo_path / "no_date.gpx", gpx_no_date)
    track.load()

    # Save it
    rel_path = repo.save(track, "special_events")

    # Should use current year/month
    current_year = datetime.now().strftime("%Y")
    current_month = datetime.now().strftime("%m")

    assert current_year in str(rel_path)
    assert current_month in str(rel_path)


def test_get_absolute_path(temp_repo):
    """Test the internal _get_absolute_path method."""
    repo, repo_path = temp_repo

    rel_path = "trail/2023/10/test.gpx"
    abs_path = repo._get_absolute_path(rel_path)

    expected = repo_path / "trail" / "2023" / "10" / "test.gpx"
    assert abs_path == expected


def test_save_with_custom_policy(custom_policy_repo, sample_gpx_track):
    """Test saving with a custom storage policy."""
    repo, repo_path = custom_policy_repo

    rel_path = repo.save(sample_gpx_track, "trail")

    # Check structure: trail/custom/filename
    assert "trail" in str(rel_path)
    assert "custom" in str(rel_path)
    assert (repo_path / rel_path).exists()

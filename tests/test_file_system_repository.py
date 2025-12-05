"""Integration tests for FileSystemRepository move and rename operations."""

import pytest
import pathlib
import tempfile
import shutil

from ouffroad.repository.FileSystemRepository import FileSystemRepository
from ouffroad.config import (
    OuffroadConfig,
    RepositoryConfig,
    CategoryConfig,
    DateBasedPolicyConfig,
    FlatPolicyConfig,
)
from ouffroad.core.file_operations import get_sidecar_path


@pytest.fixture
def temp_repo():
    """Create a temporary repository with test configuration."""
    temp_path = pathlib.Path(tempfile.mkdtemp())

    # Create test config
    config = OuffroadConfig(
        repository_path=temp_path,
        repository_config=RepositoryConfig(
            categories={
                "trail": CategoryConfig(
                    name="Trail",
                    type="track",
                    extensions=[".gpx"],
                    storage_policy=DateBasedPolicyConfig(),
                ),
                "enduro": CategoryConfig(
                    name="Enduro",
                    type="track",
                    extensions=[".gpx"],
                    storage_policy=DateBasedPolicyConfig(),
                ),
                "media": CategoryConfig(
                    name="Media",
                    type="media",
                    extensions=[".jpg", ".png"],
                    storage_policy=FlatPolicyConfig(),
                ),
            }
        ),
    )

    repo = FileSystemRepository(config)

    yield repo, temp_path

    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


def create_test_gpx(path: pathlib.Path, name: str = "Test Track"):
    """Create a minimal valid GPX file."""
    gpx_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
  <metadata>
    <time>2024-01-15T10:00:00Z</time>
  </metadata>
  <trk>
    <name>{name}</name>
    <trkseg>
      <trkpt lat="40.7128" lon="-74.0060"><ele>10</ele></trkpt>
      <trkpt lat="40.7138" lon="-74.0050"><ele>12</ele></trkpt>
    </trkseg>
  </trk>
</gpx>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(gpx_content)


class TestRepositoryMove:
    """Tests for repository move operation."""

    def test_move_track_between_categories(self, temp_repo):
        """Test moving a track from one category to another."""
        repo, temp_path = temp_repo

        # Create a track in trail category
        source_path = temp_path / "trail" / "2024" / "01" / "test.gpx"
        create_test_gpx(source_path)

        source_rel = "trail/2024/01/test.gpx"

        # Move to enduro category
        new_rel = repo.move(source_rel, "enduro")

        # Verify source no longer exists
        assert not (temp_path / source_rel).exists()

        # Verify target exists
        assert (temp_path / new_rel).exists()
        assert "enduro" in new_rel
        assert "test.gpx" in new_rel

    def test_move_track_with_sidecar(self, temp_repo):
        """Test moving track file with sidecar."""
        repo, temp_path = temp_repo

        # Create track file with sidecar
        source_path = temp_path / "trail" / "2024" / "01" / "track.gpx"
        create_test_gpx(source_path)

        sidecar = get_sidecar_path(source_path)
        sidecar.write_text('{"custom_data": "test"}')

        source_rel = "trail/2024/01/track.gpx"

        # Move to enduro category
        new_rel = repo.move(source_rel, "enduro")

        # Verify both moved
        assert not source_path.exists()
        assert not sidecar.exists()

        new_path = temp_path / new_rel
        assert new_path.exists()
        assert get_sidecar_path(new_path).exists()
        assert "enduro" in new_rel

    def test_move_with_target_folder(self, temp_repo):
        """Test moving to a specific folder."""
        repo, temp_path = temp_repo

        # Create track
        source_path = temp_path / "trail" / "2024" / "01" / "test.gpx"
        create_test_gpx(source_path)

        source_rel = "trail/2024/01/test.gpx"

        # Move to specific folder in enduro
        new_rel = repo.move(source_rel, "enduro", "2024/02")

        # Verify moved to exact location
        assert new_rel == "enduro/2024/02/test.gpx"
        assert (temp_path / new_rel).exists()

    def test_move_source_not_found(self, temp_repo):
        """Test moving non-existent file."""
        repo, _ = temp_repo

        with pytest.raises(FileNotFoundError):
            repo.move("nonexistent/file.gpx", "enduro")

    def test_move_invalid_category(self, temp_repo):
        """Test moving to invalid category."""
        repo, temp_path = temp_repo

        # Create track
        source_path = temp_path / "trail" / "2024" / "01" / "test.gpx"
        create_test_gpx(source_path)

        with pytest.raises(ValueError, match="Invalid target category"):
            repo.move("trail/2024/01/test.gpx", "invalid_category")

    def test_move_target_exists(self, temp_repo):
        """Test moving when target already exists."""
        repo, temp_path = temp_repo

        # Create source
        source_path = temp_path / "trail" / "2024" / "01" / "test.gpx"
        create_test_gpx(source_path)

        # Create target
        target_path = temp_path / "enduro" / "2024" / "01" / "test.gpx"
        create_test_gpx(target_path)

        with pytest.raises(ValueError, match="already exists"):
            repo.move("trail/2024/01/test.gpx", "enduro")


class TestRepositoryRename:
    """Tests for repository rename operation."""

    def test_rename_track(self, temp_repo):
        """Test renaming a track file."""
        repo, temp_path = temp_repo

        # Create track
        source_path = temp_path / "trail" / "2024" / "01" / "old_name.gpx"
        create_test_gpx(source_path, "Old Name")

        source_rel = "trail/2024/01/old_name.gpx"

        # Rename
        new_rel = repo.rename(source_rel, "new_name.gpx")

        # Verify
        assert not source_path.exists()
        assert new_rel == "trail/2024/01/new_name.gpx"
        assert (temp_path / new_rel).exists()

    def test_rename_with_sidecar(self, temp_repo):
        """Test renaming file with sidecar."""
        repo, temp_path = temp_repo

        # Create media with sidecar
        source_path = temp_path / "media" / "old_photo.jpg"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text("image")

        sidecar = get_sidecar_path(source_path)
        sidecar.write_text('{"location": "test"}')

        source_rel = "media/old_photo.jpg"

        # Rename
        new_rel = repo.rename(source_rel, "new_photo.jpg")

        # Verify both renamed
        assert not source_path.exists()
        assert not sidecar.exists()

        new_path = temp_path / new_rel
        assert new_path.exists()
        assert get_sidecar_path(new_path).exists()

    def test_rename_preserves_extension(self, temp_repo):
        """Test that extension is preserved if not provided."""
        repo, temp_path = temp_repo

        # Create track
        source_path = temp_path / "trail" / "2024" / "01" / "track.gpx"
        create_test_gpx(source_path)

        # Rename without extension
        new_rel = repo.rename("trail/2024/01/track.gpx", "renamed_track")

        # Verify extension added
        assert new_rel == "trail/2024/01/renamed_track.gpx"
        assert (temp_path / new_rel).exists()

    def test_rename_source_not_found(self, temp_repo):
        """Test renaming non-existent file."""
        repo, _ = temp_repo

        with pytest.raises(FileNotFoundError):
            repo.rename("nonexistent/file.gpx", "new_name.gpx")

    def test_rename_invalid_filename(self, temp_repo):
        """Test renaming with invalid filename."""
        repo, temp_path = temp_repo

        # Create track
        source_path = temp_path / "trail" / "2024" / "01" / "track.gpx"
        create_test_gpx(source_path)

        # Try invalid filenames
        with pytest.raises(ValueError, match="Invalid filename"):
            repo.rename("trail/2024/01/track.gpx", "path/with/slash.gpx")

        with pytest.raises(ValueError, match="Invalid filename"):
            repo.rename("trail/2024/01/track.gpx", "")

"""Integration tests for drag & drop file management workflow.

These tests verify the complete workflow from frontend drag & drop
to backend file operations.
"""

import pytest
import pathlib
import tempfile
import shutil
from fastapi.testclient import TestClient

from ouffroad.__main__ import create_app
from ouffroad.config import (
    OuffroadConfig,
    RepositoryConfig,
    CategoryConfig,
    DateBasedPolicyConfig,
    FlatPolicyConfig,
)
from ouffroad.core.file_operations import get_sidecar_path


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
      <trkpt lat="40.7128" lon="-74.0060"><ele>10</ele><time>2024-01-15T10:00:00Z</time></trkpt>
      <trkpt lat="40.7138" lon="-74.0050"><ele>12</ele><time>2024-01-15T10:01:00Z</time></trkpt>
    </trkseg>
  </trk>
</gpx>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(gpx_content)


@pytest.fixture
def drag_drop_env():
    """Create environment for drag & drop testing."""
    temp_path = pathlib.Path(tempfile.mkdtemp())

    config = OuffroadConfig(
        repository_path=temp_path,
        repository_config=RepositoryConfig(
            categories={
                "trail": CategoryConfig(
                    name="Trail",
                    type="track",
                    extensions=[".gpx"],
                    storage_policy=DateBasedPolicyConfig(),
                    color="gold",
                ),
                "enduro": CategoryConfig(
                    name="Enduro",
                    type="track",
                    extensions=[".gpx"],
                    storage_policy=DateBasedPolicyConfig(),
                    color="red",
                ),
                "special_events": CategoryConfig(
                    name="Special Events",
                    type="track",
                    extensions=[".gpx"],
                    storage_policy=FlatPolicyConfig(),
                    color="purple",
                ),
            }
        ),
    )

    app = create_app(config)
    client = TestClient(app)

    yield client, temp_path, config

    if temp_path.exists():
        shutil.rmtree(temp_path)


class TestDragDropWorkflow:
    """Integration tests for drag & drop workflow."""

    def test_drag_drop_between_categories_with_date_policy(self, drag_drop_env):
        """Test dragging file between categories that use DateBasedPolicy."""
        client, temp_path, config = drag_drop_env

        # 1. Create file in trail category
        source_path = temp_path / "trail" / "2024" / "01" / "morning_ride.gpx"
        create_test_gpx(source_path, "Morning Ride")

        assert source_path.exists()

        # 2. Simulate drag & drop: move to enduro category
        response = client.patch(
            "/api/file/trail/2024/01/morning_ride.gpx",
            json={"target_category": "enduro"},
        )

        assert response.status_code == 200
        data = response.json()

        # 3. Verify response
        assert data["success"] is True
        assert data["old_path"] == "trail/2024/01/morning_ride.gpx"
        assert "enduro" in data["new_path"]
        assert "2024/01" in data["new_path"]  # DateBasedPolicy preserves date

        # 4. Verify file moved in filesystem
        assert not source_path.exists()
        new_path = temp_path / data["new_path"]
        assert new_path.exists()

        # 5. Verify content preserved
        content = new_path.read_text()
        assert "Morning Ride" in content

    def test_drag_drop_to_flat_policy_category(self, drag_drop_env):
        """Test dragging file to category with FlatPolicy."""
        client, temp_path, config = drag_drop_env

        # 1. Create file in trail (DateBasedPolicy)
        source_path = temp_path / "trail" / "2024" / "01" / "track.gpx"
        create_test_gpx(source_path)

        # 2. Move to special_events (FlatPolicy)
        response = client.patch(
            "/api/file/trail/2024/01/track.gpx",
            json={"target_category": "special_events"},
        )

        assert response.status_code == 200
        data = response.json()

        # 3. Verify FlatPolicy applied (no date folders)
        assert data["new_path"] == "special_events/track.gpx"
        assert (temp_path / "special_events" / "track.gpx").exists()

    def test_drag_drop_to_specific_folder(self, drag_drop_env):
        """Test dragging file to specific folder."""
        client, temp_path, config = drag_drop_env

        # 1. Create file
        source_path = temp_path / "trail" / "2024" / "01" / "track.gpx"
        create_test_gpx(source_path)

        # 2. Drag to specific folder in enduro
        response = client.patch(
            "/api/file/trail/2024/01/track.gpx",
            json={"target_category": "enduro", "target_folder": "2024/02"},
        )

        assert response.status_code == 200
        data = response.json()

        # 3. Verify exact folder
        assert data["new_path"] == "enduro/2024/02/track.gpx"
        assert (temp_path / "enduro" / "2024" / "02" / "track.gpx").exists()

    def test_drag_drop_with_sidecar(self, drag_drop_env):
        """Test that sidecar moves with file during drag & drop."""
        client, temp_path, config = drag_drop_env

        # 1. Create file with sidecar
        source_path = temp_path / "trail" / "2024" / "01" / "track.gpx"
        create_test_gpx(source_path)

        sidecar_path = get_sidecar_path(source_path)
        sidecar_path.write_text('{"notes": "Important track"}')

        assert source_path.exists()
        assert sidecar_path.exists()

        # 2. Drag & drop
        response = client.patch(
            "/api/file/trail/2024/01/track.gpx",
            json={"target_category": "enduro"},
        )

        assert response.status_code == 200
        new_path = temp_path / response.json()["new_path"]

        # 3. Verify both moved
        assert not source_path.exists()
        assert not sidecar_path.exists()

        assert new_path.exists()
        new_sidecar = get_sidecar_path(new_path)
        assert new_sidecar.exists()
        assert "Important track" in new_sidecar.read_text()

    def test_drag_drop_error_invalid_category(self, drag_drop_env):
        """Test error handling when dropping on invalid category."""
        client, temp_path, config = drag_drop_env

        # 1. Create file
        source_path = temp_path / "trail" / "2024" / "01" / "track.gpx"
        create_test_gpx(source_path)

        # 2. Try to drop on invalid category
        response = client.patch(
            "/api/file/trail/2024/01/track.gpx",
            json={"target_category": "invalid_category"},
        )

        # 3. Verify error
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

        # 4. Verify file not moved
        assert source_path.exists()

    def test_drag_drop_error_file_not_found(self, drag_drop_env):
        """Test error when trying to drag non-existent file."""
        client, temp_path, config = drag_drop_env

        # Try to move non-existent file
        response = client.patch(
            "/api/file/trail/2024/01/nonexistent.gpx",
            json={"target_category": "enduro"},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_drag_drop_error_target_exists(self, drag_drop_env):
        """Test error when target file already exists."""
        client, temp_path, config = drag_drop_env

        # 1. Create source file
        source_path = temp_path / "trail" / "2024" / "01" / "track.gpx"
        create_test_gpx(source_path, "Source")

        # 2. Create file with same name in target
        target_path = temp_path / "enduro" / "2024" / "01" / "track.gpx"
        create_test_gpx(target_path, "Target")

        # 3. Try to drag & drop
        response = client.patch(
            "/api/file/trail/2024/01/track.gpx",
            json={"target_category": "enduro"},
        )

        # 4. Verify error
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

        # 5. Verify both files still exist
        assert source_path.exists()
        assert target_path.exists()
        assert "Source" in source_path.read_text()
        assert "Target" in target_path.read_text()

    def test_drag_drop_multiple_files_sequentially(self, drag_drop_env):
        """Test dragging multiple files one after another."""
        client, temp_path, config = drag_drop_env

        # 1. Create multiple files
        files = []
        for i in range(3):
            file_path = temp_path / "trail" / "2024" / "01" / f"track{i}.gpx"
            create_test_gpx(file_path, f"Track {i}")
            files.append(file_path)

        # 2. Move each file
        for i, file_path in enumerate(files):
            response = client.patch(
                f"/api/file/trail/2024/01/track{i}.gpx",
                json={"target_category": "enduro"},
            )

            assert response.status_code == 200
            assert not file_path.exists()

        # 3. Verify all moved
        enduro_files = list((temp_path / "enduro" / "2024" / "01").glob("*.gpx"))
        assert len(enduro_files) == 3

    def test_drag_drop_preserves_file_content(self, drag_drop_env):
        """Test that file content is preserved during drag & drop."""
        client, temp_path, config = drag_drop_env

        # 1. Create file with specific content
        source_path = temp_path / "trail" / "2024" / "01" / "detailed_track.gpx"
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test">
  <metadata>
    <time>2024-01-15T10:00:00Z</time>
    <name>Detailed Track</name>
    <desc>This is a very detailed track with lots of data</desc>
  </metadata>
  <trk>
    <name>Test Track</name>
    <trkseg>
      <trkpt lat="40.7128" lon="-74.0060"><ele>10</ele><time>2024-01-15T10:00:00Z</time></trkpt>
      <trkpt lat="40.7138" lon="-74.0050"><ele>12</ele><time>2024-01-15T10:01:00Z</time></trkpt>
      <trkpt lat="40.7148" lon="-74.0040"><ele>15</ele><time>2024-01-15T10:02:00Z</time></trkpt>
    </trkseg>
  </trk>
</gpx>"""
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(gpx_content)

        # 2. Drag & drop
        response = client.patch(
            "/api/file/trail/2024/01/detailed_track.gpx",
            json={"target_category": "enduro"},
        )

        assert response.status_code == 200
        new_path = temp_path / response.json()["new_path"]

        # 3. Verify content exactly matches
        assert new_path.read_text() == gpx_content

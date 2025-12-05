"""End-to-end integration tests for file operations.

These tests verify the complete backend stack:
- HTTP endpoint -> API layer -> Repository -> File system
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
def integration_env():
    """Create a complete integration test environment."""
    temp_path = pathlib.Path(tempfile.mkdtemp())

    # Create test config with multiple categories
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
                "media": CategoryConfig(
                    name="Media",
                    type="media",
                    extensions=[".jpg", ".png", ".mp4"],
                    storage_policy=FlatPolicyConfig(),
                ),
            }
        ),
    )

    # Create app with test client
    app = create_app(config)
    client = TestClient(app)

    yield client, temp_path, config

    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


class TestEndToEndFileOperations:
    """End-to-end integration tests for file operations."""

    def test_complete_move_workflow(self, integration_env):
        """Test complete workflow: create file -> move -> verify."""
        client, temp_path, config = integration_env

        # 1. Create a file in trail category
        source_path = temp_path / "trail" / "2024" / "01" / "morning_ride.gpx"
        create_test_gpx(source_path, "Morning Ride")

        # Verify file exists in file system
        assert source_path.exists()

        # 2. Move file to enduro category via API
        response = client.patch(
            "/api/file/trail/2024/01/morning_ride.gpx",
            json={"target_category": "enduro"},
        )

        assert response.status_code == 200
        data = response.json()
        new_path = data["new_path"]

        # 3. Verify file moved in file system
        assert not source_path.exists()
        assert (temp_path / new_path).exists()
        assert "enduro" in new_path

        # 4. Verify content preserved
        content = (temp_path / new_path).read_text()
        assert "Morning Ride" in content

    def test_move_with_sidecar_integration(self, integration_env):
        """Test that sidecars are moved along with files."""
        client, temp_path, config = integration_env

        # 1. Create file with sidecar
        source_path = temp_path / "trail" / "2024" / "01" / "track.gpx"
        create_test_gpx(source_path)

        sidecar_path = get_sidecar_path(source_path)
        sidecar_path.write_text('{"custom_data": "important metadata"}')

        # Verify both exist
        assert source_path.exists()
        assert sidecar_path.exists()

        # 2. Move via API
        response = client.patch(
            "/api/file/trail/2024/01/track.gpx", json={"target_category": "enduro"}
        )

        assert response.status_code == 200
        new_path = response.json()["new_path"]

        # 3. Verify both moved
        assert not source_path.exists()
        assert not sidecar_path.exists()

        new_file_path = temp_path / new_path
        new_sidecar_path = get_sidecar_path(new_file_path)

        assert new_file_path.exists()
        assert new_sidecar_path.exists()
        assert "important metadata" in new_sidecar_path.read_text()

    def test_rename_integration(self, integration_env):
        """Test complete rename workflow."""
        client, temp_path, config = integration_env

        # 1. Create file
        source_path = temp_path / "trail" / "2024" / "01" / "old_name.gpx"
        create_test_gpx(source_path, "Old Name")

        # 2. Rename via API
        response = client.patch(
            "/api/file/trail/2024/01/old_name.gpx",
            json={"new_filename": "new_name.gpx"},
        )

        assert response.status_code == 200
        new_path = response.json()["new_path"]

        # 3. Verify file renamed in file system
        assert not source_path.exists()
        assert (temp_path / new_path).exists()
        assert new_path == "trail/2024/01/new_name.gpx"

        # 4. Verify content preserved
        content = (temp_path / new_path).read_text()
        assert "Old Name" in content

    def test_move_and_rename_integration(self, integration_env):
        """Test combined move and rename operation."""
        client, temp_path, config = integration_env

        # 1. Create file
        source_path = temp_path / "trail" / "2024" / "01" / "temp_track.gpx"
        create_test_gpx(source_path)

        # 2. Move and rename in one operation
        response = client.patch(
            "/api/file/trail/2024/01/temp_track.gpx",
            json={
                "target_category": "special_events",
                "new_filename": "marathon_2024.gpx",
            },
        )

        assert response.status_code == 200
        new_path = response.json()["new_path"]

        # 3. Verify in file system
        assert not source_path.exists()
        assert (temp_path / new_path).exists()

        # special_events uses FlatPolicy, so no date folders
        assert "special_events/marathon_2024.gpx" == new_path

    def test_storage_policy_respected(self, integration_env):
        """Test that storage policies are respected when moving."""
        client, temp_path, config = integration_env

        # 1. Create file in trail (DateBasedPolicy)
        source_path = temp_path / "trail" / "2024" / "01" / "track.gpx"
        create_test_gpx(source_path)

        # 2. Move to special_events (FlatPolicy)
        response = client.patch(
            "/api/file/trail/2024/01/track.gpx",
            json={"target_category": "special_events"},
        )

        assert response.status_code == 200
        new_path = response.json()["new_path"]

        # 3. Verify FlatPolicy applied (no date folders)
        assert new_path == "special_events/track.gpx"
        assert (temp_path / new_path).exists()

    def test_error_handling_integration(self, integration_env):
        """Test error handling across the stack."""
        client, temp_path, config = integration_env

        # 1. Try to move non-existent file
        response = client.patch(
            "/api/file/nonexistent/file.gpx", json={"target_category": "enduro"}
        )
        assert response.status_code == 404

        # 2. Create file and try invalid category
        source_path = temp_path / "trail" / "2024" / "01" / "track.gpx"
        create_test_gpx(source_path)

        response = client.patch(
            "/api/file/trail/2024/01/track.gpx",
            json={"target_category": "invalid_category"},
        )
        assert response.status_code == 400

        # Verify file not moved
        assert source_path.exists()

    def test_concurrent_operations_safety(self, integration_env):
        """Test that operations are safe (no partial states)."""
        client, temp_path, config = integration_env

        # 1. Create file
        source_path = temp_path / "trail" / "2024" / "01" / "track.gpx"
        create_test_gpx(source_path)

        # 2. Try to move to location that would fail
        # (e.g., invalid category - should rollback)
        response = client.patch(
            "/api/file/trail/2024/01/track.gpx", json={"target_category": "invalid"}
        )

        assert response.status_code == 400

        # 3. Verify original file still exists (no partial move)
        assert source_path.exists()

        # 4. Now do valid move
        response = client.patch(
            "/api/file/trail/2024/01/track.gpx", json={"target_category": "enduro"}
        )

        assert response.status_code == 200
        assert not source_path.exists()

    def test_file_operations_consistency(self, integration_env):
        """Test that file operations maintain consistency."""
        client, temp_path, config = integration_env

        # 1. Create multiple files
        files_to_create = [
            "trail/2024/01/track1.gpx",
            "trail/2024/01/track2.gpx",
            "enduro/2024/01/track3.gpx",
        ]

        for file_path in files_to_create:
            full_path = temp_path / file_path
            create_test_gpx(full_path)

        # 2. Verify all files exist
        for file_path in files_to_create:
            assert (temp_path / file_path).exists()

        # 3. Move one file
        response = client.patch(
            "/api/file/trail/2024/01/track1.gpx", json={"target_category": "enduro"}
        )
        new_path = response.json()["new_path"]

        # 4. Verify old path gone, new path present
        assert not (temp_path / "trail/2024/01/track1.gpx").exists()
        assert (temp_path / new_path).exists()

        # 5. Verify other files unchanged
        assert (temp_path / "trail/2024/01/track2.gpx").exists()
        assert (temp_path / "enduro/2024/01/track3.gpx").exists()

"""API tests for file operations endpoint."""

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
)


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


@pytest.fixture
def test_app():
    """Create a test FastAPI app with temporary repository."""
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
            }
        ),
    )

    # Create app
    app = create_app(config)
    client = TestClient(app)

    yield client, temp_path

    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


class TestFileUpdateEndpoint:
    """Tests for PATCH /api/file/{filepath} endpoint."""

    def test_move_file_to_category(self, test_app):
        """Test moving a file to a different category."""
        client, temp_path = test_app

        # Create a test file
        source_path = temp_path / "trail" / "2024" / "01" / "test.gpx"
        create_test_gpx(source_path)

        # Move file
        response = client.patch(
            "/api/file/trail/2024/01/test.gpx", json={"target_category": "enduro"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["old_path"] == "trail/2024/01/test.gpx"
        assert "enduro" in data["new_path"]
        assert "moved to enduro" in data["message"]

    def test_move_file_to_specific_folder(self, test_app):
        """Test moving a file to a specific folder."""
        client, temp_path = test_app

        # Create a test file
        source_path = temp_path / "trail" / "2024" / "01" / "test.gpx"
        create_test_gpx(source_path)

        # Move file to specific folder
        response = client.patch(
            "/api/file/trail/2024/01/test.gpx",
            json={"target_category": "enduro", "target_folder": "2024/02"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["new_path"] == "enduro/2024/02/test.gpx"

    def test_rename_file(self, test_app):
        """Test renaming a file."""
        client, temp_path = test_app

        # Create a test file
        source_path = temp_path / "trail" / "2024" / "01" / "old_name.gpx"
        create_test_gpx(source_path)

        # Rename file
        response = client.patch(
            "/api/file/trail/2024/01/old_name.gpx",
            json={"new_filename": "new_name.gpx"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["new_path"] == "trail/2024/01/new_name.gpx"
        assert "renamed to new_name.gpx" in data["message"]

    def test_move_and_rename(self, test_app):
        """Test moving and renaming in one operation."""
        client, temp_path = test_app

        # Create a test file
        source_path = temp_path / "trail" / "2024" / "01" / "old.gpx"
        create_test_gpx(source_path)

        # Move and rename
        response = client.patch(
            "/api/file/trail/2024/01/old.gpx",
            json={"target_category": "enduro", "new_filename": "new.gpx"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "enduro" in data["new_path"]
        assert "new.gpx" in data["new_path"]
        assert "moved" in data["message"]
        assert "renamed" in data["message"]

    def test_file_not_found(self, test_app):
        """Test error when file doesn't exist."""
        client, _ = test_app

        response = client.patch(
            "/api/file/nonexistent/file.gpx", json={"target_category": "enduro"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_invalid_category(self, test_app):
        """Test error when target category is invalid."""
        client, temp_path = test_app

        # Create a test file
        source_path = temp_path / "trail" / "2024" / "01" / "test.gpx"
        create_test_gpx(source_path)

        response = client.patch(
            "/api/file/trail/2024/01/test.gpx",
            json={"target_category": "invalid_category"},
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_no_operations_specified(self, test_app):
        """Test error when no update operations are specified."""
        client, temp_path = test_app

        # Create a test file
        source_path = temp_path / "trail" / "2024" / "01" / "test.gpx"
        create_test_gpx(source_path)

        response = client.patch("/api/file/trail/2024/01/test.gpx", json={})

        assert response.status_code == 400
        assert "no update operations" in response.json()["detail"].lower()

    def test_invalid_filename(self, test_app):
        """Test error when filename is invalid."""
        client, temp_path = test_app

        # Create a test file
        source_path = temp_path / "trail" / "2024" / "01" / "test.gpx"
        create_test_gpx(source_path)

        response = client.patch(
            "/api/file/trail/2024/01/test.gpx",
            json={"new_filename": "path/with/slash.gpx"},
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

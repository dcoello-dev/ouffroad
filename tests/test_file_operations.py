"""Tests for file operation utilities."""

import pytest
import pathlib
import tempfile
import shutil
from ouffroad.core.file_operations import (
    move_file_with_sidecar,
    rename_file_with_sidecar,
    copy_file_with_sidecar,
    get_sidecar_path,
    FileOperationError,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = pathlib.Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


class TestGetSidecarPath:
    """Tests for get_sidecar_path function."""

    def test_get_sidecar_path(self):
        """Test sidecar path generation."""
        file_path = pathlib.Path("/path/to/file.jpg")
        sidecar = get_sidecar_path(file_path)
        assert sidecar == pathlib.Path("/path/to/file.jpg.json")

    def test_get_sidecar_path_with_extension(self):
        """Test sidecar path for file with multiple extensions."""
        file_path = pathlib.Path("/path/to/archive.tar.gz")
        sidecar = get_sidecar_path(file_path)
        assert sidecar == pathlib.Path("/path/to/archive.tar.gz.json")


class TestMoveFileWithSidecar:
    """Tests for move_file_with_sidecar function."""

    def test_move_file_without_sidecar(self, temp_dir):
        """Test moving a file without sidecar."""
        # Create source file
        source = temp_dir / "source.txt"
        source.write_text("test content")

        # Move file
        target = temp_dir / "subdir" / "target.txt"
        move_file_with_sidecar(source, target)

        # Verify
        assert not source.exists()
        assert target.exists()
        assert target.read_text() == "test content"

    def test_move_file_with_sidecar(self, temp_dir):
        """Test moving a file with sidecar."""
        # Create source file and sidecar
        source = temp_dir / "photo.jpg"
        source.write_text("image data")
        source_sidecar = get_sidecar_path(source)
        source_sidecar.write_text('{"latitude": 40.7, "longitude": -74.0}')

        # Move file
        target = temp_dir / "moved" / "photo.jpg"
        move_file_with_sidecar(source, target)

        # Verify both moved
        assert not source.exists()
        assert not source_sidecar.exists()
        assert target.exists()
        assert get_sidecar_path(target).exists()
        assert target.read_text() == "image data"
        assert '{"latitude": 40.7' in get_sidecar_path(target).read_text()

    def test_move_file_source_not_exists(self, temp_dir):
        """Test moving a file that doesn't exist."""
        source = temp_dir / "nonexistent.txt"
        target = temp_dir / "target.txt"

        with pytest.raises(FileNotFoundError):
            move_file_with_sidecar(source, target)

    def test_move_file_target_exists(self, temp_dir):
        """Test moving to a target that already exists."""
        source = temp_dir / "source.txt"
        source.write_text("source")
        target = temp_dir / "target.txt"
        target.write_text("target")

        with pytest.raises(FileOperationError, match="already exists"):
            move_file_with_sidecar(source, target)

    def test_move_file_rollback_on_sidecar_failure(self, temp_dir, monkeypatch):
        """Test rollback when sidecar move fails."""
        # Create source file and sidecar
        source = temp_dir / "file.txt"
        source.write_text("content")
        source_sidecar = get_sidecar_path(source)
        source_sidecar.write_text("sidecar")

        target = temp_dir / "moved" / "file.txt"

        # Mock shutil.move to fail on second call (sidecar)
        original_move = shutil.move
        call_count = [0]

        def mock_move(src, dst):
            call_count[0] += 1
            if call_count[0] == 2:  # Second call (sidecar)
                raise IOError("Simulated sidecar move failure")
            return original_move(src, dst)

        monkeypatch.setattr(shutil, "move", mock_move)

        # Attempt move
        with pytest.raises(FileOperationError, match="Failed to move sidecar"):
            move_file_with_sidecar(source, target)

        # Verify rollback: source file should still exist
        assert source.exists()
        assert source_sidecar.exists()
        assert not target.exists()


class TestRenameFileWithSidecar:
    """Tests for rename_file_with_sidecar function."""

    def test_rename_file_without_sidecar(self, temp_dir):
        """Test renaming a file without sidecar."""
        # Create file
        original = temp_dir / "old_name.txt"
        original.write_text("content")

        # Rename
        new_path = rename_file_with_sidecar(original, "new_name.txt")

        # Verify
        assert not original.exists()
        assert new_path.exists()
        assert new_path.name == "new_name.txt"
        assert new_path.read_text() == "content"

    def test_rename_file_with_sidecar(self, temp_dir):
        """Test renaming a file with sidecar."""
        # Create file and sidecar
        original = temp_dir / "video.mp4"
        original.write_text("video data")
        original_sidecar = get_sidecar_path(original)
        original_sidecar.write_text('{"location": "test"}')

        # Rename
        new_path = rename_file_with_sidecar(original, "renamed_video.mp4")

        # Verify both renamed
        assert not original.exists()
        assert not original_sidecar.exists()
        assert new_path.exists()
        assert get_sidecar_path(new_path).exists()
        assert new_path.name == "renamed_video.mp4"

    def test_rename_file_not_exists(self, temp_dir):
        """Test renaming a file that doesn't exist."""
        nonexistent = temp_dir / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            rename_file_with_sidecar(nonexistent, "new_name.txt")

    def test_rename_file_target_exists(self, temp_dir):
        """Test renaming to a name that already exists."""
        original = temp_dir / "file1.txt"
        original.write_text("file1")
        existing = temp_dir / "file2.txt"
        existing.write_text("file2")

        with pytest.raises(FileOperationError, match="already exists"):
            rename_file_with_sidecar(original, "file2.txt")


class TestCopyFileWithSidecar:
    """Tests for copy_file_with_sidecar function."""

    def test_copy_file_without_sidecar(self, temp_dir):
        """Test copying a file without sidecar."""
        source = temp_dir / "source.txt"
        source.write_text("content")

        target = temp_dir / "copy" / "target.txt"
        copy_file_with_sidecar(source, target)

        # Verify both exist
        assert source.exists()
        assert target.exists()
        assert source.read_text() == target.read_text()

    def test_copy_file_with_sidecar(self, temp_dir):
        """Test copying a file with sidecar."""
        source = temp_dir / "photo.jpg"
        source.write_text("image")
        source_sidecar = get_sidecar_path(source)
        source_sidecar.write_text("metadata")

        target = temp_dir / "backup" / "photo.jpg"
        copy_file_with_sidecar(source, target)

        # Verify all exist
        assert source.exists()
        assert source_sidecar.exists()
        assert target.exists()
        assert get_sidecar_path(target).exists()

    def test_copy_file_cleanup_on_failure(self, temp_dir, monkeypatch):
        """Test cleanup when copy fails."""
        source = temp_dir / "file.txt"
        source.write_text("content")

        target = temp_dir / "copy" / "file.txt"

        # Mock shutil.copy2 to fail
        def mock_copy2(src, dst):
            raise IOError("Simulated copy failure")

        monkeypatch.setattr(shutil, "copy2", mock_copy2)

        with pytest.raises(FileOperationError):
            copy_file_with_sidecar(source, target)

        # Verify no partial files left
        assert not target.exists()

import pathlib
from typing import Sequence
from ouffroad.core.IFile import IFile
from .Photo import Photo
from .Video import Video


class MediaFactory:
    """Factory to create appropriate media objects based on file extension."""

    PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}
    VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv"}

    @staticmethod
    def create(
        file_path: pathlib.Path, content: bytes | None = None
    ) -> Sequence[IFile]:
        """
        Create media object(s) based on file extension.
        Returns a list to maintain consistency with TrackFactory.

        Args:
            file_path: Path to the media file
            content: Optional file content as bytes

        Returns:
            List containing a single IFile object, or empty list if unsupported
        """
        ext = file_path.suffix.lower()

        if ext in MediaFactory.PHOTO_EXTENSIONS:
            return [Photo(file_path, content)]
        elif ext in MediaFactory.VIDEO_EXTENSIONS:
            return [Video(file_path, content)]
        else:
            # Unsupported format
            return []

    @staticmethod
    def is_supported(file_path: pathlib.Path) -> bool:
        """Check if the file extension is supported."""
        ext = file_path.suffix.lower()
        return (
            ext in MediaFactory.PHOTO_EXTENSIONS or ext in MediaFactory.VIDEO_EXTENSIONS
        )

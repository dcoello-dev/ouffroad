import pathlib

from abc import ABC, abstractmethod
from typing import Sequence, Optional
from ouffroad.core.IFile import IFile


class ITrackRepository(ABC):
    """Abstract repository interface for file storage (tracks and media)."""

    @abstractmethod
    def save(self, file: IFile, category: str) -> pathlib.Path:
        """Saves a file and returns its relative path."""
        pass

    @abstractmethod
    def get(self, rel_path: str) -> Sequence[IFile]:
        """Retrieves file(s) by its relative path."""
        pass

    @abstractmethod
    def list_all(self) -> Sequence[str]:
        """Lists all files in the repository."""
        pass

    @abstractmethod
    def exists(self, rel_path: str) -> bool:
        """Checks if a file exists."""
        pass

    @abstractmethod
    def move(
        self,
        source_rel_path: str,
        target_category: str,
        target_folder: Optional[str] = None,
    ) -> str:
        """
        Move a file to a different category/folder.

        Args:
            source_rel_path: Current relative path of the file
            target_category: Target category name
            target_folder: Optional target folder (e.g., "2024/01")
                          If None, storage policy determines location

        Returns:
            New relative path after move

        Raises:
            FileNotFoundError: If source file doesn't exist
            ValueError: If target category is invalid
        """
        pass

    @abstractmethod
    def rename(self, source_rel_path: str, new_filename: str) -> str:
        """
        Rename a file.

        Args:
            source_rel_path: Current relative path of the file
            new_filename: New filename (without directory path)

        Returns:
            New relative path after rename

        Raises:
            FileNotFoundError: If source file doesn't exist
            ValueError: If new filename is invalid
        """
        pass

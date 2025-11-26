import pathlib

from abc import ABC, abstractmethod
from typing import Sequence
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

from abc import ABC, abstractmethod
import pathlib
from datetime import datetime
from typing import Optional


class IStoragePolicy(ABC):
    @abstractmethod
    def get_relative_path(
        self, category: str, date: Optional[datetime], filename: str
    ) -> pathlib.Path:
        """
        Determines the relative path for storing a file based on the policy.

        Args:
            category: The category of the file (e.g., 'trail', 'enduro').
            date: The date associated with the file (can be None).
            filename: The name of the file.

        Returns:
            A pathlib.Path object representing the relative path.
        """
        pass

import pathlib
from datetime import datetime
from typing import Optional
from .IStoragePolicy import IStoragePolicy


class FlatPolicy(IStoragePolicy):
    """
    Storage policy that organizes files by category only.
    Structure: category/filename
    """

    def get_relative_path(
        self, category: str, date: Optional[datetime], filename: str
    ) -> pathlib.Path:
        return pathlib.Path(category) / filename

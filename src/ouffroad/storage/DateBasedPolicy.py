import pathlib
from datetime import datetime
from typing import Optional
from .IStoragePolicy import IStoragePolicy


class DateBasedPolicy(IStoragePolicy):
    """
    Storage policy that organizes files by category, year, and month.
    Structure: category/YYYY/MM/filename
    """

    def get_relative_path(
        self, category: str, date: Optional[datetime], filename: str
    ) -> pathlib.Path:
        if not date:
            date = datetime.now()

        year = date.strftime("%Y")
        month = date.strftime("%m")

        return pathlib.Path(category) / year / month / filename

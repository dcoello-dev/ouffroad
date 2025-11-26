import pathlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any


class IFile(ABC):
    def __init__(self, format: str, path: pathlib.Path):
        self.format_ = format
        self.path_ = path
        self.parent_, self.name_, self.ext_ = self.decompose_path(path)

    def parent(self) -> str:
        return self.parent_

    def ext(self) -> str:
        return self.ext_

    def name(self) -> str:
        return self.name_

    def path(self) -> pathlib.Path:
        return self.path_

    def format(self) -> str:
        return self.format_

    @abstractmethod
    def load(self) -> bool:
        pass

    @abstractmethod
    def save(self) -> bool:
        pass

    @abstractmethod
    def date(self) -> datetime | None:
        """Extract date from the file's metadata or content."""
        pass

    @abstractmethod
    def geojson(self) -> Dict[str, Any]:
        """Return GeoJSON representation of the file."""
        pass

    @staticmethod
    def decompose_path(path: pathlib.Path) -> tuple:
        return path.parent.resolve(), path.name, path.suffix

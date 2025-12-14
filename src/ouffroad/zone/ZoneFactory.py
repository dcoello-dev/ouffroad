import pathlib
from typing import Sequence

from .Zone import Zone


class ZoneFactory:
    @staticmethod
    def create(path: pathlib.Path, content: bytes | None = None) -> Sequence[Zone]:
        """
        Creates Zone instances for .geojson files.
        """
        suffix = path.suffix.lower()

        if suffix == ".geojson":
            return [Zone(path, content)]

        return []

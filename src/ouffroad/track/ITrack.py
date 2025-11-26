import pathlib

from abc import ABC

from ouffroad.core.IFile import IFile


class ITrack(IFile, ABC):
    def __init__(self, format: str, path: pathlib.Path):
        super().__init__(format, path)

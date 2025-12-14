import pathlib
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from ouffroad.core.IFile import IFile

logger = logging.getLogger(__name__)


class Zone(IFile):
    def __init__(self, path: pathlib.Path, content: bytes | None = None):
        super().__init__("zone", path)
        self._content = content
        self._geojson: Optional[Dict[str, Any]] = None

    def load(self) -> bool:
        try:
            if self._content:
                data = self._content.decode("utf-8")
            else:
                with open(self.path_, "r", encoding="utf-8") as f:
                    data = f.read()

            self._geojson = json.loads(data)
            return True
        except Exception as e:
            logger.error(f"Failed to load zone {self.path_}: {e}")
            return False

    def save(self) -> bool:
        try:
            if self._geojson is None:
                return False

            with open(self.path_, "w", encoding="utf-8") as f:
                json.dump(self._geojson, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save zone {self.path_}: {e}")
            return False

    def date(self) -> datetime | None:
        # Zones are static definitions, use file modification time if available
        try:
            if self.path_.exists():
                return datetime.fromtimestamp(self.path_.stat().st_mtime)
        except Exception:
            pass
        return None

    def geojson(self) -> Dict[str, Any]:
        if self._geojson is None:
            self.load()
        return self._geojson or {}

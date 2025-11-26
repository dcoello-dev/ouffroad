import os
import pathlib
import logging
from typing import Sequence, Optional

from ouffroad.core.IFile import IFile
from ouffroad.storage.IStoragePolicy import IStoragePolicy
from ouffroad.storage.DateBasedPolicy import DateBasedPolicy
from ouffroad.storage.FlatPolicy import FlatPolicy
from ouffroad.storage.ConfigurablePolicy import ConfigurablePolicy
from ouffroad.config import OuffroadConfig, CategoryConfig, StoragePolicyType
from .ITrackRepository import ITrackRepository

logger = logging.getLogger(__name__)


class FileSystemRepository(ITrackRepository):
    def __init__(self, app_config: OuffroadConfig):
        self.app_config = app_config
        self.base_path = self.app_config.repository_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_absolute_path(self, rel_path: str) -> pathlib.Path:
        return self.base_path / rel_path

    def _get_storage_policy_instance(
        self, policy_config: StoragePolicyType
    ) -> IStoragePolicy:
        """Dynamically creates a concrete storage policy instance from its configuration."""
        if policy_config.name == "DateBasedPolicy":
            return DateBasedPolicy()
        elif policy_config.name == "FlatPolicy":
            return FlatPolicy()
        elif policy_config.name == "ConfigurablePolicy":
            # ConfigurablePolicy needs its config file path; for now, assume default
            return ConfigurablePolicy(
                self.app_config.repository_path / policy_config.config_file
            )
        else:
            raise ValueError(f"Unknown storage policy: {policy_config.name}")

    def save(self, file: IFile, category: str) -> pathlib.Path:
        # Get category configuration
        if not self.app_config.repository_config:
            raise ValueError("Repository configuration not loaded.")

        category_config: Optional[CategoryConfig] = (
            self.app_config.repository_config.categories.get(category)
        )
        if not category_config:
            # Default to DateBasedPolicy if category not explicitly defined in config
            current_policy = DateBasedPolicy()
        else:
            current_policy = self._get_storage_policy_instance(
                category_config.storage_policy
            )

        # We need the date to determine the folder structure (if policy uses it)
        date = file.date()
        if not date:
            file.load()
            date = file.date()

        filename = file.name()

        # Use policy to determine relative path
        rel_path = current_policy.get_relative_path(category, date, filename)

        # Construct target directory and ensure it exists
        target_path = self.base_path / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle duplicate filenames
        base_name = target_path.stem
        ext = target_path.suffix
        parent_dir = target_path.parent

        counter = 1
        while target_path.exists():
            target_path = parent_dir / f"{base_name}_{counter}{ext}"
            counter += 1

        # Update the file's path to the new target location
        file.path_ = target_path

        if file.save():
            return target_path.relative_to(self.base_path)
        else:
            raise IOError(f"Failed to save file to {target_path}")

    def get(self, rel_path: str) -> Sequence[IFile]:
        abs_path = self._get_absolute_path(rel_path)
        if not abs_path.exists():
            return []

        # Try TrackFactory first
        from ouffroad.track.TrackFactory import TrackFactory

        result: Sequence[IFile] = TrackFactory.create(abs_path)
        if result:
            return result

        # Try MediaFactory
        from ouffroad.media.MediaFactory import MediaFactory

        result = MediaFactory.create(abs_path)
        if result:
            return result

        # Unsupported format
        return []

    def list_all(self) -> Sequence[str]:
        files = []
        for root, _, filenames in os.walk(self.base_path):
            for file in filenames:
                # Include tracks and media, exclude sidecar JSON files
                # This needs to be dynamic based on category config
                # For now, keep as is
                if file.lower().endswith(
                    (
                        ".gpx",
                        ".fit",
                        ".kml",
                        ".kmz",
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".gif",
                        ".bmp",
                        ".mp4",
                        ".mov",
                        ".avi",
                        ".mkv",
                        ".webm",
                    )
                ):
                    # Create relative path
                    full_path = pathlib.Path(root) / file
                    rel_path = full_path.relative_to(self.base_path)
                    files.append(str(rel_path).replace(os.sep, "/"))
        return files

    def exists(self, rel_path: str) -> bool:
        return self._get_absolute_path(rel_path).exists()

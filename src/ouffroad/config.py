import pathlib
import toml
import logging
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

# --- Storage Policy Configuration Models ---


class DateBasedPolicyConfig(BaseModel):
    name: Literal["DateBasedPolicy"] = "DateBasedPolicy"
    # No additional fields for DateBasedPolicy


class FlatPolicyConfig(BaseModel):
    name: Literal["FlatPolicy"] = "FlatPolicy"
    # No additional fields for FlatPolicy


class ConfigurablePolicyConfig(BaseModel):
    name: Literal["ConfigurablePolicy"] = "ConfigurablePolicy"
    config_file: str = "storage.toml"  # Default, can be overridden if needed


# Union type for all possible Storage Policy configurations
StoragePolicyType = DateBasedPolicyConfig | FlatPolicyConfig | ConfigurablePolicyConfig

# --- Category Configuration Model ---


class CategoryConfig(BaseModel):
    name: str
    type: Literal["track", "media"]
    extensions: List[str] = Field(
        default_factory=list
    )  # e.g., [".gpx", ".fit"] or [".jpg", ".mp4"]
    storage_policy: StoragePolicyType = Field(default_factory=DateBasedPolicyConfig)


# --- Repository Configuration Model ---


class RepositoryConfig(BaseModel):
    categories: Dict[str, CategoryConfig] = Field(default_factory=dict)


# --- Main Application Configuration Model ---


class OuffroadConfig(BaseModel):
    """
    Main application configuration, loaded from various sources.
    """

    repository_path: pathlib.Path = Field(
        ..., description="Path to the root of the data repository (e.g., 'uploads/')"
    )
    # The actual config loaded from repository_path/storage.toml
    repository_config: Optional[RepositoryConfig] = None

    # Other potential global settings could go here
    # host: str = "0.0.0.0"
    # port: int = 8000

    def load_repository_config(self):
        """
        Loads the repository-specific configuration (e.g., storage.toml)
        from the repository_path.
        """
        config_file_path = self.repository_path / "storage.toml"
        if config_file_path.exists():
            try:
                with open(config_file_path, "r") as f:
                    repo_toml_config = toml.load(f)
                self.repository_config = RepositoryConfig.model_validate(
                    repo_toml_config
                )
            except ValidationError as e:
                raise ValueError(
                    f"Error validating repository config in {config_file_path}: {e}"
                )
            except Exception as e:
                raise ValueError(
                    f"Error loading repository config from {config_file_path}: {e}"
                )
        else:
            # If no config file exists, use default configuration matching original frontend
            logger.warning(
                f"No repository config file found at {config_file_path}. Using default configuration."
            )
            self.repository_config = RepositoryConfig(
                categories={
                    "tracks": CategoryConfig(
                        name="tracks", type="track", extensions=[".gpx", ".fit", ".kml"]
                    ),
                    "media": CategoryConfig(
                        name="media",
                        type="media",
                        extensions=[".jpg", ".jpeg", ".png", ".mp4", ".mov"],
                    ),
                }
            )

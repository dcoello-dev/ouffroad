import pathlib
import tomllib
from datetime import datetime
from typing import Optional, Dict, Type
from .IStoragePolicy import IStoragePolicy
from .DateBasedPolicy import DateBasedPolicy
from .FlatPolicy import FlatPolicy


class ConfigurablePolicy(IStoragePolicy):
    """
    Storage policy that routes to other policies based on a TOML configuration file.
    """

    def __init__(self, config_path: pathlib.Path):
        self.config_path = config_path
        self.policies: Dict[str, IStoragePolicy] = {}
        self.default_policy = DateBasedPolicy()
        self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            # If config doesn't exist, we'll just use default for everything
            return

        with open(self.config_path, "rb") as f:
            config = tomllib.load(f)

        policy_map: Dict[str, Type[IStoragePolicy]] = {
            "date_based": DateBasedPolicy,
            "flat": FlatPolicy,
        }

        # Parse config: [category] -> policy_name
        # Example TOML:
        # [policies]
        # trail = "date_based"
        # media = "flat"

        sections = config.get("policies", {})
        for category, policy_name in sections.items():
            policy_class = policy_map.get(policy_name)
            if policy_class:
                self.policies[category] = policy_class()

    def get_relative_path(
        self, category: str, date: Optional[datetime], filename: str
    ) -> pathlib.Path:
        policy = self.policies.get(category, self.default_policy)
        return policy.get_relative_path(category, date, filename)

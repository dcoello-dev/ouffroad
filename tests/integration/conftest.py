import pytest
import toml
from fastapi.testclient import TestClient
from ouffroad.__main__ import create_app
from ouffroad.config import OuffroadConfig


@pytest.fixture
def temp_repo(tmp_path):
    """Creates a temporary repository directory structure."""
    repo_dir = tmp_path / "ouffroad_repo"
    repo_dir.mkdir()
    return repo_dir


@pytest.fixture
def test_config(temp_repo):
    """Creates a test configuration and writes it to the temp repo."""
    config_data = {
        "categories": {
            "tracks": {
                "name": "tracks",
                "type": "track",
                "extensions": [".gpx", ".fit", ".kml", ".kmz"],
                "storage_policy": {"name": "DateBasedPolicy"},
            },
            "media": {
                "name": "media",
                "type": "media",
                "extensions": [".jpg", ".jpeg", ".png", ".mp4", ".mov"],
                "storage_policy": {"name": "DateBasedPolicy"},
            },
            "misc": {
                "name": "misc",
                "type": "track",
                "extensions": [],
                "storage_policy": {"name": "FlatPolicy"},
            },
        }
    }

    config_file = temp_repo / "storage.toml"
    with open(config_file, "w") as f:
        toml.dump(config_data, f)

    config = OuffroadConfig(repository_path=temp_repo)
    config.load_repository_config()
    return config


@pytest.fixture
def client(test_config):
    """
    Returns a TestClient with the app configured to use the temp repo.
    """
    # Create app with test config
    app = create_app(test_config)

    # We don't need to override get_config because create_app sets app.state.config
    # and get_app_config reads from it.
    # However, get_config in api.py might be different from get_app_config.
    # Let's check api.py again.

    # In api.py:
    # def get_app_config(request: Request) -> OuffroadConfig:
    #     return request.app.state.config

    # So passing config to create_app should be enough.

    yield TestClient(app)

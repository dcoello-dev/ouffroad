import pytest
import pathlib
from ouffroad.storage.ConfigurablePolicy import ConfigurablePolicy
from ouffroad.storage.DateBasedPolicy import DateBasedPolicy
from ouffroad.storage.FlatPolicy import FlatPolicy


@pytest.fixture
def mock_config_content():
    return b"""
    [policies]
    trail = "date_based"
    media = "flat"
    """


def test_configurable_policy_loads_config(tmp_path, mock_config_content):
    config_path = tmp_path / "storage.toml"
    with open(config_path, "wb") as f:
        f.write(mock_config_content)

    policy = ConfigurablePolicy(config_path)

    assert "trail" in policy.policies
    assert isinstance(policy.policies["trail"], DateBasedPolicy)
    assert "media" in policy.policies
    assert isinstance(policy.policies["media"], FlatPolicy)


def test_configurable_policy_default_behavior(tmp_path):
    # No config file
    config_path = tmp_path / "nonexistent.toml"
    policy = ConfigurablePolicy(config_path)

    # Should default to DateBasedPolicy for unknown categories
    rel_path = policy.get_relative_path("unknown", None, "test.gpx")
    # DateBasedPolicy uses year/month
    assert len(rel_path.parts) > 2


def test_configurable_policy_routing(tmp_path, mock_config_content):
    config_path = tmp_path / "storage.toml"
    with open(config_path, "wb") as f:
        f.write(mock_config_content)

    policy = ConfigurablePolicy(config_path)

    # Test DateBased routing
    date_path = policy.get_relative_path("trail", None, "test.gpx")
    assert len(date_path.parts) > 2  # category/year/month/file

    # Test Flat routing
    flat_path = policy.get_relative_path("media", None, "image.jpg")
    assert len(flat_path.parts) == 2  # category/file
    assert flat_path == pathlib.Path("media/image.jpg")

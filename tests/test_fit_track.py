import pytest
import pathlib
from datetime import datetime
from unittest.mock import patch
from io import BytesIO  # Added import

from ouffroad.track.FITTrack import FITTrack


# Mocking fitparse data structures
class MockFitData:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class MockFitRecord:
    def __init__(self, data_list):
        self.data = data_list

    def __iter__(self):
        return iter(self.data)


@pytest.fixture
def mock_fit_file():
    with patch("ouffroad.track.FITTrack.FitFile") as MockFitFile:
        mock_instance = MockFitFile.return_value
        yield mock_instance


def test_fit_load(mock_fit_file):
    path = pathlib.Path("test.fit")
    track = FITTrack(path)

    assert track.load() is True
    mock_fit_file.parse.assert_called_once()


def test_fit_date_from_file_id(mock_fit_file):
    expected_date = datetime(2023, 5, 20, 10, 0, 0)

    mock_fit_file.get_messages.side_effect = lambda msg_type: (
        [MockFitRecord([MockFitData("time_created", expected_date)])]
        if msg_type == "file_id"
        else []
    )

    path = pathlib.Path("test.fit")
    track = FITTrack(path)
    track.load()

    assert track.date() == expected_date


def test_fit_date_from_record_timestamp(mock_fit_file):
    expected_date = datetime(2023, 6, 15, 14, 30, 0)

    def get_messages_side_effect(msg_type):
        if msg_type == "file_id":
            return []
        if msg_type == "record":
            return [MockFitRecord([MockFitData("timestamp", expected_date)])]
        return []

    mock_fit_file.get_messages.side_effect = get_messages_side_effect

    path = pathlib.Path("test.fit")
    track = FITTrack(path)
    track.load()

    assert track.date() == expected_date


def test_fit_geojson_generation(mock_fit_file):
    semicircle_const = 2**31 / 180
    lat_deg = 40.0
    lon_deg = -3.0
    alt = 100.0

    lat_semi = int(lat_deg * semicircle_const)
    lon_semi = int(lon_deg * semicircle_const)

    mock_record = MockFitRecord(
        [
            MockFitData("position_lat", lat_semi),
            MockFitData("position_long", lon_semi),
            MockFitData("altitude", alt),
        ]
    )

    mock_fit_file.get_messages.return_value = [mock_record]

    path = pathlib.Path("test.fit")
    track = FITTrack(path)
    track.load()

    geojson = track.geojson()

    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 1

    coords = geojson["features"][0]["geometry"]["coordinates"]
    assert len(coords) == 1

    assert abs(coords[0][0] - lon_deg) < 0.000001
    assert abs(coords[0][1] - lat_deg) < 0.000001
    assert coords[0][2] == alt


def test_fit_save_content(tmp_path, mock_fit_file):
    # Test saving raw bytes
    save_path = tmp_path / "saved_track.fit"
    dummy_content = BytesIO(b"dummy_fit_content")  # Corrected to BytesIO

    track = FITTrack(save_path, dummy_content)
    # Mock load to avoid parse error on dummy content
    track.load()

    assert track.save() is True
    assert save_path.exists()

    with open(save_path, "rb") as f:
        assert f.read() == dummy_content.getvalue()

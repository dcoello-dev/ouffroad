import pytest
import pathlib

from ouffroad.track.GPXTrack import GPXTrack

# Sample GPX content for testing
SAMPLE_GPX = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="TestCreator">
  <metadata>
    <time>2023-10-27T10:00:00Z</time>
  </metadata>
  <trk>
    <name>Test Track</name>
    <trkseg>
      <trkpt lat="40.0" lon="-3.0">
        <ele>100.0</ele>
        <time>2023-10-27T10:00:01Z</time>
      </trkpt>
      <trkpt lat="40.1" lon="-3.1">
        <ele>110.0</ele>
        <time>2023-10-27T10:00:02Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""

SAMPLE_GPX_NO_METADATA_TIME = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="TestCreator">
  <trk>
    <name>Test Track No Meta</name>
    <trkseg>
      <trkpt lat="40.0" lon="-3.0">
        <ele>100.0</ele>
        <time>2023-11-15T15:30:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""


@pytest.fixture
def gpx_track_from_content():
    path = pathlib.Path("dummy.gpx")
    content = SAMPLE_GPX.encode("utf-8")
    track = GPXTrack(path, content)
    track.load()
    return track


def test_gpx_load_from_content(gpx_track_from_content):
    assert gpx_track_from_content.gpx_ is not None
    assert len(gpx_track_from_content.gpx_.tracks) == 1
    assert gpx_track_from_content.gpx_.tracks[0].name == "Test Track"


def test_gpx_date_from_metadata(gpx_track_from_content):
    date = gpx_track_from_content.date()
    assert date is not None
    # gpxpy returns datetime with timezone info
    assert date.year == 2023
    assert date.month == 10
    assert date.day == 27
    assert date.hour == 10


def test_gpx_date_from_points():
    path = pathlib.Path("dummy.gpx")
    content = SAMPLE_GPX_NO_METADATA_TIME.encode("utf-8")
    track = GPXTrack(path, content)
    track.load()

    date = track.date()
    assert date is not None
    assert date.year == 2023
    assert date.month == 11
    assert date.day == 15
    assert date.hour == 15


def test_gpx_date_from_filename():
    filename = "12_dic_2022_09_00.gpx"
    path = pathlib.Path(filename)
    empty_gpx = """<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1"><trk><trkseg></trkseg></trk></gpx>"""

    track = GPXTrack(path, empty_gpx.encode("utf-8"))
    track.load()

    date = track.date()
    assert date is not None
    assert date.year == 2022
    assert date.month == 12
    assert date.day == 12
    assert date.hour == 9


def test_gpx_geojson_generation(gpx_track_from_content):
    geojson = gpx_track_from_content.geojson()

    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 1

    feature = geojson["features"][0]
    assert feature["type"] == "Feature"
    assert feature["properties"]["name"] == "Test Track"
    assert feature["geometry"]["type"] == "LineString"

    coords = feature["geometry"]["coordinates"]
    assert len(coords) == 2
    assert coords[0] == [-3.0, 40.0, 100.0]
    assert coords[1] == [-3.1, 40.1, 110.0]


def test_gpx_save(tmp_path):
    # Create a temporary file path
    save_path = tmp_path / "saved_track.gpx"

    content = SAMPLE_GPX.encode("utf-8")
    track = GPXTrack(save_path, content)
    track.load()

    # Modify the track name to verify we are saving the object state, not just raw bytes
    track.gpx_.tracks[0].name = "Modified Track Name"

    assert track.save() is True
    assert save_path.exists()

    # Read back and verify
    with open(save_path, "r", encoding="utf-8") as f:
        saved_content = f.read()
        assert "Modified Track Name" in saved_content

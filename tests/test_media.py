import pathlib
from datetime import datetime
from ouffroad.media.Photo import Photo
from ouffroad.media.Video import Video


def test_photo_initialization():
    """Test Photo initialization."""
    photo_path = pathlib.Path("test.jpg")
    photo = Photo(photo_path)

    assert photo.format() == "photo"
    assert photo.path() == photo_path
    assert photo.name() == "test.jpg"
    assert photo.ext() == ".jpg"


def test_video_initialization():
    """Test Video initialization."""
    video_path = pathlib.Path("test.mp4")
    video = Video(video_path)

    assert video.format() == "video"
    assert video.path() == video_path
    assert video.name() == "test.mp4"
    assert video.ext() == ".mp4"


def test_video_save_metadata(tmp_path):
    """Test saving video metadata to sidecar JSON."""
    video_path = tmp_path / "test.mp4"
    video_path.write_bytes(b"fake video")

    video = Video(video_path)
    result = video.save_metadata(40.7128, -74.0060)

    assert result

    # Check sidecar file was created
    sidecar_path = pathlib.Path(str(video_path) + ".json")
    assert sidecar_path.exists()

    # Load and verify
    video.load()
    location = video.location()
    assert location == (40.7128, -74.0060)


def test_video_geojson(tmp_path):
    """Test Video GeoJSON generation."""
    video_path = tmp_path / "test.mp4"
    video_path.write_bytes(b"fake video")

    video = Video(video_path)
    video.save_metadata(40.7128, -74.0060)
    video.load()

    geojson = video.geojson()

    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 1
    assert geojson["features"][0]["geometry"]["type"] == "Point"
    assert geojson["features"][0]["geometry"]["coordinates"] == [-74.0060, 40.7128]
    assert geojson["features"][0]["properties"]["type"] == "video"


def test_video_date_from_metadata(tmp_path):
    """Test Video date extraction from metadata."""
    video_path = tmp_path / "test.mp4"
    video_path.write_bytes(b"fake video")

    video = Video(video_path)
    video.save_metadata(40.7128, -74.0060)
    video.load()

    date = video.date()
    assert date is not None
    assert isinstance(date, datetime)


def test_photo_save_with_content(tmp_path):
    """Test Photo save with content."""
    photo_path = tmp_path / "test.jpg"
    content = b"fake image content"

    photo = Photo(photo_path, content)
    result = photo.save()

    assert result
    assert photo_path.exists()
    assert photo_path.read_bytes() == content


def test_video_save_with_content(tmp_path):
    """Test Video save with content."""
    video_path = tmp_path / "test.mp4"
    content = b"fake video content"

    video = Video(video_path, content)
    result = video.save()

    assert result
    assert video_path.exists()
    assert video_path.read_bytes() == content


def test_photo_location_without_metadata():
    """Test Photo location when no metadata available."""
    photo_path = pathlib.Path("test.jpg")
    photo = Photo(photo_path)

    location = photo.location()
    assert location is None


def test_video_location_without_metadata():
    """Test Video location when no metadata available."""
    video_path = pathlib.Path("test.mp4")
    video = Video(video_path)

    location = video.location()
    assert location is None

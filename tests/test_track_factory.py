import pathlib

from ouffroad.track.TrackFactory import TrackFactory
from ouffroad.track.GPXTrack import GPXTrack
from ouffroad.track.FITTrack import FITTrack


def test_factory_create_gpx():
    """Test that factory creates GPXTrack for .gpx files."""
    path = pathlib.Path("test.gpx")
    content = b"<gpx></gpx>"

    result = TrackFactory.create(path, content)

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], GPXTrack)


def test_factory_create_fit():
    """Test that factory creates FITTrack for .fit files."""
    path = pathlib.Path("test.fit")
    content = b"dummy_fit_content"

    result = TrackFactory.create(path, content)

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], FITTrack)


def test_factory_create_unsupported():
    """Test that factory returns empty list for unsupported formats."""
    path = pathlib.Path("test.xyz")
    content = b"dummy"

    result = TrackFactory.create(path, content)

    assert isinstance(result, list)
    assert len(result) == 0


def test_factory_case_insensitive_extensions():
    """Test that factory handles case-insensitive file extensions."""
    # Test uppercase
    result_gpx = TrackFactory.create(pathlib.Path("test.GPX"), b"<gpx></gpx>")
    assert len(result_gpx) == 1
    assert isinstance(result_gpx[0], GPXTrack)

    result_fit = TrackFactory.create(pathlib.Path("test.FIT"), b"fit")
    assert len(result_fit) == 1
    assert isinstance(result_fit[0], FITTrack)

from fastapi.testclient import TestClient
import pathlib

# Sample GPX content
SAMPLE_GPX = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata>
    <time>2023-10-27T10:00:00Z</time>
  </metadata>
  <trk>
    <name>Test Track</name>
    <trkseg>
      <trkpt lat="40.0" lon="-3.0">
        <ele>100</ele>
        <time>2023-10-27T10:00:00Z</time>
      </trkpt>
      <trkpt lat="40.1" lon="-3.1">
        <ele>110</ele>
        <time>2023-10-27T10:01:00Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""

# Sample KML content
SAMPLE_KML = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Test KML</name>
    <Placemark>
      <name>KML Track</name>
      <LineString>
        <coordinates>
          -3.0,40.0,100
          -3.1,40.1,110
        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>
"""


def test_upload_gpx(client: TestClient, temp_repo: pathlib.Path):
    """Test uploading a GPX file."""
    response = client.post(
        "/api/upload",
        files={"file": ("test.gpx", SAMPLE_GPX, "application/gpx+xml")},
        data={"category": "tracks"},
    )
    if response.status_code != 200:
        print(f"Upload failed: {response.json()}")
    assert response.status_code == 200
    saved_paths = response.json()["saved_paths"]
    assert len(saved_paths) == 1

    # Verify file exists on disk (DateBasedPolicy: 2023/10/test.gpx)
    # Note: The actual path might vary depending on how DateBasedPolicy extracts the date
    # But we know it should be in the repo
    relative_path = saved_paths[0]
    full_path = temp_repo / relative_path
    assert full_path.exists()

    # Verify content
    content = full_path.read_text(encoding="utf-8")
    assert "<gpx" in content
    assert "Test Track" in content


def test_upload_kml_conversion(client: TestClient, temp_repo: pathlib.Path):
    """Test uploading a KML file and verifying conversion to GPX."""
    response = client.post(
        "/api/upload",
        files={
            "file": ("test.kml", SAMPLE_KML, "application/vnd.google-earth.kml+xml")
        },
        data={"category": "tracks"},
    )
    if response.status_code != 200:
        print(f"Upload failed: {response.json()}")
    assert response.status_code == 200
    saved_paths = response.json()["saved_paths"]
    assert len(saved_paths) == 1

    # The saved file should be a .gpx file, not .kml
    relative_path = saved_paths[0]
    assert relative_path.endswith(".gpx")

    full_path = temp_repo / relative_path
    assert full_path.exists()

    # Verify it's valid XML (GPX)
    content = full_path.read_text(encoding="utf-8")
    assert "<gpx" in content
    assert "KML Track" in content  # Name should be preserved


def test_list_files(client: TestClient):
    """Test listing files after upload."""
    # First upload a file
    client.post(
        "/api/upload",
        files={"file": ("list_test.gpx", SAMPLE_GPX, "application/gpx+xml")},
        data={"category": "tracks"},
    )

    response = client.get("/api/tracks")
    assert response.status_code == 200
    data = response.json()
    assert "tracks" in data
    assert len(data["tracks"]) >= 1
    # Check if our uploaded file is in the list (checking suffix as path includes date folders)
    assert any(f.endswith("list_test.gpx") for f in data["tracks"])


def test_get_geojson(client: TestClient):
    """Test retrieving GeoJSON for a track."""
    # Upload
    upload_resp = client.post(
        "/api/upload",
        files={"file": ("geojson_test.gpx", SAMPLE_GPX, "application/gpx+xml")},
        data={"category": "tracks"},
    )
    if upload_resp.status_code != 200:
        print(f"Upload failed: {upload_resp.json()}")

    saved_path = upload_resp.json()["saved_paths"][0]

    # Get GeoJSON
    response = client.get(f"/api/track/{saved_path}")
    assert response.status_code == 200
    geojson = response.json()

    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) > 0
    feature = geojson["features"][0]
    assert feature["geometry"]["type"] == "LineString"
    assert feature["properties"]["name"] == "Test Track"

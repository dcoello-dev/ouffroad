import React, { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Marker,
  Popup,
  useMap,
  LayersControl,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { Media } from "../models/File";
import type { IFile } from "../models/File";
import { ApiService } from "../services/ApiService";
import { GeoJsonFeatureCollection } from "../models/GeoJson";

const DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

const { BaseLayer } = LayersControl;

interface MapProps {
  activeFiles: IFile[];
  pickingLocationFor: string | null;
  onLocationPicked: (lat: number, lng: number) => void;
}

// Component to handle map clicks for location picking
const MapClickHandler = ({
  pickingLocationFor,
  onLocationPicked,
}: {
  pickingLocationFor: string | null;
  onLocationPicked: (lat: number, lng: number) => void;
}) => {
  const map = useMap();

  useEffect(() => {
    if (!pickingLocationFor) return;

    const handleClick = (e: L.LeafletMouseEvent) => {
      onLocationPicked(e.latlng.lat, e.latlng.lng);
    };

    map.on("click", handleClick);
    map.getContainer().style.cursor = "crosshair";

    return () => {
      map.off("click", handleClick);
      map.getContainer().style.cursor = "";
    };
  }, [pickingLocationFor, onLocationPicked, map]);

  return null;
};

const GeoJsonLayer = ({ file }: { file: IFile }) => {
  const [data, setData] = useState<GeoJsonFeatureCollection | null>(null);
  const [error, setError] = useState<boolean>(false);
  const map = useMap();

  useEffect(() => {
    let mounted = true;

    const loadData = async () => {
      try {
        // Ensure config is loaded first
        await ApiService.getInstance().ensureConfigLoaded();

        const geojson = await ApiService.getInstance().getTrackGeoJSON(
          file.fullPath,
        );

        if (mounted) {
          if (!geojson || !geojson.features) {
            console.warn(`Invalid GeoJSON for ${file.filename}`, geojson);
            setError(true);
            return;
          }
          setData(geojson);
          // Don't auto-zoom to avoid jumping between tracks
        }
      } catch (err) {
        if (mounted) {
          console.error(`Failed to load GeoJSON for ${file.filename}`, err);
          setError(true);
        }
      }
    };

    loadData();

    return () => {
      mounted = false;
    };
  }, [file, map]);

  if (error || !data) return null;

  if (file.type === "media") {
    // Media (Point)
    const feature = data.features[0];
    if (!feature || !feature.geometry || !feature.geometry.coordinates) {
      console.warn(`Missing geometry for media ${file.filename}`);
      return null;
    }

    const coords = feature.geometry.coordinates;
    const position: [number, number] = [coords[1], coords[0]];
    const mediaFile = file as Media;

    // Construct media URL
    const repoBaseUrl = ApiService.getInstance().getRepoBaseUrl();
    const mediaUrl = `${repoBaseUrl}/${file.fullPath}`;
    console.log(
      "[Map] Media URL constructed:",
      mediaUrl,
      "from repoBaseUrl:",
      repoBaseUrl,
      "and fullPath:",
      file.fullPath,
    );

    const handleSetLocation = async (e: React.MouseEvent) => {
      e.stopPropagation();
      const newLat = prompt("Ingresa la latitud:", coords[1].toString());
      const newLng = prompt("Ingresa la longitud:", coords[0].toString());

      if (newLat && newLng) {
        try {
          await ApiService.getInstance().updateMediaLocation(
            file.fullPath,
            parseFloat(newLat),
            parseFloat(newLng),
          );
          alert(
            "Ubicación actualizada. Recarga la página para ver los cambios.",
          );
        } catch (error) {
          console.error("Error updating location:", error);
          alert("Error al actualizar la ubicación");
        }
      }
    };

    return (
      <Marker position={position}>
        <Popup minWidth={200}>
          <div style={{ textAlign: "center" }}>
            <h4>{file.filename.split("/").pop()}</h4>
            {mediaFile.isVideo() ? (
              <video controls style={{ width: "100%" }} src={mediaUrl} />
            ) : (
              <a href={mediaUrl} target="_blank" rel="noreferrer">
                <img
                  src={mediaUrl}
                  style={{ width: "100%" }}
                  alt={file.filename}
                />
              </a>
            )}
            <button
              onClick={handleSetLocation}
              style={{
                marginTop: "10px",
                padding: "5px 10px",
                background: "#0066cc",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "12px",
              }}
            >
              📍 Set Location
            </button>
          </div>
        </Popup>
      </Marker>
    );
  }

  // Track (LineString/MultiLineString)
  return (
    <GeoJSON
      data={data}
      style={{ color: getColor(file.category), weight: 2 }}
    />
  );
};

function getColor(category?: string): string {
  switch (category) {
    case "enduro":
      return "red";
    case "trail":
      return "gold";
    default:
      return "blue";
  }
}

export const MapComponent: React.FC<MapProps> = ({
  activeFiles,
  pickingLocationFor,
  onLocationPicked,
}) => {
  return (
    <MapContainer
      center={[0, 0]}
      zoom={2}
      style={{ height: "100%", width: "100%" }}
    >
      <MapClickHandler
        pickingLocationFor={pickingLocationFor}
        onLocationPicked={onLocationPicked}
      />
      <LayersControl position="topright">
        <BaseLayer checked name="Street Map">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxZoom={19}
          />
        </BaseLayer>
        <BaseLayer name="Satellite">
          <TileLayer
            attribution="Tiles © Esri"
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            maxZoom={19}
          />
        </BaseLayer>
        <BaseLayer name="Topographic">
          <TileLayer
            attribution="Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap"
            url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
            maxZoom={17}
          />
        </BaseLayer>
        <BaseLayer name="Terrain">
          <TileLayer
            attribution="© Stamen Design © OpenStreetMap contributors"
            url="https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png"
            maxZoom={18}
          />
        </BaseLayer>
        <BaseLayer name="Cycling">
          <TileLayer
            attribution="© OpenStreetMap contributors © CyclOSM"
            url="https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png"
            maxZoom={20}
          />
        </BaseLayer>
      </LayersControl>
      {activeFiles.map((file) => (
        <GeoJsonLayer key={file.fullPath} file={file} />
      ))}
    </MapContainer>
  );
};

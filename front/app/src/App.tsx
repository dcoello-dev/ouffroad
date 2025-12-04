import { useEffect, useState } from "react";
import { ApiService } from "./services/ApiService";
import type { IFile } from "./models/File";
import { MapComponent } from "./components/Map";
import { Sidebar } from "./components/Sidebar";
import "./index.css";

function App() {
  const [files, setFiles] = useState<IFile[]>([]);
  const [activeFiles, setActiveFiles] = useState<IFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [pickingLocation, setPickingLocation] = useState<string | null>(null);
  const [hoveredTrackIds, setHoveredTrackIds] = useState<string[]>([]);

  const loadFiles = async () => {
    try {
      await ApiService.getInstance().ensureConfigLoaded();
      const fetchedFiles = await ApiService.getInstance().getTracks();
      setFiles(fetchedFiles);
    } catch (error) {
      console.error("Failed to load files", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const handleToggle = (file: IFile) => {
    setActiveFiles((prev) => {
      const exists = prev.some((f) => f.fullPath === file.fullPath);
      if (exists) {
        return prev.filter((f) => f.fullPath !== file.fullPath);
      } else {
        return [...prev, file];
      }
    });
  };

  const handleLocationPicked = async (lat: number, lng: number) => {
    if (!pickingLocation) return;

    try {
      await ApiService.getInstance().updateMediaLocation(
        pickingLocation,
        lat,
        lng,
      );
      alert("Ubicación actualizada. Recarga la página para ver los cambios.");
      setPickingLocation(null);
    } catch (error) {
      console.error("Error updating location:", error);
      alert("Error al actualizar la ubicación");
      setPickingLocation(null);
    }
  };

  return (
    <div className="container">
      <Sidebar
        files={files}
        activeFiles={activeFiles}
        onToggle={handleToggle}
        onUploadComplete={loadFiles}
        onSetLocationRequest={setPickingLocation}
        onHover={setHoveredTrackIds}
      />
      <div className="main-content">
        {loading ? (
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              height: "100%",
            }}
          >
            Loading...
          </div>
        ) : (
          <MapComponent
            activeFiles={activeFiles}
            pickingLocationFor={pickingLocation}
            onLocationPicked={handleLocationPicked}
            hoveredTrackIds={hoveredTrackIds}
          />
        )}
      </div>
    </div>
  );
}

export default App;

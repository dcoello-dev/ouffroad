import React, { useState } from "react";
import { ApiService } from "../services/ApiService";

interface UploadProps {
  onUploadComplete: () => void;
}

export const Upload: React.FC<UploadProps> = ({ onUploadComplete }) => {
  const [uploading, setUploading] = useState(false);
  const [category, setCategory] = useState("trail");
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [showLocationInput, setShowLocationInput] = useState(false);
  const [latitude, setLatitude] = useState<string>("");
  const [longitude, setLongitude] = useState<string>("");

  const [categories, setCategories] = useState<Record<string, any>>({});

  React.useEffect(() => {
    const loadCategories = async () => {
      console.log("[Upload] Waiting for config...");
      await ApiService.getInstance().ensureConfigLoaded();
      const cats = ApiService.getInstance().getCategories();
      console.log("[Upload] Got categories:", cats);
      setCategories(cats);
      // Set default category to first available if current is not in list
      if (Object.keys(cats).length > 0 && !cats[category]) {
        const firstCat = Object.keys(cats)[0];
        console.log("[Upload] Setting default category:", firstCat);
        setCategory(firstCat);
      }
    };
    loadCategories();
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    setSelectedFiles(files);

    // Check if any file is a video
    if (files) {
      const hasVideo = Array.from(files).some((file) => {
        const ext = file.name.split(".").pop()?.toLowerCase();
        return ["mp4", "mov", "avi", "mkv"].includes(ext || "");
      });
      setShowLocationInput(hasVideo);
    } else {
      setShowLocationInput(false);
    }
  };

  const handleUpload = async () => {
    if (!selectedFiles?.length) return;

    setUploading(true);
    try {
      const location =
        latitude && longitude
          ? {
              lat: parseFloat(latitude),
              lng: parseFloat(longitude),
            }
          : undefined;

      await ApiService.getInstance().uploadFiles(
        selectedFiles,
        category,
        location,
      );
      onUploadComplete();
      alert("Upload successful!");

      // Reset form
      setSelectedFiles(null);
      setLatitude("");
      setLongitude("");
      setShowLocationInput(false);
      const fileInput = document.getElementById(
        "file-upload",
      ) as HTMLInputElement;
      if (fileInput) fileInput.value = "";
    } catch (error) {
      console.error(error);
      alert("Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  console.log(
    "[Upload] Rendering with categories:",
    categories,
    "Keys:",
    Object.keys(categories),
  );

  return (
    <div className="upload-section">
      <select
        value={category}
        onChange={(e) => setCategory(e.target.value)}
        className="category-select"
      >
        {Object.keys(categories).length > 0 ? (
          Object.keys(categories).map((cat) => (
            <option key={cat} value={cat}>
              {categories[cat].label ||
                cat.charAt(0).toUpperCase() + cat.slice(1).replace(/_/g, " ")}
            </option>
          ))
        ) : (
          <option value="loading">Loading categories...</option>
        )}
      </select>

      <input
        id="file-upload"
        type="file"
        multiple
        onChange={handleFileSelect}
        accept=".gpx,.fit,.kml,.kmz,.jpg,.jpeg,.png,.mp4,.mov,.avi,.mkv"
        className="file-input"
      />

      {showLocationInput && (
        <div className="manual-location">
          <p className="location-instruction">
            Haz clic en el mapa para seleccionar la ubicación o ingresa las
            coordenadas manualmente:
          </p>
          <input
            type="number"
            placeholder="Latitud (ej. 40.7128)"
            step="any"
            value={latitude}
            onChange={(e) => setLatitude(e.target.value)}
          />
          <input
            type="number"
            placeholder="Longitud (ej. -74.0060)"
            step="any"
            value={longitude}
            onChange={(e) => setLongitude(e.target.value)}
          />
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={uploading || !selectedFiles}
        className="upload-btn"
      >
        {uploading ? "Uploading..." : "Upload"}
      </button>
    </div>
  );
};

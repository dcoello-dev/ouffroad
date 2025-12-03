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

  return (
    <div className="upload-section">
      <select
        value={category}
        onChange={(e) => setCategory(e.target.value)}
        className="category-select"
      >
        <option value="trail">Trail</option>
        <option value="enduro">Enduro</option>
        <option value="special_events">Eventos</option>
        <option value="media">Media</option>
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

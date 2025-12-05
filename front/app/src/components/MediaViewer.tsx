import React, { useEffect, useState } from "react";
import type { IFile } from "../models/File";
import { ApiService } from "../services/ApiService";

interface MediaViewerProps {
  file: IFile | null;
  allMediaFiles: IFile[];
  onClose: () => void;
  onNavigate?: (file: IFile) => void;
}

export const MediaViewer: React.FC<MediaViewerProps> = ({
  file,
  allMediaFiles,
  onClose,
  onNavigate,
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (file) {
      const index = allMediaFiles.findIndex(
        (f) => f.fullPath === file.fullPath,
      );
      setCurrentIndex(index >= 0 ? index : 0);
    }
  }, [file, allMediaFiles]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!file) return;

      if (e.key === "Escape") {
        onClose();
      } else if (e.key === "ArrowLeft") {
        handlePrevious();
      } else if (e.key === "ArrowRight") {
        handleNext();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [file, currentIndex, allMediaFiles]);

  if (!file) return null;

  const currentFile = allMediaFiles[currentIndex] || file;
  const fileUrl = ApiService.getInstance().getFileUrl(currentFile);
  const isVideo = currentFile.filename.match(/\.(mp4|mov|avi|mkv|webm)$/i);
  const isImage = currentFile.filename.match(/\.(jpg|jpeg|png|gif|webp)$/i);

  const handlePrevious = () => {
    if (currentIndex > 0) {
      const newIndex = currentIndex - 1;
      setCurrentIndex(newIndex);
      onNavigate?.(allMediaFiles[newIndex]);
    }
  };

  const handleNext = () => {
    if (currentIndex < allMediaFiles.length - 1) {
      const newIndex = currentIndex + 1;
      setCurrentIndex(newIndex);
      onNavigate?.(allMediaFiles[newIndex]);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.9)",
        zIndex: 10000,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
        animation: "fadeIn 0.2s ease-in",
      }}
      onClick={handleBackdropClick}
    >
      {/* Close button */}
      <button
        onClick={onClose}
        style={{
          position: "absolute",
          top: "20px",
          right: "20px",
          background: "rgba(255, 255, 255, 0.1)",
          border: "none",
          color: "white",
          fontSize: "24px",
          width: "40px",
          height: "40px",
          borderRadius: "50%",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transition: "background 0.2s",
          zIndex: 10001,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "rgba(255, 255, 255, 0.2)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "rgba(255, 255, 255, 0.1)";
        }}
        title="Close (Esc)"
      >
        ✕
      </button>

      {/* Navigation buttons */}
      {allMediaFiles.length > 1 && (
        <>
          <button
            onClick={handlePrevious}
            disabled={currentIndex === 0}
            style={{
              position: "absolute",
              left: "20px",
              top: "50%",
              transform: "translateY(-50%)",
              background: "rgba(255, 255, 255, 0.1)",
              border: "none",
              color: "white",
              fontSize: "32px",
              width: "50px",
              height: "50px",
              borderRadius: "50%",
              cursor: currentIndex === 0 ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "background 0.2s",
              opacity: currentIndex === 0 ? 0.3 : 1,
            }}
            onMouseEnter={(e) => {
              if (currentIndex > 0) {
                e.currentTarget.style.background = "rgba(255, 255, 255, 0.2)";
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(255, 255, 255, 0.1)";
            }}
            title="Previous (←)"
          >
            ‹
          </button>

          <button
            onClick={handleNext}
            disabled={currentIndex === allMediaFiles.length - 1}
            style={{
              position: "absolute",
              right: "20px",
              top: "50%",
              transform: "translateY(-50%)",
              background: "rgba(255, 255, 255, 0.1)",
              border: "none",
              color: "white",
              fontSize: "32px",
              width: "50px",
              height: "50px",
              borderRadius: "50%",
              cursor:
                currentIndex === allMediaFiles.length - 1
                  ? "not-allowed"
                  : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "background 0.2s",
              opacity: currentIndex === allMediaFiles.length - 1 ? 0.3 : 1,
            }}
            onMouseEnter={(e) => {
              if (currentIndex < allMediaFiles.length - 1) {
                e.currentTarget.style.background = "rgba(255, 255, 255, 0.2)";
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(255, 255, 255, 0.1)";
            }}
            title="Next (→)"
          >
            ›
          </button>
        </>
      )}

      {/* Media content */}
      <div
        style={{
          maxWidth: "90vw",
          maxHeight: "80vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "20px",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {isImage && (
          <img
            src={fileUrl}
            alt={currentFile.filename}
            style={{
              maxWidth: "100%",
              maxHeight: "70vh",
              objectFit: "contain",
              borderRadius: "8px",
              boxShadow: "0 4px 20px rgba(0, 0, 0, 0.5)",
            }}
          />
        )}

        {isVideo && (
          <video
            src={fileUrl}
            controls
            autoPlay
            style={{
              maxWidth: "100%",
              maxHeight: "70vh",
              borderRadius: "8px",
              boxShadow: "0 4px 20px rgba(0, 0, 0, 0.5)",
            }}
          />
        )}

        {/* Metadata panel */}
        <div
          style={{
            background: "rgba(255, 255, 255, 0.1)",
            backdropFilter: "blur(10px)",
            padding: "15px 20px",
            borderRadius: "8px",
            color: "white",
            minWidth: "400px",
            maxWidth: "600px",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "10px",
            }}
          >
            <h3 style={{ margin: 0, fontSize: "18px", fontWeight: 600 }}>
              {currentFile.filename.split("/").pop()}
            </h3>
            <a
              href={fileUrl}
              download
              onClick={(e) => e.stopPropagation()}
              style={{
                background: "rgba(33, 150, 243, 0.8)",
                color: "white",
                padding: "6px 12px",
                borderRadius: "4px",
                textDecoration: "none",
                fontSize: "14px",
                transition: "background 0.2s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(33, 150, 243, 1)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(33, 150, 243, 0.8)";
              }}
            >
              ⬇️ Download
            </a>
          </div>

          <div style={{ fontSize: "14px", opacity: 0.9 }}>
            <div style={{ marginBottom: "5px" }}>
              📁 <strong>Path:</strong> {currentFile.fullPath}
            </div>
            {currentFile.category && (
              <div style={{ marginBottom: "5px" }}>
                🏷️ <strong>Category:</strong> {currentFile.category}
              </div>
            )}
            {allMediaFiles.length > 1 && (
              <div style={{ marginTop: "10px", opacity: 0.7 }}>
                {currentIndex + 1} / {allMediaFiles.length}
              </div>
            )}
          </div>
        </div>
      </div>

      <style>
        {`
          @keyframes fadeIn {
            from {
              opacity: 0;
            }
            to {
              opacity: 1;
            }
          }
        `}
      </style>
    </div>
  );
};

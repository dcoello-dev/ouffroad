import React, { useState, useEffect } from "react";
import { ApiService } from "../services/ApiService";

interface RepositorySelectorProps {
  onRepositorySet: () => void;
  onCancel?: () => void; // Optional cancel for "switch" mode
}

export const RepositorySelector: React.FC<RepositorySelectorProps> = ({
  onRepositorySet,
  onCancel,
}) => {
  const [path, setPath] = useState("");
  const [drives, setDrives] = useState<{ path: string; name: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDrives = async () => {
      try {
        const systemDrives = await ApiService.getInstance().getSystemDrives();
        setDrives(systemDrives);
      } catch (err) {
        console.error("Failed to load drives", err);
      }
    };
    loadDrives();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!path.trim()) return;

    setLoading(true);
    setError(null);

    try {
      await ApiService.getInstance().setRepository(path);
      onRepositorySet();
    } catch (err: any) {
      console.error("Failed to set repository", err);
      setError(
        err.response?.data?.detail || "Failed to set repository. Invalid path?",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="repository-selector-container">
      <div className="repository-selector-card">
        <h2>Select Repository</h2>
        <p>Please select the folder where your tracks and media are stored.</p>

        {error && <div className="error-message">{error}</div>}

        <div className="drives-list">
          {drives.map((drive) => (
            <button
              key={drive.path}
              type="button"
              className="drive-button"
              onClick={() => setPath(drive.path)}
            >
              📂 {drive.name}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <input
              type="text"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="/path/to/your/repository"
              disabled={loading}
            />
          </div>

          <div className="actions">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="cancel-button"
                disabled={loading}
              >
                Cancel
              </button>
            )}
            <button type="submit" className="submit-button" disabled={loading}>
              {loading ? "Loading..." : "Set Repository"}
            </button>
          </div>
        </form>
      </div>

      <style>{`
        .repository-selector-container {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
          background-color: #f5f5f5;
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          z-index: 1000;
        }
        .repository-selector-card {
          background: white;
          padding: 2rem;
          border-radius: 8px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          width: 100%;
          max-width: 500px;
        }
        h2 {
          margin-top: 0;
          color: #333;
        }
        p {
          color: #666;
          margin-bottom: 1.5rem;
        }
        .error-message {
          background-color: #ffebee;
          color: #c62828;
          padding: 0.75rem;
          border-radius: 4px;
          margin-bottom: 1rem;
        }
        .drives-list {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          margin-bottom: 1rem;
        }
        .drive-button {
          background: #e3f2fd;
          border: 1px solid #bbdefb;
          color: #1976d2;
          padding: 0.5rem 1rem;
          border-radius: 4px;
          cursor: pointer;
          font-size: 0.9rem;
        }
        .drive-button:hover {
          background: #bbdefb;
        }
        .input-group {
          margin-bottom: 1.5rem;
        }
        input[type="text"] {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 1rem;
          box-sizing: border-box;
        }
        .actions {
          display: flex;
          justify-content: flex-end;
          gap: 1rem;
        }
        .submit-button {
          background-color: #2196f3;
          color: white;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 4px;
          cursor: pointer;
          font-size: 1rem;
          font-weight: 500;
        }
        .submit-button:disabled {
          background-color: #bdbdbd;
          cursor: not-allowed;
        }
        .cancel-button {
          background-color: transparent;
          color: #666;
          border: 1px solid #ddd;
          padding: 0.75rem 1.5rem;
          border-radius: 4px;
          cursor: pointer;
          font-size: 1rem;
        }
        .cancel-button:hover {
          background-color: #f5f5f5;
        }
      `}</style>
    </div>
  );
};

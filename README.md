# Ouffroad - Your Personal GPX & Media Manager

Ouffroad is a powerful self-hosted application for managing, visualizing, and organizing your GPS tracks (GPX, FIT) and associated media (photos, videos). It helps you keep your outdoor adventures organized with a beautiful map-based interface.

## 🚀 Getting Started

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/ouffroad.git
    cd ouffroad
    ```

2.  **Set up the environment:**
    We recommend using `uv` for fast Python package management, but `pip` works too.

    ```bash
    # Using uv (Recommended)
    pip install uv
    uv venv
    source .venv/bin/activate
    uv pip install -e .
    ```

    ```bash
    # Using standard pip
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -e .
    ```

3.  **Build the Frontend:**
    ```bash
    cd front/app
    npm install
    npm run build
    cd ../..
    ```

### Running the Application

Start the server pointing to your data repository:

```bash
uv run ouffroad --repo /path/to/your/data
```

Open your browser at `http://localhost:8000`.

---

## 📖 How to Use Ouffroad

### 1. Uploading Files
- Click the **"Upload"** button in the sidebar.
- Drag and drop GPX, FIT, JPG, or MP4 files.
- Select a category (e.g., "Trail", "Enduro").
- Files are automatically processed and organized based on their date.

### 2. Organizing Your Library
- **Drag & Drop**: Move files between categories or folders simply by dragging them in the sidebar.
- **Rename**: Double-click any file name to rename it inline.
- **Download**: Click the download icon next to any file to save it.

### 3. Visualizing Data
- **Map View**: All your tracks and geolocated photos appear on the map.
- **Track Details**: Click a track to see elevation profiles and statistics.
- **Media Viewer**: Click the 👁️ icon on photos/videos to open the immersive lightbox viewer.

---

## 📁 Creating a New Repository

A repository is simply a folder where Ouffroad stores your files. It requires a `storage.toml` configuration file to tell Ouffroad how to organize things.

### 1. Create a Folder
Create a directory anywhere on your computer:
```bash
mkdir ~/my-adventures
```

### 2. Create `storage.toml`
Create a file named `storage.toml` inside that folder with your category definitions:

```toml
# ~/my-adventures/storage.toml

[categories.trail]
name = "Trail Riding"
type = "track"
extensions = [".gpx", ".fit"]
color = "gold"
# DateBasedPolicy organizes files by Year/Month (e.g., 2024/01/track.gpx)
storage_policy = { name = "DateBasedPolicy" }

[categories.enduro]
name = "Hard Enduro"
type = "track"
extensions = [".gpx"]
color = "red"
storage_policy = { name = "DateBasedPolicy" }

[categories.media]
name = "Photos & Videos"
type = "media"
extensions = [".jpg", ".jpeg", ".png", ".mp4"]
# FlatPolicy puts all files in one folder
storage_policy = { name = "FlatPolicy" }
```

### 3. Run Ouffroad
Launch Ouffroad pointing to your new repository:

```bash
uv run ouffroad --repo ~/my-adventures
```

Ouffroad will automatically create the necessary folder structure as you upload files.

---

## 📦 Running the Standalone Executable

If you downloaded the executable (`.exe` for Windows or binary for Linux) from the Releases page, you don't need to install Python.

### Windows (CMD or PowerShell)

Open your terminal and run:

```powershell
# Run with default 'uploads' folder
.\ouffroad.exe

# Run with a specific repository
.\ouffroad.exe --repo "C:\Users\Name\My Adventures"
```

### Linux

```bash
# Make it executable first
chmod +x ouffroad

# Run with a specific repository
./ouffroad --repo /home/user/adventures
```

---

## 🛠️ Advanced Features

- **Sidecar Files**: Metadata is stored in `.json` sidecar files next to your data, keeping your original files untouched.
- **Atomic Operations**: Moves and renames are safe; if something goes wrong, changes are rolled back.
- **GeoJSON API**: Developers can access raw data via the `/api` endpoints.

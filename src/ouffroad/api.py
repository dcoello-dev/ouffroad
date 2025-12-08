import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from pydantic import BaseModel
import os
import pathlib
from typing import Annotated, Optional  # Ensure Optional is imported

from .services.ContentManager import ContentManager
from .repository.FileSystemRepository import FileSystemRepository
from .config import OuffroadConfig  # Added import

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Dependency Providers ---
def get_app_config(request: Request) -> OuffroadConfig:
    """Provides the OuffroadConfig instance from app.state."""
    return request.app.state.config


def get_repository(
    app_config: Annotated[OuffroadConfig, Depends(get_app_config)],
) -> FileSystemRepository:
    """Provides a FileSystemRepository instance configured with the app_config."""
    return FileSystemRepository(app_config)


def get_content_manager(
    repo: Annotated[FileSystemRepository, Depends(get_repository)],
) -> ContentManager:
    """Provides a ContentManager instance configured with the repository."""
    return ContentManager(repo)


# --- Routes ---


@router.post("/upload")
async def upload_gpx(
    app_config: Annotated[
        OuffroadConfig, Depends(get_app_config)
    ],  # Obligatorio (primero)
    content_manager: Annotated[
        ContentManager, Depends(get_content_manager)
    ],  # Obligatorio (primero)
    file: UploadFile = File(...),
    category: str = Form(...),
    latitude: Optional[float] = Form(None),  # Opcional (al final)
    longitude: Optional[float] = Form(None),  # Opcional (al final)
):
    # Validate category against configured categories
    allowed_categories = (
        app_config.repository_config.categories.keys()
        if app_config.repository_config
        else []
    )
    if category not in allowed_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(allowed_categories)}",
        )

    content = await file.read()

    rel_paths = content_manager.import_file(
        pathlib.Path(file.filename), category, content
    )
    uploaded_files = [os.path.basename(p) for p in rel_paths]

    # If manual location provided for video, update sidecar
    if (
        latitude is not None
        and longitude is not None
        and file.filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))
    ):
        for rel_path in rel_paths:
            content_manager.update_media_location(rel_path, latitude, longitude)

    return {
        "message": f"Successfully processed {len(uploaded_files)} files",
        "files": uploaded_files,
        "saved_paths": rel_paths,
        "category": category,
    }


@router.get("/tracks")
async def list_tracks(
    content_manager: Annotated[ContentManager, Depends(get_content_manager)],
):
    """List all available files (tracks and media)."""
    files = content_manager.list_files()
    return {"tracks": files}


@router.get("/track/{filename:path}")
async def get_track_geojson(
    filename: str,
    content_manager: Annotated[ContentManager, Depends(get_content_manager)],
):
    """Get GeoJSON representation of any file (track or media)."""
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # Sanitize filename to remove leading slashes which could cause pathlib to treat it as absolute
    filename = filename.lstrip("/")
    return content_manager.get_geojson(filename)


class LocationUpdate(BaseModel):
    latitude: float
    longitude: float


@router.post("/media/{filename:path}/location")
async def update_media_location(
    filename: str,
    location: LocationUpdate,
    content_manager: Annotated[ContentManager, Depends(get_content_manager)],
):
    """Update location for a media file."""
    content_manager.update_media_location(
        filename, location.latitude, location.longitude
    )
    return {"message": "Location updated successfully"}


@router.get("/config")
async def get_config(
    app_config: Annotated[OuffroadConfig, Depends(get_app_config)],
):
    """Get public application configuration."""
    categories = {}
    if app_config.repository_config:
        categories = {
            name: {
                "type": conf.type,
                "extensions": conf.extensions,
                "label": conf.name,  # Expose the configured name as label
                "color": conf.color,  # Expose the configured color
            }
            for name, conf in app_config.repository_config.categories.items()
        }

    # Use the dynamic route /files as base URL
    # If no repo is configured, repo_base_url is None
    repo_base_url = "/files" if app_config.repository_path else None

    return {
        "repo_base_url": repo_base_url,
        "categories": categories,
        "repository_path": (
            str(app_config.repository_path) if app_config.repository_path else None
        ),
    }


class RepositoryConfigRequest(BaseModel):
    path: str


@router.post("/config/repository")
async def set_repository(
    config_request: RepositoryConfigRequest,
    app_config: Annotated[OuffroadConfig, Depends(get_app_config)],
):
    """Set or update the repository path."""
    print(f"DEBUG: Received repository path request: '{config_request.path}'")
    path = pathlib.Path(config_request.path)
    print(f"DEBUG: Resolved path: '{path.resolve()}'")
    print(f"DEBUG: Exists: {path.exists()}, Is Dir: {path.is_dir()}")

    if not path.exists() or not path.is_dir():
        print(f"DEBUG: Validation failed for path: {path}")
        raise HTTPException(status_code=400, detail=f"Invalid repository path: {path}")

    app_config.repository_path = path
    # Reload config from the new repository
    try:
        app_config.load_repository_config()
    except Exception as e:
        # If loading config fails, we still set the path but warn
        logger.warning(f"Failed to load config from new repository: {e}")

    return {"message": "Repository updated", "path": str(path)}


@router.get("/system/drives")
async def list_drives():
    """List available system drives/root directories."""
    drives = []

    if os.name == "nt":
        # Windows implementation
        import string
        from ctypes import windll

        # Get logical drives bitmask
        try:
            bitmask = windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    drive_path = f"{letter}:\\"
                    drives.append(
                        {"path": drive_path, "name": f"Local Disk ({letter}:)"}
                    )
                bitmask >>= 1
        except Exception:
            # Fallback if ctypes fails
            for letter in string.ascii_uppercase:
                drive_path = f"{letter}:\\"
                if os.path.exists(drive_path):
                    drives.append(
                        {"path": drive_path, "name": f"Local Disk ({letter}:)"}
                    )
    else:
        # Linux/Unix implementation
        roots = [pathlib.Path("/home"), pathlib.Path("/media"), pathlib.Path("/mnt")]

        # Add current user home if available
        try:
            home = pathlib.Path.home()
            if home not in roots:
                roots.insert(0, home)
        except Exception:
            pass

        for root in roots:
            if root.exists():
                drives.append({"path": str(root), "name": root.name or str(root)})

    return {"drives": drives}


# --- File Operations Models ---


class FileUpdateRequest(BaseModel):
    """Request model for file update operations."""

    target_category: Optional[str] = None
    target_folder: Optional[str] = None
    new_filename: Optional[str] = None


class FileUpdateResponse(BaseModel):
    """Response model for file update operations."""

    success: bool
    old_path: str
    new_path: str
    message: str


@router.patch("/file/{filepath:path}")
async def update_file(
    filepath: str,
    updates: FileUpdateRequest,
    repo: Annotated[FileSystemRepository, Depends(get_repository)],
) -> FileUpdateResponse:
    """
    Update file properties (move, rename, etc.).

    Args:
        filepath: Current relative path of the file
        updates: Update operations to perform
        repo: Repository instance (injected)

    Returns:
        FileUpdateResponse with old and new paths

    Raises:
        HTTPException 404: File not found
        HTTPException 400: Invalid parameters
        HTTPException 500: Operation failed
    """
    try:
        # Validate file exists
        if not repo.exists(filepath):
            raise HTTPException(status_code=404, detail=f"File not found: {filepath}")

        new_path = filepath
        operations = []

        # Perform move operation
        if updates.target_category:
            try:
                new_path = repo.move(
                    new_path, updates.target_category, updates.target_folder
                )
                operations.append(f"moved to {updates.target_category}")
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        # Perform rename operation
        if updates.new_filename:
            try:
                new_path = repo.rename(new_path, updates.new_filename)
                operations.append(f"renamed to {updates.new_filename}")
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        # Check if any operation was performed
        if not operations:
            raise HTTPException(
                status_code=400, detail="No update operations specified"
            )

        message = "File " + " and ".join(operations)

        return FileUpdateResponse(
            success=True, old_path=filepath, new_path=new_path, message=message
        )

    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error updating file {filepath}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

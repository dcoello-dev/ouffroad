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
    return {
        "repo_base_url": f"/{app_config.repository_path.name}",
        "categories": categories,
    }

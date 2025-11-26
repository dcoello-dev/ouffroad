import os
import uvicorn
import logging
import argparse  # Added import
import pathlib  # Added import

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .api import router as api_router
from .core.exceptions import OuffroadException, MetadataError
from .config import OuffroadConfig  # Added import

logger = logging.getLogger(__name__)


def configure_logging(log_level: str = "INFO"):
    """Configure application-wide logging."""
    # Create logs directory if it doesn't exist
    log_dir = pathlib.Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # Console handler
            logging.StreamHandler(),
            # File handler with rotation
            logging.handlers.RotatingFileHandler(
                "logs/ouffroad.log",
                maxBytes=10485760,  # 10MB
                backupCount=5,
                encoding="utf-8",
            ),
        ],
    )

    # Set level for ouffroad package
    logging.getLogger("ouffroad").setLevel(log_level)

    # Reduce noise from third-party libraries
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger.info(f"Logging configured with level: {log_level}")


def create_app(config: OuffroadConfig | None = None) -> FastAPI:
    app = FastAPI(title="ouffroad")

    @app.exception_handler(OuffroadException)
    async def ouffroad_exception_handler(request: Request, exc: OuffroadException):
        """
        Handles all custom application exceptions and returns a standardized JSON response.
        """
        status_code = 500
        content = {"message": f"Error interno del servidor: {exc}"}

        if isinstance(exc, MetadataError):
            status_code = (
                400  # Bad Request, client provided a file that cannot be processed
            )
            content = {"message": f"Error procesando el fichero: {exc}"}

        logger.error(f"Capturada excepción de la aplicación: {exc}", exc_info=True)

        return JSONResponse(
            status_code=status_code,
            content=content,
        )

    # Initialize OuffroadConfig if not provided
    if config is None:
        # Default fallback or error, but for main execution it will be passed
        # This path is mostly for when create_app is called without args (e.g. tests might pass it)
        # But in main() we parse args.
        pass
    else:
        app.state.config = config
        # Mount the repository path dynamically
        if config.repository_path.exists():
            app.mount(
                f"/{config.repository_path.name}",
                StaticFiles(directory=config.repository_path),
                name=config.repository_path.name,
            )

    app.mount("/static", StaticFiles(directory="front/static"), name="static")

    templates = Jinja2Templates(directory="front/templates")
    app.include_router(api_router, prefix="/api")

    @app.get("/")
    async def read_root(request: Request):
        # Determine the repository base URL
        # If config is present and path exists, it's mounted at /{dir_name}
        repo_base_url = "/uploads"  # Default fallback
        if app.state.config and app.state.config.repository_path.exists():
            repo_base_url = f"/{app.state.config.repository_path.name}"

        return templates.TemplateResponse(
            "index.html", {"request": request, "repo_base_url": repo_base_url}
        )

    return app


def main():
    # Configure logging first
    log_level = os.getenv("LOG_LEVEL", "INFO")
    configure_logging(log_level)

    # Argument parsing
    parser = argparse.ArgumentParser(description="Run Ouffroad application.")
    parser.add_argument(
        "--repo",
        type=str,
        default="uploads",  # Default to existing 'uploads' folder
        help="Path to the repository root (e.g., 'my_tracks/').",
    )
    args = parser.parse_args()

    # Initialize OuffroadConfig
    app_config = OuffroadConfig(repository_path=pathlib.Path(args.repo))
    app_config.load_repository_config()

    app = create_app(app_config)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True if os.environ.get("ENV") == "development" else False,
    )

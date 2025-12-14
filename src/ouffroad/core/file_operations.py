"""File operation utilities for moving and renaming files with sidecar support."""

import pathlib
import shutil
import logging

logger = logging.getLogger(__name__)


class FileOperationError(Exception):
    """Raised when a file operation fails."""

    pass


def get_sidecar_path(file_path: pathlib.Path) -> pathlib.Path:
    """
    Get the sidecar path for a given file.

    Args:
        file_path: Path to the main file

    Returns:
        Path to the sidecar file (file_path + ".json")
    """
    return pathlib.Path(str(file_path) + ".json")


def move_file_with_sidecar(
    source: pathlib.Path, target: pathlib.Path, create_dirs: bool = True
) -> None:
    """
    Move a file and its sidecar (if exists) atomically.

    If the sidecar move fails, the main file is rolled back.

    Args:
        source: Source file path
        target: Target file path
        create_dirs: Whether to create target directories

    Raises:
        FileOperationError: If the operation fails
        FileNotFoundError: If source file doesn't exist
    """
    if not source.exists():
        raise FileNotFoundError(f"Source file does not exist: {source}")

    if target.exists():
        raise FileOperationError(f"Target file already exists: {target}")

    # Create target directory if needed
    if create_dirs:
        target.parent.mkdir(parents=True, exist_ok=True)

    source_sidecar = get_sidecar_path(source)
    target_sidecar = get_sidecar_path(target)

    try:
        # Move main file
        logger.info(f"Moving file: {source} -> {target}")
        shutil.move(str(source), str(target))

        # Move sidecar if exists
        if source_sidecar.exists():
            logger.info(f"Moving sidecar: {source_sidecar} -> {target_sidecar}")
            try:
                shutil.move(str(source_sidecar), str(target_sidecar))
            except Exception as e:
                # Rollback: move main file back
                logger.error(f"Failed to move sidecar, rolling back: {e}")
                shutil.move(str(target), str(source))
                raise FileOperationError(f"Failed to move sidecar: {e}") from e

    except FileOperationError:
        raise
    except Exception as e:
        raise FileOperationError(f"Failed to move file: {e}") from e


def rename_file_with_sidecar(file_path: pathlib.Path, new_name: str) -> pathlib.Path:
    """
    Rename a file and its sidecar (if exists).

    Args:
        file_path: Current file path
        new_name: New filename (without directory)

    Returns:
        New file path

    Raises:
        FileOperationError: If the operation fails
        FileNotFoundError: If source file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    target_path = file_path.parent / new_name

    if target_path.exists():
        raise FileOperationError(f"Target file already exists: {target_path}")

    move_file_with_sidecar(file_path, target_path, create_dirs=False)

    return target_path


def copy_file_with_sidecar(
    source: pathlib.Path, target: pathlib.Path, create_dirs: bool = True
) -> None:
    """
    Copy a file and its sidecar (if exists).

    Args:
        source: Source file path
        target: Target file path
        create_dirs: Whether to create target directories

    Raises:
        FileOperationError: If the operation fails
        FileNotFoundError: If source file doesn't exist
    """
    if not source.exists():
        raise FileNotFoundError(f"Source file does not exist: {source}")

    if target.exists():
        raise FileOperationError(f"Target file already exists: {target}")

    # Create target directory if needed
    if create_dirs:
        target.parent.mkdir(parents=True, exist_ok=True)

    source_sidecar = get_sidecar_path(source)
    target_sidecar = get_sidecar_path(target)

    try:
        # Copy main file
        logger.info(f"Copying file: {source} -> {target}")
        shutil.copy2(str(source), str(target))

        # Copy sidecar if exists
        if source_sidecar.exists():
            logger.info(f"Copying sidecar: {source_sidecar} -> {target_sidecar}")
            shutil.copy2(str(source_sidecar), str(target_sidecar))

    except Exception as e:
        # Cleanup on failure
        if target.exists():
            target.unlink()
        if target_sidecar.exists():
            target_sidecar.unlink()
        raise FileOperationError(f"Failed to copy file: {e}") from e


def delete_file_with_sidecar(file_path: pathlib.Path) -> None:
    """
    Delete a file and its sidecar (if exists).

    Args:
        file_path: Path to the file to delete

    Raises:
        FileOperationError: If the operation fails
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    sidecar_path = get_sidecar_path(file_path)

    try:
        logger.info(f"Deleting file: {file_path}")
        file_path.unlink()

        if sidecar_path.exists():
            logger.info(f"Deleting sidecar: {sidecar_path}")
            sidecar_path.unlink()

    except Exception as e:
        raise FileOperationError(f"Failed to delete file: {e}") from e

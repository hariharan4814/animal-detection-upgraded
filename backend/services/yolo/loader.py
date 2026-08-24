"""
YOLO Model Loader & Lifecycle Manager.
Provides lazy, cached loading of YOLOv8 Nano weights without redundant disk reads.
Handles missing weights, missing dependencies, and test mocking safely.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Any
from django.conf import settings

logger = logging.getLogger(__name__)

_cached_model: Optional[Any] = None
_model_load_attempted: bool = False
_model_error: Optional[str] = None


def get_model_path() -> Optional[Path]:
    """
    Resolves the filesystem path to the YOLO weights file (yolov8n.pt).
    Searches in configured settings, project backend root, and project parent root.
    """
    configured_path = getattr(settings, 'YOLO_MODEL_PATH', None)
    candidate_paths = [
        Path(configured_path) if configured_path else None,
        getattr(settings, 'BASE_DIR', Path('.')) / 'yolov8n.pt',
        getattr(settings, 'BASE_DIR', Path('.')).parent / 'yolov8n.pt',
        Path('yolov8n.pt'),
    ]

    for path in candidate_paths:
        if path and path.is_file():
            return path.resolve()

    return None


def get_model() -> Optional[Any]:
    """
    Retrieves the cached YOLO model singleton, initializing it lazily upon first request.
    Gracefully returns None if dependencies or weights are unavailable without crashing the application.
    """
    global _cached_model, _model_load_attempted, _model_error

    if _cached_model is not None:
        return _cached_model

    if _model_load_attempted and _model_error is not None:
        return None

    _model_load_attempted = True

    try:
        from ultralytics import YOLO
    except ImportError as e:
        _model_error = f"Ultralytics YOLO library not installed: {e}"
        logger.warning(_model_error)
        return None

    model_path = get_model_path()
    if not model_path:
        _model_error = "YOLO weights file (yolov8n.pt) not found on disk."
        logger.warning(_model_error)
        return None

    try:
        logger.info(f"Loading YOLO model from: {model_path}")
        _cached_model = YOLO(str(model_path))
        _model_error = None
        return _cached_model
    except Exception as e:
        _model_error = f"Failed to initialize YOLO model: {e}"
        logger.error(_model_error, exc_info=True)
        _cached_model = None
        return None


def is_model_available() -> bool:
    """Returns True if the YOLO model is loaded or capable of being loaded."""
    if _cached_model is not None:
        return True
    return get_model() is not None


def get_model_error() -> Optional[str]:
    """Returns the last encountered model loading error, if any."""
    return _model_error


def set_mock_model(mock_model: Any) -> None:
    """Injects a mock model instance for automated unit testing."""
    global _cached_model, _model_load_attempted, _model_error
    _cached_model = mock_model
    _model_load_attempted = True
    _model_error = None


def reset_model_cache() -> None:
    """Resets the singleton model cache back to uninitialized state."""
    global _cached_model, _model_load_attempted, _model_error
    _cached_model = None
    _model_load_attempted = False
    _model_error = None

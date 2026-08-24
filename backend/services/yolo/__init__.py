"""
YOLO Computer Vision Subsystem.
"""

from services.yolo.loader import get_model, is_model_available, set_mock_model, reset_model_cache
from services.yolo.inference import run_inference, ANIMAL_CLASSES

__all__ = [
    'get_model',
    'is_model_available',
    'set_mock_model',
    'reset_model_cache',
    'run_inference',
    'ANIMAL_CLASSES',
]

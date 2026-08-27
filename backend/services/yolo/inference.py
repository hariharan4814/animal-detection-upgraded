"""
YOLO Computer Vision Inference Engine.
Encapsulates animal detection, confidence filtering, threat scoring, and visual annotations.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

from services.yolo.loader import get_model
from services.threat_classification import (
    ThreatLevel,
    classify_animal,
    get_threat_score,
    DEFAULT_ANIMAL_THREAT_RULES,
)

logger = logging.getLogger(__name__)

# Verified animal target classes from legacy application and COCO dataset
ANIMAL_CLASSES = [
    'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear',
    'zebra', 'giraffe', 'lion', 'tiger', 'cheetah', 'monkey',
    'leopard', 'wolf', 'fox', 'deer', 'hippo', 'hyena',
    'jackal', 'kangaroo', 'squirrel', 'penguin', 'eagle',
    'owl', 'snake', 'crocodile', 'mouse', 'rat'
]

# Color palette for visual bounding box rendering (normalized lowercase or uppercase keys)
_CLASS_COLORS = {
    'high': (0, 0, 255),       # Red for high threat
    'HIGH': (0, 0, 255),
    'medium': (0, 165, 255),   # Orange for medium threat
    'MEDIUM': (0, 165, 255),
    'low': (0, 255, 0),        # Green for low threat
    'LOW': (0, 255, 0),
}


def run_inference(
    image: np.ndarray,
    confidence_threshold: float = 0.50,
    threat_levels: Optional[Dict[str, str]] = None,
    annotate: bool = True
) -> Dict[str, Any]:
    """
    Executes YOLO object detection on an image/frame array.

    :param image: Numpy array representing image in BGR (OpenCV format) or RGB.
    :param confidence_threshold: Minimum detection confidence score (0.0 to 1.0).
    :param threat_levels: Mapping of animal species to threat tier ('high', 'medium', 'low').
    :param annotate: If True, draws bounding boxes and labels on a copy of the image.
    :return: Dictionary containing parsed detections, threat assessment, and annotated image.
    """
    model = get_model()
    if model is None:
        return {
            "success": False,
            "error": "YOLO model is not available.",
            "detections": [],
            "highest_threat_animal": None,
            "highest_threat_level": None,
            "highest_conf": 0.0,
            "annotated_frame": image
        }

    threat_mapping = threat_levels or {}
    detections: List[Dict[str, Any]] = []
    highest_threat_animal: Optional[str] = None
    highest_threat_level: Optional[str] = None
    highest_conf: float = 0.0

    annotated_frame = image.copy() if (annotate and cv2 is not None) else image

    try:
        results = model(image, stream=False, verbose=False)
    except Exception as e:
        logger.error(f"Error during YOLO inference execution: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Inference execution failed: {e}",
            "detections": [],
            "highest_threat_animal": None,
            "highest_threat_level": None,
            "highest_conf": 0.0,
            "annotated_frame": image
        }

    threat_hierarchy = {'high': 3, 'medium': 2, 'low': 1}

    for r in results:
        boxes = getattr(r, 'boxes', None)
        if boxes is None:
            continue

        for box in boxes:
            try:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                
                # Resolve label name from model names dict
                if hasattr(model, 'names') and isinstance(model.names, dict):
                    label = model.names.get(cls_id, str(cls_id)).lower()
                elif hasattr(model, 'names') and isinstance(model.names, list) and cls_id < len(model.names):
                    label = model.names[cls_id].lower()
                else:
                    label = str(cls_id).lower()

                # Filter strictly by verified animal classes and minimum confidence
                if label in ANIMAL_CLASSES and conf >= confidence_threshold:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    threat_tier = classify_animal(label, conf, custom_overrides=threat_mapping)
                    threat_lower = threat_tier.lower()

                    detections.append({
                        "label": label,
                        "confidence": round(conf, 4),
                        "threat_level": threat_lower,
                        "threat_tier": threat_tier,
                        "box": [x1, y1, x2, y2]
                    })

                    # Evaluate highest threat priority
                    current_threat_score = get_threat_score(threat_tier)
                    highest_threat_score = get_threat_score(highest_threat_level) if highest_threat_level else 0

                    if current_threat_score > highest_threat_score or (current_threat_score == highest_threat_score and conf > highest_conf):
                        highest_threat_animal = label
                        highest_threat_level = threat_lower
                        highest_conf = conf

                    # Annotate frame if OpenCV is available
                    if annotate and cv2 is not None:
                        color = _CLASS_COLORS.get(threat_tier, (0, 255, 0))
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                        label_text = f"{label.capitalize()} {conf:.2f} [{threat_tier}]"
                        cv2.putText(
                            annotated_frame,
                            label_text,
                            (x1, max(y1 - 10, 20)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            color,
                            2
                        )
            except Exception as box_err:
                logger.warning(f"Error parsing individual detection box: {box_err}")
                continue

    return {
        "success": True,
        "detections": detections,
        "highest_threat_animal": highest_threat_animal,
        "highest_threat_level": highest_threat_level,
        "highest_conf": round(highest_conf, 4) if highest_conf else 0.0,
        "annotated_frame": annotated_frame
    }

# FarmSync Camera & Live Monitoring REST API Specification (Step 13)

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 13 – Camera & Live Monitoring Integration  
**Date**: August 2026  
**Status**: ACTIVE & VERIFIED  

---

## 1. Architectural Summary & Scope

The **Camera & Live Monitoring Subsystem** (`apps.detection` & `services.yolo`) provides real-time multipart MJPEG video streaming integrated with OpenCV device acquisition, dynamic `ProjectSettings` synchronization, and YOLOv8 object detection.

### Key Architectural Decisions:
1. **Reuse of Existing Step 10 Detection & Streaming Architecture**: Reuses `VideoStreamService` and `DetectionStreamView` (`GET /api/v1/detection/stream/`). No redundant camera apps, duplicate models, or duplicate YOLO pipelines were created.
2. **Single Source of Truth Configuration**: Reads `camera_device_index`, `detection_enabled`, `detection_confidence_threshold`, and `threat_level_overrides` dynamically from `ProjectSettings` (`apps.settings_app.models.ProjectSettings`).
3. **Safe Resource Management**: Camera acquisition is wrapped in strict `try/finally` blocks, ensuring OpenCV `VideoCapture.release()` is always called upon client disconnection or generator termination.
4. **Headless & Hardware-Independent Fallback**: When physical camera hardware is absent or fails to open, `VideoStreamService` generates simulated synthetic video frames ("FarmSync Camera Stream Active") so automated tests, containerized environments, and cloud servers run without crashing.
5. **Detection Enabled/Disabled Semantics**: When `detection_enabled=True`, frames are analyzed in real time with bounding boxes and labels drawn. When `detection_enabled=False`, live frames stream continuously in raw form without running YOLO inference, creating animal logs, or dispatching alerts.

---

## 2. Legacy Evidence Audit & Classification Matrix

| Behavior | Legacy Evidence | Existing Django Implementation | Classification |
|---|---|---|---|
| **Camera View Route** | `GET /camera` in `app.py:53` rendering `templates/camera.html` | React / Frontend endpoint | **LEGACY-DERIVED** |
| **Live Stream Route** | `GET /video_feed` in `app.py:68` | `GET /api/v1/detection/stream/` | **LEGACY-DERIVED & ENHANCED** |
| **Stream Content-Type** | `multipart/x-mixed-replace; boundary=frame` in `app.py:71` | `multipart/x-mixed-replace; boundary=frame` in `DetectionStreamView` | **LEGACY-DERIVED** |
| **OpenCV Device Acquisition** | `cv2.VideoCapture(0)` in `modules/animal_detection.py:98` | `cv2.VideoCapture(settings.camera_device_index)` in `VideoStreamService` | **LEGACY-DERIVED & ENHANCED** |
| **Frame Read Failure Recovery** | `if not ret: break` in `modules/animal_detection.py:122` | Safe loop exit + synthetic frame fallback | **LEGACY-DERIVED & ENHANCED** |
| **Camera Release Cleanup** | `self.VIDEO.release()` in `modules/animal_detection.py:104` | `finally: cap.release()` in `VideoStreamService` | **LEGACY-DERIVED & ENHANCED** |
| **Real-time YOLO Inference** | `self.DETECTOR.detect_animals(frame)` in `modules/animal_detection.py:125` | `run_inference(...)` in `VideoStreamService` | **LEGACY-DERIVED** |
| **Visual Bounding Box Annotations** | `cv2.rectangle` + label in `modules/animal_detection.py:67` | Bounding boxes + species labels in `services.yolo.inference` | **LEGACY-DERIVED** |
| **Detection Disabled Stream** | Raw frames yielded when `_detect == False` in `modules/animal_detection.py:124` | Raw frames yielded when `detection_enabled == False` | **LEGACY-DERIVED** |
| **Camera Toggle State** | `GET /toggle_camera` in `app.py:78` | Controlled via settings and camera feed status | **LEGACY-DERIVED** |

---

## 3. Endpoints Reference

Base path: `/api/v1/detection/`

| Method | Endpoint | Authorization | Description | Classification |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/detection/stream/` | Authenticated | Live multipart MJPEG video stream feed (`Content-Type: multipart/x-mixed-replace; boundary=frame`). | **LEGACY-DERIVED & ENHANCED** |
| `GET` | `/api/v1/detection/status/` | Authenticated | Engine status, camera device index, active thresholds, and species support. | **NEW DJANGO ENHANCEMENT** |
| `PATCH` | `/api/v1/detection/status/` | Staff / Admin | Master toggle for real-time AI animal detection. | **LEGACY-DERIVED & ENHANCED** |

---

## 4. Frame Processing Pipeline

```
Camera Frame / Simulated Canvas
        ↓
Read Active ProjectSettings (camera_device_index, detection_enabled, threshold)
        ↓
Check detection_enabled
   ├── [True]  → Run cached YOLO inference → Apply species threat scoring → Annotate Bounding Boxes
   └── [False] → Skip inference (yield raw camera frame)
        ↓
Encode Frame as JPEG (.jpg)
        ↓
Yield multipart/x-mixed-replace HTTP chunk
        ↓
On disconnect / loop exit: Call cap.release() in finally block
```

---

## 5. Security & Hardware Independence

1. **Authentication**: Accessing `GET /api/v1/detection/stream/` requires a valid authentication token (`HTTP 401 Unauthorized` for unauthenticated clients).
2. **Resource Cleanup**: Guaranteed resource release via `finally: cap.release()`.
3. **Hardware Independence**: Full test suite runs 100% without physical camera hardware, GPU, or downloading model weights.

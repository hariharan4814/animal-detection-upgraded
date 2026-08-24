# Backend Core Services Engine (`backend/services/`)

**Layer**: Isolated Non-Web Service Subsystems  
**Status**: SERVICE DIRECTORY FOUNDATION INITIALIZED  

---

## Purpose

The `services/` directory contains isolated, standalone Python service modules that manage heavy computational, hardware, and asynchronous background tasks outside the Django HTTP request/response cycle:

1. **`services/yolo/`**:
   - Deep learning YOLOv8 model lifecycle management.
   - Singleton model loader and inference execution.
   - Bounding box rendering and threat level scoring.
   - *Scheduled Migration*: Step 10.

2. **`services/camera/`**:
   - Hardware camera capture management (OpenCV `cv2.VideoCapture`).
   - Thread-safe frame acquisition with `threading.Lock`.
   - MJPEG multipart byte stream generator.
   - *Scheduled Migration*: Step 11.

3. **`services/notifications/`**:
   - Asynchronous SMTP email dispatcher with MIME snapshot and audio attachments.
   - Headless-safe host machine audio buzzer player.
   - Background event worker to ensure zero frame latency during live video streaming.
   - *Scheduled Migration*: Step 13.

---

> **Rule**: Service modules must remain stateless or manage concurrency safely via explicit thread locking. They must not depend on Django view objects or HTTP request contexts.

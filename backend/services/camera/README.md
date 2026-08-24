# Camera Hardware & Streaming Service (`backend/services/camera/`)

**Subsystem**: Hardware Video Capture & Frame Streaming  
**Status**: SERVICE FOUNDATION INITIALIZED  

---

## Future Service Responsibilities
When migrated in **Step 11**, this service will encapsulate:
1. **Thread-Safe Capture Management**: Managing OpenCV `cv2.VideoCapture(0)` with explicit thread locking (`threading.Lock`) to prevent camera device locking across multiple WSGI worker processes.
2. **Lifecycle Control**: Exposing safe `start()`, `stop()`, `reset()`, and `status()` controls.
3. **MJPEG Stream Generation**: Encoding frame buffers into continuous multipart JPEG byte streams for consumption by `<img src="/api/detection/camera/stream/" />`.
4. **Subscriber Fan-Out**: Broadcasting captured frames to multiple simultaneous web clients without multiple hardware reads.

> **Note**: No OpenCV camera code is migrated during Step 1.

# YOLO Detection Service (`backend/services/yolo/`)

**Subsystem**: Computer Vision & AI Inference  
**Status**: SERVICE FOUNDATION INITIALIZED  

---

## Future Service Responsibilities
When migrated in **Step 10**, this service will encapsulate:
1. **Model Lifecycle Management**: Lazy Singleton loading of YOLOv8 Nano weights (`yolov8n.pt`).
2. **Inference Execution**: Non-blocking frame inference on incoming camera frames.
3. **Bounding Box & Label Rendering**: Overlaying colored bounding boxes and confidence scores.
4. **Dynamic Threat Scoring**: Evaluating detected animal species against runtime threat levels stored in the `settings_app` database.
5. **Cooldown Management**: Preventing duplicate notification triggers within the configured cooldown window.

> **Note**: No YOLO code is migrated during Step 1.

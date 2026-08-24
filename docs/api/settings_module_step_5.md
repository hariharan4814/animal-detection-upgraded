# FarmSync Settings Module Specification (Step 5)

**Project**: FarmSync / Intelligent Animal Detection System  
**Stage**: STEP 5 – Dynamic Settings Module & Configuration APIs  
**Date**: August 2026  
**Status**: ACTIVE & VERIFIED  

---

## 1. Purpose of the Settings Module

The **Settings Module** (`apps.settings_app`) is the centralized configuration engine for the FarmSync system. It provides database-backed, runtime-configurable parameters for:
1. **Outgoing SMTP Email Configuration**: Sender credentials, host, port, TLS/SSL flags.
2. **Alert Notification Recipients**: Managing farm managers, field guards, and supervisors who receive real-time hazard alerts.
3. **Dynamic Project & Vision Parameters**: YOLO detection confidence thresholds, cooldown durations between alerts, hardware camera indices, standard shift hours, and species threat classifications.
4. **Administrative Security**: Role-based access control protecting critical settings from unauthorized tampering.

---

## 2. Legacy Configuration Findings vs. New Django Capabilities

### 2.1 Legacy Configuration (`config.json` & `app.py`)
- In the legacy prototype, SMTP credentials were hard-coded in plain text directly inside `app.py` in an `EMAIL_CONFIG` dictionary.
- Animal threat level classifications were stored in a static JSON file (`config.json`).
- Cooldown (60 seconds), camera index (0), and confidence threshold (0.50) were hard-coded in python scripts.
- Modifying any setting required restarting the Flask web server and editing source code.

### 2.2 New Django Dynamic Customization
- Settings are persisted in relational database models (`EmailSenderConfig`, `AlertReceiver`, `ProjectSettings`).
- Administrators can modify settings at runtime via authenticated REST APIs without restarting the server.
- Passwords are completely write-only and never returned across the network.
- Receivers can be individually toggled active/disabled.

---

## 3. Sensitive Credential Policy

> 🔒 **SECURITY GUARANTEE**:  
> **SMTP passwords are write-only and never returned by the API.**  
> When querying `/api/v1/settings/email-sender/`, the API returns `"smtp_password_configured": true` to indicate that a secret is stored, without disclosing any portion of the password or hash. When updating configuration without providing a new password, the existing stored password is automatically preserved.

---

## 4. API Endpoints Reference

All endpoints are namespaced under `/api/v1/settings/`:

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/settings/email-sender/` | Staff / Admin | Retrieves active SMTP configuration (masked password). |
| `PUT` | `/api/v1/settings/email-sender/` | Staff / Admin | Updates active SMTP configuration (partial update supported). |
| `GET` | `/api/v1/settings/receivers/` | Authenticated | Lists all alert recipients. |
| `POST` | `/api/v1/settings/receivers/` | Staff / Admin | Registers a new alert recipient. |
| `GET` | `/api/v1/settings/receivers/{id}/` | Authenticated | Retrieves details of a specific alert recipient. |
| `PUT` | `/api/v1/settings/receivers/{id}/` | Staff / Admin | Updates an alert recipient (e.g. enable/disable). |
| `DELETE` | `/api/v1/settings/receivers/{id}/` | Staff / Admin | Deletes an alert recipient. |
| `GET` | `/api/v1/settings/project/` | Authenticated | Retrieves runtime project parameters and thresholds. |
| `PUT` | `/api/v1/settings/project/` | Staff / Admin | Updates project parameters and thresholds. |

---

## 5. Request & Response Examples

### 5.1 Email Sender Configuration
- **Request (`PUT /api/v1/settings/email-sender/`)**:
  ```json
  {
    "sender_name": "FarmSync Central Dispatcher",
    "sender_email": "alerts@farmsync.org",
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_password": "my-secret-app-password",
    "use_tls": true
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Email sender configuration updated successfully.",
    "data": {
      "id": 1,
      "sender_name": "FarmSync Central Dispatcher",
      "sender_email": "alerts@farmsync.org",
      "smtp_host": "smtp.gmail.com",
      "smtp_port": 587,
      "smtp_username": null,
      "smtp_password_configured": true,
      "use_tls": true,
      "use_ssl": false,
      "is_active": true,
      "created_at": "2026-08-24T12:00:00Z",
      "updated_at": "2026-08-24T13:00:00Z"
    }
  }
  ```

---

### 5.2 Alert Receivers
- **Request (`POST /api/v1/settings/receivers/`)**:
  ```json
  {
    "name": "Field Supervisor",
    "email": "supervisor@farmsync.org",
    "is_active": true,
    "receive_animal_alerts": true,
    "receive_attendance_reports": false
  }
  ```
- **Response (`201 Created`)**:
  ```json
  {
    "success": true,
    "message": "Alert receiver created successfully.",
    "data": {
      "id": 2,
      "name": "Field Supervisor",
      "email": "supervisor@farmsync.org",
      "is_active": true,
      "receive_animal_alerts": true,
      "receive_attendance_reports": false,
      "created_at": "2026-08-24T13:05:00Z",
      "updated_at": "2026-08-24T13:05:00Z"
    }
  }
  ```

---

### 5.3 Project Settings
- **Request (`PUT /api/v1/settings/project/`)**:
  ```json
  {
    "system_name": "FarmSync AI Security",
    "alert_cooldown_seconds": 90,
    "detection_confidence_threshold": 0.60,
    "wage_per_hour": 18.0,
    "threat_level_overrides": {
      "wolf": "high",
      "deer": "low",
      "wild boar": "medium"
    }
  }
  ```
- **Response (`200 OK`)**:
  ```json
  {
    "success": true,
    "message": "Project settings updated successfully.",
    "data": {
      "id": 1,
      "system_name": "FarmSync AI Security",
      "alert_cooldown_seconds": 90,
      "detection_confidence_threshold": 0.60,
      "camera_device_index": 0,
      "work_start_time": "08:00:00",
      "wage_per_hour": 18.0,
      "detection_enabled": true,
      "audio_buzzer_enabled": true,
      "email_alerts_enabled": true,
      "threat_level_overrides": {
        "wolf": "high",
        "deer": "low",
        "wild boar": "medium"
      },
      "created_at": "2026-08-24T12:00:00Z",
      "updated_at": "2026-08-24T13:10:00Z"
    }
  }
  ```

---

## 6. Authorization Policy

1. **Email Sender Configuration**: Strictly restricted to staff and superusers (`IsAdminUserOnly`). Regular workers attempting to access or modify SMTP settings receive `403 Forbidden`.
2. **Alert Receivers & Project Settings**: Authenticated users have read access (`GET`), while write operations (`POST`, `PUT`, `DELETE`) require staff privileges (`IsAdminOrReadOnly`).
3. **Privilege Escalation Protection**: Regular users cannot alter user roles or permissions through settings endpoints.

---

## 7. Future Service Integration

- **Step 10 & 11 (Vision & Camera)**: Will query `ProjectSettings.get_settings()` dynamically for `detection_confidence_threshold`, `alert_cooldown_seconds`, and `camera_device_index`.
- **Step 13 (Notifications)**: Will query `EmailSenderConfig.get_active_config()` and `AlertReceiver.objects.filter(is_active=True, receive_animal_alerts=True)` to dispatch real-time alerts.

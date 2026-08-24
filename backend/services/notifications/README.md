# Notifications & Alerts Service (`backend/services/notifications/`)

**Subsystem**: Alert Delivery, Email Dispatch & Audio Buzzer  
**Status**: SERVICE FOUNDATION INITIALIZED  

---

## Future Service Responsibilities
When migrated in **Step 13**, this service will encapsulate:
1. **Asynchronous SMTP Email Dispatch**: Assembling MIME multipart emails with attached animal snapshot JPEGs and audio files, transmitting them via background threads to eliminate video frame freezes.
2. **Dynamic Credential Resolution**: Retrieving SMTP configuration securely from `settings_app` database models and `.env` environment variables without exposing secrets.
3. **Headless-Safe Audio Buzzer**: Executing local `pygame.mixer` audio playback with automated fallback checks for headless/cloud server environments.
4. **Attendance Notifications**: Sending personalized check-in/out confirmation emails to farm workers upon attendance logging.

> **Note**: No alert logic or credentials are migrated during Step 1.

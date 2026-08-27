/**
 * TypeScript contracts for the FarmSync Django REST Framework backend (/api/v1).
 * Aligned with backend serializers, threat classification, and domain models.
 */

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  errors?: Record<string, unknown>;
}

export interface User {
  id: number;
  username: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  is_staff?: boolean;
  is_superuser?: boolean;
  date_joined?: string;
  last_login?: string | null;
  role?: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user?: User;
}

export interface Farmer {
  id: number;
  name: string;
  phone: string;
  field: string;
  email?: string | null;
  created_at?: string;
  updated_at?: string;
}

export type FarmerInput = {
  name: string;
  phone: string;
  field: string;
  email?: string;
};

export interface AttendanceRecord {
  id: number;
  farmer: number;
  farmer_name?: string;
  date?: string;
  check_in?: string | null;
  check_out?: string | null;
  total_hours?: number | null;
  location?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface AttendanceReportData {
  start_date: string | null;
  end_date: string | null;
  farmer_id: number | null;
  total_records: number;
  total_hours_sum: number;
  records: AttendanceRecord[];
}

export type TaskStatus = "Pending" | "Completed";

export interface Task {
  id: number;
  task_name: string;
  assigned_to?: number | null;
  assigned_to_name?: string | null;
  status: TaskStatus;
  date?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface TaskInput {
  task_name: string;
  assigned_to?: number | null;
  status?: TaskStatus;
  date?: string;
}

export interface DashboardSummary {
  date?: string;
  farmers?: {
    total_farmers: number;
  };
  attendance?: {
    today_attendance: number;
    total_records: number;
  };
  tasks?: {
    total_tasks: number;
    completed_tasks: number;
    pending_tasks: number;
  };
  detections?: {
    detections_today: number;
    total_detections: number;
    high_threat_detections?: number;
    medium_threat_detections?: number;
    low_threat_detections?: number;
  };
  alerts?: {
    alerts_today: number;
    total_alerts: number;
    triggered_alerts: number;
    high_threat_alerts?: number;
    medium_threat_alerts?: number;
    low_threat_alerts?: number;
  };
  [key: string]: unknown;
}

export interface RecentAlertItem {
  id: number;
  animal_type: string;
  threat_level?: "HIGH" | "MEDIUM" | "LOW" | string;
  alert_type: string;
  status: string;
  image_path?: string | null;
  timestamp: string;
}

export interface RecentDetectionItem {
  id: number;
  animal_type: string;
  threat_level?: "HIGH" | "MEDIUM" | "LOW" | string;
  confidence: number | null;
  field: string;
  image_path: string;
  timestamp: string;
}

export interface RecentTaskItem {
  id: number;
  task_name: string;
  assigned_to_name?: string | null;
  status: string;
  date: string;
}

export interface DashboardRecentActivity {
  recent_alerts: RecentAlertItem[];
  recent_detections: RecentDetectionItem[];
  recent_tasks: RecentTaskItem[];
}

export interface ActivityItem {
  id?: number | string;
  type?: string;
  message?: string;
  description?: string;
  threat_level?: string;
  image_path?: string | null;
  timestamp?: string;
  created_at?: string;
  badge?: string;
  badgeVariant?: "default" | "secondary" | "destructive" | "outline";
  [key: string]: unknown;
}

export interface DetectionStatus {
  detection_enabled: boolean;
  engine_available?: boolean;
  model_name?: string;
  confidence_threshold?: number;
  camera_device_index?: number;
  alert_cooldown_seconds?: number;
  audio_buzzer_enabled?: boolean;
  email_alerts_enabled?: boolean;
  attach_alert_image_to_email?: boolean;
  supported_classes_count?: number;
  supported_classes?: string[];
  camera_active?: boolean;
  message?: string;
  [key: string]: unknown;
}

export interface DetectionItem {
  animal?: string;
  animal_type?: string;
  label?: string;
  confidence?: number;
  threat_level?: "high" | "medium" | "low" | string;
  threat_tier?: "HIGH" | "MEDIUM" | "LOW" | string;
  box?: number[];
  [key: string]: unknown;
}

export interface DetectionLog {
  id: number;
  animal_type: string;
  confidence: number;
  threat_level?: "HIGH" | "MEDIUM" | "LOW" | string;
  timestamp: string;
  field: string;
  image_path?: string | null;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export interface AnalyzeResult {
  success?: boolean;
  detection_enabled?: boolean;
  animal_detected?: boolean;
  detections_count?: number;
  detections?: DetectionItem[];
  highest_threat_animal?: string;
  highest_threat_level?: string;
  highest_threat_tier?: string;
  highest_confidence?: number;
  animal_log?: DetectionLog;
  alert_triggered?: boolean;
  alert_type?: string;
  alert_id?: number | null;
  email_notifications_enabled?: boolean;
  email_attempted?: boolean;
  email_sent?: boolean;
  email_status?: "sent" | "failed" | "disabled" | "cooldown" | "none" | string;
  message?: string;
  [key: string]: unknown;
}

export interface HazardAlert {
  id: number;
  animal_log?: number | null;
  animal_type?: string;
  confidence?: number | null;
  threat_level?: "HIGH" | "MEDIUM" | "LOW" | string;
  field?: string;
  image_path?: string | null;
  download_url?: string | null;
  detection_timestamp?: string | null;
  alert_type?: string;
  status?: string;
  email_sent?: boolean;
  buzzer_triggered?: boolean;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export interface ProjectSettings {
  id?: number;
  system_name: string;
  alert_cooldown_seconds: number;
  detection_confidence_threshold: number;
  camera_device_index: number;
  work_start_time: string;
  wage_per_hour: number | string;
  detection_enabled: boolean;
  audio_buzzer_enabled: boolean;
  email_alerts_enabled: boolean;
  attach_alert_image_to_email?: boolean;
  threat_level_overrides: Record<string, "high" | "medium" | "low">;
  created_at?: string;
  updated_at?: string;
}

export interface EmailSenderConfig {
  id?: number;
  sender_name?: string;
  sender_email?: string;
  smtp_host?: string;
  smtp_port?: number;
  smtp_username?: string;
  smtp_password?: string;
  smtp_password_configured?: boolean;
  use_tls?: boolean;
  use_ssl?: boolean;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export interface AlertReceiver {
  id: number;
  name?: string;
  email: string;
  is_active?: boolean;
  receive_animal_alerts?: boolean;
  receive_attendance_reports?: boolean;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export interface AnimalThreatRule {
  id: number;
  animal_name: string;
  threat_level: "HIGH" | "MEDIUM" | "LOW";
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ThreatEmailTemplate {
  id: number;
  threat_level: "HIGH" | "MEDIUM" | "LOW";
  subject_template: string;
  body_template: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface TemplatePreviewInput {
  threat_level: "HIGH" | "MEDIUM" | "LOW";
  subject_template?: string;
  body_template?: string;
  sample_animal_name?: string;
  sample_confidence?: number;
  sample_camera_name?: string;
  sample_alert_id?: string;
}

export interface TemplatePreviewResult {
  success: boolean;
  threat_level: string;
  subject: string;
  body: string;
  context?: Record<string, string>;
  error?: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

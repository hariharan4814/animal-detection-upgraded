import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { UseQueryOptions } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  api,
  apiRequest,
  humanizeError,
  normalizeAlert,
  normalizeDetectionLog,
  normalizeDetectionResponse,
  toList,
} from "@/lib/api";
import { toDate } from "@/lib/format";
import type {
  ActivityItem,
  AlertReceiver,
  AnalyzeResult,
  AnimalThreatRule,
  AttendanceRecord,
  AttendanceReportData,
  DashboardRecentActivity,
  DashboardSummary,
  DetectionLog,
  DetectionStatus,
  EmailSenderConfig,
  Farmer,
  FarmerInput,
  HazardAlert,
  Paginated,
  ProjectSettings,
  Task,
  TaskInput,
  TemplatePreviewInput,
  TemplatePreviewResult,
  ThreatEmailTemplate,
} from "@/types/api";

type ListResponse<T> = Paginated<T> | T[];

function listQuery<T>(key: unknown[], path: string, options?: Partial<UseQueryOptions<T[]>>) {
  return {
    queryKey: key,
    queryFn: async () => toList(await api.get<ListResponse<T>>(path)),
    ...options,
  };
}

/* ---------------- Dashboard ---------------- */

export function useDashboardSummary() {
  return useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: () => api.get<DashboardSummary>("/dashboard/summary/"),
    refetchInterval: 5000,
    refetchOnWindowFocus: true,
    staleTime: 3000,
  });
}

export function useRecentActivity() {
  return useQuery({
    queryKey: ["dashboard", "activity"],
    queryFn: async (): Promise<ActivityItem[]> => {
      const raw = await api.get<DashboardRecentActivity>("/dashboard/recent-activity/");
      const items: ActivityItem[] = [];

      if (raw.recent_alerts && Array.isArray(raw.recent_alerts)) {
        for (const a of raw.recent_alerts) {
          const threat = a.threat_level ? ` [${a.threat_level}]` : "";
          items.push({
            id: `alert-${a.id}`,
            type: "Alert",
            message: `Hazard Alert: ${a.animal_type}${threat} (${a.alert_type})`,
            threat_level: a.threat_level,
            image_path: a.image_path,
            timestamp: a.timestamp,
            badge: a.threat_level || a.status,
            badgeVariant: a.threat_level === "HIGH" ? "destructive" : "secondary",
          });
        }
      }

      if (raw.recent_detections && Array.isArray(raw.recent_detections)) {
        for (const d of raw.recent_detections) {
          const conf = d.confidence !== null ? ` (${Math.round(d.confidence * 100)}%)` : "";
          const threat = d.threat_level ? ` [${d.threat_level}]` : "";
          items.push({
            id: `detection-${d.id}`,
            type: "Detection",
            message: `AI Detection: ${d.animal_type}${threat}${conf} in ${d.field}`,
            threat_level: d.threat_level,
            image_path: d.image_path,
            timestamp: d.timestamp,
            badge: d.threat_level || "Detection",
            badgeVariant: d.threat_level === "HIGH" ? "destructive" : "default",
          });
        }
      }

      if (raw.recent_tasks && Array.isArray(raw.recent_tasks)) {
        for (const t of raw.recent_tasks) {
          items.push({
            id: `task-${t.id}`,
            type: "Task",
            message: `Task: ${t.task_name} (${t.status})`,
            description: t.assigned_to_name ? `Assigned to ${t.assigned_to_name}` : undefined,
            timestamp: t.date,
            badge: t.status,
            badgeVariant: t.status === "Completed" ? "secondary" : "outline",
          });
        }
      }

      // Sort chronological descending
      items.sort((a, b) => {
        const timeA = a.timestamp ? (toDate(a.timestamp)?.getTime() ?? 0) : 0;
        const timeB = b.timestamp ? (toDate(b.timestamp)?.getTime() ?? 0) : 0;
        return timeB - timeA;
      });

      return items;
    },
    refetchInterval: 5000,
    refetchOnWindowFocus: true,
    staleTime: 3000,
  });
}

/* ---------------- Farmers ---------------- */

export function useFarmers() {
  return useQuery({
    ...listQuery<Farmer>(["farmers"], "/farmers/"),
    refetchInterval: 12000,
    refetchOnWindowFocus: true,
    staleTime: 6000,
  });
}

export function useFarmerMutations() {
  const qc = useQueryClient();
  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ["farmers"] });
    void qc.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const create = useMutation({
    mutationFn: (input: FarmerInput) => api.post<Farmer>("/farmers/", input),
    onSuccess: () => {
      invalidate();
      toast.success("Farmer created successfully");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });

  const update = useMutation({
    mutationFn: ({ id, input }: { id: number; input: Partial<FarmerInput> }) =>
      api.patch<Farmer>(`/farmers/${id}/`, input),
    onSuccess: () => {
      invalidate();
      toast.success("Farmer updated successfully");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.delete<null>(`/farmers/${id}/`),
    onSuccess: () => {
      invalidate();
      toast.success("Farmer deleted successfully");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });

  return { create, update, remove };
}

/* ---------------- Attendance ---------------- */

export function useAttendance() {
  return useQuery({
    ...listQuery<AttendanceRecord>(["attendance"], "/attendance/"),
    refetchInterval: 8000,
    refetchOnWindowFocus: true,
    staleTime: 4000,
  });
}

export function useAttendanceReport(filters?: {
  start_date?: string;
  end_date?: string;
  farmer_id?: number;
}) {
  const params = new URLSearchParams();
  if (filters?.start_date) params.set("start_date", filters.start_date);
  if (filters?.end_date) params.set("end_date", filters.end_date);
  if (filters?.farmer_id) params.set("farmer_id", String(filters.farmer_id));
  const queryString = params.toString() ? `?${params.toString()}` : "";

  return useQuery({
    queryKey: ["attendance", "report", filters],
    queryFn: () => api.get<AttendanceReportData>(`/attendance/report/${queryString}`),
  });
}

export function useAttendanceActions() {
  const qc = useQueryClient();
  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ["attendance"] });
    void qc.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const checkIn = useMutation({
    mutationFn: ({ farmer_id, location }: { farmer_id: number; location?: string }) =>
      api.post<AttendanceRecord>("/attendance/check-in/", {
        farmer_id,
        ...(location ? { device_location: location } : {}),
      }),
    onSuccess: () => {
      invalidate();
      toast.success("Check-in recorded successfully");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });

  const checkOut = useMutation({
    mutationFn: (payload: {
      farmer_id?: number;
      attendance_id?: number;
      work_description: string;
      location?: string;
      check_out_time?: string;
      date?: string;
    }) =>
      api.post<AttendanceRecord>("/attendance/check-out/", {
        ...(payload.farmer_id ? { farmer_id: payload.farmer_id } : {}),
        ...(payload.attendance_id ? { attendance_id: payload.attendance_id } : {}),
        work_description: payload.work_description,
        ...(payload.location ? { device_location: payload.location } : {}),
        ...(payload.check_out_time ? { check_out_time: payload.check_out_time } : {}),
        ...(payload.date ? { date: payload.date } : {}),
      }),
    onSuccess: (data) => {
      invalidate();
      if (data?.email_sent) {
        toast.success("Attendance Completed", {
          description: "Work shift recorded and email report sent to worker and administrator.",
        });
      } else if (data?.email_error) {
        toast.warning("Attendance Recorded", {
          description: "Shift saved, but the email report could not be delivered.",
        });
      } else {
        toast.success("Check-out recorded successfully");
      }
    },
    onError: (e) => toast.error(humanizeError(e)),
  });

  return { checkIn, checkOut };
}

/* ---------------- Tasks ---------------- */

export function useTasks() {
  return useQuery({
    ...listQuery<Task>(["tasks"], "/tasks/"),
    refetchInterval: 8000,
    refetchOnWindowFocus: true,
    staleTime: 4000,
  });
}

export function useTaskMutations() {
  const qc = useQueryClient();
  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ["tasks"] });
    void qc.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const create = useMutation({
    mutationFn: (input: TaskInput) => api.post<Task>("/tasks/", input),
    onSuccess: () => {
      invalidate();
      toast.success("Task created successfully");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });

  const update = useMutation({
    mutationFn: ({ id, input }: { id: number; input: Partial<TaskInput> }) =>
      api.patch<Task>(`/tasks/${id}/`, input),
    onSuccess: () => {
      invalidate();
      toast.success("Task updated successfully");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.delete<null>(`/tasks/${id}/`),
    onSuccess: () => {
      invalidate();
      toast.success("Task deleted successfully");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });

  return { create, update, remove };
}

/* ---------------- Detection ---------------- */

export function useDetectionStatus() {
  return useQuery({
    queryKey: ["detection", "status"],
    queryFn: () => api.get<DetectionStatus>("/detection/status/"),
    refetchInterval: 8000,
    refetchOnWindowFocus: true,
    staleTime: 4000,
  });
}

export function useToggleDetection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (enabled: boolean) =>
      api.patch<DetectionStatus>("/detection/status/", { detection_enabled: enabled }),
    onSuccess: (data) => {
      qc.setQueryData(["detection", "status"], data);
      void qc.invalidateQueries({ queryKey: ["detection", "status"] });
      toast.success(
        data.detection_enabled ? "AI detection engine enabled" : "AI detection engine disabled",
      );
    },
    onError: (e) => toast.error(humanizeError(e)),
  });
}

export function useAnalyzeImage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, fieldName = "Main Field" }: { file: File; fieldName?: string }) => {
      const form = new FormData();
      form.append("image", file);
      form.append("field", fieldName);
      const res = await apiRequest<unknown>("/detection/analyze/", { method: "POST", body: form });
      return normalizeDetectionResponse(res);
    },
    onSuccess: (data) => {
      void qc.invalidateQueries({ queryKey: ["detection", "logs"] });
      void qc.invalidateQueries({ queryKey: ["alerts"] });
      void qc.invalidateQueries({ queryKey: ["dashboard"] });
      void qc.invalidateQueries({ queryKey: ["detection", "status"] });
      if (data.alert_triggered) {
        toast.warning(
          `Hazard alert triggered: ${data.highest_threat_animal ?? "Intruder"} (${data.alert_type ?? "Alert"})`,
        );
      } else {
        toast.success("Image analysis completed");
      }
    },
    onError: (e) => toast.error(humanizeError(e)),
  });
}

export function useDetectionLogs() {
  return useQuery({
    queryKey: ["detection", "logs"],
    queryFn: async () => {
      const raw = await api.get<ListResponse<DetectionLog>>("/detection/logs/");
      const list = toList(raw);
      return list.map(normalizeDetectionLog);
    },
    refetchInterval: 5000,
    refetchOnWindowFocus: true,
    staleTime: 3000,
  });
}

/* ---------------- Alerts ---------------- */

export function useAlerts() {
  return useQuery({
    queryKey: ["alerts"],
    queryFn: async () => {
      const raw = await api.get<ListResponse<HazardAlert>>("/alerts/");
      const list = toList(raw);
      return list.map(normalizeAlert);
    },
    refetchInterval: 5000,
    refetchOnWindowFocus: true,
    staleTime: 3000,
  });
}

export function useDeleteAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete<null>(`/alerts/${id}/`),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["alerts"] });
      void qc.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Alert and evidence record deleted successfully");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });
}

/* ---------------- Settings & Configurations ---------------- */

export function useSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: () => api.get<ProjectSettings>("/settings/"),
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: Partial<ProjectSettings>) =>
      api.patch<ProjectSettings>("/settings/", input),
    onSuccess: (data) => {
      qc.setQueryData(["settings"], data);
      void qc.invalidateQueries({ queryKey: ["detection", "status"] });
      toast.success("Project settings saved successfully");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });
}

export function useEmailSender() {
  return useQuery({
    queryKey: ["settings", "email-sender"],
    queryFn: () => api.get<EmailSenderConfig>("/settings/email-sender/"),
  });
}

export function useUpdateEmailSender() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: Partial<EmailSenderConfig>) =>
      api.put<EmailSenderConfig>("/settings/email-sender/", input),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["settings", "email-sender"] });
      toast.success("Email sender configuration updated successfully");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });
}

export function useReceivers() {
  return useQuery(listQuery<AlertReceiver>(["settings", "receivers"], "/settings/receivers/"));
}

export function useReceiverMutations() {
  const qc = useQueryClient();
  const invalidate = () => void qc.invalidateQueries({ queryKey: ["settings", "receivers"] });

  const create = useMutation({
    mutationFn: (input: Partial<AlertReceiver>) =>
      api.post<AlertReceiver>("/settings/receivers/", input),
    onSuccess: () => {
      invalidate();
      toast.success("Alert receiver added successfully");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });

  const update = useMutation({
    mutationFn: ({ id, input }: { id: number; input: Partial<AlertReceiver> }) =>
      api.put<AlertReceiver>(`/settings/receivers/${id}/`, input),
    onSuccess: () => {
      invalidate();
      toast.success("Alert receiver updated successfully");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.delete<null>(`/settings/receivers/${id}/`),
    onSuccess: () => {
      invalidate();
      toast.success("Alert receiver removed successfully");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });

  return { create, update, remove };
}

/* ---------------- Animal Threat Rules ---------------- */

export function useThreatRules() {
  return useQuery(
    listQuery<AnimalThreatRule>(["settings", "threat-rules"], "/settings/threat-rules/"),
  );
}

export function useThreatRuleMutations() {
  const qc = useQueryClient();
  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ["settings", "threat-rules"] });
    void qc.invalidateQueries({ queryKey: ["detection", "status"] });
  };

  const create = useMutation({
    mutationFn: (input: Partial<AnimalThreatRule>) =>
      api.post<AnimalThreatRule>("/settings/threat-rules/", input),
    onSuccess: () => {
      invalidate();
      toast.success("Threat classification rule created successfully");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });

  const update = useMutation({
    mutationFn: ({ id, input }: { id: number; input: Partial<AnimalThreatRule> }) =>
      api.patch<AnimalThreatRule>(`/settings/threat-rules/${id}/`, input),
    onSuccess: () => {
      invalidate();
      toast.success("Threat classification rule updated successfully");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });

  const remove = useMutation({
    mutationFn: (id: number) => api.delete<null>(`/settings/threat-rules/${id}/`),
    onSuccess: () => {
      invalidate();
      toast.success("Threat rule deleted successfully");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });

  const resetDefaults = useMutation({
    mutationFn: () => api.post<AnimalThreatRule[]>("/settings/threat-rules/reset-defaults/", {}),
    onSuccess: () => {
      invalidate();
      toast.success("Threat rules restored to defaults");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });

  return { create, update, remove, resetDefaults };
}

/* ---------------- Threat Email Templates ---------------- */

export function useEmailTemplates() {
  return useQuery(
    listQuery<ThreatEmailTemplate>(["settings", "email-templates"], "/settings/email-templates/"),
  );
}

export function useUpdateEmailTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      threat_level,
      input,
    }: {
      threat_level: string;
      input: Partial<ThreatEmailTemplate>;
    }) => api.put<ThreatEmailTemplate>(`/settings/email-templates/${threat_level}/`, input),
    onSuccess: (_, variables) => {
      void qc.invalidateQueries({ queryKey: ["settings", "email-templates"] });
      toast.success(
        `${variables.threat_level.toUpperCase()} threat email template saved successfully`,
      );
    },
    onError: (e) => toast.error(humanizeError(e)),
  });
}

export function useResetEmailTemplates() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      api.post<ThreatEmailTemplate[]>("/settings/email-templates/reset-defaults/", {}),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["settings", "email-templates"] });
      toast.success("Email templates restored to factory defaults");
    },
    onError: (e) => toast.error(humanizeError(e)),
  });
}

export function usePreviewEmailTemplate() {
  return useMutation({
    mutationFn: (input: TemplatePreviewInput) =>
      api.post<TemplatePreviewResult>("/settings/email-templates/preview/", input),
  });
}

import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Bell,
  CameraIcon,
  CheckCircle2,
  ClipboardList,
  Cpu,
  ScanEye,
  ShieldAlert,
  ShieldCheck,
  Users,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { EmptyState, ErrorState } from "@/components/common/states";
import {
  useAlerts,
  useDashboardSummary,
  useDetectionLogs,
  useDetectionStatus,
  useRecentActivity,
} from "@/hooks/use-api";
import { displayName, useAuth } from "@/lib/auth";
import { formatDateTime, timeAgo } from "@/lib/format";

export const Route = createFileRoute("/app/")({
  head: () => ({
    meta: [
      { title: "Dashboard — FarmSync Command Center" },
      {
        name: "description",
        content: "Live farm operations KPIs, AI monitoring status and recent activity in FarmSync.",
      },
      { property: "og:title", content: "FarmSync Dashboard" },
      { property: "og:description", content: "Farm operations and AI monitoring at a glance." },
    ],
  }),
  component: DashboardPage,
});

const QUICK_ACTIONS = [
  { to: "/app/monitoring", label: "Live monitoring", icon: CameraIcon },
  { to: "/app/alerts", label: "Hazard alerts", icon: ShieldAlert },
  { to: "/app/farmers", label: "Farmer directory", icon: Users },
  { to: "/app/tasks", label: "Task roster", icon: ClipboardList },
] as const;

function DashboardPage() {
  const { user } = useAuth();
  const summary = useDashboardSummary();
  const activity = useRecentActivity();
  const status = useDetectionStatus();
  const logs = useDetectionLogs();
  const alerts = useAlerts();

  const s = summary.data;
  const detectionOn = status.data?.detection_enabled ?? false;

  const totalFarmers =
    s?.farmers?.total_farmers ??
    (typeof s?.["total_farmers"] === "number" ? s["total_farmers"] : 0);
  const presentToday =
    s?.attendance?.today_attendance ??
    (typeof s?.["present_today"] === "number" ? s["present_today"] : 0);
  const pendingTasks =
    s?.tasks?.pending_tasks ?? (typeof s?.["pending_tasks"] === "number" ? s["pending_tasks"] : 0);
  const totalAlerts = s?.alerts?.total_alerts ?? alerts.data?.length ?? 0;
  const highThreatAlerts =
    s?.alerts?.high_threat_alerts ??
    alerts.data?.filter((a) => (a.threat_level || "").toUpperCase() === "HIGH").length ??
    0;

  return (
    <div className="space-y-6">
      {/* Command banner */}
      <section className="hero-gradient reveal relative overflow-hidden rounded-3xl p-6 lg:p-8">
        <div className="grid-overlay absolute inset-0 opacity-20" aria-hidden="true" />
        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-widest text-primary-foreground/60">
              FarmSync Operations Command Center
            </p>
            <h1 className="mt-3 text-2xl font-semibold text-primary-foreground sm:text-3xl">
              Welcome back, {displayName(user) || "operator"}
            </h1>
            <p className="mt-2 max-w-xl text-sm text-primary-foreground/70">
              Integrated farm workforce management and AI perimeter threat surveillance console.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <div className="rounded-xl border border-primary-foreground/15 bg-primary-foreground/10 px-4 py-3">
              <p className="text-[10px] uppercase tracking-widest text-primary-foreground/55">
                AI Vision Pipeline
              </p>
              <p className="mt-1 flex items-center gap-2 text-sm font-semibold text-primary-foreground">
                <span
                  className={`size-2 rounded-full ${detectionOn ? "bg-accent" : "bg-primary-foreground/40"}`}
                  aria-hidden="true"
                />
                {status.isLoading ? "Checking…" : detectionOn ? "Active" : "Disabled"}
              </p>
            </div>
            <div className="rounded-xl border border-primary-foreground/15 bg-primary-foreground/10 px-4 py-3">
              <p className="text-[10px] uppercase tracking-widest text-primary-foreground/55">
                High Threat Hazards
              </p>
              <p className="mt-1 flex items-center gap-2 text-sm font-semibold text-primary-foreground">
                <span
                  className={`size-2 rounded-full ${highThreatAlerts > 0 ? "bg-destructive animate-ping" : "bg-accent"}`}
                  aria-hidden="true"
                />
                {highThreatAlerts > 0 ? `${highThreatAlerts} High Threat` : "All Clear"}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* KPIs */}
      {summary.isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-2xl" />
          ))}
        </div>
      ) : summary.isError ? (
        <ErrorState error={summary.error} onRetry={() => void summary.refetch()} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <KpiCard label="Total farmers" value={totalFarmers} icon={Users} />
          <KpiCard label="Present today" value={presentToday} icon={CheckCircle2} tone="accent" />
          <KpiCard label="Pending tasks" value={pendingTasks} icon={ClipboardList} tone="warning" />
          <KpiCard
            label="Hazard alerts"
            value={totalAlerts}
            icon={ShieldAlert}
            tone={highThreatAlerts > 0 ? "destructive" : "default"}
          />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Activity timeline */}
        <section className="surface-card lg:col-span-2">
          <header className="flex items-center justify-between border-b border-border px-5 py-4">
            <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
              Recent Activity & Security Feed
            </h2>
            <Activity className="size-4 text-muted-foreground" aria-hidden="true" />
          </header>
          <div className="p-5">
            {activity.isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 rounded-lg" />
                ))}
              </div>
            ) : activity.isError ? (
              <ErrorState error={activity.error} onRetry={() => void activity.refetch()} />
            ) : (activity.data ?? []).length === 0 ? (
              <EmptyState
                title="No recent activity"
                description="Activity from attendance, tasks, detections and alerts will appear here."
                icon={<Activity className="size-7" aria-hidden="true" />}
              />
            ) : (
              <ol className="relative space-y-4 border-l border-border pl-5">
                {(activity.data ?? []).slice(0, 8).map((item, i) => {
                  const ts = (item.timestamp ?? item.created_at) as string | undefined;
                  const isHighThreat = item.threat_level === "HIGH";
                  return (
                    <li key={item.id ?? i} className="reveal relative">
                      <span
                        className={`absolute -left-[27px] top-1.5 size-2.5 rounded-full ring-4 ring-background ${
                          isHighThreat ? "bg-destructive animate-pulse" : "bg-primary"
                        }`}
                        aria-hidden="true"
                      />
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="text-sm font-medium flex items-center gap-1.5">
                          {isHighThreat && <AlertTriangle className="size-3.5 text-destructive" />}
                          {item.message ?? item.description ?? item.type ?? "Activity"}
                        </p>
                        {item.badge && (
                          <Badge variant={item.badgeVariant ?? "outline"} className="text-[10px]">
                            {item.badge}
                          </Badge>
                        )}
                      </div>
                      {item.description && (
                        <p className="mt-0.5 text-xs text-muted-foreground">{item.description}</p>
                      )}
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        {ts ? `${formatDateTime(ts)} · ${timeAgo(ts)}` : "—"}
                      </p>
                    </li>
                  );
                })}
              </ol>
            )}
          </div>
        </section>

        <div className="space-y-6">
          {/* AI monitoring status */}
          <section className="surface-card relative overflow-hidden bg-sidebar p-5 text-sidebar-foreground">
            <div className="grid-overlay absolute inset-0 opacity-25" aria-hidden="true" />
            <div className="relative">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-widest text-sidebar-foreground/60">
                  AI Perimeter Vision
                </h2>
                <Cpu className="size-4 text-sidebar-primary" aria-hidden="true" />
              </div>
              <p className="mt-4 flex items-center gap-2 text-2xl font-semibold">
                <span className="relative flex size-2.5">
                  {detectionOn && (
                    <span className="absolute inline-flex size-full animate-ping rounded-full bg-sidebar-primary opacity-70" />
                  )}
                  <span
                    className={`relative inline-flex size-2.5 rounded-full ${detectionOn ? "bg-sidebar-primary" : "bg-sidebar-foreground/30"}`}
                  />
                </span>
                {detectionOn ? "Active" : "Disabled"}
              </p>
              <dl className="mt-5 space-y-2 text-xs">
                <div className="flex justify-between">
                  <dt className="text-sidebar-foreground/60">Total detections logged</dt>
                  <dd>{logs.isLoading ? "…" : (logs.data?.length ?? 0)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sidebar-foreground/60">Hazard alert events</dt>
                  <dd>{alerts.isLoading ? "…" : (alerts.data?.length ?? 0)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sidebar-foreground/60">Camera hardware index</dt>
                  <dd>{status.data?.camera_device_index ?? 0}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-sidebar-foreground/60">Model engine</dt>
                  <dd>{status.data?.model_name ?? "YOLOv8n"}</dd>
                </div>
              </dl>
              <Link
                to="/app/monitoring"
                className="mt-5 inline-flex items-center gap-1.5 text-xs font-medium text-sidebar-primary hover:underline"
              >
                Open AI monitoring
                <ArrowUpRight className="size-3.5" aria-hidden="true" />
              </Link>
            </div>
          </section>

          {/* Quick actions */}
          <section className="surface-card p-5">
            <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
              Quick Actions
            </h2>
            <div className="mt-4 grid grid-cols-2 gap-3">
              {QUICK_ACTIONS.map(({ to, label, icon: Icon }) => (
                <Link
                  key={to}
                  to={to}
                  className="group flex flex-col gap-2 rounded-xl border border-border bg-muted/40 p-4 transition-colors hover:border-primary/40 hover:bg-primary/5"
                >
                  <Icon className="size-4 text-primary" aria-hidden="true" />
                  <span className="text-xs font-medium">{label}</span>
                </Link>
              ))}
            </div>
          </section>

          {/* Hazard alerts widget */}
          <section className="surface-card p-5">
            <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
              Recent Hazard Alerts
            </h2>
            {alerts.isLoading ? (
              <Skeleton className="mt-4 h-16 rounded-lg" />
            ) : (alerts.data ?? []).length === 0 ? (
              <p className="mt-4 text-xs text-muted-foreground">No hazard alerts recorded.</p>
            ) : (
              <ul className="mt-4 space-y-3">
                {(alerts.data ?? []).slice(0, 3).map((alert) => {
                  const isHigh = (alert.threat_level || "").toUpperCase() === "HIGH";
                  return (
                    <li key={alert.id} className="flex items-center justify-between gap-3">
                      <span className="flex items-center gap-2 text-sm font-medium capitalize">
                        {isHigh ? (
                          <AlertTriangle className="size-4 text-destructive" aria-hidden="true" />
                        ) : (
                          <Bell className="size-4 text-primary" aria-hidden="true" />
                        )}
                        {alert.animal_type ? `${alert.animal_type}` : (alert.alert_type ?? "Alert")}
                      </span>
                      <div className="flex items-center gap-1.5">
                        <Badge variant={isHigh ? "destructive" : "outline"} className="text-[10px]">
                          {alert.threat_level || "ALERT"}
                        </Badge>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
            <Link
              to="/app/alerts"
              className="mt-4 inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:underline"
            >
              View all alerts
              <ArrowUpRight className="size-3.5" aria-hidden="true" />
            </Link>
          </section>
        </div>
      </div>
    </div>
  );
}

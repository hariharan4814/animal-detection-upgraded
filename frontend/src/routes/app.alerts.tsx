import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  AlertTriangle,
  Bell,
  Download,
  Eye,
  Lock,
  Mail,
  MapPin,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  Volume2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { EmptyState, ErrorState, LoadingRows, PageHeader } from "@/components/common/states";
import { useAlerts, useDeleteAlert } from "@/hooks/use-api";
import { useAuth } from "@/lib/auth";
import { mediaUrl } from "@/lib/api";
import { confidencePercent, formatDateTime, timeAgo } from "@/lib/format";
import type { HazardAlert } from "@/types/api";

export const Route = createFileRoute("/app/alerts")({
  head: () => ({
    meta: [
      { title: "Hazard Alerts — FarmSync" },
      {
        name: "description",
        content:
          "Hazard alert history, evidence inspection, and dispatch logs triggered by AI detections.",
      },
      { property: "og:title", content: "Hazard Alert Center — FarmSync" },
      {
        property: "og:description",
        content: "Evidence management and logs of triggered farm hazard alerts.",
      },
    ],
  }),
  component: AlertsPage,
});

function AlertsPage() {
  const { isStaff } = useAuth();
  const { data, isLoading, isError, error, refetch } = useAlerts();
  const deleteMutation = useDeleteAlert();

  const [threatFilter, setThreatFilter] = useState<string>("ALL");
  const [activeAlert, setActiveAlert] = useState<HazardAlert | null>(null);
  const [lightboxAlert, setLightboxAlert] = useState<HazardAlert | null>(null);
  const [deletingAlert, setDeletingAlert] = useState<HazardAlert | null>(null);

  const rawAlerts = data ?? [];

  const alerts = rawAlerts.filter((a) => {
    if (threatFilter === "ALL") return true;
    return (a.threat_level || "MEDIUM").toUpperCase() === threatFilter;
  });

  const getThreatBadge = (level?: string) => {
    const tier = (level || "MEDIUM").toUpperCase();
    if (tier === "HIGH") {
      return (
        <Badge variant="destructive" className="flex items-center gap-1 text-[10px]">
          <AlertTriangle className="size-3" />
          HIGH THREAT
        </Badge>
      );
    }
    if (tier === "LOW") {
      return (
        <Badge
          variant="secondary"
          className="flex items-center gap-1 text-[10px] text-success border-success/30"
        >
          <ShieldCheck className="size-3" />
          LOW THREAT
        </Badge>
      );
    }
    return (
      <Badge
        variant="outline"
        className="flex items-center gap-1 text-[10px] text-warning border-warning/30"
      >
        <ShieldAlert className="size-3" />
        MEDIUM THREAT
      </Badge>
    );
  };

  const handleDownload = (alert: HazardAlert, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    const url = alert.download_url || (alert.image_path ? mediaUrl(alert.image_path) : null);
    if (!url) return;
    const link = document.createElement("a");
    link.href = url;
    link.download = `alert_${alert.id}_evidence.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Hazard Alert Center"
        description="Historical log of animal hazard dispatches, threat severity, and evidentiary snapshots captured by AI cameras."
      />

      {/* Filter Chips & Overview Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5 rounded-xl bg-muted/60 p-1">
          {["ALL", "HIGH", "MEDIUM", "LOW"].map((tier) => (
            <button
              key={tier}
              type="button"
              onClick={() => setThreatFilter(tier)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                threatFilter === tier
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {tier === "ALL" && "All Alerts"}
              {tier === "HIGH" && "🚨 High Threat"}
              {tier === "MEDIUM" && "⚠️ Medium Threat"}
              {tier === "LOW" && "ℹ️ Low Threat"}
            </button>
          ))}
        </div>

        <span className="text-xs text-muted-foreground">
          Showing <span className="font-semibold text-foreground">{alerts.length}</span> alert
          records
        </span>
      </div>

      {isLoading ? (
        <LoadingRows />
      ) : isError ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : alerts.length === 0 ? (
        <EmptyState
          title="No alerts found"
          description={
            threatFilter !== "ALL"
              ? `No ${threatFilter} threat alerts match the active filter.`
              : "Hazard alert events appear here when an AI detection crosses configured threat thresholds."
          }
          icon={<ShieldAlert className="size-7" aria-hidden="true" />}
        />
      ) : (
        <ol className="relative space-y-4 border-l border-border pl-6">
          {alerts.map((alert) => {
            const animal = alert.animal_type || "Animal Intrusion";
            const pct = confidencePercent(alert.confidence);
            const ts = alert.created_at || alert.detection_timestamp;
            const isHigh = (alert.threat_level || "MEDIUM").toUpperCase() === "HIGH";
            const isBuzzer = alert.buzzer_triggered || alert.alert_type?.includes("Buzzer");
            const isEmail = alert.email_sent || alert.alert_type?.includes("Email");

            return (
              <li key={alert.id} className="relative">
                <span
                  className={`absolute -left-[31px] top-4 flex size-4 items-center justify-center rounded-full ring-4 ring-background ${
                    isHigh ? "bg-destructive/20" : "bg-primary/15"
                  }`}
                  aria-hidden="true"
                >
                  <span
                    className={`size-1.5 rounded-full ${
                      isHigh ? "bg-destructive animate-pulse" : "bg-primary"
                    }`}
                  />
                </span>

                <div className="surface-card reveal w-full p-5 text-left transition-all hover:border-primary/40">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      {alert.image_path ? (
                        <button
                          type="button"
                          onClick={() => setLightboxAlert(alert)}
                          className="group relative size-16 shrink-0 overflow-hidden rounded-lg border border-border bg-black/60 focus:outline-none"
                          title="Click to view full evidence photo"
                        >
                          <img
                            src={mediaUrl(alert.image_path) ?? ""}
                            alt="Snapshot"
                            className="size-full object-cover transition-transform group-hover:scale-105"
                            onError={(e) => {
                              (e.target as HTMLElement).style.display = "none";
                            }}
                          />
                          <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition-opacity group-hover:opacity-100">
                            <Eye className="size-4 text-white" />
                          </div>
                        </button>
                      ) : (
                        <div className="flex size-16 shrink-0 items-center justify-center rounded-lg border border-border bg-muted/40 text-muted-foreground">
                          <Bell className="size-6" />
                        </div>
                      )}

                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <h2 className="text-base font-semibold capitalize flex items-center gap-1.5">
                            {animal}
                          </h2>
                          {getThreatBadge(alert.threat_level)}
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground flex items-center gap-1.5">
                          <MapPin className="size-3" />
                          {alert.field || "Main Field"} · Alert #{alert.id}
                        </p>
                        <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-muted-foreground">
                          {isBuzzer && (
                            <span className="inline-flex items-center gap-1 text-warning">
                              <Volume2 className="size-3" /> Siren Sounded
                            </span>
                          )}
                          {isEmail && (
                            <span className="inline-flex items-center gap-1 text-primary">
                              <Mail className="size-3" /> Email Dispatched
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      <Badge
                        variant={
                          alert.status === "Triggered"
                            ? "destructive"
                            : alert.status === "Sent"
                              ? "secondary"
                              : "outline"
                        }
                        className="text-[10px]"
                      >
                        {alert.status ?? "Triggered"}
                      </Badge>

                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 text-xs gap-1.5"
                        onClick={() => setActiveAlert(alert)}
                      >
                        <Eye className="size-3.5" />
                        Details
                      </Button>

                      {alert.image_path && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-8 text-xs gap-1.5"
                          onClick={(e) => handleDownload(alert, e)}
                        >
                          <Download className="size-3.5" />
                          Download
                        </Button>
                      )}

                      {isStaff && (
                        <Button
                          size="icon"
                          variant="ghost"
                          className="size-8 text-muted-foreground hover:text-destructive"
                          aria-label={`Delete Alert #${alert.id}`}
                          onClick={() => setDeletingAlert(alert)}
                        >
                          <Trash2 className="size-3.5" />
                        </Button>
                      )}
                    </div>
                  </div>

                  <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border/50 pt-3 text-xs text-muted-foreground">
                    <span>{ts ? `${formatDateTime(ts)} · ${timeAgo(ts)}` : "—"}</span>
                    {pct !== null && (
                      <div className="flex items-center gap-2 min-w-32">
                        <Progress value={pct} className="h-1.5 w-16" />
                        <span className="font-mono tabular-nums">{pct}% conf</span>
                      </div>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      )}

      {/* Lightbox / Full Evidence Image Modal */}
      <Dialog open={!!lightboxAlert} onOpenChange={(v) => !v && setLightboxAlert(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 capitalize">
              <ShieldAlert className="size-5 text-destructive" />
              Evidence Snapshot: {lightboxAlert?.animal_type} (Alert #{lightboxAlert?.id})
            </DialogTitle>
            <DialogDescription>
              Captured by camera sensor in {lightboxAlert?.field || "Main Field"} at{" "}
              {formatDateTime(lightboxAlert?.created_at ?? lightboxAlert?.detection_timestamp)}
            </DialogDescription>
          </DialogHeader>
          {lightboxAlert?.image_path && (
            <div className="overflow-hidden rounded-xl border border-border bg-black aspect-video flex items-center justify-center">
              <img
                src={mediaUrl(lightboxAlert.image_path) ?? ""}
                alt="Full alert evidence snapshot"
                className="size-full object-contain"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = "none";
                }}
              />
            </div>
          )}
          <DialogFooter className="flex justify-between sm:justify-between items-center">
            {getThreatBadge(lightboxAlert?.threat_level)}
            <div className="flex gap-2">
              {lightboxAlert && (
                <Button size="sm" variant="outline" onClick={() => handleDownload(lightboxAlert)}>
                  <Download className="size-3.5" aria-hidden="true" />
                  Download Evidence
                </Button>
              )}
              <Button size="sm" onClick={() => setLightboxAlert(null)}>
                Close
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Alert Details Sheet */}
      <Sheet open={!!activeAlert} onOpenChange={(v) => !v && setActiveAlert(null)}>
        <SheetContent className="w-full overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle className="capitalize flex items-center gap-2">
              <ShieldAlert className="size-5 text-destructive" />
              Alert #{activeAlert?.id} — {activeAlert?.animal_type ?? "Hazard Alert"}
            </SheetTitle>
            <SheetDescription>Threat evaluation and dispatch audit log</SheetDescription>
          </SheetHeader>

          {activeAlert && (
            <div className="space-y-5 px-4 pb-6 mt-4">
              {activeAlert.image_path ? (
                <div
                  className="rounded-xl overflow-hidden border border-border bg-black aspect-video flex items-center justify-center cursor-pointer group"
                  onClick={() => {
                    setLightboxAlert(activeAlert);
                    setActiveAlert(null);
                  }}
                >
                  <img
                    src={mediaUrl(activeAlert.image_path) ?? ""}
                    alt="Alert detection snapshot"
                    className="size-full object-contain transition-transform group-hover:scale-105"
                    onError={(e) => {
                      (e.target as HTMLElement).style.display = "none";
                    }}
                  />
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-border p-6 text-center text-xs text-muted-foreground">
                  No snapshot image linked to this alert.
                </div>
              )}

              <dl className="space-y-3 text-sm">
                {[
                  ["Alert ID", `#${activeAlert.id}`],
                  ["Animal Species", activeAlert.animal_type ?? "—"],
                  ["Assessed Threat Tier", activeAlert.threat_level ?? "MEDIUM"],
                  ["Notification Channel", activeAlert.alert_type ?? "Email"],
                  ["Dispatch Status", activeAlert.status ?? "Triggered"],
                  ["Audio Buzzer Siren", activeAlert.buzzer_triggered ? "Yes (Triggered)" : "No"],
                  [
                    "Email Notification",
                    activeAlert.email_sent ? "Yes (Delivered)" : "Pending / None",
                  ],
                  [
                    "Model Confidence",
                    confidencePercent(activeAlert.confidence) !== null
                      ? `${confidencePercent(activeAlert.confidence)}%`
                      : "—",
                  ],
                  ["Location / Sector", activeAlert.field ?? "Main Field"],
                  [
                    "Triggered Timestamp",
                    formatDateTime(activeAlert.created_at ?? activeAlert.detection_timestamp),
                  ],
                ].map(([k, v]) => (
                  <div
                    key={k}
                    className="flex justify-between gap-4 border-b border-border pb-2 text-xs"
                  >
                    <dt className="text-muted-foreground">{k}</dt>
                    <dd className="text-right font-medium capitalize max-w-[200px] truncate">
                      {String(v)}
                    </dd>
                  </div>
                ))}
              </dl>

              <div className="flex gap-2 pt-2">
                {activeAlert.image_path && (
                  <Button
                    variant="outline"
                    className="w-full text-xs"
                    onClick={() => handleDownload(activeAlert)}
                  >
                    <Download className="size-3.5" aria-hidden="true" />
                    Download Snapshot
                  </Button>
                )}
                {isStaff && (
                  <Button
                    variant="destructive"
                    className="w-full text-xs"
                    onClick={() => {
                      setDeletingAlert(activeAlert);
                      setActiveAlert(null);
                    }}
                  >
                    <Trash2 className="size-3.5" aria-hidden="true" />
                    Delete Alert
                  </Button>
                )}
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Delete Alert Confirmation Dialog */}
      <AlertDialog open={!!deletingAlert} onOpenChange={(v) => !v && setDeletingAlert(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Alert #{deletingAlert?.id}?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to permanently delete this hazard alert record and its
              associated evidence image snapshot? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => {
                if (deletingAlert) {
                  deleteMutation.mutate(deletingAlert.id);
                  setDeletingAlert(null);
                }
              }}
            >
              Delete Alert & Evidence
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

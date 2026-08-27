import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  AlertTriangle,
  ImageIcon,
  MapPin,
  ScanEye,
  Search,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState, ErrorState, LoadingRows, PageHeader } from "@/components/common/states";
import { useDetectionLogs } from "@/hooks/use-api";
import { mediaUrl } from "@/lib/api";
import { confidencePercent, formatDateTime, timeAgo } from "@/lib/format";
import type { DetectionLog } from "@/types/api";

export const Route = createFileRoute("/app/detection-logs")({
  head: () => ({
    meta: [
      { title: "Detection Logs — FarmSync" },
      {
        name: "description",
        content:
          "Historical animal detection events with confidence, threat classification, and snapshots.",
      },
      { property: "og:title", content: "Detection Logs — FarmSync" },
      { property: "og:description", content: "Review the FarmSync YOLO detection event history." },
    ],
  }),
  component: DetectionLogsPage,
});

function DetectionLogsPage() {
  const { data, isLoading, isError, error, refetch } = useDetectionLogs();
  const [query, setQuery] = useState("");
  const [threatFilter, setThreatFilter] = useState<string>("ALL");
  const [active, setActive] = useState<DetectionLog | null>(null);

  const logs = useMemo(() => {
    const list = data ?? [];
    const q = query.trim().toLowerCase();
    return list.filter((l) => {
      if (threatFilter !== "ALL" && (l.threat_level || "MEDIUM").toUpperCase() !== threatFilter) {
        return false;
      }
      if (!q) return true;
      return [l.animal_type, l.field].some((v) =>
        String(v ?? "")
          .toLowerCase()
          .includes(q),
      );
    });
  }, [data, query, threatFilter]);

  const getThreatBadge = (level?: string) => {
    const tier = (level || "MEDIUM").toUpperCase();
    if (tier === "HIGH") {
      return (
        <Badge variant="destructive" className="flex items-center gap-1 text-[10px]">
          <AlertTriangle className="size-3" />
          HIGH
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
          LOW
        </Badge>
      );
    }
    return (
      <Badge
        variant="outline"
        className="flex items-center gap-1 text-[10px] text-warning border-warning/30"
      >
        <ShieldAlert className="size-3" />
        MEDIUM
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Detection Logs"
        description="Chronological event log of all AI animal detection records and evaluated threat classifications."
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="relative w-full max-w-md">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            className="pl-9"
            placeholder="Search by animal species or field location..."
            aria-label="Search detection logs"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        <div className="flex flex-wrap gap-1 rounded-xl bg-muted/60 p-1">
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
              {tier === "ALL" && "All Detections"}
              {tier === "HIGH" && "🚨 High Threat"}
              {tier === "MEDIUM" && "⚠️ Medium Threat"}
              {tier === "LOW" && "ℹ️ Low Threat"}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <LoadingRows />
      ) : isError ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : logs.length === 0 ? (
        <EmptyState
          title="No detection logs found"
          description={
            threatFilter !== "ALL" || query
              ? "No records match the active search and threat filter criteria."
              : "Detection events will appear here once the YOLO engine records an intrusion."
          }
          icon={<ScanEye className="size-7" aria-hidden="true" />}
        />
      ) : (
        <div className="surface-card overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Event ID</TableHead>
                <TableHead>Animal Species</TableHead>
                <TableHead>Threat Level</TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Field / Location</TableHead>
                <TableHead>Snapshot</TableHead>
                <TableHead>Timestamp</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map((log) => {
                const pct = confidencePercent(log.confidence);
                return (
                  <TableRow
                    key={log.id}
                    tabIndex={0}
                    role="button"
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => setActive(log)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        setActive(log);
                      }
                    }}
                  >
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      #{log.id}
                    </TableCell>
                    <TableCell className="font-medium capitalize">
                      <span className="flex items-center gap-2">
                        <ScanEye className="size-4 text-primary" />
                        {log.animal_type ?? "Unknown"}
                      </span>
                    </TableCell>
                    <TableCell>{getThreatBadge(log.threat_level)}</TableCell>
                    <TableCell className="min-w-36">
                      {pct === null ? (
                        "—"
                      ) : (
                        <div className="flex items-center gap-2">
                          <Progress value={pct} className="h-1.5 w-20" />
                          <span className="text-xs font-mono tabular-nums">{pct}%</span>
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <span className="flex items-center gap-1 text-xs">
                        <MapPin className="size-3 text-muted-foreground" />
                        {log.field || "Main Field"}
                      </span>
                    </TableCell>
                    <TableCell>
                      {log.image_path ? (
                        <Badge variant="outline" className="text-[10px] gap-1">
                          <ImageIcon className="size-2.5" />
                          Saved
                        </Badge>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                      {formatDateTime(log.timestamp ?? log.created_at)}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}

      <Sheet open={!!active} onOpenChange={(v) => !v && setActive(null)}>
        <SheetContent className="w-full overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle className="capitalize flex items-center gap-2">
              <ScanEye className="size-5 text-primary" />
              {active?.animal_type ?? "Detection"} Event Log
            </SheetTitle>
            <SheetDescription>
              {timeAgo(active?.timestamp ?? active?.created_at) || "Detection record"}
            </SheetDescription>
          </SheetHeader>

          {active && (
            <div className="space-y-5 px-4 pb-6 mt-4">
              {active.image_path ? (
                <div className="rounded-xl overflow-hidden border border-border bg-black/60 aspect-video flex items-center justify-center">
                  <img
                    src={mediaUrl(active.image_path) ?? ""}
                    alt={`Snapshot of ${active.animal_type ?? "detection"}`}
                    loading="lazy"
                    className="size-full object-contain"
                    onError={(e) => {
                      (e.target as HTMLElement).style.display = "none";
                    }}
                  />
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-border p-6 text-center text-xs text-muted-foreground">
                  No snapshot captured for this event.
                </div>
              )}

              <dl className="space-y-3 text-sm">
                {[
                  ["Log Record ID", `#${active.id}`],
                  ["Animal Species", active.animal_type ?? "—"],
                  ["Threat Classification", active.threat_level ?? "MEDIUM"],
                  [
                    "Model Confidence",
                    confidencePercent(active.confidence) !== null
                      ? `${confidencePercent(active.confidence)}%`
                      : "—",
                  ],
                  ["Field Sector", active.field ?? "Main Field"],
                  ["Event Timestamp", formatDateTime(active.timestamp ?? active.created_at)],
                  ["Snapshot Storage Path", active.image_path ?? "None"],
                ].map(([k, v]) => (
                  <div
                    key={k}
                    className="flex justify-between gap-4 border-b border-border pb-2 text-xs"
                  >
                    <dt className="text-muted-foreground">{k}</dt>
                    <dd className="text-right font-medium capitalize max-w-[200px] truncate">
                      {v}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}

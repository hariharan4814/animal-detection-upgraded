import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { CalendarClock, Filter, LogIn, LogOut, Timer, Loader2, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState, ErrorState, LoadingRows, PageHeader } from "@/components/common/states";
import {
  useAttendance,
  useAttendanceActions,
  useAttendanceReport,
  useFarmers,
} from "@/hooks/use-api";
import { useAuth } from "@/lib/auth";
import { formatDate, formatTime, toNumber } from "@/lib/format";
import type { AttendanceRecord } from "@/types/api";

export const Route = createFileRoute("/app/attendance")({
  head: () => ({
    meta: [
      { title: "Attendance — FarmSync" },
      {
        name: "description",
        content: "Check-in, check-out and attendance reporting for farm workers.",
      },
      { property: "og:title", content: "Attendance Management — FarmSync" },
      {
        property: "og:description",
        content: "Track worker shifts, durations and wages in FarmSync.",
      },
    ],
  }),
  component: AttendancePage,
});

function shiftState(record: AttendanceRecord) {
  if (record.check_out) return { label: "Completed", variant: "secondary" as const };
  if (record.check_in) return { label: "Active shift", variant: "default" as const };
  return { label: "Pending", variant: "outline" as const };
}

function AttendancePage() {
  const { isStaff } = useAuth();
  const attendance = useAttendance();
  const farmers = useFarmers();
  const { checkIn, checkOut } = useAttendanceActions();
  const [selected, setSelected] = useState<string>("");
  const [locationInput, setLocationInput] = useState<string>("");

  // Report filter states
  const [reportStartDate, setReportStartDate] = useState<string>("");
  const [reportEndDate, setReportEndDate] = useState<string>("");
  const [reportFarmerId, setReportFarmerId] = useState<string>("all");

  const reportFilters = {
    ...(reportStartDate ? { start_date: reportStartDate } : {}),
    ...(reportEndDate ? { end_date: reportEndDate } : {}),
    ...(reportFarmerId && reportFarmerId !== "all" ? { farmer_id: Number(reportFarmerId) } : {}),
  };

  const report = useAttendanceReport(reportFilters);

  const records = attendance.data ?? [];
  const farmerId = selected ? Number(selected) : null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Attendance"
        description="Shift check-in and check-out console with real-time duration and reporting."
      />

      {isStaff && (
        <section className="surface-card reveal p-5">
          <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
            Shift console
          </h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-[1.5fr_1.5fr_auto] sm:items-end">
            <div className="space-y-2">
              <label htmlFor="farmer-select" className="text-xs font-medium text-muted-foreground">
                Select Worker *
              </label>
              <Select value={selected} onValueChange={setSelected}>
                <SelectTrigger id="farmer-select" className="w-full">
                  <SelectValue placeholder="Choose a registered farmer" />
                </SelectTrigger>
                <SelectContent>
                  {(farmers.data ?? []).map((f) => (
                    <SelectItem key={f.id} value={String(f.id)}>
                      {f.name} ({f.field})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label htmlFor="location-input" className="text-xs font-medium text-muted-foreground">
                Field Location (Optional)
              </label>
              <Input
                id="location-input"
                placeholder="e.g. Field Station A"
                value={locationInput}
                onChange={(e) => setLocationInput(e.target.value)}
              />
            </div>

            <div className="flex gap-2">
              <Button
                disabled={!farmerId || checkIn.isPending}
                onClick={() =>
                  farmerId &&
                  checkIn.mutate({ farmer_id: farmerId, location: locationInput || undefined })
                }
              >
                {checkIn.isPending ? (
                  <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                ) : (
                  <LogIn className="size-4" aria-hidden="true" />
                )}
                Check in
              </Button>
              <Button
                variant="outline"
                disabled={!farmerId || checkOut.isPending}
                onClick={() =>
                  farmerId &&
                  checkOut.mutate({ farmer_id: farmerId, location: locationInput || undefined })
                }
              >
                {checkOut.isPending ? (
                  <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                ) : (
                  <LogOut className="size-4" aria-hidden="true" />
                )}
                Check out
              </Button>
            </div>
          </div>
        </section>
      )}

      <Tabs defaultValue="records">
        <TabsList>
          <TabsTrigger value="records">Daily Attendance Records</TabsTrigger>
          <TabsTrigger value="report">Attendance Reports</TabsTrigger>
        </TabsList>

        <TabsContent value="records" className="mt-4">
          {attendance.isLoading ? (
            <LoadingRows />
          ) : attendance.isError ? (
            <ErrorState error={attendance.error} onRetry={() => void attendance.refetch()} />
          ) : records.length === 0 ? (
            <EmptyState
              title="No attendance records"
              description="Records appear once farm workers check in for a shift."
              icon={<CalendarClock className="size-7" aria-hidden="true" />}
            />
          ) : (
            <div className="surface-card overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Farmer</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Check In</TableHead>
                    <TableHead>Check Out</TableHead>
                    <TableHead>Total Hours</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {records.map((r) => {
                    const state = shiftState(r);
                    const hours = toNumber(r.total_hours);
                    return (
                      <TableRow key={r.id}>
                        <TableCell className="font-medium">
                          {r.farmer_name ?? `Farmer #${r.farmer}`}
                        </TableCell>
                        <TableCell>{formatDate(r.date)}</TableCell>
                        <TableCell>{formatTime(r.check_in)}</TableCell>
                        <TableCell>{formatTime(r.check_out)}</TableCell>
                        <TableCell>
                          {hours !== null && hours !== undefined ? (
                            <span className="inline-flex items-center gap-1.5 font-mono text-xs">
                              <Timer
                                className="size-3.5 text-muted-foreground"
                                aria-hidden="true"
                              />
                              {hours.toFixed(2)} hrs
                            </span>
                          ) : (
                            "—"
                          )}
                        </TableCell>
                        <TableCell>
                          {r.location ? (
                            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                              <MapPin className="size-3" aria-hidden="true" />
                              {r.location}
                            </span>
                          ) : (
                            "—"
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge variant={state.variant}>{state.label}</Badge>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>

        <TabsContent value="report" className="mt-4 space-y-4">
          <div className="surface-card p-4">
            <div className="flex flex-wrap items-end gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Start Date</label>
                <Input
                  type="date"
                  value={reportStartDate}
                  onChange={(e) => setReportStartDate(e.target.value)}
                  className="w-40 text-xs"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">End Date</label>
                <Input
                  type="date"
                  value={reportEndDate}
                  onChange={(e) => setReportEndDate(e.target.value)}
                  className="w-40 text-xs"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Filter Farmer</label>
                <Select value={reportFarmerId} onValueChange={setReportFarmerId}>
                  <SelectTrigger className="w-48 text-xs">
                    <SelectValue placeholder="All Farmers" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Farmers</SelectItem>
                    {(farmers.data ?? []).map((f) => (
                      <SelectItem key={f.id} value={String(f.id)}>
                        {f.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setReportStartDate("");
                  setReportEndDate("");
                  setReportFarmerId("all");
                }}
              >
                Reset Filters
              </Button>
            </div>
          </div>

          {report.isLoading ? (
            <LoadingRows rows={3} />
          ) : report.isError ? (
            <ErrorState error={report.error} onRetry={() => void report.refetch()} />
          ) : !report.data?.records || report.data.records.length === 0 ? (
            <EmptyState
              title="No report data found"
              description="No attendance records match the selected filter criteria."
              icon={<Filter className="size-7" aria-hidden="true" />}
            />
          ) : (
            <div className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="surface-card p-4">
                  <p className="text-xs uppercase tracking-widest text-muted-foreground">
                    Total Filtered Records
                  </p>
                  <p className="mt-1 text-2xl font-semibold">{report.data.total_records}</p>
                </div>
                <div className="surface-card p-4">
                  <p className="text-xs uppercase tracking-widest text-muted-foreground">
                    Total Hours Logged
                  </p>
                  <p className="mt-1 text-2xl font-semibold text-primary">
                    {report.data.total_hours_sum.toFixed(2)} hrs
                  </p>
                </div>
              </div>

              <div className="surface-card overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Farmer</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Check In</TableHead>
                      <TableHead>Check Out</TableHead>
                      <TableHead>Total Hours</TableHead>
                      <TableHead>Location</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {report.data.records.map((r) => (
                      <TableRow key={r.id}>
                        <TableCell className="font-medium">
                          {r.farmer_name ?? `Farmer #${r.farmer}`}
                        </TableCell>
                        <TableCell>{formatDate(r.date)}</TableCell>
                        <TableCell>{formatTime(r.check_in)}</TableCell>
                        <TableCell>{formatTime(r.check_out)}</TableCell>
                        <TableCell className="font-mono text-xs">
                          {r.total_hours ? `${r.total_hours.toFixed(2)} hrs` : "—"}
                        </TableCell>
                        <TableCell>{r.location ?? "—"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

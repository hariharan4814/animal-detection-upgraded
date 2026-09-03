import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  CalendarClock,
  CheckCircle2,
  FileText,
  Filter,
  LogIn,
  LogOut,
  Mail,
  MapPin,
  Timer,
  AlertCircle,
  Clock,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import { formatDate, formatDateTime, formatTime, toNumber } from "@/lib/format";
import type { AttendanceRecord, Farmer } from "@/types/api";

export const Route = createFileRoute("/app/attendance")({
  head: () => ({
    meta: [
      { title: "Attendance — FarmSync" },
      {
        name: "description",
        content: "Check-in, check-out and automated work reporting for farm workers.",
      },
      { property: "og:title", content: "Attendance & Work Reporting — FarmSync" },
      {
        property: "og:description",
        content:
          "Track worker shifts, work descriptions and automated daily email reports in FarmSync.",
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

/* -------------------------------------------------------------------------- */
/* Complete Work Session (Checkout) Modal Dialog                              */
/* -------------------------------------------------------------------------- */
interface CheckOutModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  farmer: Farmer | null;
  activeRecord?: AttendanceRecord | null;
  locationFallback?: string;
}

function CheckOutModal({
  open,
  onOpenChange,
  farmer,
  activeRecord,
  locationFallback,
}: CheckOutModalProps) {
  const { checkOut } = useAttendanceActions();
  const [workDescription, setWorkDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  const currentTimeStr = useMemo(() => {
    const d = new Date();
    return d.toTimeString().split(" ")[0]; // HH:MM:SS
  }, []);

  const handleCheckoutSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleanDesc = workDescription.trim();
    if (!cleanDesc) {
      setError("Please describe what work was completed today.");
      return;
    }
    if (cleanDesc.length < 5) {
      setError("Please provide a detailed summary (at least 5 characters).");
      return;
    }

    try {
      await checkOut.mutateAsync({
        farmer_id: farmer?.id,
        attendance_id: activeRecord?.id,
        work_description: cleanDesc,
        location: locationFallback || activeRecord?.location || farmer?.field,
        check_out_time: currentTimeStr,
      });
      setWorkDescription("");
      onOpenChange(false);
    } catch {
      // Error handled by mutation toast
    }
  };

  const isFormValid = workDescription.trim().length >= 5;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <LogOut className="size-4" aria-hidden="true" />
            </div>
            <div>
              <DialogTitle>Complete Work Session</DialogTitle>
              <DialogDescription>
                Record shift completion and dispatch the automated daily work report.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <form onSubmit={handleCheckoutSubmit} className="space-y-4">
          {/* Shift Details Summary */}
          <div className="rounded-lg border border-border bg-muted/40 p-3.5 text-xs space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground font-medium">Worker:</span>
              <span className="font-semibold text-foreground">
                {farmer?.name ?? activeRecord?.farmer_name ?? "Selected Worker"}
              </span>
            </div>
            {(farmer?.email || activeRecord?.farmer_email) && (
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground font-medium">Worker Email:</span>
                <span className="font-mono text-foreground">
                  {farmer?.email || activeRecord?.farmer_email}
                </span>
              </div>
            )}
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground font-medium">Check-In Time:</span>
              <span className="font-mono text-foreground">
                {formatTime(activeRecord?.check_in) || "Current Session"}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground font-medium">Check-Out Time:</span>
              <span className="font-mono text-foreground">{currentTimeStr}</span>
            </div>
            <div className="flex justify-between items-center pt-1 border-t border-border/60">
              <span className="text-muted-foreground font-medium">Report Recipients:</span>
              <span className="text-primary font-medium text-[11px]">
                Worker Email &amp; Administrator (hariharan4814@gmail.com)
              </span>
            </div>
          </div>

          {/* Mandatory Work Description */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="work-desc" className="text-xs font-semibold">
                What work did you complete today? <span className="text-destructive">*</span>
              </Label>
              <span className="text-[11px] text-muted-foreground">
                {workDescription.trim().length} chars (min 5)
              </span>
            </div>
            <Textarea
              id="work-desc"
              rows={4}
              placeholder="Example: Completed irrigation in Field A, applied organic fertilizer, and inspected tomato crops for pests."
              value={workDescription}
              onChange={(e) => {
                setWorkDescription(e.target.value);
                if (error) setError(null);
              }}
              className="text-xs resize-none"
              required
            />
            {error && <p className="text-xs text-destructive">{error}</p>}
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              This summary will be permanently attached to the shift record and sent as an HTML
              report to the worker and farm supervisor.
            </p>
          </div>

          <DialogFooter className="gap-2 sm:gap-0 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={checkOut.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!isFormValid || checkOut.isPending}>
              {checkOut.isPending ? (
                <>
                  <Loader2 className="size-4 animate-spin mr-1.5" aria-hidden="true" />
                  Saving &amp; Sending Report...
                </>
              ) : (
                <>
                  <CheckCircle2 className="size-4 mr-1.5" aria-hidden="true" />
                  Complete Shift &amp; Send Report
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

/* -------------------------------------------------------------------------- */
/* Work Session Details Modal Dialog                                          */
/* -------------------------------------------------------------------------- */
function WorkDetailsDialog({
  record,
  open,
  onOpenChange,
}: {
  record: AttendanceRecord | null;
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  if (!record) return null;
  const hours = toNumber(record.total_hours);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <FileText className="size-4" aria-hidden="true" />
            </div>
            <div>
              <DialogTitle>Work Session Summary</DialogTitle>
              <DialogDescription>Shift log and verified daily work report.</DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 text-xs">
          {/* Worker & Time Cards */}
          <div className="rounded-lg border border-border bg-muted/30 p-3.5 space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground font-medium">Worker:</span>
              <span className="font-semibold text-foreground text-sm">
                {record.farmer_name ?? `Farmer #${record.farmer}`}
              </span>
            </div>
            {record.farmer_email && (
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground font-medium">Email:</span>
                <span className="font-mono text-foreground">{record.farmer_email}</span>
              </div>
            )}
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground font-medium">Date:</span>
              <span className="font-medium text-foreground">{formatDate(record.date)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground font-medium">Location:</span>
              <span className="font-medium text-foreground">{record.location || "Main Field"}</span>
            </div>
            <div className="grid grid-cols-3 gap-2 pt-2 border-t border-border text-center">
              <div className="bg-background rounded p-1.5 border border-border/50">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">
                  Check-In
                </span>
                <span className="font-mono font-semibold">{formatTime(record.check_in)}</span>
              </div>
              <div className="bg-background rounded p-1.5 border border-border/50">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">
                  Check-Out
                </span>
                <span className="font-mono font-semibold">{formatTime(record.check_out)}</span>
              </div>
              <div className="bg-background rounded p-1.5 border border-border/50">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider block">
                  Duration
                </span>
                <span className="font-mono font-bold text-primary">
                  {hours !== null && hours !== undefined ? `${hours.toFixed(2)} hrs` : "—"}
                </span>
              </div>
            </div>
          </div>

          {/* Work Completed Display Card */}
          <div className="rounded-lg border border-border bg-card p-3.5 space-y-1.5">
            <div className="flex items-center gap-1.5 font-semibold text-foreground">
              <FileText className="size-3.5 text-primary" aria-hidden="true" />
              <span>Work Completed Today:</span>
            </div>
            <p className="text-xs leading-relaxed text-foreground/90 whitespace-pre-wrap bg-muted/30 p-2.5 rounded border border-border/40">
              {record.work_description || "No specific task notes provided for this shift."}
            </p>
          </div>

          {/* Email Dispatch Audit Status */}
          <div className="rounded-lg border border-border p-3 space-y-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground block">
              Automated Email Delivery Audit
            </span>
            {record.email_sent ? (
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="size-4 shrink-0" aria-hidden="true" />
                <div className="text-[11px]">
                  <span className="font-medium">Report Delivered</span>
                  {record.email_sent_at && (
                    <span className="text-muted-foreground ml-1">
                      ({formatDateTime(record.email_sent_at)})
                    </span>
                  )}
                </div>
              </div>
            ) : record.email_error ? (
              <div className="flex items-start gap-2 text-amber-600 dark:text-amber-400">
                <AlertCircle className="size-4 shrink-0 mt-0.5" aria-hidden="true" />
                <div className="text-[11px]">
                  <span className="font-medium">Delivery Notice:</span> {record.email_error}
                </div>
              </div>
            ) : record.check_out ? (
              <div className="flex items-center gap-2 text-muted-foreground text-[11px]">
                <Clock className="size-3.5" aria-hidden="true" />
                <span>Email dispatch recorded.</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-muted-foreground text-[11px]">
                <Clock className="size-3.5" aria-hidden="true" />
                <span>Work session active &mdash; report will send upon checkout.</span>
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button type="button" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/* -------------------------------------------------------------------------- */
/* Main Attendance Management Page                                            */
/* -------------------------------------------------------------------------- */
function AttendancePage() {
  const { isStaff } = useAuth();
  const attendance = useAttendance();
  const farmers = useFarmers();
  const { checkIn } = useAttendanceActions();
  const [selectedFarmerId, setSelectedFarmerId] = useState<string>("");
  const [locationInput, setLocationInput] = useState<string>("");

  // Checkout modal state
  const [checkoutModalOpen, setCheckoutModalOpen] = useState<boolean>(false);
  const [checkoutFarmer, setCheckoutFarmer] = useState<Farmer | null>(null);
  const [checkoutRecord, setCheckoutRecord] = useState<AttendanceRecord | null>(null);

  // Detail view state
  const [detailsModalOpen, setDetailsModalOpen] = useState<boolean>(false);
  const [viewingRecord, setViewingRecord] = useState<AttendanceRecord | null>(null);

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
  const selectedFarmer =
    (farmers.data ?? []).find((f) => String(f.id) === selectedFarmerId) ?? null;

  const handleOpenCheckout = (farmer: Farmer | null, record?: AttendanceRecord | null) => {
    setCheckoutFarmer(farmer);
    setCheckoutRecord(record ?? null);
    setCheckoutModalOpen(true);
  };

  const handleOpenDetails = (record: AttendanceRecord) => {
    setViewingRecord(record);
    setDetailsModalOpen(true);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Attendance &amp; Work Reports"
        description="Shift console with mandatory work tracking and automated email summary reporting."
      />

      {isStaff && (
        <section className="surface-card reveal p-5">
          <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
            Shift Console
          </h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-[1.5fr_1.5fr_auto] sm:items-end">
            <div className="space-y-2">
              <label htmlFor="farmer-select" className="text-xs font-medium text-muted-foreground">
                Select Registered Worker *
              </label>
              <Select value={selectedFarmerId} onValueChange={setSelectedFarmerId}>
                <SelectTrigger id="farmer-select" className="w-full">
                  <SelectValue placeholder="Choose a registered farmer" />
                </SelectTrigger>
                <SelectContent>
                  {(farmers.data ?? []).map((f) => (
                    <SelectItem key={f.id} value={String(f.id)}>
                      {f.name} ({f.field}) &mdash; {f.email || "No email"}
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
                placeholder="e.g. Sector 4 - North Orchard"
                value={locationInput}
                onChange={(e) => setLocationInput(e.target.value)}
              />
            </div>

            <div className="flex gap-2">
              <Button
                disabled={!selectedFarmer || checkIn.isPending}
                onClick={() =>
                  selectedFarmer &&
                  checkIn.mutate({
                    farmer_id: selectedFarmer.id,
                    location: locationInput || undefined,
                  })
                }
              >
                {checkIn.isPending ? (
                  <Loader2 className="size-4 animate-spin mr-1.5" aria-hidden="true" />
                ) : (
                  <LogIn className="size-4 mr-1.5" aria-hidden="true" />
                )}
                Check in
              </Button>
              <Button
                variant="outline"
                disabled={!selectedFarmer}
                onClick={() => handleOpenCheckout(selectedFarmer)}
              >
                <LogOut className="size-4 mr-1.5" aria-hidden="true" />
                Check out
              </Button>
            </div>
          </div>
        </section>
      )}

      <Tabs defaultValue="records">
        <TabsList>
          <TabsTrigger value="records">Daily Attendance &amp; Work Activity</TabsTrigger>
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
                    <TableHead>Worker</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Check In</TableHead>
                    <TableHead>Check Out</TableHead>
                    <TableHead>Total Hours</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Work Completed Today</TableHead>
                    <TableHead>Status &amp; Report</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {records.map((r) => {
                    const state = shiftState(r);
                    const hours = toNumber(r.total_hours);
                    const matchingFarmer =
                      (farmers.data ?? []).find((f) => f.id === r.farmer) ?? null;

                    return (
                      <TableRow key={r.id}>
                        <TableCell className="font-medium">
                          <div>
                            <span className="font-semibold text-foreground">
                              {r.farmer_name ?? `Farmer #${r.farmer}`}
                            </span>
                            {r.farmer_email && (
                              <span className="block text-[11px] text-muted-foreground truncate max-w-[160px]">
                                {r.farmer_email}
                              </span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>{formatDate(r.date)}</TableCell>
                        <TableCell className="font-mono text-xs">
                          {formatTime(r.check_in)}
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          {formatTime(r.check_out)}
                        </TableCell>
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
                        <TableCell className="max-w-[200px]">
                          {r.work_description ? (
                            <span
                              className="line-clamp-2 text-xs text-foreground/90 cursor-pointer hover:underline"
                              onClick={() => handleOpenDetails(r)}
                              title={r.work_description}
                            >
                              {r.work_description}
                            </span>
                          ) : (
                            <span className="text-muted-foreground text-xs italic">
                              {r.check_out ? "No details" : "Shift in progress"}
                            </span>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col gap-1 items-start">
                            <Badge variant={state.variant}>{state.label}</Badge>
                            {r.email_sent && (
                              <span className="inline-flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400">
                                <Mail className="size-3" aria-hidden="true" />
                                Report sent
                              </span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1.5">
                            {!r.check_out && isStaff ? (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleOpenCheckout(matchingFarmer, r)}
                              >
                                <LogOut className="size-3.5 mr-1" aria-hidden="true" />
                                Checkout
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleOpenDetails(r)}
                              >
                                View Report
                              </Button>
                            )}
                          </div>
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
                      <TableHead>Worker</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Check In</TableHead>
                      <TableHead>Check Out</TableHead>
                      <TableHead>Total Hours</TableHead>
                      <TableHead>Location</TableHead>
                      <TableHead>Work Completed</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {report.data.records.map((r) => (
                      <TableRow key={r.id}>
                        <TableCell className="font-medium">
                          {r.farmer_name ?? `Farmer #${r.farmer}`}
                        </TableCell>
                        <TableCell>{formatDate(r.date)}</TableCell>
                        <TableCell className="font-mono text-xs">
                          {formatTime(r.check_in)}
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          {formatTime(r.check_out)}
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          {r.total_hours ? `${r.total_hours.toFixed(2)} hrs` : "—"}
                        </TableCell>
                        <TableCell>{r.location ?? "—"}</TableCell>
                        <TableCell className="max-w-[220px]">
                          <span
                            className="line-clamp-2 text-xs cursor-pointer hover:underline"
                            onClick={() => handleOpenDetails(r)}
                            title={r.work_description ?? ""}
                          >
                            {r.work_description || "—"}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button size="sm" variant="ghost" onClick={() => handleOpenDetails(r)}>
                            Details
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Checkout Modal Dialog */}
      {checkoutModalOpen && (
        <CheckOutModal
          open={checkoutModalOpen}
          onOpenChange={setCheckoutModalOpen}
          farmer={checkoutFarmer}
          activeRecord={checkoutRecord}
          locationFallback={locationInput}
        />
      )}

      {/* Work Details Dialog */}
      {detailsModalOpen && (
        <WorkDetailsDialog
          record={viewingRecord}
          open={detailsModalOpen}
          onOpenChange={setDetailsModalOpen}
        />
      )}
    </div>
  );
}

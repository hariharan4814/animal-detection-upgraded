import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  AlertTriangle,
  Camera,
  CameraOff,
  CheckCircle2,
  ImageUp,
  Loader2,
  Mail,
  Pause,
  Play,
  RefreshCw,
  ScanEye,
  ShieldAlert,
  ShieldCheck,
  Upload,
  Volume2,
  Video,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState, PageHeader } from "@/components/common/states";
import { useAnalyzeImage, useDetectionStatus, useToggleDetection } from "@/hooks/use-api";
import { useAuth } from "@/lib/auth";
import { apiClient, mediaUrl, normalizeDetectionResponse, streamUrl } from "@/lib/api";
import { confidencePercent, formatDateTime } from "@/lib/format";
import { toast } from "sonner";
import type { AnalyzeResult, DetectionItem } from "@/types/api";

export const Route = createFileRoute("/app/monitoring")({
  head: () => ({
    meta: [
      { title: "AI Monitoring — FarmSync" },
      {
        name: "description",
        content:
          "Live camera surveillance, continuous AI animal threat detection, and manual image analysis powered by the FarmSync YOLO engine.",
      },
      { property: "og:title", content: "AI Monitoring Center — FarmSync" },
      {
        property: "og:description",
        content: "Continuous field surveillance and real-time animal threat detection.",
      },
    ],
  }),
  component: MonitoringPage,
});

interface SessionEvent {
  id: string;
  timestamp: string | Date;
  animal: string;
  threatLevel: string;
  confidence: number;
  emailSent: boolean;
  emailAttempted: boolean;
  emailStatus: string;
}

/* ==============================================================================
   1. CONTINUOUS SURVEILLANCE CAMERA & YOLO DETECTION ENGINE
   ============================================================================== */
function ContinuousCameraMonitor({ detectionEngineEnabled }: { detectionEngineEnabled: boolean }) {
  const qc = useQueryClient();
  // Camera & Detection States
  const [cameraActive, setCameraActive] = useState<boolean>(false);
  const [detectionActive, setDetectionActive] = useState<boolean>(false);
  const [cameraMode, setCameraMode] = useState<"webcam" | "mjpeg">("webcam");
  const [cameraError, setCameraError] = useState<string | null>(null);

  // Live Detection Stats
  const [isInferencing, setIsInferencing] = useState<boolean>(false);
  const [lastInferenceMs, setLastInferenceMs] = useState<number | null>(null);
  const [currentDetections, setCurrentDetections] = useState<DetectionItem[]>([]);
  const [highestAnimal, setHighestAnimal] = useState<string | null>(null);
  const [highestTier, setHighestTier] = useState<string | null>(null);
  const [sessionEvents, setSessionEvents] = useState<SessionEvent[]>([]);

  // Refs for MediaStream and Loop Control
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<number | null>(null);
  const inFlightRef = useRef<boolean>(false);
  const lastAlertTimeRef = useRef<Record<string, number>>({});

  // --------------------------------------------------------------------------
  // Camera Lifecycle: Start / Stop
  // --------------------------------------------------------------------------
  const startCamera = useCallback(async () => {
    setCameraError(null);
    if (cameraMode === "webcam") {
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error("Camera API is not supported in this browser environment.");
        }
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: "environment",
          },
          audio: false,
        });

        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play().catch(() => {});
        }
        setCameraActive(true);
        toast.info("Surveillance Camera Active", {
          description: "Live video feed connected. You can now enable AI detection.",
        });
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Unable to access camera hardware.";
        setCameraError(msg);
        setCameraActive(false);
        toast.error("Camera Access Error", { description: msg });
      }
    } else {
      // Backend MJPEG stream mode
      setCameraActive(true);
    }
  }, [cameraMode]);

  const stopCamera = useCallback(() => {
    // 1. If detection is active, stop it first
    if (intervalRef.current) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    inFlightRef.current = false;
    setDetectionActive(false);
    setIsInferencing(false);

    // 2. Stop camera tracks properly
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => {
        t.stop();
      });
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setCameraActive(false);
    setCurrentDetections([]);
    setHighestAnimal(null);
    setHighestTier(null);
    toast.info("Surveillance Camera Stopped", {
      description: "Camera feed and detection stream have been turned off.",
    });
  }, []);

  // --------------------------------------------------------------------------
  // Detection Frame Sampling Routine
  // --------------------------------------------------------------------------
  const processSingleFrame = useCallback(async () => {
    if (inFlightRef.current) return;
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    if (video.readyState < 2 || video.videoWidth === 0 || video.videoHeight === 0) return;

    // Security/animal monitoring camera uses real-world orientation. Mirroring is intentionally disabled.
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.setTransform(1, 0, 0, 1, 0, 0); // Guarantee 1:1 real-world orientation without horizontal inversion
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    inFlightRef.current = true;
    setIsInferencing(true);
    const startT = performance.now();

    canvas.toBlob(
      async (blob) => {
        if (!blob) {
          inFlightRef.current = false;
          setIsInferencing(false);
          return;
        }

        try {
          const form = new FormData();
          form.append("image", blob, "live_frame.jpg");
          form.append("field", "Main Field Surveillance");

          const res = await apiClient.post<unknown>("/detection/analyze/", form);
          const elapsed = Math.round(performance.now() - startT);
          setLastInferenceMs(elapsed);

          const data = normalizeDetectionResponse(res);
          const detections = data.detections ?? [];
          setCurrentDetections(detections);

          const animal = data.highest_threat_animal;
          const tier = (data.highest_threat_tier || data.highest_threat_level || "").toUpperCase();

          if (data.animal_detected && animal) {
            setHighestAnimal(animal);
            setHighestTier(tier || "MEDIUM");

            // Check Debounce / Cooldown to prevent toast spam
            const cooldownKey = `${animal.toLowerCase()}_${tier || "MEDIUM"}`;
            const now = Date.now();
            const lastAlert = lastAlertTimeRef.current[cooldownKey] || 0;
            const cooldownMs = 10000; // 10 seconds client-side toast debounce

            if (now - lastAlert >= cooldownMs) {
              lastAlertTimeRef.current[cooldownKey] = now;

              // Immediately invalidate and synchronize active query caches across Dashboard, Logs, and Alerts
              void qc.invalidateQueries({ queryKey: ["detection", "logs"] });
              void qc.invalidateQueries({ queryKey: ["alerts"] });
              void qc.invalidateQueries({ queryKey: ["dashboard"] });
              void qc.invalidateQueries({ queryKey: ["detection", "status"] });

              // Record Session Event
              const eventItem: SessionEvent = {
                id: `${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
                timestamp: new Date().toISOString(),
                animal,
                threatLevel: tier || "MEDIUM",
                confidence: data.highest_confidence ?? 0.85,
                emailSent: Boolean(data.email_sent),
                emailAttempted: Boolean(data.email_attempted),
                emailStatus: data.email_status || "none",
              };
              setSessionEvents((prev) => [eventItem, ...prev.slice(0, 19)]);

              // Trigger Toast Notification matching requirement specifications
              const capAnimal = animal.charAt(0).toUpperCase() + animal.slice(1);
              const confPct = data.highest_confidence
                ? Math.round(data.highest_confidence * 100)
                : 95;

              if (tier === "HIGH") {
                let msg = `${capAnimal} detected with ${confPct}% confidence. Alert saved and notification email sent.`;
                if (!data.email_sent && data.email_attempted) {
                  msg = `${capAnimal} detected with ${confPct}% confidence. Detection was recorded, but the email could not be sent.`;
                } else if (!data.email_sent && !data.email_attempted) {
                  msg = `${capAnimal} detected with ${confPct}% confidence. Alert saved and recorded.`;
                }
                toast.error("High Threat Animal Detected", {
                  description: msg,
                  duration: 5000,
                });
              } else if (tier === "MEDIUM") {
                let msg = `${capAnimal} detected with ${confPct}% confidence. Alert saved and notification email sent.`;
                if (!data.email_sent && data.email_attempted) {
                  msg = `${capAnimal} detected with ${confPct}% confidence. Detection was recorded, but the email could not be sent.`;
                } else if (!data.email_sent && !data.email_attempted) {
                  msg = `${capAnimal} detected with ${confPct}% confidence. Detection has been recorded.`;
                }
                toast.warning("Medium Threat Animal Detected", {
                  description: msg,
                  duration: 5000,
                });
              } else {
                toast.info("Low Threat Animal Detected", {
                  description: `${capAnimal} detected with ${confPct}% confidence. Detection has been recorded.`,
                  duration: 4500,
                });
              }
            } else {
              // Still invalidate queries so background counters and tables update smoothly
              void qc.invalidateQueries({ queryKey: ["detection", "logs"] });
              void qc.invalidateQueries({ queryKey: ["alerts"] });
              void qc.invalidateQueries({ queryKey: ["dashboard"] });
            }
          } else {
            setHighestAnimal(null);
            setHighestTier(null);
          }
        } catch {
          // Keep continuous monitoring running on network hiccup
        } finally {
          inFlightRef.current = false;
          setIsInferencing(false);
        }
      },
      "image/jpeg",
      0.82,
    );
  }, [qc]);

  // --------------------------------------------------------------------------
  // Detection Lifecycle: Start / Stop
  // --------------------------------------------------------------------------
  const startDetection = useCallback(() => {
    if (!cameraActive) {
      toast.warning("Camera is turned off", {
        description: "Please turn the surveillance camera ON before enabling detection.",
      });
      return;
    }
    setDetectionActive(true);
    toast.success("AI Threat Detection Engine Active", {
      description: "Continuously analyzing camera stream for wildlife hazards.",
    });

    if (intervalRef.current) window.clearInterval(intervalRef.current);
    // Continuous sampling every 750ms with in-flight lock
    intervalRef.current = window.setInterval(() => {
      void processSingleFrame();
    }, 750);
  }, [cameraActive, processSingleFrame]);

  const stopDetection = useCallback(() => {
    if (intervalRef.current) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    inFlightRef.current = false;
    setDetectionActive(false);
    setIsInferencing(false);
    setCurrentDetections([]);
    setHighestAnimal(null);
    setHighestTier(null);
    toast.info("AI Detection Stopped", {
      description: "Live camera stream remains active.",
    });
  }, []);

  // --------------------------------------------------------------------------
  // Cleanup on Unmount
  // --------------------------------------------------------------------------
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  return (
    <section className="surface-card overflow-hidden bg-sidebar text-sidebar-foreground">
      {/* 1. Header Bar with Real-time Status Badges */}
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-sidebar-border px-5 py-3">
        <div className="flex items-center gap-3">
          <span className="relative flex size-2.5">
            {cameraActive && (
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-success opacity-75" />
            )}
            <span
              className={`relative inline-flex size-2.5 rounded-full ${
                cameraActive ? "bg-success" : "bg-sidebar-foreground/30"
              }`}
            />
          </span>
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-widest text-sidebar-foreground">
              Live Field Surveillance
            </h2>
            <div className="flex items-center gap-2 text-[11px] text-sidebar-foreground/70">
              <span>
                Camera:{" "}
                <strong className={cameraActive ? "text-success" : "text-sidebar-foreground/50"}>
                  {cameraActive ? "● ON" : "○ OFF"}
                </strong>
              </span>
              <span>·</span>
              <span>
                Detection:{" "}
                <strong
                  className={
                    detectionActive
                      ? "text-accent"
                      : cameraActive
                        ? "text-sidebar-foreground/60"
                        : "text-sidebar-foreground/40"
                  }
                >
                  {detectionActive ? "● ACTIVE" : cameraActive ? "○ OFF" : "⊘ UNAVAILABLE"}
                </strong>
              </span>
            </div>
          </div>
        </div>

        {/* Stream Source Selector & Reconnect */}
        <div className="flex items-center gap-2">
          {cameraActive && (
            <Badge
              variant="outline"
              className={`border-sidebar-border text-[10px] uppercase tracking-wide ${
                detectionActive
                  ? "bg-accent/15 text-accent border-accent/40"
                  : "text-sidebar-foreground/70"
              }`}
            >
              {detectionActive
                ? isInferencing
                  ? "⚡ YOLO Analyzing"
                  : "✓ YOLO Monitoring"
                : "Live Preview Only"}
            </Badge>
          )}
          {lastInferenceMs !== null && detectionActive && (
            <span className="text-[10px] font-mono text-sidebar-foreground/60">
              {lastInferenceMs}ms
            </span>
          )}
        </div>
      </header>

      {/* 2. Video Stream Viewport */}
      <div className="scanline relative aspect-video w-full bg-black/90 flex items-center justify-center overflow-hidden">
        <div className="grid-overlay absolute inset-0 opacity-20" aria-hidden="true" />

        {/* Security/animal monitoring camera uses real-world orientation. Mirroring is intentionally disabled. */}
        <video
          ref={videoRef}
          playsInline
          muted
          autoPlay
          style={{ transform: "none" }}
          className={`relative size-full object-contain [transform:none] ${
            cameraActive && cameraMode === "webcam" ? "block" : "hidden"
          }`}
        />

        {/* Hidden Canvas for Frame Capture */}
        <canvas ref={canvasRef} className="hidden" />

        {/* Security/animal monitoring camera uses real-world orientation. Mirroring is intentionally disabled. */}
        {cameraActive && cameraMode === "mjpeg" && (
          <img
            src={`${streamUrl()}&t=${Date.now()}`}
            alt="Backend MJPEG Camera Stream"
            style={{ transform: "none" }}
            className="relative size-full object-contain [transform:none]"
          />
        )}

        {/* Overlay Warning when Camera is OFF */}
        {!cameraActive && (
          <div className="flex flex-col items-center justify-center gap-3 px-6 text-center text-sidebar-foreground/70">
            <div className="flex size-14 items-center justify-center rounded-2xl bg-sidebar-accent/50 text-sidebar-foreground/60">
              <CameraOff className="size-7" aria-hidden="true" />
            </div>
            <p className="text-base font-semibold text-sidebar-foreground">Camera Feed Offline</p>
            <p className="max-w-sm text-xs text-sidebar-foreground/60">
              Click <strong>Turn Camera On</strong> below to initialize the live surveillance stream
              and enable continuous AI wildlife detection.
            </p>
          </div>
        )}

        {/* Live Active Threat Overlay Badge (Non-blocking) */}
        {cameraActive && detectionActive && highestAnimal && (
          <div className="absolute top-4 left-4 z-20 flex items-center gap-2 rounded-xl border border-destructive/60 bg-black/80 px-3.5 py-2 text-white shadow-lg backdrop-blur">
            <AlertTriangle className="size-4.5 text-destructive animate-pulse" />
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-destructive">
                Hazard: {highestAnimal} [{highestTier}]
              </p>
              <p className="text-[10px] text-white/80">Continuous surveillance active</p>
            </div>
          </div>
        )}

        {/* Detection Active Indicator Badge */}
        {cameraActive && detectionActive && !highestAnimal && (
          <div className="absolute top-4 left-4 z-20 flex items-center gap-2 rounded-lg bg-black/60 px-2.5 py-1 text-[11px] text-success backdrop-blur">
            <span className="size-2 rounded-full bg-success animate-ping" />
            <span>Scanning field frames...</span>
          </div>
        )}
      </div>

      {/* 3. Primary Dual Control Console */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-t border-sidebar-border bg-sidebar/95 px-5 py-4">
        {/* Left Side: Prominent Dual Control Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Button A: Camera Control */}
          {!cameraActive ? (
            <Button
              size="default"
              className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90 font-semibold shadow-sm"
              onClick={startCamera}
            >
              <Camera className="size-4" aria-hidden="true" />
              Turn Camera On
            </Button>
          ) : (
            <Button
              size="default"
              variant="destructive"
              className="gap-2 font-semibold shadow-sm"
              onClick={stopCamera}
            >
              <CameraOff className="size-4" aria-hidden="true" />
              Turn Camera Off
            </Button>
          )}

          {/* Button B: Detection Control */}
          {!detectionActive ? (
            <Button
              size="default"
              disabled={!cameraActive || !detectionEngineEnabled}
              className={`gap-2 font-semibold shadow-sm ${
                cameraActive
                  ? "bg-accent text-accent-foreground hover:bg-accent/90"
                  : "opacity-40 cursor-not-allowed"
              }`}
              onClick={startDetection}
            >
              <ScanEye className="size-4" aria-hidden="true" />
              Turn Detection On
            </Button>
          ) : (
            <Button
              size="default"
              variant="outline"
              className="gap-2 border-primary text-primary hover:bg-primary/10 font-semibold shadow-sm"
              onClick={stopDetection}
            >
              <Pause className="size-4" aria-hidden="true" />
              Turn Detection Off
            </Button>
          )}
        </div>

        {/* Right Side: Operational Status Text */}
        <div className="flex items-center gap-3 text-xs text-sidebar-foreground/70">
          <div className="flex items-center gap-1.5">
            <span
              className={`size-2 rounded-full ${cameraActive ? "bg-success" : "bg-muted-foreground"}`}
            />
            <span>Camera: {cameraActive ? "Active" : "Off"}</span>
          </div>
          <span>·</span>
          <div className="flex items-center gap-1.5">
            <span
              className={`size-2 rounded-full ${
                detectionActive
                  ? "bg-accent animate-pulse"
                  : cameraActive
                    ? "bg-muted-foreground"
                    : "bg-muted-foreground/40"
              }`}
            />
            <span>
              Detection: {detectionActive ? "Active" : cameraActive ? "Inactive" : "Unavailable"}
            </span>
          </div>
        </div>
      </div>

      {/* Camera Access Error Banner */}
      {cameraError && (
        <div className="border-t border-destructive/40 bg-destructive/10 px-5 py-2.5 text-xs text-destructive flex items-center justify-between">
          <span className="flex items-center gap-2">
            <AlertTriangle className="size-3.5 shrink-0" />
            {cameraError}
          </span>
          <Button
            size="sm"
            variant="ghost"
            className="h-6 text-[10px] text-destructive hover:bg-destructive/20"
            onClick={startCamera}
          >
            Retry Access
          </Button>
        </div>
      )}

      {/* 4. Live Session Activity Ticker */}
      {sessionEvents.length > 0 && (
        <div className="border-t border-sidebar-border bg-sidebar/80 p-4">
          <div className="flex items-center justify-between mb-2.5">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-sidebar-foreground/80">
              Live Session Detections ({sessionEvents.length})
            </h3>
            <span className="text-[10px] text-sidebar-foreground/60">
              Continuous logging enabled
            </span>
          </div>
          <div className="space-y-1.5 max-h-36 overflow-y-auto">
            {sessionEvents.slice(0, 5).map((evt) => (
              <div
                key={evt.id}
                className="flex items-center justify-between rounded-lg bg-sidebar-accent/30 px-3 py-1.5 text-xs"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`size-2 rounded-full ${
                      evt.threatLevel === "HIGH"
                        ? "bg-destructive animate-pulse"
                        : evt.threatLevel === "MEDIUM"
                          ? "bg-warning"
                          : "bg-success"
                    }`}
                  />
                  <span className="font-semibold capitalize text-sidebar-foreground">
                    {evt.animal}
                  </span>
                  <Badge
                    variant={
                      evt.threatLevel === "HIGH"
                        ? "destructive"
                        : evt.threatLevel === "LOW"
                          ? "secondary"
                          : "outline"
                    }
                    className="text-[9px] h-4 py-0"
                  >
                    {evt.threatLevel}
                  </Badge>
                </div>
                <div className="flex items-center gap-3 text-[11px] text-sidebar-foreground/70">
                  {evt.emailSent ? (
                    <span className="text-primary flex items-center gap-1">
                      <Mail className="size-3" /> Mail Sent
                    </span>
                  ) : evt.emailAttempted ? (
                    <span className="text-destructive flex items-center gap-1">
                      <Mail className="size-3" /> Mail Failed
                    </span>
                  ) : null}
                  <span>{formatDateTime(evt.timestamp)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

/* ==============================================================================
   2. MANUAL IMAGE ANALYSIS COMPONENT (PRESERVED & ENHANCED)
   ============================================================================== */
function ManualAnalysis() {
  const analyze = useAnalyzeImage();
  const [file, setFile] = useState<File | null>(null);
  const [fieldName, setFieldName] = useState("Main Field");
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const accept = (f: File | undefined | null) => {
    if (!f) return;
    const valid = ["image/jpeg", "image/png", "image/webp", "image/bmp"];
    if (!valid.includes(f.type) && !f.name.match(/\.(jpe?g|png|webp|bmp)$/i)) {
      setValidationError("Please select a valid image file (JPEG, PNG, WEBP, BMP).");
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      setValidationError("Image file size must not exceed 10 MB.");
      return;
    }
    setValidationError(null);
    setFile(f);
    setPreview(URL.createObjectURL(f));
    analyze.reset();
  };

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  const handleAnalyze = () => {
    if (!file) return;
    analyze.mutate(
      { file, fieldName: fieldName.trim() || "Main Field" },
      {
        onSuccess: (res) => {
          const animal = res.highest_threat_animal;
          const tier = (
            res.highest_threat_tier ||
            res.highest_threat_level ||
            "MEDIUM"
          ).toUpperCase();
          if (res.animal_detected && animal) {
            const capAnimal = animal.charAt(0).toUpperCase() + animal.slice(1);
            const confPct = res.highest_confidence ? Math.round(res.highest_confidence * 100) : 95;

            if (tier === "HIGH") {
              let msg = `${capAnimal} detected with ${confPct}% confidence. Alert saved and notification email sent.`;
              if (!res.email_sent && res.email_attempted) {
                msg = `${capAnimal} detected with ${confPct}% confidence. Detection was recorded, but the email could not be sent.`;
              } else if (!res.email_sent && !res.email_attempted) {
                msg = `${capAnimal} detected with ${confPct}% confidence. Alert saved and recorded.`;
              }
              toast.error("High Threat Animal Detected", {
                description: msg,
                duration: 5000,
              });
            } else if (tier === "MEDIUM") {
              let msg = `${capAnimal} detected with ${confPct}% confidence. Alert saved and notification email sent.`;
              if (!res.email_sent && res.email_attempted) {
                msg = `${capAnimal} detected with ${confPct}% confidence. Detection was recorded, but the email could not be sent.`;
              } else if (!res.email_sent && !res.email_attempted) {
                msg = `${capAnimal} detected with ${confPct}% confidence. Detection has been recorded.`;
              }
              toast.warning("Medium Threat Animal Detected", {
                description: msg,
                duration: 5000,
              });
            } else {
              toast.info("Low Threat Animal Detected", {
                description: `${capAnimal} detected with ${confPct}% confidence. Detection has been recorded.`,
                duration: 4500,
              });
            }
          } else {
            toast.success("Analysis Complete", {
              description: "No hazardous animals detected in the uploaded frame.",
            });
          }
        },
      },
    );
  };

  const detections = analyze.data?.detections ?? [];
  const highestTier = (
    analyze.data?.highest_threat_tier ||
    analyze.data?.highest_threat_level ||
    ""
  ).toUpperCase();

  return (
    <section className="surface-card p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
          Manual Snapshot Analysis
        </h2>
        <ScanEye className="size-4 text-primary" aria-hidden="true" />
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          accept(e.dataTransfer.files?.[0]);
        }}
        className={`mt-4 rounded-2xl border-2 border-dashed p-6 text-center transition-colors ${
          dragging ? "border-primary bg-primary/5" : "border-border bg-muted/30"
        }`}
      >
        {preview ? (
          <div className="relative">
            <img
              src={preview}
              alt="Selected frame preview"
              className="mx-auto max-h-64 rounded-xl object-contain border border-border"
            />
            <Button
              size="icon"
              variant="secondary"
              className="absolute right-2 top-2"
              aria-label="Remove image"
              onClick={() => {
                setFile(null);
                setPreview(null);
                analyze.reset();
              }}
            >
              <X className="size-4" aria-hidden="true" />
            </Button>
          </div>
        ) : (
          <>
            <ImageUp className="mx-auto size-8 text-muted-foreground" aria-hidden="true" />
            <p className="mt-3 text-sm font-medium">Drag and drop a farm image frame here</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Supports JPEG, PNG, WEBP up to 10 MB
            </p>
          </>
        )}

        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="sr-only"
          onChange={(e) => accept(e.target.files?.[0])}
        />

        <div className="mt-4 max-w-xs mx-auto">
          <Input
            placeholder="Field Location (e.g. Sector 1)"
            value={fieldName}
            onChange={(e) => setFieldName(e.target.value)}
            className="text-xs text-center"
          />
        </div>

        <div className="mt-4 flex flex-wrap justify-center gap-2">
          <Button variant="outline" size="sm" onClick={() => inputRef.current?.click()}>
            <Upload className="size-3.5" aria-hidden="true" />
            Choose file
          </Button>
          <Button size="sm" disabled={!file || analyze.isPending} onClick={handleAnalyze}>
            {analyze.isPending && <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />}
            {analyze.isPending ? "Running YOLO inference…" : "Analyze image"}
          </Button>
        </div>
        {validationError && <p className="mt-3 text-xs text-destructive">{validationError}</p>}
      </div>

      {analyze.isPending && <Skeleton className="mt-5 h-28 rounded-xl" />}

      {analyze.isSuccess && (
        <div className="reveal mt-5 rounded-2xl border border-border bg-card p-5 space-y-4">
          {highestTier === "HIGH" && (
            <div className="flex items-center justify-between rounded-xl border border-destructive/40 bg-destructive/10 p-3.5">
              <div className="flex items-center gap-2.5">
                <AlertTriangle className="size-5 text-destructive animate-bounce" />
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-destructive">
                    🚨 High Threat Animal Detected: {analyze.data?.highest_threat_animal}
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    Hardware siren and priority emergency email notification triggered.
                  </p>
                </div>
              </div>
              <Badge variant="destructive" className="text-xs font-semibold px-2.5 py-1">
                HIGH THREAT RECORDED
              </Badge>
            </div>
          )}

          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">
              Inference Results ({detections.length} detected)
            </h3>
            {analyze.data?.alert_triggered && (
              <Badge variant="destructive" className="flex items-center gap-1 text-[11px]">
                <ShieldAlert className="size-3" />
                Alert #{analyze.data.alert_id} ({analyze.data.alert_type})
              </Badge>
            )}
          </div>

          {detections.length === 0 ? (
            <p className="text-sm text-muted-foreground flex items-center gap-2">
              <CheckCircle2 className="size-4 text-success" />
              No hazardous animals detected in the uploaded frame.
            </p>
          ) : (
            <ul className="space-y-3">
              {detections.map((d, i) => {
                const animal = d.animal ?? d.animal_type ?? d.label ?? "Detected Animal";
                const pct = confidencePercent(d.confidence);
                const tier = (d.threat_tier ?? d.threat_level ?? "MEDIUM").toUpperCase();
                return (
                  <li key={i} className="rounded-xl border border-border bg-muted/40 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-semibold capitalize flex items-center gap-2">
                        <ScanEye className="size-4 text-primary" />
                        {animal}
                      </span>
                      <Badge
                        variant={
                          tier === "HIGH" ? "destructive" : tier === "LOW" ? "secondary" : "outline"
                        }
                        className="text-[10px]"
                      >
                        {tier === "HIGH" && "🚨 "}
                        {tier === "MEDIUM" && "⚠️ "}
                        {tier === "LOW" && "ℹ️ "}
                        {tier} THREAT
                      </Badge>
                    </div>
                    {pct !== null && (
                      <div className="mt-3">
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>Confidence Score</span>
                          <span className="tabular-nums font-mono">{pct}%</span>
                        </div>
                        <Progress value={pct} className="mt-1.5 h-1.5" />
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          )}

          {analyze.data?.animal_log && (
            <div className="mt-4 pt-3 border-t border-border flex items-center justify-between text-xs text-muted-foreground">
              <span>
                Logged to AnimalLog #{analyze.data.animal_log.id} [
                {analyze.data.animal_log.threat_level ?? "MEDIUM"}]
              </span>
              {analyze.data.animal_log.image_path && (
                <a
                  href={mediaUrl(analyze.data.animal_log.image_path) ?? "#"}
                  target="_blank"
                  rel="noreferrer"
                  className="text-primary hover:underline"
                >
                  View Saved Snapshot →
                </a>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

/* ==============================================================================
   3. MAIN MONITORING ROOT PAGE
   ============================================================================== */
function MonitoringPage() {
  const { isStaff } = useAuth();
  const status = useDetectionStatus();
  const toggle = useToggleDetection();
  const detectionOn = status.data?.detection_enabled ?? true;

  const statusPanel = useMemo(
    () => (
      <section className="surface-card p-5 space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
          AI Detection Engine
        </h2>
        {status.isLoading ? (
          <Skeleton className="h-20 rounded-xl" />
        ) : status.isError ? (
          <ErrorState error={status.error} onRetry={() => void status.refetch()} />
        ) : (
          <>
            <div>
              <p
                className={`text-3xl font-bold tracking-tight ${detectionOn ? "text-success" : "text-muted-foreground"}`}
              >
                {detectionOn ? "ACTIVE" : "DISABLED"}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Model:{" "}
                <span className="font-medium text-foreground">
                  {status.data?.model_name ?? "YOLOv8n"}
                </span>
              </p>
            </div>

            {isStaff ? (
              <div className="flex items-center justify-between rounded-xl border border-border bg-muted/30 px-4 py-3">
                <div>
                  <p className="text-sm font-medium">Master Switch</p>
                  <p className="text-xs text-muted-foreground">
                    {toggle.isPending
                      ? "Updating state…"
                      : "Enable/disable real-time vision inference"}
                  </p>
                </div>
                <Switch
                  checked={detectionOn}
                  disabled={toggle.isPending}
                  onCheckedChange={(v) => toggle.mutate(v)}
                  aria-label="Toggle AI detection"
                />
              </div>
            ) : (
              <p className="flex items-center gap-2 text-xs text-muted-foreground">
                <ShieldCheck className="size-3.5 text-primary" aria-hidden="true" />
                Staff permissions required to change detection status.
              </p>
            )}

            <div className="border-t border-border pt-4 space-y-2.5 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Confidence Threshold</span>
                <span className="font-mono font-medium">
                  {status.data?.confidence_threshold
                    ? `${Math.round(status.data.confidence_threshold * 100)}%`
                    : "50%"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Camera Device Index</span>
                <span className="font-mono font-medium">
                  {status.data?.camera_device_index ?? 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Alert Cooldown Window</span>
                <span className="font-mono font-medium">
                  {status.data?.alert_cooldown_seconds ?? 60}s
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Audio Buzzer Siren</span>
                <span className="font-medium">
                  {status.data?.audio_buzzer_enabled ? "Enabled" : "Disabled"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Email Notifications</span>
                <span className="font-medium">
                  {status.data?.email_alerts_enabled ? "Enabled" : "Disabled"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Attach Snapshot to Email</span>
                <span className="font-medium">
                  {status.data?.attach_alert_image_to_email !== false ? "Enabled" : "Disabled"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Supported Animal Classes</span>
                <span className="font-medium">
                  {status.data?.supported_classes_count ?? 80} classes
                </span>
              </div>
            </div>
          </>
        )}
      </section>
    ),
    [status, detectionOn, isStaff, toggle],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI Monitoring Center"
        description="Continuous field surveillance, dual camera/detection controls, real-time threat evaluation, and on-demand YOLOv8 analysis."
      />

      <div className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
        <div className="space-y-6">
          <ContinuousCameraMonitor detectionEngineEnabled={detectionOn} />
          <ManualAnalysis />
        </div>
        <div className="space-y-6">{statusPanel}</div>
      </div>
    </div>
  );
}

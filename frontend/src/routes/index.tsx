import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowRight,
  Bell,
  CameraIcon,
  ClipboardList,
  Cpu,
  Database,
  Leaf,
  LineChart,
  ScanEye,
  ServerCog,
  ShieldAlert,
  Sprout,
  Timer,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import heroImage from "@/assets/farm-hero.jpg";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "FarmSync — Smart Farm Management & AI Animal Detection" },
      {
        name: "description",
        content:
          "FarmSync unites workforce, attendance and task management with YOLO-powered animal intrusion detection, live camera monitoring and automated hazard alerts.",
      },
      { property: "og:title", content: "FarmSync — Where Smart Farming Meets AI Vision" },
      {
        property: "og:description",
        content:
          "AI-powered smart agriculture platform: farm operations, live monitoring, animal detection logs and automated hazard alerts.",
      },
    ],
  }),
  component: Landing,
});

const CAPABILITIES = [
  {
    icon: Users,
    title: "Smart Workforce",
    text: "Maintain a complete farmer directory with contact details, roles and status.",
  },
  {
    icon: Timer,
    title: "Attendance Tracking",
    text: "Check-in and check-out workflows with shift duration and wage reporting.",
  },
  {
    icon: ClipboardList,
    title: "Task Management",
    text: "Assign agricultural work to farmers and track Pending or Completed status.",
  },
  {
    icon: CameraIcon,
    title: "Live AI Monitoring",
    text: "Stream the field camera with detection status visible at a glance.",
  },
  {
    icon: ScanEye,
    title: "YOLO Animal Detection",
    text: "Backend YOLOv8 inference classifies intruding animals with confidence scoring.",
  },
  {
    icon: Bell,
    title: "Automated Alerts",
    text: "Email and buzzer notifications triggered from immutable hazard records.",
  },
];

const FLOW = [
  { icon: CameraIcon, label: "Camera / Image" },
  { icon: Cpu, label: "AI Detection" },
  { icon: ShieldAlert, label: "Threat Evaluation" },
  { icon: Database, label: "Animal Log" },
  { icon: Bell, label: "Automated Alert" },
];

function Landing() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      <header className="absolute inset-x-0 top-0 z-20">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5 lg:px-8">
          <div className="flex items-center gap-3">
            <span className="flex size-9 items-center justify-center rounded-xl bg-primary/90 text-primary-foreground">
              <Leaf className="size-5" aria-hidden="true" />
            </span>
            <span className="text-lg font-semibold text-primary-foreground">FarmSync</span>
          </div>
          <Button asChild variant="secondary" size="sm">
            <Link to={isAuthenticated ? "/app" : "/login"}>
              {isAuthenticated ? "Dashboard" : "Sign in"}
              <ArrowRight className="size-4" aria-hidden="true" />
            </Link>
          </Button>
        </div>
      </header>

      {/* HERO */}
      <section className="relative isolate overflow-hidden">
        <img
          src={heroImage}
          alt="Farmland at dawn monitored by a field camera"
          width={1920}
          height={1088}
          className="absolute inset-0 size-full object-cover"
        />
        <div className="hero-gradient absolute inset-0 opacity-90" aria-hidden="true" />
        <div className="grid-overlay absolute inset-0 opacity-25" aria-hidden="true" />

        <div className="relative mx-auto grid max-w-7xl gap-12 px-5 pb-24 pt-32 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:px-8 lg:pb-32 lg:pt-40">
          <div className="reveal">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary-foreground/20 bg-primary-foreground/10 px-3 py-1 text-xs font-medium uppercase tracking-widest text-primary-foreground/85">
              <Sprout className="size-3.5" aria-hidden="true" />
              AI-powered smart agriculture
            </span>
            <h1 className="mt-6 text-4xl font-semibold leading-[1.05] text-primary-foreground sm:text-5xl lg:text-6xl">
              Where smart farming
              <br />
              meets <span className="text-gradient">AI vision</span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-primary-foreground/80 sm:text-lg">
              FarmSync runs your daily farm operations — farmers, attendance, tasks — while a
              YOLO-powered vision engine watches the field, logs animal intrusions and triggers
              hazard alerts automatically.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link to={isAuthenticated ? "/app" : "/login"}>
                  {isAuthenticated ? "Launch Dashboard" : "Access FarmSync"}
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="secondary">
                <a href="#capabilities">Explore features</a>
              </Button>
            </div>
            <dl className="mt-12 grid max-w-lg grid-cols-3 gap-6 border-t border-primary-foreground/15 pt-6">
              {[
                ["Operations", "Workforce & tasks"],
                ["Vision", "YOLOv8 detection"],
                ["Response", "Email & buzzer"],
              ].map(([k, v]) => (
                <div key={k}>
                  <dt className="text-xs uppercase tracking-widest text-primary-foreground/55">
                    {k}
                  </dt>
                  <dd className="mt-1 text-sm font-medium text-primary-foreground">{v}</dd>
                </div>
              ))}
            </dl>
          </div>

          {/* AI monitoring visual */}
          <div className="reveal">
            <div className="scanline overflow-hidden rounded-3xl border border-primary-foreground/15 bg-background/10 p-3 backdrop-blur-md">
              <div className="rounded-2xl border border-primary-foreground/10 bg-foreground/70 p-5">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-xs font-medium uppercase tracking-widest text-primary-foreground/80">
                    <span className="relative flex size-2">
                      <span className="absolute inline-flex size-full animate-ping rounded-full bg-accent opacity-70" />
                      <span className="relative inline-flex size-2 rounded-full bg-accent" />
                    </span>
                    Field camera 01
                  </span>
                  <span className="text-xs text-primary-foreground/60">AI detection active</span>
                </div>

                <div className="grid-overlay mt-4 aspect-video rounded-xl border border-primary-foreground/10 bg-primary-foreground/5">
                  <div className="flex size-full items-center justify-center">
                    <ScanEye className="size-14 text-accent/70" aria-hidden="true" />
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-3 gap-3 text-center">
                  {[
                    ["Threat", "Evaluated"],
                    ["Logs", "Immutable"],
                    ["Alerts", "Automated"],
                  ].map(([k, v]) => (
                    <div
                      key={k}
                      className="rounded-lg border border-primary-foreground/10 bg-primary-foreground/5 px-2 py-3"
                    >
                      <p className="text-[10px] uppercase tracking-widest text-primary-foreground/55">
                        {k}
                      </p>
                      <p className="mt-1 text-xs font-medium text-primary-foreground">{v}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CAPABILITIES */}
      <section id="capabilities" className="mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-widest text-primary">
            System capabilities
          </p>
          <h2 className="mt-3 text-3xl font-semibold sm:text-4xl">
            One platform for farm operations and field security
          </h2>
        </div>
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {CAPABILITIES.map(({ icon: Icon, title, text }) => (
            <article
              key={title}
              className="surface-card group p-6 transition-transform duration-300 hover:-translate-y-1"
            >
              <span className="flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                <Icon className="size-5" aria-hidden="true" />
              </span>
              <h3 className="mt-5 text-base font-semibold">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{text}</p>
            </article>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="border-y border-border bg-muted/40 py-20 lg:py-24">
        <div className="mx-auto max-w-7xl px-5 lg:px-8">
          <h2 className="text-3xl font-semibold sm:text-4xl">How detection works</h2>
          <p className="mt-3 max-w-2xl text-sm text-muted-foreground">
            Every frame follows the same deterministic pipeline inside the Django backend.
          </p>
          <ol className="mt-12 grid gap-4 md:grid-cols-5">
            {FLOW.map(({ icon: Icon, label }, i) => (
              <li key={label} className="surface-card relative flex flex-col gap-3 p-5">
                <span className="text-xs font-semibold text-muted-foreground">0{i + 1}</span>
                <Icon className="size-6 text-primary" aria-hidden="true" />
                <span className="text-sm font-medium">{label}</span>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* TWO PILLARS */}
      <section className="mx-auto grid max-w-7xl gap-6 px-5 py-20 lg:grid-cols-2 lg:px-8 lg:py-28">
        <div className="surface-card p-8">
          <span className="flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <LineChart className="size-5" aria-hidden="true" />
          </span>
          <h2 className="mt-5 text-2xl font-semibold">Smart farm management</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Run the human side of the farm from a single operations console.
          </p>
          <ul className="mt-6 space-y-3 text-sm">
            {[
              ["Farmers", "Directory with contact and role information"],
              ["Attendance", "Shift check-in, check-out and duration"],
              ["Tasks", "Assignment with Pending / Completed status"],
              ["Operations", "Dashboard KPIs and recent activity"],
            ].map(([k, v]) => (
              <li key={k} className="flex gap-3 rounded-lg bg-muted/50 px-4 py-3">
                <span className="w-24 shrink-0 font-medium">{k}</span>
                <span className="text-muted-foreground">{v}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="surface-card relative overflow-hidden bg-sidebar p-8 text-sidebar-foreground">
          <div className="grid-overlay absolute inset-0 opacity-30" aria-hidden="true" />
          <div className="relative">
            <span className="flex size-11 items-center justify-center rounded-xl bg-sidebar-primary/15 text-sidebar-primary">
              <ShieldAlert className="size-5" aria-hidden="true" />
            </span>
            <h2 className="mt-5 text-2xl font-semibold">AI vision security</h2>
            <p className="mt-2 text-sm text-sidebar-foreground/70">
              Continuous monitoring that turns a camera feed into an accountable incident record.
            </p>
            <ul className="mt-6 space-y-3 text-sm">
              {[
                ["Camera", "Authenticated MJPEG live stream"],
                ["YOLO", "Server-side inference only"],
                ["Detection", "Animal type and confidence"],
                ["Threat level", "Configurable overrides"],
                ["Alerts", "Immutable triggered records"],
              ].map(([k, v]) => (
                <li
                  key={k}
                  className="flex gap-3 rounded-lg border border-sidebar-border bg-sidebar-accent/40 px-4 py-3"
                >
                  <span className="w-24 shrink-0 font-medium">{k}</span>
                  <span className="text-sidebar-foreground/70">{v}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* ARCHITECTURE */}
      <section className="border-t border-border bg-muted/40 py-20 lg:py-24">
        <div className="mx-auto max-w-5xl px-5 text-center lg:px-8">
          <h2 className="text-3xl font-semibold sm:text-4xl">System architecture</h2>
          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { icon: Leaf, title: "FarmSync Frontend", text: "React interface layer" },
              { icon: ServerCog, title: "Django REST API", text: "Business rules & auth" },
              { icon: Cpu, title: "YOLO AI Engine", text: "Animal inference" },
              { icon: Database, title: "Logs & Alerts", text: "Detection history" },
            ].map(({ icon: Icon, title, text }) => (
              <div key={title} className="surface-card p-6">
                <Icon className="mx-auto size-6 text-primary" aria-hidden="true" />
                <h3 className="mt-4 text-sm font-semibold">{title}</h3>
                <p className="mt-1 text-xs text-muted-foreground">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="hero-gradient relative overflow-hidden">
        <div className="grid-overlay absolute inset-0 opacity-20" aria-hidden="true" />
        <div className="relative mx-auto max-w-3xl px-5 py-24 text-center lg:px-8">
          <h2 className="text-3xl font-semibold text-primary-foreground sm:text-4xl">
            Ready to manage your farm smarter?
          </h2>
          <p className="mt-4 text-sm text-primary-foreground/75">
            Sign in to the FarmSync command center and bring operations and AI monitoring together.
          </p>
          <Button asChild size="lg" className="mt-8">
            <Link to={isAuthenticated ? "/app" : "/login"}>
              {isAuthenticated ? "Open Dashboard" : "Access FarmSync"}
              <ArrowRight className="size-4" aria-hidden="true" />
            </Link>
          </Button>
        </div>
      </section>

      <footer className="border-t border-border bg-background py-8">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-5 text-xs text-muted-foreground sm:flex-row lg:px-8">
          <span className="flex items-center gap-2">
            <Leaf className="size-4 text-primary" aria-hidden="true" />
            FarmSync — AI-Powered Smart Farm Management
          </span>
          <span>Powered by Django REST Framework and YOLOv8</span>
        </div>
      </footer>
    </div>
  );
}

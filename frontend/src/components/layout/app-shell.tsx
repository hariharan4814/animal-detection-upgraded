import { useState } from "react";
import type { ReactNode } from "react";
import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import {
  Activity,
  CameraIcon,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Menu,
  ScanEye,
  Settings2,
  ShieldAlert,
  Users,
  Leaf,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { displayName, useAuth } from "@/lib/auth";
import { useQueryClient } from "@tanstack/react-query";

const NAV_ITEMS = [
  { to: "/app", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { to: "/app/farmers", label: "Farmers", icon: Users },
  { to: "/app/attendance", label: "Attendance", icon: Activity },
  { to: "/app/tasks", label: "Tasks", icon: ClipboardList },
  { to: "/app/monitoring", label: "AI Monitoring", icon: CameraIcon },
  { to: "/app/detection-logs", label: "Detection Logs", icon: ScanEye },
  { to: "/app/alerts", label: "Hazard Alerts", icon: ShieldAlert },
  { to: "/app/settings", label: "Settings", icon: Settings2 },
] as const;

const NAV_GROUPS = [
  {
    label: "Operations",
    items: [
      { to: "/app", label: "Dashboard", icon: LayoutDashboard, exact: true },
      { to: "/app/farmers", label: "Farmers", icon: Users },
      { to: "/app/attendance", label: "Attendance", icon: Activity },
      { to: "/app/tasks", label: "Tasks", icon: ClipboardList },
    ],
  },
  {
    label: "AI Security",
    items: [
      { to: "/app/monitoring", label: "AI Monitoring", icon: CameraIcon },
      { to: "/app/detection-logs", label: "Detection Logs", icon: ScanEye },
      { to: "/app/alerts", label: "Hazard Alerts", icon: ShieldAlert },
    ],
  },
  {
    label: "System",
    items: [{ to: "/app/settings", label: "Settings", icon: Settings2 }],
  },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { user, isStaff, logout } = useAuth();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const handleLogout = async () => {
    await qc.cancelQueries();
    qc.clear();
    await logout();
    void navigate({ to: "/login", replace: true });
  };

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      {/* Top Utility Bar */}
      <div className="w-full border-b border-border/60 bg-muted/40">
        <div className="mx-auto flex h-8 w-full max-w-[1800px] items-center justify-between px-4 sm:px-6 lg:px-8 xl:px-10 2xl:px-12">
          <div className="flex items-center gap-2 text-[11px] font-medium text-muted-foreground">
            <span className="size-1.5 rounded-full bg-success" aria-hidden="true" />
            <span className="hidden sm:inline">FarmSync Enterprise Agriculture Platform</span>
            <span className="sm:hidden">FarmSync Enterprise</span>
          </div>

          <div className="flex items-center gap-3 text-[11px]">
            <div className="flex items-center gap-1.5 font-medium text-foreground">
              <span className="max-w-[160px] truncate">{displayName(user) || "User"}</span>
              <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-primary">
                {isStaff ? "Administrator" : "Member"}
              </span>
            </div>
            <span className="text-border" aria-hidden="true">
              |
            </span>
            <button
              type="button"
              onClick={handleLogout}
              className="font-medium text-muted-foreground transition-colors hover:text-destructive focus-visible:underline focus-visible:outline-none"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>

      {/* Main Corporate Header / Navbar */}
      <header className="sticky top-0 z-40 w-full border-b border-border bg-card/95 shadow-2xs backdrop-blur supports-[backdrop-filter]:bg-card/85">
        <div className="mx-auto flex h-16 w-full max-w-[1800px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8 xl:px-10 2xl:px-12">
          {/* Left: Brand Identity */}
          <div className="flex items-center gap-3">
            <Link
              to="/app"
              className="flex items-center gap-2.5 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-2xs">
                <Leaf className="size-4.5" aria-hidden="true" />
              </span>
              <span className="font-sans text-xl font-bold tracking-tight text-foreground">
                FarmSync
              </span>
            </Link>
          </div>

          {/* Center: Clean Text-Based Horizontal Navigation */}
          <nav
            className="hidden h-full items-center gap-4 lg:flex xl:gap-6 2xl:gap-8"
            aria-label="Main navigation"
          >
            {NAV_ITEMS.map((item) => {
              const active =
                "exact" in item && item.exact
                  ? pathname === item.to
                  : pathname === item.to || pathname.startsWith(`${item.to}/`);
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  aria-current={active ? "page" : undefined}
                  className={`inline-flex h-full items-center border-b-2 px-1 text-xs transition-colors xl:text-sm ${
                    active
                      ? "border-primary font-semibold text-primary"
                      : "border-transparent font-medium text-muted-foreground hover:border-border hover:text-foreground"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Right Side: Quick Action & Mobile Menu */}
          <div className="flex items-center gap-2.5">
            <Link
              to="/app/monitoring"
              className="hidden items-center gap-1.5 rounded-md border border-border bg-background px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:border-primary/40 hover:text-primary sm:inline-flex"
            >
              <span className="size-1.5 rounded-full bg-success" aria-hidden="true" />
              <span>Live Monitor</span>
            </Link>

            {/* Mobile / Tablet Drawer Menu (< lg) */}
            <Sheet open={open} onOpenChange={setOpen}>
              <SheetTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  className="size-9 lg:hidden"
                  aria-label="Open navigation menu"
                >
                  <Menu className="size-4" aria-hidden="true" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="flex w-[300px] flex-col bg-card p-0">
                <SheetTitle className="sr-only">FarmSync navigation</SheetTitle>
                <div className="flex h-16 items-center gap-2.5 border-b border-border px-5">
                  <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-2xs">
                    <Leaf className="size-4.5" aria-hidden="true" />
                  </span>
                  <span className="font-sans text-xl font-bold tracking-tight text-foreground">
                    FarmSync
                  </span>
                </div>

                {/* Mobile Navigation Links */}
                <div className="flex-1 space-y-6 overflow-y-auto p-4">
                  {NAV_GROUPS.map((group) => (
                    <div key={group.label}>
                      <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                        {group.label}
                      </p>
                      <ul className="space-y-1">
                        {group.items.map((item) => {
                          const active =
                            "exact" in item && item.exact
                              ? pathname === item.to
                              : pathname === item.to || pathname.startsWith(`${item.to}/`);
                          const Icon = item.icon;
                          return (
                            <li key={item.to}>
                              <Link
                                to={item.to}
                                onClick={() => setOpen(false)}
                                aria-current={active ? "page" : undefined}
                                className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                                  active
                                    ? "bg-primary/10 font-semibold text-primary"
                                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                                }`}
                              >
                                <Icon
                                  className={`size-4.5 ${active ? "text-primary" : "text-muted-foreground"}`}
                                  aria-hidden="true"
                                />
                                {item.label}
                              </Link>
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  ))}
                </div>

                {/* Mobile User Panel */}
                <div className="border-t border-border bg-muted/30 p-4">
                  <div className="flex items-center justify-between">
                    <div className="min-w-0 flex-1 pr-2">
                      <p className="truncate text-sm font-semibold text-foreground">
                        {displayName(user) || "User"}
                      </p>
                      <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                        {isStaff ? "Administrator" : "Member"}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleLogout}
                      className="gap-1 text-xs text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                    >
                      <LogOut className="size-3.5" aria-hidden="true" />
                      <span>Sign Out</span>
                    </Button>
                  </div>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>

      {/* Main Application Page Content */}
      <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8 xl:px-10 2xl:px-12 lg:py-8">
        <div className="mx-auto w-full max-w-[1800px] space-y-6">{children}</div>
      </main>
    </div>
  );
}

import { useEffect, useState } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { ArrowLeft, Leaf, Loader2, LockKeyhole, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useAuth } from "@/lib/auth";
import { humanizeError } from "@/lib/api";
import heroImage from "@/assets/farm-hero.jpg";

export const Route = createFileRoute("/login")({
  ssr: false,
  head: () => ({
    meta: [
      { title: "Sign in — FarmSync" },
      {
        name: "description",
        content:
          "Sign in to the FarmSync command center to manage farm operations and AI monitoring.",
      },
      { property: "og:title", content: "Sign in — FarmSync" },
      {
        property: "og:description",
        content: "Secure JWT sign-in for the FarmSync smart agriculture platform.",
      },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && isAuthenticated) void navigate({ to: "/app", replace: true });
  }, [isLoading, isAuthenticated, navigate]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username.trim(), password);
      void navigate({ to: "/app", replace: true });
    } catch (err) {
      setError(humanizeError(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden overflow-hidden lg:block">
        <img
          src={heroImage}
          alt=""
          aria-hidden="true"
          className="absolute inset-0 size-full object-cover"
        />
        <div className="hero-gradient absolute inset-0 opacity-90" aria-hidden="true" />
        <div className="grid-overlay absolute inset-0 opacity-25" aria-hidden="true" />
        <div className="relative flex h-full flex-col justify-between p-12">
          <div className="flex items-center gap-3">
            <span className="flex size-9 items-center justify-center rounded-xl bg-primary-foreground/15 text-primary-foreground">
              <Leaf className="size-5" aria-hidden="true" />
            </span>
            <span className="text-lg font-semibold text-primary-foreground">FarmSync</span>
          </div>
          <div>
            <h2 className="max-w-md text-3xl font-semibold leading-tight text-primary-foreground">
              Farm operations and AI vision security in one command center.
            </h2>
            <p className="mt-4 flex items-center gap-2 text-sm text-primary-foreground/70">
              <ShieldCheck className="size-4" aria-hidden="true" />
              Protected by JWT authentication and backend role permissions.
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center px-5 py-12">
        <div className="w-full max-w-sm reveal">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="size-3.5" aria-hidden="true" />
            Back to overview
          </Link>

          <div className="mt-8 flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <LockKeyhole className="size-5" aria-hidden="true" />
          </div>
          <h1 className="mt-5 text-2xl font-semibold">Sign in to FarmSync</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Use your FarmSync account credentials.
          </p>

          <form onSubmit={onSubmit} className="mt-8 space-y-5" noValidate>
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                name="username"
                autoComplete="username"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="your.username"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>

            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting && <Loader2 className="size-4 animate-spin" aria-hidden="true" />}
              {submitting ? "Signing in" : "Sign in"}
            </Button>
          </form>

          <p className="mt-6 text-xs leading-relaxed text-muted-foreground">
            FarmSync connects to your Django REST API. Set{" "}
            <code className="rounded bg-muted px-1 py-0.5">VITE_API_BASE_URL</code> to the backend
            origin.
          </p>
        </div>
      </div>
    </div>
  );
}

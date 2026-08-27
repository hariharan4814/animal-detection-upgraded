import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Loader2,
  Lock,
  Mail,
  Plus,
  Save,
  ShieldAlert,
  Trash2,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
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
import { EmptyState, ErrorState, LoadingRows, PageHeader } from "@/components/common/states";
import {
  useEmailSender,
  useReceiverMutations,
  useReceivers,
  useUpdateEmailSender,
} from "@/hooks/use-api";
import { useAuth } from "@/lib/auth";
import { formatDateTime } from "@/lib/format";
import { toast } from "sonner";
import type { AlertReceiver } from "@/types/api";

export const Route = createFileRoute("/app/settings")({
  head: () => ({
    meta: [
      { title: "Email Settings — FarmSync" },
      {
        name: "description",
        content:
          "Configure email sender credentials and alert receivers for automated wildlife threat notifications.",
      },
      { property: "og:title", content: "Email Notification Settings — FarmSync" },
      {
        property: "og:description",
        content: "Manage SMTP credentials and alert recipient list in FarmSync.",
      },
    ],
  }),
  component: SettingsPage,
});

/* ==============================================================================
   1. SENDER EMAIL CONFIGURATION PANEL
   ============================================================================== */
function SenderEmailConfigPanel() {
  const { isStaff } = useAuth();
  const { data: sender, isLoading, isError, error, refetch } = useEmailSender();
  const updateSender = useUpdateEmailSender();

  const [senderName, setSenderName] = useState("");
  const [senderEmail, setSenderEmail] = useState("");
  const [smtpHost, setSmtpHost] = useState("smtp.gmail.com");
  const [smtpPort, setSmtpPort] = useState(587);
  const [smtpUsername, setSmtpUsername] = useState("");
  const [smtpPassword, setSmtpPassword] = useState("");
  const [useTls, setUseTls] = useState(true);
  const [isActive, setIsActive] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Sync state when sender data loads
  const [synced, setSynced] = useState(false);
  if (sender && !synced) {
    setSenderName(sender.sender_name ?? "FarmSync Alert System");
    setSenderEmail(sender.sender_email ?? "alerts@example.com");
    setSmtpHost(sender.smtp_host ?? "smtp.gmail.com");
    setSmtpPort(sender.smtp_port ?? 587);
    setSmtpUsername(sender.smtp_username ?? "");
    setUseTls(sender.use_tls ?? true);
    setIsActive(sender.is_active ?? true);
    setSynced(true);
  }

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!senderEmail.trim()) {
      toast.error("Sender email is required.");
      return;
    }

    const payload: Record<string, unknown> = {
      sender_name: senderName.trim() || "FarmSync Alert System",
      sender_email: senderEmail.trim(),
      smtp_host: smtpHost.trim() || "smtp.gmail.com",
      smtp_port: Number(smtpPort) || 587,
      smtp_username: smtpUsername.trim() || senderEmail.trim(),
      use_tls: useTls,
      use_ssl: !useTls && smtpPort === 465,
      is_active: isActive,
    };

    // Google App Password: write-only. If empty, backend retains existing password.
    if (smtpPassword.trim()) {
      payload.smtp_password = smtpPassword.trim();
    }

    updateSender.mutate(payload, {
      onSuccess: () => {
        setSmtpPassword("");
        toast.success("Sender Email Configuration Saved", {
          description: "SMTP credentials and notification preferences have been saved securely.",
        });
      },
      onError: (err: unknown) => {
        const msg = err instanceof Error ? err.message : "Failed to update email sender.";
        toast.error("Save Error", { description: msg });
      },
    });
  };

  if (isLoading) {
    return (
      <div className="surface-card p-6">
        <LoadingRows count={3} />
      </div>
    );
  }

  if (isError) {
    return <ErrorState error={error} onRetry={() => void refetch()} />;
  }

  return (
    <section className="surface-card p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
        <div className="flex items-center gap-3">
          <span className="flex size-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Mail className="size-5" aria-hidden="true" />
          </span>
          <div>
            <h2 className="text-base font-semibold">Sender Email Configuration</h2>
            <p className="text-xs text-muted-foreground">
              Configure the outgoing SMTP account used to dispatch animal threat notifications.
            </p>
          </div>
        </div>
        <Badge variant={sender?.is_active ? "default" : "secondary"}>
          {sender?.is_active ? "● SMTP Active" : "○ Inactive"}
        </Badge>
      </div>

      <form onSubmit={handleSave} className="space-y-5">
        <div className="grid gap-4 sm:grid-cols-2">
          {/* Sender Email Address */}
          <div className="space-y-1.5">
            <Label htmlFor="senderEmail" className="text-xs font-semibold">
              Sender Email Address <span className="text-destructive">*</span>
            </Label>
            <Input
              id="senderEmail"
              type="email"
              placeholder="e.g. farmsync.alerts@gmail.com"
              value={senderEmail}
              onChange={(e) => setSenderEmail(e.target.value)}
              disabled={!isStaff || updateSender.isPending}
              required
            />
            <p className="text-[11px] text-muted-foreground">
              Outgoing alert emails will be delivered from this address.
            </p>
          </div>

          {/* Google App Password (Masked) */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label htmlFor="smtpPassword" className="text-xs font-semibold">
                Google App Password
              </Label>
              {sender?.smtp_password_configured && (
                <Badge
                  variant="outline"
                  className="gap-1 border-success/40 bg-success/10 text-[10px] text-success"
                >
                  <Lock className="size-3" /> Password Configured
                </Badge>
              )}
            </div>
            <Input
              id="smtpPassword"
              type="password"
              autoComplete="new-password"
              placeholder={
                sender?.smtp_password_configured
                  ? "•••••••••••••••• (Leave blank to keep current)"
                  : "16-digit Google App Password (e.g. abcd efgh ijkl mnop)"
              }
              value={smtpPassword}
              onChange={(e) => setSmtpPassword(e.target.value)}
              disabled={!isStaff || updateSender.isPending}
            />
            <p className="text-[11px] text-muted-foreground flex items-center gap-1">
              <Lock className="size-3 shrink-0 text-muted-foreground" />
              Write-only security: Google App Password is never exposed via API responses.
            </p>
          </div>
        </div>

        {/* Instructions helper card */}
        <div className="rounded-xl border border-border bg-muted/40 p-4 text-xs text-muted-foreground space-y-2">
          <p className="font-semibold text-foreground flex items-center gap-1.5">
            <HelpCircle className="size-3.5 text-primary" />
            How to generate a Google App Password for Gmail:
          </p>
          <ol className="list-decimal pl-5 space-y-1">
            <li>
              Enable <strong>2-Step Verification</strong> in your Google Account security settings.
            </li>
            <li>
              Navigate to <strong>Security &gt; 2-Step Verification &gt; App Passwords</strong>.
            </li>
            <li>
              Create an app password for <em>FarmSync</em> and paste the 16-character code above.
            </li>
          </ol>
        </div>

        {/* Toggle Advanced SMTP Settings */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced((prev) => !prev)}
            className="text-xs font-medium text-primary hover:underline"
          >
            {showAdvanced
              ? "Hide advanced SMTP settings ▲"
              : "Show advanced SMTP server settings ▼"}
          </button>
        </div>

        {showAdvanced && (
          <div className="reveal grid gap-4 rounded-xl border border-border bg-muted/20 p-4 sm:grid-cols-3">
            <div className="space-y-1.5">
              <Label htmlFor="smtpHost" className="text-xs">
                SMTP Host
              </Label>
              <Input
                id="smtpHost"
                value={smtpHost}
                onChange={(e) => setSmtpHost(e.target.value)}
                placeholder="smtp.gmail.com"
                disabled={!isStaff || updateSender.isPending}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="smtpPort" className="text-xs">
                SMTP Port
              </Label>
              <Input
                id="smtpPort"
                type="number"
                value={smtpPort}
                onChange={(e) => setSmtpPort(Number(e.target.value))}
                placeholder="587"
                disabled={!isStaff || updateSender.isPending}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="senderName" className="text-xs">
                Display Sender Name
              </Label>
              <Input
                id="senderName"
                value={senderName}
                onChange={(e) => setSenderName(e.target.value)}
                placeholder="FarmSync Alert System"
                disabled={!isStaff || updateSender.isPending}
              />
            </div>
            <div className="flex items-center justify-between sm:col-span-3 pt-2">
              <div>
                <p className="text-xs font-medium">Use STARTTLS Encryption</p>
                <p className="text-[11px] text-muted-foreground">
                  Recommended for Gmail SMTP on port 587
                </p>
              </div>
              <Switch
                checked={useTls}
                onCheckedChange={setUseTls}
                disabled={!isStaff || updateSender.isPending}
                aria-label="Use TLS"
              />
            </div>
          </div>
        )}

        {isStaff && (
          <div className="flex justify-end pt-2">
            <Button
              type="submit"
              disabled={updateSender.isPending}
              className="gap-2 bg-primary font-semibold shadow-sm"
            >
              {updateSender.isPending ? (
                <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              ) : (
                <Save className="size-4" aria-hidden="true" />
              )}
              {updateSender.isPending ? "Saving Settings…" : "Save Email Settings"}
            </Button>
          </div>
        )}
      </form>
    </section>
  );
}

/* ==============================================================================
   2. ALERT RECEIVERS PANEL
   ============================================================================== */
function AlertReceiversPanel() {
  const { isStaff } = useAuth();
  const { data, isLoading, isError, error, refetch } = useReceivers();
  const { create, remove } = useReceiverMutations();

  const [newEmail, setNewEmail] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<AlertReceiver | null>(null);

  const receivers = data ?? [];

  const handleAddReceiver = (e: React.FormEvent) => {
    e.preventDefault();
    const email = newEmail.trim().toLowerCase();

    // Client-side email validation
    if (!email) {
      toast.error("Please enter an email address.");
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      toast.error("Please enter a valid email address.");
      return;
    }

    // Check for duplicate in local cache
    const duplicate = receivers.some((r) => r.email.toLowerCase() === email);
    if (duplicate) {
      toast.error("Duplicate Email Address", {
        description: `An alert receiver with the email "${email}" is already registered.`,
      });
      return;
    }

    const name = email.split("@")[0].charAt(0).toUpperCase() + email.split("@")[0].slice(1);

    create.mutate(
      {
        email,
        name,
        is_active: true,
        receive_animal_alerts: true,
      },
      {
        onSuccess: () => {
          setNewEmail("");
          toast.success("Alert Receiver Added", {
            description: `${email} has been registered to receive threat alerts.`,
          });
        },
        onError: (err: unknown) => {
          const msg = err instanceof Error ? err.message : "Failed to add alert receiver.";
          toast.error("Error Adding Receiver", { description: msg });
        },
      },
    );
  };

  const handleConfirmDelete = () => {
    if (!deleteTarget) return;
    remove.mutate(deleteTarget.id, {
      onSuccess: () => {
        toast.success("Alert Receiver Removed", {
          description: `${deleteTarget.email} will no longer receive alerts.`,
        });
        setDeleteTarget(null);
      },
      onError: (err: unknown) => {
        const msg = err instanceof Error ? err.message : "Failed to remove alert receiver.";
        toast.error("Error Removing Receiver", { description: msg });
        setDeleteTarget(null);
      },
    });
  };

  return (
    <section className="surface-card p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
        <div className="flex items-center gap-3">
          <span className="flex size-9 items-center justify-center rounded-xl bg-accent/15 text-accent-foreground">
            <Users className="size-5" aria-hidden="true" />
          </span>
          <div>
            <h2 className="text-base font-semibold">Alert Receivers</h2>
            <p className="text-xs text-muted-foreground">
              Configure the email addresses that should receive animal threat notifications.
            </p>
          </div>
        </div>
        <Badge variant="outline" className="text-xs font-mono">
          {receivers.length} {receivers.length === 1 ? "Recipient" : "Recipients"}
        </Badge>
      </div>

      {/* Add Receiver Form */}
      {isStaff && (
        <form onSubmit={handleAddReceiver} className="flex flex-wrap gap-2 sm:items-end">
          <div className="flex-1 min-w-[240px] space-y-1.5">
            <Label htmlFor="receiverEmailInput" className="text-xs font-semibold">
              Add Receiver Email Address
            </Label>
            <Input
              id="receiverEmailInput"
              type="email"
              placeholder="e.g. hariharan4814@gmail.com"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              disabled={create.isPending}
              required
            />
          </div>
          <Button
            type="submit"
            disabled={create.isPending || !newEmail.trim()}
            className="gap-2 bg-primary font-semibold shadow-sm"
          >
            {create.isPending ? (
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            ) : (
              <Plus className="size-4" aria-hidden="true" />
            )}
            Add Receiver
          </Button>
        </form>
      )}

      {/* Receiver List */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Configured Alert Recipients
        </h3>

        {isLoading ? (
          <LoadingRows count={3} />
        ) : isError ? (
          <ErrorState error={error} onRetry={() => void refetch()} />
        ) : receivers.length === 0 ? (
          <EmptyState
            title="No alert receivers configured"
            description="Add one or more email addresses above to receive automated animal intrusion alerts."
            icon={<Mail className="size-8" aria-hidden="true" />}
          />
        ) : (
          <div className="divide-y divide-border rounded-xl border border-border bg-card overflow-hidden">
            {receivers.map((receiver) => (
              <div
                key={receiver.id}
                className="flex flex-wrap items-center justify-between gap-3 p-4 transition-colors hover:bg-muted/30"
              >
                <div className="flex items-center gap-3">
                  <div className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <Mail className="size-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">{receiver.email}</p>
                    <p className="text-[11px] text-muted-foreground">
                      {receiver.name && receiver.name !== receiver.email
                        ? `${receiver.name} · `
                        : ""}
                      Added {receiver.created_at ? formatDateTime(receiver.created_at) : "recently"}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Badge
                    variant={receiver.is_active ? "outline" : "secondary"}
                    className="text-[10px] uppercase"
                  >
                    {receiver.is_active ? "Active" : "Disabled"}
                  </Badge>
                  {isStaff && (
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 text-xs text-destructive hover:bg-destructive/10 hover:text-destructive gap-1.5"
                      onClick={() => setDeleteTarget(receiver)}
                    >
                      <Trash2 className="size-3.5" />
                      Remove
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Alert Dialog */}
      <AlertDialog open={Boolean(deleteTarget)} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="size-5" />
              Remove Alert Receiver?
            </AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove <strong>{deleteTarget?.email}</strong> from receiving
              automated threat notifications?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={remove.isPending}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              disabled={remove.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {remove.isPending ? "Removing…" : "Remove Receiver"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  );
}

/* ==============================================================================
   3. MAIN SETTINGS ROOT PAGE
   ============================================================================== */
function SettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Email Notification Settings"
        description="Configure SMTP sender credentials and alert receivers for automated wildlife threat notifications."
      />

      <div className="max-w-4xl space-y-6">
        <SenderEmailConfigPanel />
        <AlertReceiversPanel />
      </div>
    </div>
  );
}

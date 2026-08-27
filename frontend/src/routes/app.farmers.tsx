import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  Loader2,
  Mail,
  MapPin,
  Pencil,
  Phone,
  Plus,
  Search,
  Trash2,
  UserRound,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import { useFarmerMutations, useFarmers } from "@/hooks/use-api";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";
import { initialsFrom } from "@/lib/format";
import type { Farmer, FarmerInput } from "@/types/api";

export const Route = createFileRoute("/app/farmers")({
  head: () => ({
    meta: [
      { title: "Farmers — FarmSync" },
      {
        name: "description",
        content: "Manage the FarmSync farmer directory: add, edit and remove workforce records.",
      },
      { property: "og:title", content: "Farmer Management — FarmSync" },
      {
        property: "og:description",
        content: "Workforce directory for the FarmSync smart farm platform.",
      },
    ],
  }),
  component: FarmersPage,
});

function FarmerForm({
  open,
  onOpenChange,
  farmer,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  farmer: Farmer | null;
}) {
  const { create, update } = useFarmerMutations();
  const [values, setValues] = useState<FarmerInput>({
    name: farmer?.name ?? "",
    phone: farmer?.phone ?? "",
    field: farmer?.field ?? "Main Field",
    email: farmer?.email ?? "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const pending = create.isPending || update.isPending;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    const payload: FarmerInput = {
      name: values.name.trim(),
      phone: values.phone.trim(),
      field: values.field.trim(),
      ...(values.email && values.email.trim() ? { email: values.email.trim() } : {}),
    };
    if (!payload.name) return setErrors({ name: "Farmer name cannot be blank." });
    if (!payload.phone) return setErrors({ phone: "Contact phone number cannot be blank." });
    if (!payload.field)
      return setErrors({ field: "Assigned agricultural field/location cannot be blank." });

    try {
      if (farmer) await update.mutateAsync({ id: farmer.id, input: payload });
      else await create.mutateAsync(payload);
      onOpenChange(false);
    } catch (err) {
      if (err instanceof ApiError) setErrors(err.fieldErrors);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{farmer ? "Edit farmer" : "Add farmer"}</DialogTitle>
          <DialogDescription>
            {farmer
              ? "Update the registered farm worker record."
              : "Register a new farm worker in the workforce directory."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4" noValidate>
          <div className="space-y-2">
            <Label htmlFor="name">Full Name *</Label>
            <Input
              id="name"
              placeholder="e.g. Ramesh Kumar"
              value={values.name}
              onChange={(e) => setValues((v) => ({ ...v, name: e.target.value }))}
              aria-invalid={!!errors["name"]}
              required
            />
            {errors["name"] && <p className="text-xs text-destructive">{errors["name"]}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="phone">Phone Number *</Label>
            <Input
              id="phone"
              name="phone"
              inputMode="tel"
              placeholder="e.g. +91 98765 43210"
              value={values.phone}
              onChange={(e) => setValues((v) => ({ ...v, phone: e.target.value }))}
              aria-invalid={!!errors["phone"]}
              required
            />
            {errors["phone"] && <p className="text-xs text-destructive">{errors["phone"]}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="field">Assigned Field / Sector *</Label>
            <Input
              id="field"
              placeholder="e.g. Sector 4 - North Orchard"
              value={values.field}
              onChange={(e) => setValues((v) => ({ ...v, field: e.target.value }))}
              aria-invalid={!!errors["field"]}
              required
            />
            {errors["field"] && <p className="text-xs text-destructive">{errors["field"]}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email Address (Optional)</Label>
            <Input
              id="email"
              type="email"
              placeholder="e.g. ramesh@farm.example.com"
              value={values.email ?? ""}
              onChange={(e) => setValues((v) => ({ ...v, email: e.target.value }))}
              aria-invalid={!!errors["email"]}
            />
            {errors["email"] && <p className="text-xs text-destructive">{errors["email"]}</p>}
          </div>
          {errors["detail"] && <p className="text-xs text-destructive">{errors["detail"]}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={pending}>
              {pending && <Loader2 className="size-4 animate-spin" aria-hidden="true" />}
              {farmer ? "Save changes" : "Add farmer"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function FarmersPage() {
  const { isStaff } = useAuth();
  const { data, isLoading, isError, error, refetch } = useFarmers();
  const { remove } = useFarmerMutations();
  const [query, setQuery] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Farmer | null>(null);
  const [deleting, setDeleting] = useState<Farmer | null>(null);

  const farmers = useMemo(() => {
    const list = data ?? [];
    const q = query.trim().toLowerCase();
    if (!q) return list;
    return list.filter((f) =>
      [f.name, f.phone, f.field, f.email].some((v) => (v ?? "").toLowerCase().includes(q)),
    );
  }, [data, query]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Farmers"
        description="Workforce directory backed by the FarmSync API."
        actions={
          isStaff && (
            <Button
              onClick={() => {
                setEditing(null);
                setFormOpen(true);
              }}
            >
              <Plus className="size-4" aria-hidden="true" />
              Add farmer
            </Button>
          )
        }
      />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full max-w-md">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            className="pl-9"
            placeholder="Search by name, phone, field or email..."
            aria-label="Search farmers"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <p className="text-xs font-medium text-muted-foreground">
          Showing <span className="font-semibold text-foreground">{farmers.length}</span>{" "}
          {farmers.length === 1 ? "registered worker" : "registered workers"}
        </p>
      </div>

      {isLoading ? (
        <LoadingRows />
      ) : isError ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : farmers.length === 0 ? (
        <EmptyState
          title={query ? "No matching farmers" : "No farmers yet"}
          description={
            query
              ? "Try a different search term."
              : "Add your first farmer to start tracking attendance and tasks."
          }
          icon={<Users className="size-7" aria-hidden="true" />}
          action={
            isStaff && !query ? (
              <Button
                onClick={() => {
                  setEditing(null);
                  setFormOpen(true);
                }}
              >
                <Plus className="size-4" aria-hidden="true" />
                Add farmer
              </Button>
            ) : undefined
          }
        />
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 2xl:grid-cols-4">
          {farmers.map((farmer) => (
            <article
              key={farmer.id}
              className="surface-card reveal flex flex-col justify-between p-5"
            >
              <div>
                <div className="flex items-start gap-4">
                  <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                    {initialsFrom(farmer.name)}
                  </span>
                  <div className="min-w-0 flex-1">
                    <h2 className="truncate text-base font-semibold">{farmer.name}</h2>
                    <p className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
                      <Phone className="size-3" aria-hidden="true" />
                      {farmer.phone}
                    </p>
                    {farmer.email && (
                      <p className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground truncate">
                        <Mail className="size-3 shrink-0" aria-hidden="true" />
                        {farmer.email}
                      </p>
                    )}
                  </div>
                </div>

                <div className="mt-4 flex items-center gap-1.5">
                  <Badge variant="secondary" className="text-[11px] font-normal">
                    <MapPin className="mr-1 size-3 text-primary" aria-hidden="true" />
                    {farmer.field}
                  </Badge>
                </div>
              </div>

              {isStaff && (
                <div className="mt-5 flex gap-2 border-t border-border pt-4">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setEditing(farmer);
                      setFormOpen(true);
                    }}
                  >
                    <Pencil className="size-3.5" aria-hidden="true" />
                    Edit
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setDeleting(farmer)}>
                    <Trash2 className="size-3.5 text-destructive" aria-hidden="true" />
                    Delete
                  </Button>
                </div>
              )}
            </article>
          ))}
        </div>
      )}

      {!isStaff && (
        <p className="flex items-center gap-2 text-xs text-muted-foreground">
          <UserRound className="size-3.5" aria-hidden="true" />
          Read-only access. Staff or admin permissions are required to modify farmers.
        </p>
      )}

      {formOpen && (
        <FarmerForm
          key={editing?.id ?? "new"}
          open={formOpen}
          onOpenChange={setFormOpen}
          farmer={editing}
        />
      )}

      <AlertDialog open={!!deleting} onOpenChange={(v) => !v && setDeleting(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete {deleting?.name}?</AlertDialogTitle>
            <AlertDialogDescription>
              This permanently removes the farmer record from the database. This action cannot be
              undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (deleting) remove.mutate(deleting.id);
                setDeleting(null);
              }}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

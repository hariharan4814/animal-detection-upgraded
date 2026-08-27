import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  Calendar,
  CheckCircle2,
  ClipboardList,
  Circle,
  Loader2,
  Pencil,
  Plus,
  Search,
  Trash2,
  User,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import { useFarmers, useTaskMutations, useTasks } from "@/hooks/use-api";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { Task, TaskInput, TaskStatus } from "@/types/api";

export const Route = createFileRoute("/app/tasks")({
  head: () => ({
    meta: [
      { title: "Tasks — FarmSync" },
      {
        name: "description",
        content: "Assign agricultural tasks to farmers and track Pending or Completed status.",
      },
      { property: "og:title", content: "Task Management — FarmSync" },
      {
        property: "og:description",
        content: "Plan and track farm work with FarmSync task management.",
      },
    ],
  }),
  component: TasksPage,
});

const STATUSES: TaskStatus[] = ["Pending", "Completed"];

function TaskForm({
  open,
  onOpenChange,
  task,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  task: Task | null;
}) {
  const { create, update } = useTaskMutations();
  const farmers = useFarmers();
  const [taskName, setTaskName] = useState(task?.task_name ?? "");
  const [status, setStatus] = useState<TaskStatus>(task?.status ?? "Pending");
  const [assigned, setAssigned] = useState<string>(
    task?.assigned_to ? String(task.assigned_to) : "unassigned",
  );
  const [date, setDate] = useState(task?.date ?? new Date().toISOString().split("T")[0]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const pending = create.isPending || update.isPending;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    if (!taskName.trim()) return setErrors({ task_name: "Task name cannot be blank." });
    const payload: TaskInput = {
      task_name: taskName.trim(),
      status,
      assigned_to: assigned && assigned !== "unassigned" ? Number(assigned) : null,
      date: date || undefined,
    };
    try {
      if (task) await update.mutateAsync({ id: task.id, input: payload });
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
          <DialogTitle>{task ? "Edit task" : "Create task"}</DialogTitle>
          <DialogDescription>
            Assign agricultural tasks with verified status tracking (Pending / Completed).
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4" noValidate>
          <div className="space-y-2">
            <Label htmlFor="task_name">Task Name *</Label>
            <Input
              id="task_name"
              placeholder="e.g. Irrigation of Zone 2"
              value={taskName}
              onChange={(e) => setTaskName(e.target.value)}
              aria-invalid={!!errors["task_name"]}
              required
            />
            {errors["task_name"] && (
              <p className="text-xs text-destructive">{errors["task_name"]}</p>
            )}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="assigned">Assign Worker</Label>
              <Select value={assigned} onValueChange={setAssigned}>
                <SelectTrigger id="assigned">
                  <SelectValue placeholder="Unassigned" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="unassigned">Unassigned</SelectItem>
                  {(farmers.data ?? []).map((f) => (
                    <SelectItem key={f.id} value={String(f.id)}>
                      {f.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Select value={status} onValueChange={(v) => setStatus(v as TaskStatus)}>
                <SelectTrigger id="status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STATUSES.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="task_date">Scheduled Date</Label>
            <Input
              id="task_date"
              type="date"
              value={date ?? ""}
              onChange={(e) => setDate(e.target.value)}
            />
            {errors["date"] && <p className="text-xs text-destructive">{errors["date"]}</p>}
          </div>
          {errors["detail"] && <p className="text-xs text-destructive">{errors["detail"]}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={pending}>
              {pending && <Loader2 className="size-4 animate-spin" aria-hidden="true" />}
              {task ? "Save changes" : "Create task"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function TasksPage() {
  const { isStaff } = useAuth();
  const { data, isLoading, isError, error, refetch } = useTasks();
  const { update, remove } = useTaskMutations();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | TaskStatus>("all");
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Task | null>(null);
  const [deleting, setDeleting] = useState<Task | null>(null);

  const tasks = useMemo(() => data ?? [], [data]);
  const completed = tasks.filter((t) => t.status === "Completed").length;
  const progress = tasks.length ? Math.round((completed / tasks.length) * 100) : 0;

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return tasks.filter((t) => {
      const matchQuery =
        !q || [t.task_name, t.assigned_to_name].some((v) => (v ?? "").toLowerCase().includes(q));
      const matchStatus = filter === "all" || t.status === filter;
      return matchQuery && matchStatus;
    });
  }, [tasks, query, filter]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tasks"
        description="Agricultural work assignment and completion tracking."
        actions={
          isStaff && (
            <Button
              onClick={() => {
                setEditing(null);
                setFormOpen(true);
              }}
            >
              <Plus className="size-4" aria-hidden="true" />
              Create task
            </Button>
          )
        }
      />

      <section className="surface-card reveal grid gap-4 p-5 sm:grid-cols-3">
        <div>
          <p className="text-xs uppercase tracking-widest text-muted-foreground">Total tasks</p>
          <p className="mt-2 text-2xl font-semibold">{tasks.length}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-widest text-muted-foreground">Pending</p>
          <p className="mt-2 text-2xl font-semibold text-warning">{tasks.length - completed}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-widest text-muted-foreground">Completion</p>
          <p className="mt-2 text-2xl font-semibold">{progress}%</p>
          <Progress value={progress} className="mt-2" />
        </div>
      </section>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative w-full max-w-md">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <Input
              className="pl-9"
              placeholder="Search tasks by name or assigned worker..."
              aria-label="Search tasks"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <Select value={filter} onValueChange={(v) => setFilter(v as typeof filter)}>
            <SelectTrigger className="w-full sm:w-48" aria-label="Filter by status">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              {STATUSES.map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <p className="text-xs font-medium text-muted-foreground">
          Showing <span className="font-semibold text-foreground">{visible.length}</span> of{" "}
          {tasks.length} tasks
        </p>
      </div>

      {isLoading ? (
        <LoadingRows />
      ) : isError ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : visible.length === 0 ? (
        <EmptyState
          title="No tasks found"
          description="Create a task and assign it to a farmer to get started."
          icon={<ClipboardList className="size-7" aria-hidden="true" />}
        />
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
          {visible.map((task) => {
            const done = task.status === "Completed";
            return (
              <article
                key={task.id}
                className="surface-card reveal flex flex-col justify-between p-5"
              >
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h2
                        className={`text-base font-semibold ${done ? "text-muted-foreground line-through" : ""}`}
                      >
                        {task.task_name}
                      </h2>
                    </div>
                    <Badge variant={done ? "secondary" : "outline"} className="shrink-0">
                      {task.status}
                    </Badge>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-x-6 gap-y-1 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <User className="size-3 text-primary" aria-hidden="true" />
                      {task.assigned_to_name ??
                        (task.assigned_to ? `Worker #${task.assigned_to}` : "Unassigned")}
                    </span>
                    {task.date && (
                      <span className="flex items-center gap-1">
                        <Calendar className="size-3 text-muted-foreground" aria-hidden="true" />
                        {formatDate(task.date)}
                      </span>
                    )}
                  </div>
                </div>

                {isStaff && (
                  <div className="mt-5 flex flex-wrap gap-2 border-t border-border pt-4">
                    <Button
                      size="sm"
                      variant={done ? "outline" : "default"}
                      disabled={update.isPending}
                      onClick={() =>
                        update.mutate({
                          id: task.id,
                          input: { status: done ? "Pending" : "Completed" },
                        })
                      }
                    >
                      {done ? (
                        <Circle className="size-3.5" aria-hidden="true" />
                      ) : (
                        <CheckCircle2 className="size-3.5" aria-hidden="true" />
                      )}
                      Mark {done ? "Pending" : "Completed"}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setEditing(task);
                        setFormOpen(true);
                      }}
                    >
                      <Pencil className="size-3.5" aria-hidden="true" />
                      Edit
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => setDeleting(task)}>
                      <Trash2 className="size-3.5 text-destructive" aria-hidden="true" />
                      Delete
                    </Button>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}

      {formOpen && (
        <TaskForm
          key={editing?.id ?? "new"}
          open={formOpen}
          onOpenChange={setFormOpen}
          task={editing}
        />
      )}

      <AlertDialog open={!!deleting} onOpenChange={(v) => !v && setDeleting(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this task?</AlertDialogTitle>
            <AlertDialogDescription>
              "{deleting?.task_name}" will be permanently removed. This action cannot be undone.
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

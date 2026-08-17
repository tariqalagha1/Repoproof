export const colors = {
  bg: "#0f1117", surface: "#1a1d27", border: "#2a2d3a",
  text: "#e4e6f0", dim: "#8b8fa3", accent: "#7c5cfc", accentHover: "#6a4ce8",
  success: "#4ade80", warning: "#fbbf24", error: "#f87171", info: "#60a5fa",
};

export const lifecycleColors: Record<string, string> = {
  created: "#8b8fa3", discovering: "#60a5fa", plan_ready: "#a78bfa",
  awaiting_approval: "#fbbf24", approved: "#4ade80", provisioning: "#60a5fa",
  executing: "#60a5fa", verifying: "#a78bfa", reporting: "#fbbf24",
  completed: "#4ade80", partial: "#fbbf24", blocked: "#fb923c",
  failed: "#f87171", cancelled: "#8b8fa3",
};

export const stageStatusColors: Record<string, string> = {
  pending: "#8b8fa3", ready: "#60a5fa", awaiting_approval: "#fbbf24",
  running: "#60a5fa", retrying: "#fbbf24",
  completed: "#4ade80", completed_with_findings: "#fbbf24",
  partial: "#fb923c", blocked: "#fb923c", failed: "#f87171",
  cancelled: "#8b8fa3", paused: "#a78bfa",
  skipped_not_applicable: "#555862",
};

export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

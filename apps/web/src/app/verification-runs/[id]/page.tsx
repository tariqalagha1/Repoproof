"use client";

import { api } from "@/lib/api";
import { colors, lifecycleColors, formatDate } from "@/lib/theme";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

const ADVANCE_FLOW = [
  "discovering",
  "plan_ready",
  "awaiting_approval",
  "approved",
  "provisioning",
  "executing",
  "verifying",
  "reporting",
  "completed",
];

export default function VerificationRunDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [run, setRun] = useState<any | null>(null);
  const [transitions, setTransitions] = useState<any[]>([]);
  const [checkpoints, setCheckpoints] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [advancing, setAdvancing] = useState(false);

  const loadData = async () => {
    try {
      const [r, t, c] = await Promise.all([
        api.runs.get(id),
        api.runs.transitions(id).catch(() => [] as any[]),
        api.runs.checkpoints(id).catch(() => [] as any[]),
      ]);
      setRun(r);
      setTransitions(t);
      setCheckpoints(c);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [id]);

  const handleAdvance = async () => {
    if (!run) return;
    const currentIdx = ADVANCE_FLOW.indexOf(run.lifecycle_state);
    if (currentIdx < 0 || currentIdx >= ADVANCE_FLOW.length - 1) return;
    const nextState = ADVANCE_FLOW[currentIdx + 1];
    setAdvancing(true);
    try {
      const updated = await api.runs.transition(run.id, nextState, "Advancing through foundation states");
      setRun(updated);
      const t = await api.runs.transitions(id);
      setTransitions(t);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Transition failed");
    } finally {
      setAdvancing(false);
    }
  };

  const handleSaveCheckpoint = async () => {
    if (!run) return;
    try {
      const cp = await api.runs.createCheckpoint(run.id, `snapshot-${Date.now()}`, {
        state: run.lifecycle_state,
        timestamp: new Date().toISOString(),
      });
      setCheckpoints((prev) => [...prev, cp]);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Failed to save checkpoint");
    }
  };

  if (loading) return <p style={{ color: colors.dim }}>Loading run...</p>;
  if (error) return <p style={{ color: colors.error }}>Error: {error}</p>;
  if (!run) return <p style={{ color: colors.error }}>Run not found</p>;

  const canAdvance = ADVANCE_FLOW.indexOf(run.lifecycle_state) < ADVANCE_FLOW.length - 1
    && !["completed", "failed", "cancelled"].includes(run.lifecycle_state);

  return (
    <div>
      <Link
        href={`/projects/${run.project_id}`}
        style={{ color: colors.accent, fontSize: 14, textDecoration: "none" }}
      >
        ← Back to Project
      </Link>

      <h1 style={{ fontSize: 24, margin: "16px 0 8px" }}>
        Verification Run {run.id.slice(0, 12)}...
      </h1>

      {/* State badge */}
      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 24, flexWrap: "wrap" }}>
        <span
          style={{
            background: lifecycleColors[run.lifecycle_state] || colors.dim,
            color: "#fff",
            padding: "6px 16px",
            borderRadius: 999,
            fontSize: 14,
            fontWeight: 700,
            textTransform: "uppercase",
          }}
        >
          {run.lifecycle_state}
        </span>
        <span style={{ color: colors.dim, fontSize: 14 }}>Version {run.version}</span>
        <span style={{ color: colors.dim, fontSize: 14 }}>Created {formatDate(run.created_at)}</span>
      </div>

      {/* Action buttons */}
      <div style={{ display: "flex", gap: 12, marginBottom: 32 }}>
        {canAdvance && (
          <button
            onClick={handleAdvance}
            disabled={advancing}
            style={{
              background: colors.accent,
              color: "#fff",
              border: "none",
              padding: "10px 20px",
              borderRadius: 8,
              cursor: "pointer",
              fontWeight: 600,
              opacity: advancing ? 0.6 : 1,
            }}
          >
            {advancing ? "Advancing..." : "Advance Lifecycle"}
          </button>
        )}
        <button
          onClick={handleSaveCheckpoint}
          style={{
            background: "transparent",
            color: colors.accent,
            border: `1px solid ${colors.accent}`,
            padding: "10px 20px",
            borderRadius: 8,
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          Save Checkpoint
        </button>
      </div>

      {/* Lifecycle progress bar */}
      <div style={{ marginBottom: 32 }}>
        <h3 style={{ fontSize: 16, marginBottom: 12 }}>Lifecycle Progress</h3>
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          {ADVANCE_FLOW.map((state) => {
            const idx = ADVANCE_FLOW.indexOf(state);
            const currentIdx = ADVANCE_FLOW.indexOf(run.lifecycle_state);
            const isPast = idx <= currentIdx;
            return (
              <div
                key={state}
                style={{
                  background: isPast ? lifecycleColors[state] || colors.accent : colors.surface,
                  border: `1px solid ${isPast ? "transparent" : colors.border}`,
                  color: isPast ? "#fff" : colors.dim,
                  padding: "6px 12px",
                  borderRadius: 6,
                  fontSize: 11,
                  fontWeight: isPast ? 600 : 400,
                  textTransform: "uppercase",
                  textAlign: "center",
                  flex: "0 0 auto",
                }}
              >
                {state.replace(/_/g, " ")}
              </div>
            );
          })}
        </div>
      </div>

      {/* Transition history */}
      <div
        style={{
          background: colors.surface,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
          padding: 20,
          marginBottom: 24,
        }}
      >
        <h3 style={{ margin: "0 0 16px", fontSize: 16 }}>Transition History</h3>
        {transitions.length === 0 ? (
          <p style={{ color: colors.dim, fontSize: 14 }}>No transitions recorded.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {transitions.map((t) => (
              <div
                key={t.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  padding: "8px 0",
                  borderBottom: `1px solid ${colors.border}`,
                  fontSize: 13,
                }}
              >
                <span style={{ color: colors.dim, minWidth: 160 }}>{formatDate(t.transitioned_at)}</span>
                <span style={{ color: lifecycleColors[t.from_state] || colors.dim, fontWeight: 500 }}>
                  {t.from_state}
                </span>
                <span style={{ color: colors.dim }}>→</span>
                <span style={{ color: lifecycleColors[t.to_state] || colors.text, fontWeight: 600 }}>
                  {t.to_state}
                </span>
                <span style={{ color: colors.dim, flex: 1 }}>{t.reason}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Checkpoints */}
      <div
        style={{
          background: colors.surface,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
          padding: 20,
        }}
      >
        <h3 style={{ margin: "0 0 16px", fontSize: 16 }}>Checkpoints ({checkpoints.length})</h3>
        {checkpoints.length === 0 ? (
          <p style={{ color: colors.dim, fontSize: 14 }}>No checkpoints saved yet.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {checkpoints.map((cp) => (
              <div
                key={cp.id}
                style={{
                  padding: "10px 0",
                  borderBottom: `1px solid ${colors.border}`,
                  fontSize: 13,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ fontWeight: 600 }}>{cp.name}</span>
                  <span style={{ color: colors.dim }}>{formatDate(cp.created_at)}</span>
                </div>
                <pre
                  style={{
                    margin: "8px 0 0",
                    fontSize: 11,
                    color: colors.dim,
                    background: colors.bg,
                    padding: 8,
                    borderRadius: 4,
                    overflow: "auto",
                  }}
                >
                  {JSON.stringify(cp.state_snapshot, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

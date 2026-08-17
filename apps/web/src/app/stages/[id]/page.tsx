"use client";

import { api, StageDetail } from "@/lib/api";
import { colors, stageStatusColors, formatDate } from "@/lib/theme";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function StageDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [stage, setStage] = useState<StageDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.stages.get(id).then(setStage).catch(e => setError(e.message)).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p style={{ color: colors.dim }}>Loading stage...</p>;
  if (error) return <p style={{ color: colors.error }}>Error: {error}</p>;
  if (!stage) return <p style={{ color: colors.error }}>Stage not found</p>;

  return (
    <div>
      <Link href={`/master-jobs/${stage.master_job_id}`} style={{ color: colors.accent, fontSize: 14, textDecoration: "none" }}>← Back to Job</Link>

      <h1 style={{ fontSize: 24, margin: "16px 0 8px" }}>{stageName(stage.stage_type)}</h1>

      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 24, flexWrap: "wrap" }}>
        <span style={{ background: stageStatusColors[stage.status] || colors.dim, color: "#fff", padding: "4px 14px", borderRadius: 999, fontSize: 13, fontWeight: 700, textTransform: "uppercase" }}>{stage.status.replace(/_/g, " ")}</span>
        <span style={{ fontSize: 12, color: colors.dim }}>Criticality: {stage.criticality}</span>
        <span style={{ fontSize: 12, color: colors.dim }}>Applicability: {stage.applicability}</span>
        <span style={{ fontSize: 12, color: colors.dim }}>Attempt {stage.attempt_count}</span>
      </div>

      {stage.blocked_reason && (
        <div style={{ background: "rgba(251,146,60,0.1)", border: "1px solid #fb923c", borderRadius: 8, padding: 12, marginBottom: 16 }}>
          <p style={{ margin: 0, fontSize: 13, color: "#fb923c" }}>Blocked: {stage.blocked_reason}</p>
        </div>
      )}

      {/* Checks */}
      <h2 style={{ fontSize: 18, marginBottom: 12 }}>Verification Checks ({stage.checks.length})</h2>
      {stage.checks.length === 0 ? (
        <p style={{ color: colors.dim, fontSize: 14 }}>No checks defined for this stage.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {stage.checks.map(check => (
            <div key={check.id} style={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: 10, padding: "14px 20px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <span style={{ fontWeight: 600, fontSize: 14 }}>{check.name}</span>
                  <span style={{ background: stageStatusColors[check.status] || colors.dim, color: "#fff", padding: "1px 8px", borderRadius: 999, fontSize: 10, fontWeight: 700, textTransform: "uppercase" }}>{check.status}</span>
                </div>
                <p style={{ margin: "4px 0 0", fontSize: 12, color: colors.dim }}>{check.description}</p>
                {check.blocked_reason && <p style={{ margin: "4px 0 0", fontSize: 11, color: "#fb923c" }}>{check.blocked_reason}</p>}
              </div>
              <span style={{ fontSize: 11, color: colors.dim, textTransform: "uppercase", flexShrink: 0 }}>{check.evidence_classification.replace(/_/g, " ")}</span>
            </div>
          ))}
        </div>
      )}

      {/* Timing */}
      <div style={{ marginTop: 24, display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))" }}>
        <div style={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: 8, padding: 12 }}>
          <p style={{ margin: 0, fontSize: 12, color: colors.dim }}>Started</p>
          <p style={{ margin: "4px 0 0", fontSize: 14 }}>{formatDate(stage.started_at)}</p>
        </div>
        <div style={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: 8, padding: 12 }}>
          <p style={{ margin: 0, fontSize: 12, color: colors.dim }}>Completed</p>
          <p style={{ margin: "4px 0 0", fontSize: 14 }}>{formatDate(stage.completed_at)}</p>
        </div>
      </div>
    </div>
  );
}

function stageName(type: string): string {
  const names: Record<string, string> = {
    "00_intake": "Intake", "01_passive_discovery": "Passive Discovery",
    "02_plan_generation": "Plan Generation", "03_policy_validation": "Policy Validation",
    "04_environment_provisioning": "Environment Provisioning",
    "05_dependency_installation": "Dependency Installation",
    "06_pre_runtime_verification": "Pre-Runtime Verification",
    "07_build": "Build", "08_infrastructure_startup": "Infrastructure Startup",
    "09_application_startup": "Application Startup",
    "10_live_workflow_testing": "Live Workflow Testing",
    "11_architecture_portability": "Architecture Portability",
    "12_production_readiness": "Production Readiness",
    "13_output_correctness": "Output Correctness",
    "14_compliance": "Compliance", "15_final_advisory_report": "Final Advisory Report",
  };
  return names[type] || type;
}

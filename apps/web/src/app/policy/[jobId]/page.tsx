"use client";

import { useEffect, useState } from "react";

interface PolicyResult {
  id: string;
  outcome: string;
  policy_version: string;
  total: number;
  allowed: number;
  allowed_with_restrictions: number;
  require_approval: number;
  denied: number;
  blocked: number;
  critical_risks: number;
  high_risks: number;
}

export default function PolicyDashboard({ params }: { params: { jobId: string } }) {
  const jobId = params.jobId;
  const [result, setResult] = useState<PolicyResult | null>(null);
  const [decisions, setDecisions] = useState<any[]>([]);
  const [approvals, setApprovals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch(`/api/v1/policy-results/by-job/${jobId}`);
        if (!res.ok) throw new Error("No policy result");
        const data: PolicyResult = await res.json();
        setResult(data);

        const decRes = await fetch(`/api/v1/policy-results/${data.id}/decisions`);
        setDecisions(await decRes.json());

        const appRes = await fetch(`/api/v1/policy-results/${data.id}/approvals`);
        setApprovals(await appRes.json());
      } catch (e: any) {
        setError(e.message || "Failed to load policy data");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [jobId]);

  if (loading) return <div className="p-8 text-gray-500">Loading policy results…</div>;
  if (error) return <div className="p-8 text-red-500">Error: {error}</div>;
  if (!result) return <div className="p-8 text-gray-500">No policy result available.</div>;

  const outcomeColor =
    result.outcome === "approved" ? "bg-green-100 text-green-800" :
    result.outcome === "approved_with_restrictions" ? "bg-yellow-100 text-yellow-800" :
    result.outcome === "denied" ? "bg-red-100 text-red-800" :
    "bg-gray-100 text-gray-800";

  const deniedItems = decisions.filter((d: any) => d.decision === "deny");

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <h2 className="text-2xl font-bold">Policy Validation</h2>

      {/* Overall Outcome */}
      <div className={`rounded-lg p-4 ${outcomeColor}`}>
        <span className="font-semibold text-lg">Outcome: {result.outcome.replace(/_/g, " ").toUpperCase()}</span>
        <span className="ml-4 text-sm">Policy v{result.policy_version}</span>
      </div>

      {/* Summary Grid */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
        {[
          ["Allowed", result.allowed, "text-green-600"],
          ["Restricted", result.allowed_with_restrictions, "text-yellow-600"],
          ["Approval", result.require_approval, "text-orange-600"],
          ["Denied", result.denied, "text-red-600"],
          ["Blocked", result.blocked, "text-gray-600"],
          ["Total", result.total, "text-blue-600"],
        ].map(([label, count, color]) => (
          <div key={label as string} className="bg-white rounded-lg p-3 text-center shadow-sm">
            <div className={`text-2xl font-bold ${color}`}>{count as number}</div>
            <div className="text-xs text-gray-500">{label as string}</div>
          </div>
        ))}
      </div>

      {/* Risk Summary */}
      <div className="bg-white rounded-lg p-4 shadow-sm">
        <h3 className="font-semibold mb-2">Risk Summary</h3>
        <div className="flex gap-6">
          <div><span className="text-red-600 font-bold">{result.critical_risks}</span> Critical</div>
          <div><span className="text-orange-600 font-bold">{result.high_risks}</span> High</div>
        </div>
      </div>

      {/* Denied Items */}
      {deniedItems.length > 0 && (
        <div className="bg-red-50 rounded-lg p-4">
          <h3 className="font-semibold text-red-800 mb-2">Denied Items ({deniedItems.length})</h3>
          <ul className="space-y-1 text-sm">
            {deniedItems.map((d: any, i: number) => (
              <li key={i} className="text-red-700">
                <span className="font-mono">{d.rule_id}</span>: {d.reason}
                <span className="ml-2 text-xs bg-red-200 px-1 rounded">{d.risk_level}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Approval Requests */}
      {approvals.length > 0 && (
        <div className="bg-orange-50 rounded-lg p-4">
          <h3 className="font-semibold text-orange-800 mb-2">Approval Requests ({approvals.length})</h3>
          <ul className="space-y-2 text-sm">
            {approvals.map((a: any, i: number) => (
              <li key={i} className="text-orange-700">
                <span className="font-medium">{a.action_type}</span>: {a.reason}
                <span className="ml-2 text-xs bg-orange-200 px-1 rounded">{a.risk_level}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Decisions Table */}
      <div className="bg-white rounded-lg p-4 shadow-sm">
        <h3 className="font-semibold mb-2">All Decisions ({decisions.length})</h3>
        <div className="max-h-64 overflow-y-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="py-1">Rule</th>
                <th className="py-1">Area</th>
                <th className="py-1">Decision</th>
                <th className="py-1">Risk</th>
                <th className="py-1">Reason</th>
              </tr>
            </thead>
            <tbody>
              {decisions.slice(0, 50).map((d: any, i: number) => (
                <tr key={i} className="border-b border-gray-100">
                  <td className="py-1 font-mono text-xs">{d.rule_id}</td>
                  <td className="py-1 text-xs">{d.policy_area?.replace(/_/g, " ")}</td>
                  <td className={`py-1 text-xs font-medium ${
                    d.decision === "allow" ? "text-green-600" :
                    d.decision === "allow_with_restrictions" ? "text-yellow-600" :
                    d.decision === "deny" ? "text-red-600" : "text-gray-600"
                  }`}>{d.decision.replace(/_/g, " ")}</td>
                  <td className="py-1 text-xs">{d.risk_level}</td>
                  <td className="py-1 text-xs text-gray-500 truncate max-w-[200px]">{d.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Status Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
        ⚠ Nothing has been executed. All commands remain NOT_EXECUTED.
        Environment provisioning is {result.outcome === "approved" || result.outcome === "approved_with_restrictions" ? "READY" : "BLOCKED"}.
      </div>
    </div>
  );
}

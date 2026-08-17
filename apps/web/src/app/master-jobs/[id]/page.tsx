'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  getMasterJob,
  getJobStages,
  getJobProgress,
  getPolicyResultByJob,
  getCompatibility,
  completeIntake,
  runDiscovery,
  generatePlan,
  validatePolicy,
  provisionEnvironment,
  pauseJob,
  resumeJob,
  cancelJob,
} from '@/lib/api';

export default function MasterJobDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [job, setJob] = useState<any>(null);
  const [stages, setStages] = useState<any[]>([]);
  const [progress, setProgress] = useState<any>(null);
  const [policyResults, setPolicyResults] = useState<any[]>([]);
  const [compatibility, setCompatibility] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const [j, stg, prog, pol, comp] = await Promise.all([
        getMasterJob(id),
        getJobStages(id).catch(() => []),
        getJobProgress(id).catch(() => null),
        getPolicyResultByJob(id).catch(() => []),
        getCompatibility(id).catch(() => null),
      ]);
      setJob(j);
      setStages(stg);
      setProgress(prog);
      setPolicyResults(pol);
      setCompatibility(comp);
    } catch (err: any) {
      setError(err.message || 'Failed to load master job');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const doAction = async (action: string, fn: (jobId: string) => Promise<any>) => {
    setActionLoading(action);
    try {
      await fn(id);
      await fetchData();
    } catch (err: any) {
      alert(err.message || `Failed: ${action}`);
    } finally {
      setActionLoading(null);
    }
  };

  const statusColors: Record<string, string> = {
    pending: '#ff9800',
    running: '#2196f3',
    completed: '#4caf50',
    failed: '#f44336',
    cancelled: '#9e9e9e',
    paused: '#ffc107',
    in_progress: '#2196f3',
    skipped: '#bdbdbd',
  };

  if (loading) {
    return (
      <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
        <Link href="/dashboard">&larr; Dashboard</Link>
        <h1>Master Job</h1>
        <p>Loading…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
        <Link href="/dashboard">&larr; Dashboard</Link>
        <h1>Master Job</h1>
        <p style={{ color: 'red' }}>Error: {error}</p>
        <button onClick={fetchData}>Retry</button>
      </div>
    );
  }

  if (!job) {
    return (
      <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
        <Link href="/dashboard">&larr; Dashboard</Link>
        <h1>Master Job Not Found</h1>
      </div>
    );
  }

  const progressPct =
    progress?.percent != null
      ? progress.percent
      : stages.length > 0
        ? Math.round((stages.filter((s: any) => s.status === 'completed').length / stages.length) * 100)
        : 0;

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif', maxWidth: 1100, margin: '0 auto' }}>
      <Link href="/dashboard">&larr; Dashboard</Link>

      {/* Job Header */}
      <div style={{ marginTop: '1rem', marginBottom: '1.5rem' }}>
        <h1>Master Job</h1>
        <p>
          <strong>Repository:</strong> {job.repository_url || '—'}<br />
          <strong>Branch:</strong> {job.branch || 'main'}<br />
          <strong>Status:</strong>{' '}
          <span style={{
            padding: '0.15rem 0.5rem',
            borderRadius: 10,
            backgroundColor: statusColors[job.status] || '#888',
            color: '#fff',
            fontSize: '0.85rem',
            fontWeight: 600,
          }}>
            {job.status || 'unknown'}
          </span>
        </p>
      </div>

      {/* Progress Bar */}
      <div style={{ marginBottom: '1.5rem' }}>
        <strong>Progress: {progressPct}%</strong>
        <div style={{
          height: 12,
          backgroundColor: '#e0e0e0',
          borderRadius: 6,
          marginTop: '0.25rem',
          overflow: 'hidden',
        }}>
          <div style={{
            width: `${progressPct}%`,
            height: '100%',
            backgroundColor: '#4caf50',
            borderRadius: 6,
            transition: 'width 0.3s',
          }} />
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <button
          onClick={() => doAction('completeIntake', completeIntake)}
          disabled={actionLoading === 'completeIntake'}
          style={{ padding: '0.5rem 0.75rem' }}
        >
          {actionLoading === 'completeIntake' ? '…' : 'Complete Intake'}
        </button>
        <button
          onClick={() => doAction('runDiscovery', runDiscovery)}
          disabled={actionLoading === 'runDiscovery'}
          style={{ padding: '0.5rem 0.75rem' }}
        >
          {actionLoading === 'runDiscovery' ? '…' : 'Discover'}
        </button>
        <button
          onClick={() => doAction('generatePlan', generatePlan)}
          disabled={actionLoading === 'generatePlan'}
          style={{ padding: '0.5rem 0.75rem' }}
        >
          {actionLoading === 'generatePlan' ? '…' : 'Generate Plan'}
        </button>
        <button
          onClick={() => doAction('validatePolicy', validatePolicy)}
          disabled={actionLoading === 'validatePolicy'}
          style={{ padding: '0.5rem 0.75rem' }}
        >
          {actionLoading === 'validatePolicy' ? '…' : 'Validate Policy'}
        </button>
        <button
          onClick={() => {
            // Provision needs a stage_id — use first non-completed stage or prompt
            const nextStage = stages.find((s: any) => s.status !== 'completed');
            if (!nextStage) {
              alert('No pending stage to provision');
              return;
            }
            doAction('provisionEnvironment', () =>
              provisionEnvironment({ master_job_id: id, stage_id: nextStage.id })
            );
          }}
          disabled={actionLoading === 'provisionEnvironment'}
          style={{ padding: '0.5rem 0.75rem' }}
        >
          {actionLoading === 'provisionEnvironment' ? '…' : 'Provision'}
        </button>
        <span style={{ flexGrow: 1 }} />
        <button
          onClick={() => doAction('pauseJob', pauseJob)}
          disabled={actionLoading === 'pauseJob'}
          style={{ padding: '0.5rem 0.75rem', backgroundColor: '#ffc107', border: 'none', borderRadius: 4 }}
        >
          {actionLoading === 'pauseJob' ? '…' : 'Pause'}
        </button>
        <button
          onClick={() => doAction('resumeJob', resumeJob)}
          disabled={actionLoading === 'resumeJob'}
          style={{ padding: '0.5rem 0.75rem', backgroundColor: '#4caf50', border: 'none', borderRadius: 4, color: '#fff' }}
        >
          {actionLoading === 'resumeJob' ? '…' : 'Resume'}
        </button>
        <button
          onClick={() => doAction('cancelJob', cancelJob)}
          disabled={actionLoading === 'cancelJob'}
          style={{ padding: '0.5rem 0.75rem', backgroundColor: '#f44336', border: 'none', borderRadius: 4, color: '#fff' }}
        >
          {actionLoading === 'cancelJob' ? '…' : 'Cancel'}
        </button>
      </div>

      {/* Stages Grid */}
      <section style={{ marginBottom: '2rem' }}>
        <h2>Pipeline Stages ({stages.length})</h2>
        {stages.length === 0 ? (
          <p style={{ color: '#888' }}>No stages yet.</p>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
            gap: '0.75rem',
          }}>
            {stages
              .sort((a: any, b: any) => (a.sequence || 0) - (b.sequence || 0))
              .map((s: any) => {
                const sc = statusColors[s.status] || '#888';
                return (
                  <Link
                    key={s.id}
                    href={`/stages/${s.id}`}
                    style={{
                      textDecoration: 'none',
                      color: 'inherit',
                      padding: '0.75rem',
                      border: '1px solid #ddd',
                      borderRadius: 8,
                      borderLeft: `4px solid ${sc}`,
                      display: 'block',
                    }}
                  >
                    <div style={{ fontWeight: 600, marginBottom: '0.3rem' }}>
                      {s.stage_type || s.name || 'Stage'}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#888' }}>
                      Seq: {s.sequence != null ? s.sequence : '—'}
                    </div>
                    <span style={{
                      display: 'inline-block',
                      marginTop: '0.3rem',
                      padding: '0.1rem 0.5rem',
                      borderRadius: 8,
                      backgroundColor: sc,
                      color: '#fff',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                    }}>
                      {s.status || 'unknown'}
                    </span>
                  </Link>
                );
              })}
          </div>
        )}
      </section>

      {/* Policy Results */}
      <section>
        <h2>Policy Results ({policyResults.length})</h2>
        {policyResults.length === 0 ? (
          <p style={{ color: '#888' }}>No policy results.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {policyResults.map((pr: any) => (
              <Link
                key={pr.id}
                href={`/policy-results/${pr.id}`}
                style={{
                  textDecoration: 'none',
                  color: 'inherit',
                  padding: '0.75rem',
                  border: '1px solid #ddd',
                  borderRadius: 8,
                  display: 'block',
                }}
              >
                <strong>{pr.decision || 'No decision'}</strong>
                <span style={{ fontSize: '0.8rem', color: '#888', marginLeft: '0.75rem' }}>
                  {pr.created_at || ''}
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Compatibility Score */}
      {compatibility && (
        <section style={{ marginTop: '2rem' }}>
          <h2>Compatibility Score</h2>
          <div style={{
            padding: '1.25rem',
            border: '1px solid #ddd',
            borderRadius: 10,
            backgroundColor: '#fafafa',
          }}>
            {/* Overall */}
            <div style={{ textAlign: 'center', marginBottom: '1.25rem' }}>
              <div style={{ fontSize: '3rem' }}>{compatibility.overall?.emoji || '🟡'}</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 700, marginTop: '0.25rem' }}>
                {compatibility.overall?.badge || 'UNKNOWN'}
              </div>
              <div style={{ fontSize: '0.85rem', color: '#888', marginTop: '0.25rem' }}>
                {compatibility.stages_completed}/{compatibility.stages_total} stages completed
              </div>
            </div>

            {/* Breakdown grid */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
              gap: '0.75rem',
            }}>
              {compatibility.breakdown && Object.entries(compatibility.breakdown).map(([key, val]: [string, any]) => (
                <div key={key} style={{
                  padding: '0.75rem',
                  border: '1px solid #e0e0e0',
                  borderRadius: 8,
                  textAlign: 'center',
                  backgroundColor: '#fff',
                }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#888', textTransform: 'uppercase' }}>
                    {key}
                  </div>
                  <div style={{ fontSize: '1.5rem', margin: '0.3rem 0' }}>
                    {val.emoji || '🟡'}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#555' }}>
                    {val.secrets_found != null && `🔑 ${val.secrets_found}`}
                    {val.vulnerabilities != null && `🐛 ${val.vulnerabilities}`}
                    {val.mismatches != null && `📦 ${val.mismatches}`}
                    {val.passed != null && `✓ ${val.passed}`}
                  </div>
                </div>
              ))}
            </div>

            {/* Warnings */}
            {compatibility.warnings?.length > 0 && (
              <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: '#fff3cd', borderRadius: 6 }}>
                <strong>⚠ Warnings:</strong>
                <ul style={{ margin: '0.3rem 0 0 1rem', padding: 0 }}>
                  {compatibility.warnings.map((w: string, i: number) => (
                    <li key={i} style={{ fontSize: '0.85rem' }}>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Recommendations */}
            {compatibility.recommendations?.length > 0 && (
              <div style={{ marginTop: '0.75rem', padding: '0.75rem', backgroundColor: '#d4edda', borderRadius: 6 }}>
                <strong>💡 Recommendations:</strong>
                <ul style={{ margin: '0.3rem 0 0 1rem', padding: 0 }}>
                  {compatibility.recommendations.map((r: string, i: number) => (
                    <li key={i} style={{ fontSize: '0.85rem' }}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}

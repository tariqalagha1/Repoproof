'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  getProject,
  getMasterJobs,
  createMasterJob,
} from '@/lib/api';

export default function ProjectDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [project, setProject] = useState<any>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create master job form
  const [repoUrl, setRepoUrl] = useState('');
  const [branch, setBranch] = useState('main');
  const [creatingJob, setCreatingJob] = useState(false);

  const fetchData = useCallback(async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const [proj, masterJobs] = await Promise.all([
        getProject(id),
        getMasterJobs(id),
      ]);
      setProject(proj);
      setJobs(masterJobs);
    } catch (err: any) {
      setError(err.message || 'Failed to load project');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    try {
      setCreatingJob(true);
      const job = await createMasterJob({
        project_id: id,
        repository_url: repoUrl.trim(),
        branch: branch.trim() || 'main',
      });
      setJobs((prev) => [...prev, job]);
      setRepoUrl('');
      setBranch('main');
    } catch (err: any) {
      alert(err.message || 'Failed to create master job');
    } finally {
      setCreatingJob(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
        <Link href="/dashboard">&larr; Back to Dashboard</Link>
        <h1>Project</h1>
        <p>Loading…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
        <Link href="/dashboard">&larr; Back to Dashboard</Link>
        <h1>Project</h1>
        <p style={{ color: 'red' }}>Error: {error}</p>
        <button onClick={fetchData}>Retry</button>
      </div>
    );
  }

  if (!project) {
    return (
      <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
        <Link href="/dashboard">&larr; Back to Dashboard</Link>
        <h1>Project Not Found</h1>
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif', maxWidth: 1000, margin: '0 auto' }}>
      <Link href="/dashboard">&larr; Back to Dashboard</Link>

      {/* Project Info */}
      <div style={{ marginTop: '1rem', marginBottom: '2rem' }}>
        <h1>{project.name}</h1>
        {project.description && <p style={{ color: '#555' }}>{project.description}</p>}
        <p style={{ fontSize: '0.85rem', color: '#999' }}>
          ID: {project.id} &middot; Status: {project.status || 'active'}
        </p>
      </div>

      {/* Repository Connection / Create Master Job Form */}
      <div style={{
        marginBottom: '2rem',
        padding: '1rem',
        border: '1px solid #ddd',
        borderRadius: 8,
        backgroundColor: '#fafafa',
      }}>
        <h3 style={{ marginTop: 0 }}>New Master Job</h3>
        <form onSubmit={handleCreateJob} style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Repository URL (e.g. https://github.com/user/repo)"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            required
            style={{ flex: 3, minWidth: 300, padding: '0.5rem' }}
          />
          <input
            type="text"
            placeholder="Branch"
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            style={{ flex: 1, minWidth: 120, padding: '0.5rem' }}
          />
          <button type="submit" disabled={creatingJob} style={{ padding: '0.5rem 1rem' }}>
            {creatingJob ? 'Creating…' : 'Create Job'}
          </button>
        </form>
      </div>

      {/* Master Jobs List */}
      <section>
        <h2>Master Jobs</h2>
        {jobs.length === 0 ? (
          <p style={{ color: '#888' }}>No master jobs yet. Create one above.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {jobs.map((j: any) => {
              const statusColors: Record<string, string> = {
                pending: '#ff9800',
                running: '#2196f3',
                completed: '#4caf50',
                failed: '#f44336',
                cancelled: '#9e9e9e',
                paused: '#ffc107',
              };
              const sc = statusColors[j.status] || '#888';
              return (
                <Link
                  key={j.id}
                  href={`/master-jobs/${j.id}`}
                  style={{
                    textDecoration: 'none',
                    color: 'inherit',
                    padding: '1rem',
                    border: '1px solid #ddd',
                    borderRadius: 8,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <strong>{j.repository_url || 'Unknown repo'}</strong>
                    <span style={{ marginLeft: '0.75rem', fontSize: '0.85rem', color: '#666' }}>
                      {j.branch || 'main'}
                    </span>
                  </div>
                  <span style={{
                    padding: '0.2rem 0.6rem',
                    borderRadius: 12,
                    backgroundColor: sc,
                    color: '#fff',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                  }}>
                    {j.status || 'unknown'}
                  </span>
                </Link>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  getProjects,
  createProject,
  getGates,
  getProviderStatus,
} from '@/lib/api';

export default function DashboardPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [gates, setGates] = useState<any[]>([]);
  const [providerStatus, setProviderStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New project form
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [creating, setCreating] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [projRes, gatesRes, statusRes] = await Promise.all([
        getProjects(),
        getGates().catch(() => []),
        getProviderStatus().catch(() => null),
      ]);
      setProjects(projRes);
      setGates(gatesRes);
      setProviderStatus(statusRes);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    try {
      setCreating(true);
      const created = await createProject({
        name: newName.trim(),
        description: newDesc.trim() || undefined,
      });
      setProjects((prev) => [...prev, created]);
      setNewName('');
      setNewDesc('');
    } catch (err: any) {
      alert(err.message || 'Failed to create project');
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
        <h1>RepoProof AI Dashboard</h1>
        <p>Loading…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
        <h1>RepoProof AI Dashboard</h1>
        <p style={{ color: 'red' }}>Error: {error}</p>
        <button onClick={fetchData}>Retry</button>
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif', maxWidth: 1100, margin: '0 auto' }}>
      <h1>RepoProof AI Dashboard</h1>

      {/* LLM Provider Status */}
      {providerStatus && (
        <div style={{
          marginBottom: '1.5rem',
          padding: '0.75rem 1rem',
          borderRadius: 8,
          backgroundColor: providerStatus.available ? '#e6ffe6' : '#ffe6e6',
          border: `1px solid ${providerStatus.available ? '#4caf50' : '#f44336'}`,
        }}>
          <strong>LLM Provider:</strong>{' '}
          {providerStatus.provider || 'unknown'} —{' '}
          {providerStatus.available ? 'Online' : 'Offline'}
        </div>
      )}

      {/* New Project Form */}
      <div style={{
        marginBottom: '2rem',
        padding: '1rem',
        border: '1px solid #ddd',
        borderRadius: 8,
        backgroundColor: '#fafafa',
      }}>
        <h3 style={{ marginTop: 0 }}>New Project</h3>
        <form onSubmit={handleCreate} style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Project name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            required
            style={{ flex: 1, minWidth: 180, padding: '0.5rem' }}
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            style={{ flex: 2, minWidth: 240, padding: '0.5rem' }}
          />
          <button type="submit" disabled={creating} style={{ padding: '0.5rem 1rem' }}>
            {creating ? 'Creating…' : 'Create'}
          </button>
        </form>
      </div>

      {/* Project List */}
      <section style={{ marginBottom: '2rem' }}>
        <h2>Projects</h2>
        {projects.length === 0 ? (
          <p style={{ color: '#888' }}>No projects yet. Create one above.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {projects.map((p: any) => (
              <Link
                key={p.id}
                href={`/projects/${p.id}`}
                style={{
                  textDecoration: 'none',
                  color: 'inherit',
                  padding: '1rem',
                  border: '1px solid #ddd',
                  borderRadius: 8,
                  display: 'block',
                }}
              >
                <strong>{p.name}</strong>
                {p.description && (
                  <span style={{ marginLeft: '0.75rem', color: '#666' }}>{p.description}</span>
                )}
                <span style={{ float: 'right', fontSize: '0.85rem', color: '#999' }}>
                  {p.status || 'active'}
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Verification Gates */}
      <section>
        <h2>Verification Gates</h2>
        {gates.length === 0 ? (
          <p style={{ color: '#888' }}>No gate definitions available.</p>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '1rem',
          }}>
            {gates.map((g: any) => (
              <div
                key={g.id || g.name}
                style={{
                  padding: '1rem',
                  border: '1px solid #ddd',
                  borderRadius: 8,
                  backgroundColor: '#fff',
                }}
              >
                <h4 style={{ margin: '0 0 0.5rem 0' }}>{g.name || g.label}</h4>
                <p style={{ fontSize: '0.85rem', color: '#666', margin: 0 }}>
                  {g.description || 'Verification gate'}
                </p>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

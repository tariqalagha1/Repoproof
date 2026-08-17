const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Projects ──────────────────────────────────────────
export function getProjects() {
  return fetchAPI<any[]>('/projects/');
}

export function createProject(data: { name: string; description?: string }) {
  return fetchAPI<any>('/projects/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function getProject(id: string) {
  return fetchAPI<any>(`/projects/${id}`);
}

// ── Master Jobs ──────────────────────────────────────
export function getMasterJobs(projectId?: string) {
  const qs = projectId ? `?project_id=${encodeURIComponent(projectId)}` : '';
  return fetchAPI<any[]>(`/master-jobs/${qs}`);
}

export function createMasterJob(data: {
  project_id: string;
  repository_url: string;
  branch?: string;
}) {
  return fetchAPI<any>('/master-jobs/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function getMasterJob(id: string) {
  return fetchAPI<any>(`/master-jobs/${id}`);
}

export function getJobStages(id: string) {
  return fetchAPI<any[]>(`/master-jobs/${id}/stages`);
}

export function getJobProgress(id: string) {
  return fetchAPI<any>(`/master-jobs/${id}/progress`);
}

export function completeIntake(id: string) {
  return fetchAPI<any>(`/master-jobs/${id}/complete-intake`, {
    method: 'POST',
  });
}

export function pauseJob(id: string) {
  return fetchAPI<any>(`/master-jobs/${id}/pause`, {
    method: 'POST',
  });
}

export function resumeJob(id: string) {
  return fetchAPI<any>(`/master-jobs/${id}/resume`, {
    method: 'POST',
  });
}

export function cancelJob(id: string) {
  return fetchAPI<any>(`/master-jobs/${id}/cancel`, {
    method: 'POST',
  });
}

export function runDiscovery(id: string) {
  return fetchAPI<any>(`/master-jobs/${id}/discover`, {
    method: 'POST',
  });
}

export function generatePlan(id: string) {
  return fetchAPI<any>(`/master-jobs/${id}/generate-plan`, {
    method: 'POST',
  });
}

export function validatePolicy(id: string) {
  return fetchAPI<any>(`/master-jobs/${id}/validate-policy`, {
    method: 'POST',
  });
}

// ── Plans ────────────────────────────────────────────
export function getPlan(id: string) {
  return fetchAPI<any>(`/plans/${id}`);
}

// ── Policy Results ───────────────────────────────────
export function getPolicyResult(id: string) {
  return fetchAPI<any>(`/policy-results/${id}`);
}

export function getPolicyResultByJob(jobId: string) {
  return fetchAPI<any[]>(`/policy-results/by-job/${jobId}`);
}

// ── LLM Provider ─────────────────────────────────────
export function getProviderStatus() {
  return fetchAPI<any>('/llm/status');
}

// ── Environments ─────────────────────────────────────
export function provisionEnvironment(data: {
  master_job_id: string;
  stage_id: string;
}) {
  return fetchAPI<any>('/environments/provision', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function getEnvironment(id: string) {
  return fetchAPI<any>(`/environments/${id}`);
}

export function getEnvironmentsByJob(jobId: string) {
  return fetchAPI<any[]>(`/environments/by-job/${jobId}`);
}

// ── Gates ────────────────────────────────────────────
export function getGates() {
  return fetchAPI<any[]>('/gates');
}

// ── Compatibility ────────────────────────────────────
export function getCompatibility(jobId: string) {
  return fetchAPI<any>(`/compatibility/${jobId}`);
}

const API_BASE = "/api/v1";

async function fetchApi<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// People
export async function fetchPeople(params: Record<string, string | number>) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  });
  return fetchApi<{
    items: import("./types").PersonSummary[];
    total: number;
    page: number;
    pages: number;
  }>(`/people?${qs}`);
}

export async function fetchPerson(id: string) {
  return fetchApi<import("./types").PersonDetail>(`/people/${id}`);
}

export async function updatePerson(
  id: string,
  data: Record<string, unknown>
) {
  return fetchApi<{ status: string }>(`/people/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

// Dashboard - returns the actual backend shape

export async function fetchDashboard(): Promise<any> {
  return fetchApi<any>("/dashboard/overview");
}

// Pipeline

export async function fetchPipelineStats(): Promise<any> {
  return fetchApi<any>("/pipeline/stats");
}

export async function advancePipelineStage(
  personIds: string[],
  toStage: string
) {
  return fetchApi<{ updated: number }>("/pipeline/bulk-advance", {
    method: "POST",
    body: JSON.stringify({ person_ids: personIds, target_stage: toStage }),
  });
}

// Signals
export async function fetchSignals(params: Record<string, string | number>) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  });
  return fetchApi<{
    items: import("./types").SignalItem[];
    total: number;
    page: number;
    pages: number;
  }>(`/signals?${qs}`);
}


export async function fetchSignalSummary(): Promise<any> {
  return fetchApi<any>("/signals/summary");
}

// Organizations
export async function fetchOrganizations() {
  return fetchApi<{
    items: import("./types").Organization[];
    total: number;
  }>("/organizations");
}

// Discovery
export async function triggerDiscovery(strategy: string) {
  return fetchApi<{ status: string; run_id: string }>(
    `/discovery/run/${strategy}`,
    { method: "POST" }
  );
}

// Export
export async function exportCSV(params: Record<string, string>) {
  const qs = new URLSearchParams(params);
  const res = await fetch(`${API_BASE}/export/csv?${qs}`);
  return res.blob();
}

import type { DeleteMarkedResponse, ScanConfig, SessionDetail, SessionSummary } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  listSessions: () => request<SessionSummary[]>("/api/sessions"),
  startScan: (payload: ScanConfig) =>
    request<SessionDetail>("/api/scans", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getSession: (sessionId: number) => request<SessionDetail>(`/api/sessions/${sessionId}`),
  updateDecisions: (
    sessionId: number,
    decisions: Array<{ image_id: number; marked_for_delete: boolean }>,
  ) =>
    request<SessionDetail>(`/api/sessions/${sessionId}/decisions`, {
      method: "POST",
      body: JSON.stringify({ decisions }),
    }),
  deleteMarked: (sessionId: number) =>
    request<DeleteMarkedResponse>(`/api/sessions/${sessionId}/delete-marked`, {
      method: "POST",
    }),
};

import type { QueryResponse, IndexStats, HealthResponse, RefreshResponse, DemandListResponse } from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${path} → ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  query: (question: string, use_filters = true) =>
    request<QueryResponse>("/query", {
      method: "POST",
      body: JSON.stringify({ question, use_filters }),
    }),

  health: () => request<HealthResponse>("/health"),

  stats: () => request<IndexStats>("/index/stats"),

  refresh: () =>
    request<RefreshResponse>("/index/refresh", { method: "POST" }),

  refreshStatus: () => request<RefreshResponse>("/index/refresh/status"),

  raiseDemand: (specs: Record<string, any>, contact_email: string, contact_phone?: string) =>
    request<{ status: string; message: string; demand_id: string }>("/demand/raise", {
      method: "POST",
      body: JSON.stringify({ specs, contact_email, contact_phone }),
    }),

  getDemands: () => request<DemandListResponse>("/demand/list"),
};
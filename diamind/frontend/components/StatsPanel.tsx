"use client";

import { useEffect, useState, useCallback } from "react";
import { RefreshCw, CheckCircle, AlertCircle, Database, Gem, BookOpen } from "lucide-react";
import { api } from "@/lib/api";
import type { IndexStats, HealthResponse } from "@/types";

export function StatsPanel() {
  const [stats, setStats]   = useState<IndexStats | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading]   = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [s, h] = await Promise.all([api.stats(), api.health()]);
      setStats(s);
      setHealth(h);
    } catch {
      // silently fail — health indicator will show degraded
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleRefresh() {
    setRefreshing(true);
    setRefreshMsg("Starting refresh…");
    try {
      await api.refresh();
      setRefreshMsg("Refresh running…");
      // poll until done
      const poll = setInterval(async () => {
        const status = await api.refreshStatus();
        setRefreshMsg(status.message);
        if (status.status === "done" || status.status === "error") {
          clearInterval(poll);
          setRefreshing(false);
          if (status.status === "done") {
            await load();
            setRefreshMsg("");
          }
        }
      }, 3000);
    } catch (e: unknown) {
      setRefreshMsg(e instanceof Error ? e.message : "Refresh failed.");
      setRefreshing(false);
    }
  }

  const ok = health?.status === "ok";

  return (
    <div className="flex items-center gap-4 flex-wrap">
      {/* Status indicator */}
      <div className="flex items-center gap-1.5">
        {loading ? (
          <div className="w-2 h-2 rounded-full bg-slate-500 animate-pulse" />
        ) : ok ? (
          <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
        ) : (
          <AlertCircle className="w-3.5 h-3.5 text-red-400" />
        )}
        <span className={`text-xs font-medium ${ok ? "text-emerald-400" : "text-red-400"}`}>
          {loading ? "Connecting…" : ok ? "Live" : "Degraded"}
        </span>
      </div>

      {stats && (
        <>
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Database className="w-3.5 h-3.5" />
            <span>{stats.total_vectors.toLocaleString()} vectors</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Gem className="w-3.5 h-3.5 text-amber-400" />
            <span>{stats.diamond_records} stones</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <BookOpen className="w-3.5 h-3.5 text-blue-400" />
            <span>{stats.domain_chunks} knowledge chunks</span>
          </div>
        </>
      )}

      {/* Refresh */}
      <button
        onClick={handleRefresh}
        disabled={refreshing}
        className="ml-auto flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-slate-700
                   text-xs text-slate-400 hover:text-slate-200 hover:border-slate-500
                   disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <RefreshCw className={`w-3 h-3 ${refreshing ? "animate-spin" : ""}`} />
        {refreshing ? "Refreshing…" : "Refresh index"}
      </button>

      {refreshMsg && (
        <span className="text-xs text-amber-400">{refreshMsg}</span>
      )}
    </div>
  );
}
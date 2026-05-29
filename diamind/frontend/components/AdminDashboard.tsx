"use client";

import { useEffect, useState } from "react";
import { Mail, Phone, ShieldAlert, CheckCircle, RefreshCw, Radio, Terminal } from "lucide-react";
import { api } from "@/lib/api";
import type { DemandItem, NotificationLog } from "@/types";

export function AdminDashboard() {
  const [demands, setDemands] = useState<DemandItem[]>([]);
  const [notifications, setNotifications] = useState<NotificationLog[]>([]);
  const [loading, setLoading] = useState(false);

  async function loadData() {
    setLoading(true);
    try {
      const res = await api.getDemands();
      setDemands(res.demands);
      setNotifications(res.notifications);
    } catch (e) {
      console.error("Error loading demands dashboard:", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    // Poll every 5 seconds to show real-time notification engine triggers
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-1">
      {/* Left: Raised Demands */}
      <div className="bg-slate-800/40 rounded-xl border border-slate-700/60 p-5 flex flex-col space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-amber-500" />
            <h2 className="text-sm font-semibold text-slate-200">Active Demand Registry</h2>
          </div>
          <button
            onClick={loadData}
            disabled={loading}
            className="p-1.5 rounded-lg border border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-500 disabled:opacity-50 transition-all"
            title="Refresh Registry"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        {demands.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center py-12 text-slate-500 text-xs">
            <Radio className="w-8 h-8 mb-2 stroke-1 animate-pulse" />
            <p>No customer demands raised yet.</p>
            <p className="text-[10px] text-slate-600 mt-1">Demands will appear here when inventory checks return empty.</p>
          </div>
        ) : (
          <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
            {demands.map((demand) => (
              <div
                key={demand.id}
                className="bg-slate-900/55 rounded-xl border border-slate-850 p-4 space-y-3 hover:border-slate-700 transition-all"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono text-amber-400 font-medium">{demand.id}</span>
                  <span className="text-[10px] text-slate-500">
                    {new Date(demand.created_at).toLocaleString()}
                  </span>
                </div>

                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(demand.specs).map(([key, value]) => {
                    if (value === undefined || value === null || value === "") return null;
                    return (
                      <span
                        key={key}
                        className="px-2 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300 border border-slate-700/40"
                      >
                        <span className="text-slate-500 capitalize">{key.replace("_", " ")}:</span>{" "}
                        <span className="text-slate-200 font-medium">{String(value)}</span>
                      </span>
                    );
                  })}
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-800/60 pt-2.5 text-xs text-slate-400">
                  <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1">
                      <Mail className="w-3.5 h-3.5 text-slate-500" />
                      {demand.contact_email}
                    </span>
                    {demand.contact_phone && (
                      <span className="flex items-center gap-1">
                        <Phone className="w-3.5 h-3.5 text-slate-500" />
                        {demand.contact_phone}
                      </span>
                    )}
                  </div>
                  <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                    Pending Match
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Right: Notification Engine log */}
      <div className="bg-slate-800/40 rounded-xl border border-slate-700/60 p-5 flex flex-col space-y-4">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-emerald-400" />
          <h2 className="text-sm font-semibold text-slate-200">Notification Engine Telemetry</h2>
        </div>

        {notifications.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center py-12 text-slate-500 text-xs">
            <Terminal className="w-8 h-8 mb-2 stroke-1 text-slate-600" />
            <p>Notification logs empty.</p>
            <p className="text-[10px] text-slate-600 mt-1">Automatic B2B notification feeds will stream here.</p>
          </div>
        ) : (
          <div className="space-y-2.5 max-h-[60vh] overflow-y-auto font-mono text-[11px] pr-1">
            {notifications.map((log) => {
              const isEmail = log.channel === "Email";
              const isSMS = log.channel === "SMS";
              return (
                <div
                  key={log.id}
                  className="bg-slate-950/80 rounded border border-slate-900 p-3 space-y-1.5"
                >
                  <div className="flex items-center justify-between text-[10px] text-slate-500 border-b border-slate-900/60 pb-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-1.5 py-0.2 rounded font-bold uppercase ${
                          isEmail
                            ? "bg-blue-900/40 text-blue-400 border border-blue-900/60"
                            : isSMS
                            ? "bg-purple-900/40 text-purple-400 border border-purple-900/60"
                            : "bg-emerald-900/40 text-emerald-400 border border-emerald-900/60"
                        }`}
                      >
                        {log.channel}
                      </span>
                      <span>Target: {log.recipient}</span>
                    </div>
                    <span>{new Date(log.sent_at).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-slate-300 leading-normal">{log.message}</p>
                  <div className="flex items-center justify-between text-[9px] text-slate-600 pt-0.5">
                    <span>TX_ID: {log.id}</span>
                    <span className="flex items-center gap-0.5 text-emerald-500">
                      <CheckCircle className="w-2.5 h-2.5" /> Dispatched
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

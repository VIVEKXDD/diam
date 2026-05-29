"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Filter, AlertTriangle, Send, CheckCircle } from "lucide-react";
import { SourceCard } from "./SourceCard";
import { api } from "@/lib/api";
import type { Message } from "@/types";

function FiltersChips({ filters }: { filters: Record<string, unknown> }) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(filters);
  if (entries.length === 0) return null;

  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1 text-[11px] text-slate-500 hover:text-slate-400 transition-colors"
      >
        <Filter className="w-3 h-3" />
        {entries.length} filter{entries.length !== 1 ? "s" : ""} applied
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>
      {open && (
        <pre className="mt-1.5 px-3 py-2 rounded-md bg-slate-900/60 border border-slate-700/50
                        text-[10px] font-mono text-slate-400 overflow-x-auto">
          {JSON.stringify(filters, null, 2)}
        </pre>
      )}
    </div>
  );
}

function RaiseDemandPanel({ specs }: { specs: Record<string, any> }) {
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleRaise() {
    if (!email) return;
    setSubmitting(true);
    try {
      await api.raiseDemand(specs, email, phone || undefined);
      setSubmitted(true);
    } catch (e) {
      console.error(e);
      alert("Failed to raise demand.");
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <div className="mt-3 p-3 bg-emerald-950/40 border border-emerald-500/20 rounded-xl flex items-center gap-2.5 text-xs text-slate-300">
        <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
        <div>
          <p className="font-semibold text-slate-200">Demand Broadcasted Successfully!</p>
          <p className="text-[10px] text-slate-400">Notification alerts have been queued for supplier sales engines.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-3 p-4 bg-slate-900/50 border border-slate-700/50 rounded-xl space-y-3">
      <div className="flex items-start gap-2.5 text-xs text-amber-400">
        <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold">Inventory Shortfall Alert</p>
          <p className="text-[11px] text-slate-450 leading-normal">
            No matching stones are currently available. You can broadcast this demand directly to Glowstar, Ratnakala, Vaibhav, and Zhaveri procurement channels.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
        <div>
          <label className="block text-[10px] text-slate-500 mb-1">Contact Email *</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="buyer@company.com"
            className="w-full px-2.5 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-amber-500/40"
          />
        </div>
        <div>
          <label className="block text-[10px] text-slate-500 mb-1">Phone Number (Optional)</label>
          <input
            type="text"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+1 (555) 000-0000"
            className="w-full px-2.5 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-amber-500/40"
          />
        </div>
      </div>

      <button
        onClick={handleRaise}
        disabled={!email || submitting}
        className="w-full py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 disabled:opacity-40 disabled:cursor-not-allowed text-xs text-slate-900 font-semibold transition-all flex items-center justify-center gap-1.5"
      >
        <Send className="w-3 h-3" />
        {submitting ? "Broadcasting..." : "Broadcast Demand to Suppliers"}
      </button>
    </div>
  );
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const sources = message.sources ?? [];

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] px-4 py-2.5 rounded-2xl rounded-tr-sm
                        bg-blue-600 text-white text-sm leading-relaxed">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start w-full">
      <div className="max-w-[85%] w-full space-y-2">
        {/* Gem avatar + answer */}
        <div className="flex items-start gap-2.5">
          <div className="flex-shrink-0 w-7 h-7 rounded-full bg-amber-500/20 border border-amber-500/30
                          flex items-center justify-center mt-0.5">
            <span className="text-sm">💎</span>
          </div>
          <div className="flex-1 px-4 py-3 rounded-2xl rounded-tl-sm
                          bg-slate-800 border border-slate-700/60
                          text-sm text-slate-100 leading-relaxed whitespace-pre-wrap">
            {message.content}

            {/* Filters */}
            {message.filters && <FiltersChips filters={message.filters} />}

            {/* Raise Demand Panel */}
            {message.demand_raisable && message.recommended_criteria && (
              <RaiseDemandPanel specs={message.recommended_criteria} />
            )}

            {/* Sources toggle */}
            {sources.length > 0 && (
              <button
                onClick={() => setSourcesOpen((v) => !v)}
                className="mt-3 flex items-center gap-1.5 text-[11px] text-slate-500
                           hover:text-slate-300 transition-colors"
              >
                {sourcesOpen ? (
                  <ChevronUp className="w-3 h-3" />
                ) : (
                  <ChevronDown className="w-3 h-3" />
                )}
                {sources.length} source{sources.length !== 1 ? "s" : ""}
              </button>
            )}
          </div>
        </div>

        {/* Sources */}
        {sourcesOpen && sources.length > 0 && (
          <div className="ml-9 space-y-1.5">
            {sources.map((src, i) => (
              <SourceCard key={src.id} source={src} index={i + 1} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Loader2, MessageSquare, Terminal } from "lucide-react";
import { StatsPanel } from "@/components/StatsPanel";
import { MessageBubble } from "@/components/MessageBubble";
import { AdminDashboard } from "@/components/AdminDashboard";
import { api } from "@/lib/api";
import type { Message } from "@/types";

const SUGGESTIONS = [
  "Show me GIA round diamonds, 1–2ct, G or H, VS1, EX cut, under $6,000/ct",
  "Which supplier has the best rap discount on EX/EX/EX rounds?",
  "What is fluorescence and how does it affect price for a D color stone?",
  "Find all available Glowstar stones from Canada",
];

let msgCounter = 0;
function uid() {
  return `msg-${++msgCounter}-${Date.now()}`;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [useFilters, setUseFilters] = useState(true);
  const [tab, setTab]           = useState<"chat" | "admin">("chat");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (tab === "chat") {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading, tab]);

  const submit = useCallback(async (question: string) => {
    if (!question.trim() || loading) return;

    const userMsg: Message = {
      id: uid(), role: "user", content: question.trim(), timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.query(question.trim(), useFilters);
      const assistantMsg: Message = {
        id:        uid(),
        role:      "assistant",
        content:   res.answer,
        sources:   res.sources,
        filters:   Object.keys(res.filters_applied).length > 0 ? res.filters_applied : undefined,
        timestamp: new Date(),
        demand_raisable: res.demand_raisable,
        recommended_criteria: res.recommended_criteria,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e: unknown) {
      const errMsg: Message = {
        id:        uid(),
        role:      "assistant",
        content:   `Error: ${e instanceof Error ? e.message : "Something went wrong."}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [loading, useFilters]);

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit(input);
    }
  }

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-slate-100">

      {/* Header */}
      <header className="flex-shrink-0 border-b border-slate-800 bg-slate-900/95 backdrop-blur-sm px-6 py-3">
        <div className="max-w-4xl mx-auto space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xl">💎</span>
              <div>
                <h1 className="text-base font-semibold text-slate-100 leading-tight">Diamind</h1>
                <p className="text-xs text-slate-500 font-medium">B2B Diamond Intelligence Engine</p>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center bg-slate-950/60 p-1 rounded-xl border border-slate-800">
              <button
                onClick={() => setTab("chat")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  tab === "chat"
                    ? "bg-amber-500 text-slate-950 shadow"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5" />
                Intelligence Chat
              </button>
              <button
                onClick={() => setTab("admin")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  tab === "admin"
                    ? "bg-amber-500 text-slate-950 shadow"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <Terminal className="w-3.5 h-3.5" />
                Procurement Panel
              </button>
            </div>
          </div>
          <StatsPanel />
        </div>
      </header>

      {/* Main Area */}
      <div className="flex-1 overflow-hidden">
        {tab === "chat" ? (
          <div className="flex flex-col h-full">
            {/* Messages Scroll Area */}
            <main className="flex-1 overflow-y-auto">
              <div className="max-w-4xl mx-auto px-6 py-6 space-y-6">

                {/* Empty state */}
                {messages.length === 0 && (
                  <div className="flex flex-col items-center justify-center min-h-[50vh] gap-8">
                    <div className="text-center space-y-2">
                      <p className="text-4xl">💎</p>
                      <h2 className="text-xl font-semibold text-slate-200">
                        Ask about your inventory
                      </h2>
                      <p className="text-xs text-slate-550 max-w-sm">
                        Search diamonds by attributes and pricing, or ask any grading or market question.
                      </p>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-2xl">
                      {SUGGESTIONS.map((s) => (
                        <button
                          key={s}
                          onClick={() => submit(s)}
                          className="px-4 py-3 text-left text-xs text-slate-400 rounded-xl
                                     border border-slate-700/60 bg-slate-800/40
                                     hover:bg-slate-850 hover:text-slate-200 hover:border-slate-600
                                     transition-all leading-relaxed"
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Message list */}
                {messages.map((msg) => (
                  <MessageBubble key={msg.id} message={msg} />
                ))}

                {/* Typing indicator */}
                {loading && (
                  <div className="flex items-start gap-2.5">
                    <div className="w-7 h-7 rounded-full bg-amber-500/20 border border-amber-500/30
                                    flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-sm">💎</span>
                    </div>
                    <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-slate-800 border border-slate-700/60">
                      <div className="flex gap-1 items-center h-4">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce [animation-delay:0ms]" />
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce [animation-delay:150ms]" />
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce [animation-delay:300ms]" />
                      </div>
                    </div>
                  </div>
                )}

                <div ref={bottomRef} />
              </div>
            </main>

            {/* Chat Input Footer */}
            <footer className="flex-shrink-0 border-t border-slate-800 bg-slate-900/95 backdrop-blur-sm px-6 py-4">
              <div className="max-w-4xl mx-auto space-y-2">
                <div className="flex gap-3">
                  <div className="flex-1 relative">
                    <textarea
                      ref={inputRef}
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={handleKey}
                      placeholder="Ask about diamonds…"
                      rows={1}
                      disabled={loading}
                      className="w-full resize-none rounded-xl px-4 py-3 pr-12
                                 bg-slate-800 border border-slate-700 text-slate-100
                                 placeholder:text-slate-600 text-sm leading-relaxed
                                 focus:outline-none focus:ring-1 focus:ring-amber-500/50 focus:border-amber-500/50
                                 disabled:opacity-50 disabled:cursor-not-allowed
                                 transition-colors"
                      style={{ maxHeight: "120px", overflowY: "auto" }}
                      onInput={(e) => {
                        const t = e.currentTarget;
                        t.style.height = "auto";
                        t.style.height = `${Math.min(t.scrollHeight, 120)}px`;
                      }}
                    />
                    <button
                      onClick={() => submit(input)}
                      disabled={!input.trim() || loading}
                      className="absolute right-3 bottom-2.5 p-1.5 rounded-lg
                                 bg-amber-500 text-slate-900 hover:bg-amber-400
                                 disabled:opacity-40 disabled:cursor-not-allowed
                                 transition-colors"
                    >
                      {loading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Filter toggle */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setUseFilters((v) => !v)}
                    className={`relative w-8 h-4 rounded-full transition-colors ${
                      useFilters ? "bg-amber-500" : "bg-slate-700"
                    }`}
                  >
                    <span
                      className={`absolute top-0.5 w-3 h-3 rounded-full bg-white shadow transition-transform ${
                        useFilters ? "translate-x-4" : "translate-x-0.5"
                      }`}
                    />
                  </button>
                  <span className="text-[10px] text-slate-500 font-medium">
                    Smart filters {useFilters ? "on" : "off"}
                  </span>
                  <span className="text-[10px] text-slate-600 ml-1">
                    {useFilters
                      ? "— query is analysed for color, carat, price etc. before searching"
                      : "— pure semantic search, no metadata filtering"}
                  </span>
                </div>
              </div>
            </footer>
          </div>
        ) : (
          <main className="h-full overflow-y-auto px-6 py-6 max-w-7xl mx-auto">
            <AdminDashboard />
          </main>
        )}
      </div>

    </div>
  );
}

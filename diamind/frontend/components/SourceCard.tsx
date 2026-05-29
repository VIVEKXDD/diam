"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Gem, BookOpen } from "lucide-react";
import type { SourceDocument } from "@/types";

function fmt(n: number | undefined, prefix = "") {
  if (n === undefined || n === null) return null;
  return `${prefix}${n.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
}

function DiamondCard({ s }: { s: SourceDocument }) {
  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-2 text-xs">
      {s.supplier && (
        <span className="text-slate-400">
          Supplier <span className="text-amber-400 font-medium">{s.supplier}</span>
        </span>
      )}
      {s.stone_id && (
        <span className="text-slate-400">
          ID <span className="text-slate-200 font-mono">{s.stone_id}</span>
        </span>
      )}
      {s.carat !== undefined && (
        <span className="text-slate-400">
          Carat <span className="text-slate-200">{s.carat} ct</span>
        </span>
      )}
      {s.shape && (
        <span className="text-slate-400">
          Shape <span className="text-slate-200">{s.shape}</span>
        </span>
      )}
      {s.color && (
        <span className="text-slate-400">
          Color <span className="text-slate-200">{s.color}</span>
        </span>
      )}
      {s.clarity && (
        <span className="text-slate-400">
          Clarity <span className="text-slate-200">{s.clarity}</span>
        </span>
      )}
      {s.cut && (
        <span className="text-slate-400">
          Cut <span className="text-slate-200">{s.cut}</span>
        </span>
      )}
      {s.price_per_carat !== undefined && (
        <span className="text-slate-400">
          Price/ct{" "}
          <span className="text-emerald-400 font-medium">
            {fmt(s.price_per_carat, "$")}
          </span>
        </span>
      )}
      {s.price !== undefined && (
        <span className="text-slate-400">
          Total{" "}
          <span className="text-emerald-400 font-medium">{fmt(s.price, "$")}</span>
        </span>
      )}
    </div>
  );
}

function DomainCard({ s }: { s: SourceDocument }) {
  return (
    <div className="mt-2 text-xs space-y-0.5">
      {s.topic && (
        <p className="text-slate-400">
          Topic{" "}
          <span className="text-amber-400 capitalize">
            {s.topic.replace(/_/g, " ")}
          </span>
        </p>
      )}
      {s.section && (
        <p className="text-slate-400">
          Section <span className="text-slate-200">{s.section}</span>
        </p>
      )}
    </div>
  );
}

export function SourceCard({ source, index }: { source: SourceDocument; index: number }) {
  const [open, setOpen] = useState(false);
  const isDiamond = source.doc_type === "diamond_record";

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/60 overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-slate-700/40 transition-colors"
      >
        <span className="flex-shrink-0 w-5 h-5 rounded-full bg-slate-700 flex items-center justify-center text-[10px] text-slate-400 font-mono">
          {index}
        </span>
        {isDiamond ? (
          <Gem className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
        ) : (
          <BookOpen className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
        )}
        <span className="flex-1 text-xs text-slate-300 truncate">
          {isDiamond
            ? `${source.supplier ?? "?"} · ${source.carat ?? "?"}ct ${source.color ?? "?"}/${source.clarity ?? "?"}`
            : (source.section ?? source.topic ?? source.id)}
        </span>
        <span className="text-[10px] text-slate-500 font-mono flex-shrink-0">
          {(source.score * 100).toFixed(0)}%
        </span>
        {open ? (
          <ChevronUp className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
        )}
      </button>

      {open && (
        <div className="px-3 pb-3 border-t border-slate-700/50">
          {isDiamond ? <DiamondCard s={source} /> : <DomainCard s={source} />}
          <p className="mt-2 text-[10px] font-mono text-slate-600">{source.id}</p>
        </div>
      )}
    </div>
  );
}
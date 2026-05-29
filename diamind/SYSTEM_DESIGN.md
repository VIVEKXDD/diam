# Diamind — System Design

## Overview

Diamind is an agentic Retrieval-Augmented Generation (RAG) system for diamond inventory intelligence. It ingests raw supplier Excel files from multiple heterogeneous sources, normalises them into a canonical schema, converts the data into embedded vector documents alongside curated industry knowledge, and exposes a natural-language query interface over that knowledge base.

The system answers three classes of questions:
- **Inventory lookup** — "Show me GIA round G VS1 stones under $5,000/ct"
- **Market analysis** — "Which supplier has the best rap discount on EX/EX/EX rounds?"
- **Domain education** — "What is fluorescence and how does it affect price for a D colour stone?"

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA INGESTION                           │
│                                                                 │
│  Supplier Excel files                                           │
│  (Glowstar, Ratnakala, ──► map_supplier.py ──► combined_       │
│   Vaibhav, Zhaveri)         ETL + cleaning      mapped.xlsx    │
│                             mapping_flat.json                   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     KNOWLEDGE BASE LAYER                        │
│                                                                 │
│   combined_mapped.xlsx                                          │
│          +               ──► prepare_kb.py ──► kb_documents    │
│   knowledge/*.md                                  .jsonl        │
│   (8 domain knowledge                        (399 documents)    │
│    files, 60 sections)                                          │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      VECTOR STORE                               │
│                                                                 │
│   kb_documents.jsonl ──► embed_and_upsert.py ──► Pinecone      │
│                          BAAI/bge-base-en-v1.5    (cloud)       │
│                          768-dim vectors          index:        │
│                          cosine similarity        diamond-kb    │
└────────────────────────────────┬────────────────────────────────┘
                                 │ query time
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       QUERY AGENT                               │
│                                                                 │
│   User query                                                    │
│       │                                                         │
│       ├──► [Stage 1] Filter extraction                          │
│       │    Groq LLM (llama-3.3-70b-versatile)                  │
│       │    → structured Pinecone metadata filters               │
│       │                                                         │
│       ├──► [Stage 2] Embed query                                │
│       │    bge-base-en-v1.5 + BGE query prefix                  │
│       │    → 768-dim query vector                               │
│       │                                                         │
│       ├──► [Stage 3] Retrieve                                   │
│       │    Pinecone ANN search, top_k=8                         │
│       │    with metadata pre-filter                             │
│       │    (fallback: retry without filters if 0 results)       │
│       │                                                         │
│       └──► [Stage 4] Answer                                     │
│            Groq LLM (llama-3.3-70b-versatile)                  │
│            context = retrieved chunk texts                      │
│            → natural language answer                            │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
        ┌───────────────────┐     ┌───────────────────────┐
        │   FastAPI Server  │     │   CLI (query_agent.py) │
        │   api/main.py     │     │   python query_agent.py│
        │   port 8001       │     └───────────────────────┘
        └─────────┬─────────┘
                  │ HTTP / JSON
                  ▼
        ┌───────────────────┐
        │  Next.js Frontend │
        │  frontend/        │
        │  port 3001        │
        └───────────────────┘
```

---

## Components

### 1. ETL Pipeline — `map_supplier.py`

Transforms raw heterogeneous supplier Excel files into a single normalised schema.

**Inputs:** One or more `.xlsx` files per supplier, optional `--supplier` hint, optional `--master` or `--output` path.

**Outputs:** A styled Excel workbook with one sheet per supplier (or a merged `MASTER` sheet), plus a `_mapping_report` tab.

**Key stages:**

| Stage | Function | What it does |
|-------|----------|-------------|
| Load rules | `load_rules` | Reads `mapping_flat.json` → `c2a` (canonical→aliases) + `warn` (per-field warnings) |
| Build alias map | `build_alias_map` | Inverts `c2a` to `{alias: canonical}`. Resolves collisions using `SUPPLIER_ALIAS_PRIORITY`. |
| Map columns | `map_df` | Renames columns to canonical names, prepends `supplier` column, drops unmapped columns |
| Clean data | `clean_df` | Strip unit suffixes, median-impute numeric nulls (price exempt), similarity-impute string nulls, fill remaining with `"UNKNOWN"` |
| Write Excel | `write_excel` | Styled output via openpyxl: dark blue headers, alternating rows, green supplier column, frozen pane B2 |
| Report sheet | `append_report_sheet` | `_mapping_report` tab listing renamed columns + warnings + dropped columns |

**Collision resolution:** When the same source alias (e.g., `"Amount"`) maps to multiple canonical fields (`price_per_carat` vs. `price`), `SUPPLIER_ALIAS_PRIORITY` in `map_supplier.py` defines per-supplier preference. Without a supplier hint, the first canonical wins and a warning is printed.

**Supplier-specific quirks encoded here:**

| Supplier | Quirk |
|----------|-------|
| Vaibhav | `Amount` = price per carat (all others: total price) |
| Zhaveri | `Depth` column = `depth_pct`, not raw mm depth |
| Karigar | Melee parcels — no stone IDs, certs, or lab data |

---

### 2. Mapping Rules — `mapping_flat.json`

The single source of truth for all column normalisations. Two top-level keys:

```json
{
  "canonical_to_all_suppliers": {
    "color": ["Color", "Col", "Color (IGI)"],
    "price_per_carat": ["Price/Ct", "Amount", "Rate", "Vendor Price"]
  },
  "warnings": {
    "price_per_carat": {
      "Vaibhav": "Column named 'Amount' but contains price PER CARAT..."
    }
  }
}
```

To add a new supplier: add their column names as aliases to the relevant canonical fields. To add a new canonical field: add a new key with its aliases. No code changes needed unless there are new alias collisions.

---

### 3. Knowledge Base — `prepare_kb.py` + `knowledge/`

Produces `kb_documents.jsonl` — 399 documents, one JSON object per line, ready for embedding.

**Two document types:**

#### `diamond_record` (339 documents)
One per stone row. Converted from structured data to natural language so the embedding model can capture semantic relationships between field names and values.

```
Supplier: GLOWSTAR | Stone ID: G26-13148 | Shape: Round Brilliant Cut | ...

Certification: certified by GIA, certificate #7542529481.
4Cs: 10.07 carat, color J, clarity FL, cut EX, polish EX, symmetry EX.
Pricing: Rapaport price $44000/ct, discount -35.0%, ask price $28600.00/ct...
```

Metadata stored alongside the vector: `supplier`, `shape`, `carat`, `color`, `clarity`, `cut`, `polish`, `symmetry`, `fluorescence`, `price_per_carat`, `price`, `rap_discount`, `lab`, `location`, `availability`, `origin`, `stone_id`. All used for Pinecone metadata pre-filtering at query time.

#### `domain_knowledge` (60 chunks)
Eight markdown files in `knowledge/`, each covering one industry topic. Chunked at `##` section boundaries so each chunk is topically focused and retrieval is precise.

| File | Topic | Chunks |
|------|-------|--------|
| `01_grading_4cs.md` | Color D–Z, Clarity FL–I3, Cut/Polish/Symmetry, Carat magic sizes | 7 |
| `02_pricing_rapaport.md` | Rapaport system, rap price/value/discount, price calculations | 7 |
| `03_shapes.md` | Shape codes, pricing vs round, bow-tie effect, measurements | 5 |
| `04_proportions.md` | Table%, depth%, crown/pavilion angles, girdle, culet, H&A | 11 |
| `05_quality_indicators.md` | Fluorescence, milky, shade, BGM, natts, eye-clean, white/black visibility | 9 |
| `06_inclusions.md` | Feather, crystal, cloud, pinpoint, needle, twinning wisp, laser drill | 7 |
| `07_grading_labs.md` | GIA vs IGI vs HRD vs EGL — consistency and market premiums | 9 |
| `08_origin_location.md` | Mining origins, Kimberley Process, location, supplier profiles | 5 |

---

### 4. Vector Store — Pinecone

**Index:** `diamond-kb`, serverless, AWS us-east-1.
**Dimensions:** 768 (matches `bge-base-en-v1.5` output).
**Metric:** Cosine similarity.
**Vectors:** 399 total (339 diamond + 60 domain).

Each vector is stored with its full metadata dict. Document text is NOT stored in Pinecone — it is held locally in `kb_documents.jsonl` and re-attached at query time. This avoids Pinecone's metadata size limits and keeps the text mutable without re-embedding.

---

### 5. Embedding Model — `BAAI/bge-base-en-v1.5`

Run locally via `sentence-transformers`. No API key required.

- **768 dimensions**, cosine metric
- Trained specifically for retrieval tasks (BGE = Beijing General Embedding)
- **Asymmetric embedding:** documents are embedded as-is; queries use the prefix `"Represent this sentence for searching relevant passages: "` — required by BGE for optimal retrieval quality
- ~400 MB, cached after first download
- CPU-compatible; no GPU required for this data scale

---

### 6. Query Agent — `query_agent.py`

Two-stage pipeline per query:

**Stage 1 — Filter extraction (Groq)**

The user's natural language query is sent to `llama-3.3-70b-versatile` with a structured system prompt. The LLM outputs a JSON dict of metadata filters:

```json
{
  "doc_type": "diamond_record",
  "shape": "RBC",
  "color": ["G", "H"],
  "clarity": "VS1",
  "carat_min": 1.0,
  "carat_max": 2.0,
  "ppc_max": 6000
}
```

This is converted into a Pinecone filter expression (`$eq`, `$in`, `$gte`, `$lte`). Filter routing:

| Query intent | `doc_type` |
|-------------|-----------|
| Grading/education ("what is SI2?") | `domain_knowledge` |
| Inventory/pricing ("find me a G VS1") | `diamond_record` |
| Mixed/comparison | none — searches both |

**Stage 2 — Retrieve + Answer**

1. Query is embedded with BGE prefix → 768-dim vector
2. Pinecone ANN search with metadata filter, `top_k=8`
3. If filters return 0 results: retry without filters (`top_k=12`)
4. Document texts re-attached from `kb_documents.jsonl`
5. Groq (`llama-3.3-70b-versatile`) generates final answer from retrieved context

**Why two LLM calls instead of one?** Filter extraction requires structured JSON output (temperature 0, deterministic). Answer generation requires natural language (temperature 0.2, more expressive). Separating them lets each call be tuned independently.

---

### 7. API — `api/main.py`

FastAPI server, port 8001.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/query` | POST | Full two-stage pipeline. Returns `answer`, `sources[]`, `filters_applied` |
| `/health` | GET | Pinecone connectivity + model load status |
| `/index/stats` | GET | Live vector count from Pinecone + doc type breakdown from local JSONL |
| `/index/refresh` | POST | Background thread: `prepare_kb.py` → `embed_and_upsert.py` → agent reload |
| `/index/refresh/status` | GET | Poll refresh progress: `idle / running / done / error` |

**CORS:** Configured via `CORS_ORIGINS` env var. Defaults to `http://localhost:3000,http://localhost:3001`.

**Agent lifecycle:** `DiamondAgentWithTexts` is instantiated once at startup (`lifespan` context manager) and reused across requests. The embedding model is kept in memory — loading it per-request would add ~2s latency.

**Refresh concurrency:** A `threading.Lock` prevents two simultaneous refreshes. A second POST to `/index/refresh` while one is running returns `"status": "running"` immediately.

---

### 8. Frontend — `frontend/`

Next.js 14, TypeScript, Tailwind CSS, port 3001.

**Component tree:**

```
RootLayout (app/layout.tsx)
└── Home (app/page.tsx)
      ├── StatsPanel          live index stats + health + refresh button
      ├── MessageBubble[]     scrollable chat history
      │     ├── user message  right-aligned, blue
      │     └── assistant message
      │           ├── answer text
      │           ├── FiltersChips    collapsible JSON of applied filters
      │           └── SourceCard[]   collapsible per retrieved chunk
      │                 ├── DiamondCard  supplier/carat/color/clarity/price
      │                 └── DomainCard   topic/section
      └── QueryInput          textarea + send button + smart-filters toggle
```

**API client** (`lib/api.ts`): typed fetch wrappers for all 5 endpoints. Base URL from `NEXT_PUBLIC_API_URL` env var.

**Smart filters toggle:** Users can disable filter extraction to fall back to pure semantic search — useful for open-ended questions where metadata filters would over-constrain results.

---

## Data Flow

### Ingestion path (run when supplier data changes)

```
Raw .xlsx files
    │
    ▼ map_supplier.py
Canonical schema + cleaned data (combined_mapped.xlsx)
    │
    ▼ prepare_kb.py
Natural language documents + domain knowledge chunks (kb_documents.jsonl)
    │
    ▼ embed_and_upsert.py
768-dim vectors (Pinecone, index: diamond-kb)
```

### Query path (per user request)

```
User query (natural language)
    │
    ▼ Groq llama-3.3-70b [Stage 1, temp=0]
Structured metadata filters (JSON)
    │
    ├──► Pinecone metadata pre-filter
    │
    ▼ bge-base-en-v1.5 (local)
768-dim query vector
    │
    ▼ Pinecone ANN search (top_k=8, cosine)
Top-k vector IDs + scores + metadata
    │
    ▼ kb_documents.jsonl (local lookup)
Full document texts
    │
    ▼ Groq llama-3.3-70b [Stage 2, temp=0.2]
Natural language answer
    │
    ▼ FastAPI /query response
{ answer, sources[], filters_applied }
    │
    ▼ Next.js frontend
Rendered chat message + collapsible sources
```

---

## Technology Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| ETL | Python, pandas, openpyxl | Supplier data is Excel-native; openpyxl gives full styling control |
| Vector DB | Pinecone serverless | Managed ANN search, metadata filtering, free tier covers this scale |
| Embedding | BAAI/bge-base-en-v1.5 | Free, local, purpose-built for retrieval, outperforms ada-002 on BEIR |
| LLM inference | Groq (llama-3.3-70b) | Fast inference (~200 tok/s), free tier, high quality for structured extraction + QA |
| API | FastAPI | Async, automatic OpenAPI docs, Pydantic validation |
| Frontend | Next.js 14, Tailwind | App router, TypeScript, rapid UI development |

---

## Key Design Decisions

**Why natural language for diamond records, not JSON?**
Embedding models are trained on natural text. A raw JSON object `{"color": "G", "carat": 1.5}` embeds poorly — the model has no semantic connection between field names and values unless they appear in prose. Rendering each row as descriptive text dramatically improves retrieval quality for attribute-based queries.

**Why section-level chunking for domain knowledge?**
A file like `01_grading_4cs.md` covers six distinct topics. Embedding the whole file as one document means a query about SI2 retrieves the entire 4Cs document, injecting noise about colour and carat into the context. Section-level chunks keep retrieved context topically focused.

**Why two LLM calls per query?**
Filter extraction is a structured classification task (temp=0, JSON output). Answer generation is a synthesis task (temp=0.2, prose output). Using the same call for both would require complex prompt engineering and produce less reliable filter extraction. The latency cost is ~300ms for the extra call — negligible given Groq's speed.

**Why store document texts locally, not in Pinecone?**
Pinecone metadata fields have a 40KB per-vector limit. Diamond record texts are ~500–800 bytes each, safely within limits — but domain knowledge sections can be 2–4KB. More importantly, storing texts locally means they can be updated (e.g., correcting a domain knowledge file) without re-embedding. The local JSONL lookup at query time is microseconds.

**Why bge-base-en-v1.5 over an API-based model?**
Zero cost, no rate limits, no external dependency at query time. The model runs on CPU and loads in ~2s. For 399 documents and expected query volumes (B2B tool, not consumer scale), local inference is the right trade-off.

**Why metadata pre-filtering before ANN search?**
Pure semantic search for "round G VS1 under $5,000/ct" would retrieve semantically similar documents, but semantic similarity doesn't guarantee the price constraint is met. Metadata filtering enforces hard constraints (price ≤ 5000, color = G) before the ANN search, so the LLM only sees genuinely qualifying stones.

---

## Extension Points

**New suppliers:** Add column aliases to `mapping_flat.json`. Add collision rules to `SUPPLIER_ALIAS_PRIORITY` if needed. No code changes required.

**New domain knowledge:** Add a numbered `.md` file to `knowledge/`. `prepare_kb.py` picks it up automatically.

**Refreshing inventory:** Hit `POST /index/refresh` via the API or UI, or run the three-step pipeline manually. The agent reloads automatically after refresh.

**Streaming responses:** Replace the single Groq call in `agent.answer()` with a streaming call and switch the `/query` endpoint to return `StreamingResponse` with SSE. The frontend's `lib/api.ts` would use `EventSource` instead of `fetch`.

**Scaling:** Pinecone serverless scales automatically. The embedding model and Groq are the bottlenecks at high query volume — both can be parallelised or swapped for hosted inference endpoints.
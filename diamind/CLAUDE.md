# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python-based ETL pipeline for processing raw diamond supplier Excel files. It normalizes heterogeneous column names from multiple suppliers into a single canonical schema, cleans the data, and writes styled Excel output.

## Commands

**Validate the script (syntax check):**
```bash
python -m py_compile map_supplier.py
```

**Run mapping + cleaning on a single file:**
```bash
python map_supplier.py data/Vaibhav.xlsx -s Vaibhav --output data/vaibhav_cleaned.xlsx
```

**Batch-process all suppliers into one combined workbook:**
```bash
python map_supplier.py data/Glowstar.xlsx data/Ratnakala.xlsx data/Vaibhav.xlsx data/Zhaveri.xlsx \
  -s Glowstar -s Ratnakala -s Vaibhav -s Zhaveri \
  --output data/combined_mapped.xlsx
```

**Append normalized rows into a master workbook:**
```bash
python map_supplier.py data/Vaibhav.xlsx -s Vaibhav --master data/master.xlsx
```

## Architecture

### Single-script pipeline: `map_supplier.py`

The full pipeline runs in sequence:

1. **Load rules** — reads `mapping_flat.json` → two structures:
   - `c2a` (`canonical_to_all_suppliers`): `{ canonical_field: [alias1, alias2, …] }`
   - `warn`: per-canonical, per-supplier warning messages shown during mapping

2. **Build alias map** (`build_alias_map`) — inverts `c2a` into `{ normalized_alias: canonical_field }`. Handles collisions (same source alias matching multiple canonicals) using `SUPPLIER_ALIAS_PRIORITY` when a supplier hint is provided; otherwise picks first match and warns.

3. **Map columns** (`map_df`) — renames DataFrame columns to canonical names, prepends a `supplier` column, drops columns with no alias match, then runs `clean_df`.

4. **Clean data** (`clean_df`) — four-stage cleaning:
   - `normalize_value`: strips unit suffixes (`mm`, `ct`, `%`, etc.), trims whitespace, converts numeric strings to numbers
   - Median imputation for all numeric columns with zero/null values — **price columns are exempt** (any column with "price" in the name is left blank)
   - `impute_strings_by_similarity`: fills missing string values by finding rows with ≥50% matching non-null field values and borrowing their value
   - Remaining blanks filled with `"UNKNOWN"`

5. **Write Excel** (`write_excel`) — uses openpyxl directly for styled output: dark blue headers, alternating row fills, green `supplier` column, frozen pane at B2.

6. **Append report sheet** (`append_report_sheet`) — adds `_mapping_report` tab with two sections: renamed columns (with any warnings) and dropped columns.

7. **Master mode** (`--master`) — loads existing `MASTER` sheet from target workbook, concatenates with newly processed data, and saves back. Column order follows canonical order from `mapping_flat.json`.

### Mapping rules: `mapping_flat.json`

The single source of truth for all column mappings. Structure:
```json
{
  "canonical_to_all_suppliers": { "canonical_field": ["Alias1", "Alias2"] },
  "warnings": { "canonical_field": { "SupplierName": "warning text" } }
}
```

To add a new supplier or alias: edit `mapping_flat.json`. For collision disambiguation (same alias used by multiple suppliers for different canonical fields), add an entry to `SUPPLIER_ALIAS_PRIORITY` in `map_supplier.py`.

### Known supplier-specific quirks

- **Vaibhav**: `"Amount"` = price per carat (not total price)
- **Ratnakala / Glowstar**: `"Amount"` = total price
- **Zhaveri**: `"Depth"` maps to `depth_pct`, not raw `depth`
- **Karigar**: sells melee parcels — `stone_id`, `cert_number`, `lab` are always blank

### Dependencies

`pandas`, `numpy`, `openpyxl` — no other third-party dependencies. The `.env` file contains a `GROQ_API_KEY` for future/separate use; it is not consumed by `map_supplier.py`.

---

## RAG Knowledge Base

### Knowledge base preparation: `prepare_kb.py`

Converts the processed diamond data and domain knowledge into documents ready for embedding and storage in Pinecone (or any vector DB).

**Run against combined_mapped.xlsx (default):**
```bash
python prepare_kb.py
```

**Run against a master workbook:**
```bash
python prepare_kb.py --source data/master.xlsx --sheet MASTER
```

**Dry run (count only, no file written):**
```bash
python prepare_kb.py --dry-run
```

Output: `kb_documents.jsonl` — one JSON object per line:
```json
{ "id": "...", "text": "...", "metadata": { "doc_type": "...", ... } }
```

### Two document types

**`diamond_record`** (339 documents from current data): One document per stone. Natural language text covering all fields (certification, 4Cs, proportions, pricing, quality notes, origin). Metadata includes all filterable numeric/categorical fields: `supplier`, `shape`, `carat`, `color`, `clarity`, `cut`, `polish`, `symmetry`, `fluorescence`, `price_per_carat`, `price`, `rap_discount`, `location`, `availability`, `origin`, `lab`.

**`domain_knowledge`** (60 chunks): Industry rules and grading context, chunked by `##` section heading. Metadata includes `topic` and `section` for targeted retrieval. Source files are in `knowledge/`.

### Domain knowledge files (`knowledge/`)

| File | Topic | Chunks |
|------|-------|--------|
| `01_grading_4cs.md` | Color/Clarity/Cut/Polish/Symmetry/Carat grading scales | 7 |
| `02_pricing_rapaport.md` | Rapaport system, rap price, rap discount, price calculations | 7 |
| `03_shapes.md` | All diamond shapes, pricing vs round, bow-tie effect, measurements | 5 |
| `04_proportions.md` | Table%, depth%, crown/pavilion angles, girdle, culet, H&A | 11 |
| `05_quality_indicators.md` | Fluorescence, milky, shade, BGM, natts, eye-clean, white/black fields | 9 |
| `06_inclusions.md` | Inclusion types (feather, crystal, cloud, pinpoint, needle, etc.) | 7 |
| `07_grading_labs.md` | GIA vs IGI vs HRD vs EGL — grading consistency and market premiums | 9 |
| `08_origin_location.md` | Mining origins, Kimberley Process, location/availability, supplier profiles | 5 |

To add more domain knowledge: create a new numbered `.md` file in `knowledge/` using `#` for the file title and `##` for each section. `prepare_kb.py` will pick it up automatically on next run.

---

## Query Agent

### `query_agent.py` — two-stage agentic RAG

**Interactive CLI:**
```bash
python query_agent.py
```

**Single query:**
```bash
python query_agent.py -q "round G VS1 under 5000 per carat"
python query_agent.py -q "what does rap discount mean?"
python query_agent.py --verbose -q "best EX/EX/EX rounds from Glowstar"
```

### Pipeline per query

1. **Filter extraction** — Groq (`llama-3.3-70b-versatile`) reads the query and outputs a JSON dict of Pinecone metadata filters (shape, color, carat range, price ceiling, etc.)
2. **Embed query** — `bge-base-en-v1.5` with the BGE query prefix (`"Represent this sentence..."`)
3. **Retrieve** — Pinecone ANN search with metadata pre-filter, `top_k=8`. Falls back to unfiltered search if filters return zero results.
4. **Attach texts** — document text is re-attached from `kb_documents.jsonl` (Pinecone stores metadata only, not the full text)
5. **Answer** — Groq generates the final answer from the retrieved chunks

### Filter routing logic

| Query type | `doc_type` filter set to |
|------------|--------------------------|
| Grading / education ("what is SI2?") | `domain_knowledge` |
| Inventory / pricing ("find me a 1ct G VS1") | `diamond_record` |
| Mixed / comparison | none (searches both) |

### Runtime flags

| Flag | Effect |
|------|--------|
| `--verbose` / `!v` in interactive | Show extracted filters + retrieved chunk IDs and scores |
| `--no-filter` / `!nf` in interactive | Skip filter extraction, pure semantic search |

### Models used

| Role | Model |
|------|-------|
| Embedding | `BAAI/bge-base-en-v1.5` (local, 768d) |
| Filter extraction + answer | `llama-3.3-70b-versatile` via Groq |

---

## FastAPI Server

### Start

```bash
pip install fastapi "uvicorn[standard]"
uvicorn api.main:app --reload --port 8000
```

Interactive docs available at `http://localhost:8000/docs`.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/query` | Ask the agent a question |
| `GET` | `/health` | Liveness check — Pinecone + model status |
| `GET` | `/index/stats` | Vector count, dimension, doc type breakdown |
| `POST` | `/index/refresh` | Re-build KB + re-embed + re-upsert (background) |
| `GET` | `/index/refresh/status` | Poll refresh progress |

### POST /query — request / response shape

```json
// Request
{ "question": "round G VS1 under 5000 per carat", "use_filters": true }

// Response
{
  "answer": "...",
  "sources": [
    {
      "id": "diamond_Glowstar_Sheet1_42",
      "score": 0.847,
      "doc_type": "diamond_record",
      "supplier": "GLOWSTAR",
      "carat": 1.2,
      "color": "G",
      "clarity": "VS1",
      "price_per_carat": 4800.0,
      "price": 5760.0
    }
  ],
  "filters_applied": { "doc_type": { "$eq": "diamond_record" }, ... }
}
```

### CORS

Set `CORS_ORIGINS` in `.env` as a comma-separated list of allowed origins. Defaults to `http://localhost:3000` (Next.js dev server).

```
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### /index/refresh flow

`POST /index/refresh` returns immediately with `"status": "started"`. The refresh runs in a background thread: `prepare_kb.py` → `embed_and_upsert.py` → agent reload. Poll `GET /index/refresh/status` to track progress. Only one refresh can run at a time.

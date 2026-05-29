# Diamind — Usage Guide

## Prerequisites

Python 3.11+, Node.js 18+.

```bash
pip install pandas numpy openpyxl pinecone sentence-transformers python-dotenv groq fastapi "uvicorn[standard]"
```

`.env` (project root):
```
GROQ_API_KEY=...
PINECONE_API_KEY=...
PINECONE_INDEX=diamond-kb
CORS_ORIGINS=http://localhost:3000       # comma-separate for multiple
```

---

## Full Pipeline — run when adding new supplier data

```bash
# 1. Map + clean raw Excel files
python map_supplier.py data/Glowstar.xlsx data/Ratnakala.xlsx data/Vaibhav.xlsx data/Zhaveri.xlsx \
  -s Glowstar -s Ratnakala -s Vaibhav -s Zhaveri \
  --output data/combined_mapped.xlsx

# 2. Build knowledge base documents
python prepare_kb.py

# 3. Embed and upsert to Pinecone  (first run downloads model ~400 MB)
python embed_and_upsert.py
```

To process a single new supplier into the master workbook instead:

```bash
python map_supplier.py data/NewSupplier.xlsx -s NewSupplier --master data/master.xlsx
python prepare_kb.py --source data/master.xlsx --sheet MASTER
python embed_and_upsert.py
```

---

## Start the API

```bash
uvicorn api.main:app --reload --port 8000
```

Interactive docs: `http://localhost:8000/docs`

---

## Start the Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

---

## CLI Testing

```bash
# Single question
python query_agent.py -q "round G VS1 under 5000 per carat"

# With verbose filter + chunk output
python query_agent.py --verbose -q "best EX/EX/EX rounds from Glowstar"

# No metadata filters (pure semantic search)
python query_agent.py --no-filter -q "what is fluorescence?"

# Interactive mode  (prefix !v for verbose, !nf to skip filters)
python query_agent.py
```

---

## API Reference

### POST /query

Ask the agent a question. Returns the answer, retrieved source documents, and the Pinecone filters that were applied.

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "round G VS1 under 5000 per carat", "use_filters": true}'
```

Response:
```json
{
  "answer": "Here are the matching stones...",
  "sources": [
    {
      "id": "diamond_Glowstar_Sheet1_42",
      "score": 0.847,
      "doc_type": "diamond_record",
      "supplier": "GLOWSTAR",
      "carat": 1.2,
      "color": "G",
      "clarity": "VS1",
      "cut": "EX",
      "price_per_carat": 4800.0,
      "price": 5760.0
    }
  ],
  "filters_applied": {
    "doc_type": {"$eq": "diamond_record"},
    "color": {"$eq": "G"},
    "clarity": {"$eq": "VS1"},
    "price_per_carat": {"$lte": 5000.0}
  }
}
```

### GET /health

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok", "pinecone": "connected", "model": "loaded", "index_name": "diamond-kb"}
```

### GET /index/stats

```bash
curl http://localhost:8000/index/stats
```

```json
{
  "index_name": "diamond-kb",
  "total_vectors": 399,
  "dimension": 768,
  "diamond_records": 339,
  "domain_chunks": 60
}
```

### POST /index/refresh

Triggers a background re-run of `prepare_kb.py` → `embed_and_upsert.py`. Returns immediately.

```bash
curl -X POST http://localhost:8000/index/refresh
```

```json
{"status": "started", "message": "Refresh started in background. Poll GET /index/refresh/status to see updated vector count."}
```

Poll for completion:

```bash
curl http://localhost:8000/index/refresh/status
```

```json
{"status": "done", "message": "Refresh complete.", "docs_indexed": 399}
```

---

## Adding a New Supplier

1. Add the supplier's column aliases to `mapping_flat.json` under `canonical_to_all_suppliers`.
2. If any alias is ambiguous (same column name used by multiple suppliers for different fields), add a rule to `SUPPLIER_ALIAS_PRIORITY` in `map_supplier.py`.
3. Add any supplier-specific warnings to the `warnings` section of `mapping_flat.json`.
4. Run the full pipeline (steps 1–3 above).

## Adding Domain Knowledge

Create a new numbered `.md` file in `knowledge/`:

```markdown
# Topic Title

## Section One

Content...

## Section Two

Content...
```

`prepare_kb.py` picks it up automatically on next run. Re-run steps 2–3 of the pipeline to embed and upsert the new chunks.
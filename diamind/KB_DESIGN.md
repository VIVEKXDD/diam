# Knowledge Base Design: Diamond RAG System

## Overview

The goal is to answer natural language questions about a diamond inventory — pricing, grading, supplier comparison, market context — using a Retrieval-Augmented Generation (RAG) system. Before any embedding or vector storage can happen, the raw data must be transformed into documents that an embedding model can meaningfully encode and that a retrieval system can surface for the right queries.

This document explains every decision made in building that knowledge base.

---

## What We Built

The knowledge base has two distinct layers:

| Layer | Source | Documents | Purpose |
|-------|--------|-----------|---------|
| Diamond records | `combined_mapped.xlsx` | 339 | The actual inventory — one document per stone |
| Domain knowledge | `knowledge/*.md` | 60 chunks | Industry rules, grading scales, pricing formulas |

These are combined into a single `kb_documents.jsonl` file (445 KB) where each line is one document ready to be embedded and upserted to Pinecone.

---

## Layer 1 — Diamond Records

### Why one document per stone?

Each diamond is an atomic unit of inventory. A buyer or analyst asks about a specific stone or a set of stones meeting criteria. Splitting a single stone's data across multiple chunks would fragment information that belongs together (e.g., the price and the clarity grade that explains it). Merging multiple stones into one chunk would make retrieval too coarse — a query for "G VS1" would retrieve a chunk containing dozens of stones and give the LLM too much noise.

One document per stone is the natural granularity.

### Why natural language, not raw field values?

A diamond record in the Excel has columns like `crown_angle = 34.0` and `pav_depth = 44.0`. An embedding model trained on natural language does not represent `34.0` and `"crown angle"` as semantically close concepts unless they appear together as natural text. By rendering the row as:

```
Angles: crown angle 34.0°, crown height 14.0%, pavilion angle 41.4°, pavilion depth 44.0%.
```

...the embedding captures the semantic relationship between the measurement type and its value, and that text will be retrieved when a user asks "what is the crown angle?" or "find me a diamond with ideal pavilion proportions."

### Document structure

Each diamond document is structured in the same order every time:

```
[Header line: Supplier | Stone ID | Shape | Weight | Color | Clarity]

Certification: lab, cert number, date.
4Cs: carat, color, clarity, cut, polish, symmetry.
Fluorescence: grade (color if present).
Proportions: measurements, table%, depth%.
Angles: crown angle/height, pavilion angle/depth.
Girdle/Culet: girdle description, girdle%, lower half%, culet.
Hearts & Arrows: grade.
Pricing: rap price, rap value, discount%, price/ct, total price.
Quality notes: milky, shade, BGM, natts, white/black visibility fields.
Eye clean: Y/N.
Inclusions: list from certificate.
Inclusion type: code if present.
Origin/Location: origin, location, availability, sheet date.
Comments / Description / Certificate comments.
```

Blank and "UNKNOWN" / "NONE" fields are suppressed — they do not appear in the text at all. This keeps documents focused on information that actually exists, avoids polluting the embedding with meaningless "UNKNOWN" tokens, and reduces document length for stones where suppliers provided sparse data.

### Metadata design

Each diamond document carries a metadata dict that Pinecone stores alongside the vector. Metadata serves two purposes:

1. **Pre-filtering** — narrow the candidate set before ANN search (e.g., only retrieve stones from Glowstar with carat ≥ 1.0)
2. **Post-retrieval display** — the LLM or downstream application can use metadata to format answers without re-parsing the text

Metadata fields and their types:

| Field | Type | Use |
|-------|------|-----|
| `doc_type` | string | Distinguishes diamond records from domain knowledge |
| `supplier` | string | Filter by supplier |
| `lab` | string | Filter GIA-only, etc. |
| `shape` | string | Filter by shape code |
| `carat` | float | Range filter (e.g., carat >= 1.0 AND carat <= 2.0) |
| `color` | string | Filter by color grade |
| `clarity` | string | Filter by clarity grade |
| `cut` | string | Filter EX only |
| `polish` | string | |
| `symmetry` | string | |
| `fluorescence` | string | Filter NON/NONE only |
| `price_per_carat` | float | Range filter |
| `price` | float | Range filter |
| `rap_discount` | float | Filter by discount depth |
| `location` | string | Filter by stock location |
| `availability` | string | Filter AV (available) only |
| `origin` | string | Filter by mining origin |
| `stone_id` | string | Exact lookup |
| `source_sheet` | string | Traces back to original Excel sheet |

**Price fields are only included when non-null.** A stone with no quoted price simply omits `price_per_carat` and `price` from its metadata dict — Pinecone metadata filtering treats missing keys correctly (they won't match a `$eq` or range filter, which is the right behavior).

---

## Layer 2 — Domain Knowledge

### Why domain knowledge is necessary

Diamond grading uses a specialized vocabulary. Without context, an LLM retrieves a diamond record saying "clarity SI2" but cannot explain to the user what SI2 means, whether it is eye-clean, how it affects price, or why two SI2 stones from different suppliers are priced differently. Domain knowledge bridges the gap between raw data and meaningful answers.

Additionally, questions like "what is a Hearts and Arrows diamond?" or "how does fluorescence affect price for a D color stone?" have no answer in the inventory data — they require industry knowledge that must be embedded alongside the records.

### Source files

Eight markdown files in `knowledge/`, each covering one domain topic:

| File | Content |
|------|---------|
| `01_grading_4cs.md` | Color (D–Z with pricing implications), Clarity (FL–I3, eye-clean thresholds), Cut/Polish/Symmetry grades, Carat magic sizes |
| `02_pricing_rapaport.md` | How the Rapaport Price List works, definitions of `rap_price` / `rap_value` / `rap_discount` / `price_per_carat` / `price`, calculation formulas, why price fields are never imputed |
| `03_shapes.md` | All shape codes (RBC, EM, PR, OV, etc.) with descriptions, price discount vs. round, bow-tie effect, step-cut clarity visibility, measurement field format |
| `04_proportions.md` | Ideal ranges for table%, depth%, crown angle/height, pavilion angle/depth, lower half, girdle thickness, culet size, Hearts & Arrows |
| `05_quality_indicators.md` | Fluorescence grades and value impact by color range, milky severity scale, shade types, BGM notation, natts, eye-clean definition, white/black visibility fields |
| `06_inclusions.md` | Every inclusion type in the dataset (feather, crystal, cloud, pinpoint, needle, twinning wisp, laser drill hole, etc.) with severity ranking, certificate comment phrases decoded |
| `07_grading_labs.md` | GIA vs IGI vs HRD vs EGL — grading consistency, typical price premiums/discounts, why lab matters when comparing stones |
| `08_origin_location.md` | Mining origins and their market reputations, Kimberley Process, location field meanings, supplier profiles and their specific quirks |

### Chunking strategy for domain knowledge

Domain knowledge files are split by `##` section headings. Each `##` section becomes one independent document. The `#` title block (introduction before the first `##`) becomes its own chunk.

**Why section-level chunking?**

- A file like `01_grading_4cs.md` covers Color, Clarity, Cut, Polish, Symmetry, and Carat — six distinct topics. If the whole file were one document, a query about "what is SI2?" would retrieve the entire 4Cs file, forcing the LLM to read about color and carat weight to find the answer about clarity.
- Section-level chunks mean "what is SI2?" retrieves only the Clarity section. "What is the difference between EX and VG cut?" retrieves only the Cut section.
- Each section is self-contained — it includes its heading and full body text, so the LLM gets the context it needs without requiring adjacent chunks.

**Section sizes** range from ~200 to ~800 tokens. This is well within the typical embedding model context window (most models handle 512–8192 tokens) and avoids both extremes: chunks too small lose context, chunks too large dilute the signal for specific queries.

### Domain knowledge metadata

```json
{
  "doc_type":    "domain_knowledge",
  "topic":       "grading_4cs",
  "section":     "Clarity",
  "source_file": "01_grading_4cs.md"
}
```

This allows the RAG system to optionally filter domain knowledge by topic (e.g., always include a pricing chunk when the query mentions "rap" or "discount"), or to weight domain knowledge vs. inventory records differently in the retrieval step.

---

## The `kb_documents.jsonl` Format

Every document — whether a diamond record or a domain chunk — follows the same schema:

```json
{
  "id":       "diamond_Glowstar_Sheet1_0",
  "text":     "Supplier: GLOWSTAR | Stone ID: G26-13148 | ...",
  "metadata": { "doc_type": "diamond_record", "supplier": "GLOWSTAR", ... }
}
```

This maps directly to the Pinecone upsert format. The `id` is used to deduplicate and update records when the inventory is refreshed. The `text` is what gets embedded. The `metadata` is stored as-is in Pinecone alongside the vector for filtering and display.

---

## Supplier-Specific Rules Encoded in the Documents

Several data anomalies are resolved during document generation so the embedded text is semantically correct:

| Supplier | Issue | Resolution |
|----------|-------|-----------|
| Vaibhav | "Amount" column = price per carat (all others = total price) | Correctly mapped to `price_per_carat` by `map_supplier.py` before KB prep |
| Zhaveri | "Depth" column = depth% (not raw depth in mm) | Correctly mapped to `depth_pct` |
| Karigar | Melee parcels — no stone IDs, certs, or labs | Fields suppressed in document (no "cert_number: UNKNOWN" noise) |
| All | Certificate numbers stored as floats (e.g., `7.542529e+09`) | Converted to clean integers (`7542529481`) in document text |

---

## What Is NOT in the Knowledge Base

**Price fields with no value**: A blank price is left out of both the text and metadata. Substituting a median would create false pricing information.

**UNKNOWN / NONE values**: Fields filled with "UNKNOWN" by the cleaning pipeline are suppressed in the text. They carry no real information and would add noise to the embedding.

**Empty/header-only sheets**: Glowstar Sheet2 and Sheet3 had only a supplier column. These are skipped.

**Karigar data**: Not present in the current combined file. When added, Karigar stones will produce shorter documents (no cert, stone_id, or individual grading data) but will still embed correctly because absent fields are simply omitted.

---

## Extending the Knowledge Base

**Adding a new supplier**: Run `map_supplier.py` with the new file, then re-run `prepare_kb.py`. New stone documents get new IDs and can be upserted into Pinecone without affecting existing vectors.

**Adding domain knowledge**: Create a new `knowledge/NN_topic.md` file. Use `#` for the file title and `##` for each section. `prepare_kb.py` picks it up automatically. Re-run and upsert only the new domain chunks (their IDs start with `domain_`).

**Refreshing pricing**: Supplier sheets have a `sheet_date` field. When new sheets arrive, re-run the full pipeline (`map_supplier.py` → `prepare_kb.py`) and upsert the updated documents to Pinecone. Existing IDs will be overwritten with fresh vectors and metadata.
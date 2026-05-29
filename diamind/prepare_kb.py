"""
prepare_kb.py
-------------
Builds the knowledge base for the diamond RAG system.

Two document types are produced:
  1. diamond_record  — one document per diamond row from the master/combined sheet
  2. domain_knowledge — one document per section (## heading) from the knowledge/ markdown files

Output: kb_documents.jsonl
  Each line is a JSON object with:
    {
      "id":       unique string identifier,
      "text":     full text to embed,
      "metadata": { filterable fields for Pinecone metadata filtering }
    }

Usage
-----
    # From combined_mapped.xlsx (default)
    python prepare_kb.py

    # From a specific master workbook
    python prepare_kb.py --source data/master.xlsx --sheet MASTER

    # Preview count without writing
    python prepare_kb.py --dry-run
"""

import json
import re
import argparse
from pathlib import Path

import pandas as pd
import numpy as np


SCRIPT_DIR   = Path(__file__).parent
KNOWLEDGE_DIR = SCRIPT_DIR / "knowledge"
DEFAULT_SOURCE = SCRIPT_DIR / "data" / "combined_mapped.xlsx"
OUTPUT_PATH   = SCRIPT_DIR / "kb_documents.jsonl"

# Sheets to skip (metadata/empty sheets)
SKIP_SHEETS = {"_mapping_report"}

# Columns that are never imputed and may legitimately be blank
PRICE_COLS = {"rap_price", "rap_value", "rap_discount", "price_per_carat", "price"}

# Human-readable shape names
SHAPE_NAMES = {
    "RBC": "Round Brilliant Cut", "ROUND": "Round Brilliant Cut",
    "RD":  "Round Brilliant Cut", "EM": "Emerald Cut",
    "PR":  "Princess Cut",        "OV": "Oval",
    "MQ":  "Marquise",            "PS": "Pear",
    "RD":  "Radiant",             "CU": "Cushion",
    "AS":  "Asscher",             "HT": "Heart",
}


# =============================================================================
# helpers
# =============================================================================

def val(v, default=""):
    """Return a clean string for a value, or default if missing."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return default
    s = str(v).strip()
    return s if s and s.lower() not in ("nan", "none", "unknown") else default


def fmt_float(v, decimals=2, default=""):
    try:
        f = float(v)
        if np.isnan(f):
            return default
        return f"{f:.{decimals}f}"
    except (TypeError, ValueError):
        return default


def shape_label(code: str) -> str:
    upper = str(code).strip().upper()
    return SHAPE_NAMES.get(upper, upper.title())


# =============================================================================
# diamond record → natural language document
# =============================================================================

def row_to_text(row: pd.Series, supplier_hint: str = "") -> str:
    supplier    = val(row.get("supplier"), supplier_hint or "UNKNOWN")
    stone_id    = val(row.get("stone_id"))
    lab         = val(row.get("lab"))
    _cn_raw = row.get("cert_number")
    try:
        _cn_f = float(_cn_raw)
        cert_number = str(int(_cn_f)) if not np.isnan(_cn_f) else ""
    except (TypeError, ValueError):
        cert_number = val(_cn_raw)
    shape_code  = val(row.get("shape"), "ROUND")
    shape_name  = shape_label(shape_code)
    carat       = fmt_float(row.get("carat"), 2)
    color       = val(row.get("color"))
    clarity     = val(row.get("clarity"))
    cut         = val(row.get("cut"))
    polish      = val(row.get("polish"))
    symmetry    = val(row.get("symmetry"))
    fluor       = val(row.get("fluorescence"))
    fluor_color = val(row.get("fluorescence_color"))
    measurements = val(row.get("measurements"))
    table_pct   = fmt_float(row.get("table_pct"), 1)
    depth_pct   = fmt_float(row.get("depth_pct"), 1)
    crown_angle = fmt_float(row.get("crown_angle"), 1)
    crown_height = fmt_float(row.get("crown_height"), 1)
    pav_angle   = fmt_float(row.get("pav_angle"), 1)
    pav_depth   = fmt_float(row.get("pav_depth"), 1)
    girdle      = val(row.get("girdle"))
    girdle_pct  = fmt_float(row.get("girdle_pct"), 1)
    lower_half  = fmt_float(row.get("lower_half"), 0)
    culet       = val(row.get("culet"))
    hna         = val(row.get("hna"))
    rap_price   = fmt_float(row.get("rap_price"), 0)
    rap_value   = fmt_float(row.get("rap_value"), 0)
    rap_disc    = fmt_float(row.get("rap_discount"), 1)
    ppc         = fmt_float(row.get("price_per_carat"), 2)
    price       = fmt_float(row.get("price"), 2)
    milky       = val(row.get("milky"))
    shade       = val(row.get("shade"))
    bgm         = val(row.get("bgm"))
    natts       = val(row.get("natts"))
    inclusions  = val(row.get("inclusions"))
    origin      = val(row.get("origin"))
    location    = val(row.get("location"))
    availability = val(row.get("availability"))
    comments    = val(row.get("comments"))
    cert_comments = val(row.get("cert_comments"))
    description = val(row.get("description"))
    eye_clean   = val(row.get("eye_clean"))
    cert_date   = val(row.get("cert_date"))
    sheet_date  = val(row.get("sheet_date"))
    inclusion_type = val(row.get("inclusion_type"))
    white_table = val(row.get("white_table"))
    white_side  = val(row.get("white_side"))
    table_black = val(row.get("table_black"))
    side_black  = val(row.get("side_black"))
    length      = fmt_float(row.get("length"), 2)
    width       = fmt_float(row.get("width"), 2)
    depth       = fmt_float(row.get("depth"), 2)

    # ── Build document ────────────────────────────────────────────────────────
    parts = []

    # Header line
    header_parts = [f"Supplier: {supplier}"]
    if stone_id:
        header_parts.append(f"Stone ID: {stone_id}")
    header_parts += [f"Shape: {shape_name}", f"Weight: {carat} ct"]
    if color:
        header_parts.append(f"Color: {color}")
    if clarity:
        header_parts.append(f"Clarity: {clarity}")
    parts.append(" | ".join(header_parts))
    parts.append("")

    # Certification
    cert_parts = []
    if lab:
        cert_parts.append(f"certified by {lab}")
    if cert_number:
        cert_parts.append(f"certificate #{cert_number}")
    if cert_date:
        cert_parts.append(f"dated {cert_date}")
    if cert_parts:
        parts.append(f"Certification: {', '.join(cert_parts)}.")

    # 4Cs
    grades = []
    if carat:
        grades.append(f"{carat} carat")
    if color:
        grades.append(f"color {color}")
    if clarity:
        grades.append(f"clarity {clarity}")
    if cut:
        grades.append(f"cut {cut}")
    if polish:
        grades.append(f"polish {polish}")
    if symmetry:
        grades.append(f"symmetry {symmetry}")
    if grades:
        parts.append(f"4Cs: {', '.join(grades)}.")

    # Fluorescence
    fluor_parts = []
    if fluor:
        fluor_parts.append(fluor)
    if fluor_color:
        fluor_parts.append(f"({fluor_color})")
    if fluor_parts:
        parts.append(f"Fluorescence: {' '.join(fluor_parts)}.")

    # Measurements and proportions
    meas_parts = []
    if measurements:
        meas_parts.append(f"measurements {measurements} mm")
    elif length and width and depth:
        meas_parts.append(f"measurements {length} × {width} × {depth} mm")
    if table_pct:
        meas_parts.append(f"table {table_pct}%")
    if depth_pct:
        meas_parts.append(f"depth {depth_pct}%")
    if meas_parts:
        parts.append(f"Proportions: {', '.join(meas_parts)}.")

    crown_parts = []
    if crown_angle:
        crown_parts.append(f"crown angle {crown_angle}°")
    if crown_height:
        crown_parts.append(f"crown height {crown_height}%")
    pav_parts = []
    if pav_angle:
        pav_parts.append(f"pavilion angle {pav_angle}°")
    if pav_depth:
        pav_parts.append(f"pavilion depth {pav_depth}%")
    angle_parts = crown_parts + pav_parts
    if angle_parts:
        parts.append(f"Angles: {', '.join(angle_parts)}.")

    girdle_parts = []
    if girdle:
        girdle_parts.append(f"girdle {girdle}")
    if girdle_pct:
        girdle_parts.append(f"({girdle_pct}%)")
    if lower_half:
        girdle_parts.append(f"lower half {lower_half}%")
    if culet:
        girdle_parts.append(f"culet {culet}")
    if girdle_parts:
        parts.append(f"Girdle/Culet: {' '.join(girdle_parts)}.")

    if hna:
        parts.append(f"Hearts & Arrows: {hna}.")

    # Pricing
    price_parts = []
    if rap_price:
        price_parts.append(f"Rapaport price ${rap_price}/ct")
    if rap_value:
        price_parts.append(f"Rap value ${rap_value}")
    if rap_disc:
        price_parts.append(f"discount {rap_disc}%")
    if ppc:
        price_parts.append(f"ask price ${ppc}/ct")
    if price:
        price_parts.append(f"total price ${price}")
    if price_parts:
        parts.append(f"Pricing: {', '.join(price_parts)}.")

    # Quality indicators
    quality_parts = []
    if milky and milky.upper() not in ("NONE", "0", "ML-0"):
        quality_parts.append(f"milky: {milky}")
    if shade and shade.upper() not in ("NONE", "NN", "NO"):
        quality_parts.append(f"shade: {shade}")
    if bgm and "NO BROWN" not in bgm.upper() and bgm.upper() not in ("BC0 - BT0", "NONE"):
        quality_parts.append(f"BGM: {bgm}")
    if natts and natts.upper() not in ("NONE", "NON"):
        quality_parts.append(f"natts: {natts}")
    if white_table and str(white_table) not in ("0", "NONE", ""):
        quality_parts.append(f"white table: {white_table}")
    if table_black and str(table_black) not in ("0", "NONE", ""):
        quality_parts.append(f"table black: {table_black}")
    if white_side and str(white_side) not in ("0", "NONE", ""):
        quality_parts.append(f"white side: {white_side}")
    if side_black and str(side_black) not in ("0", "NONE", ""):
        quality_parts.append(f"side black: {side_black}")
    if quality_parts:
        parts.append(f"Quality notes: {', '.join(quality_parts)}.")

    if eye_clean:
        parts.append(f"Eye clean: {eye_clean}.")

    # Inclusions
    if inclusions:
        parts.append(f"Inclusions: {inclusions}.")
    if inclusion_type and inclusion_type.upper() not in ("NONE", "MIX"):
        parts.append(f"Inclusion type: {inclusion_type}.")

    # Origin and availability
    origin_parts = []
    if origin:
        origin_parts.append(f"origin {origin}")
    if location:
        origin_parts.append(f"location {location}")
    if availability and availability.upper() not in ("UNKNOWN", ""):
        origin_parts.append(f"availability {availability}")
    if sheet_date:
        origin_parts.append(f"sheet dated {sheet_date}")
    if origin_parts:
        parts.append(f"Origin/Location: {', '.join(origin_parts)}.")

    # Comments
    for comment_val, label in [(comments, "Comments"), (description, "Description"), (cert_comments, "Certificate comments")]:
        if comment_val:
            parts.append(f"{label}: {comment_val}")

    return "\n".join(parts)


def row_to_metadata(row: pd.Series) -> dict:
    """Extract filterable metadata fields for Pinecone metadata filtering."""

    def safe_float(v):
        try:
            f = float(v)
            return None if np.isnan(f) else round(f, 4)
        except (TypeError, ValueError):
            return None

    def safe_str(v):
        s = val(v)
        return s.upper() if s else None

    return {k: v for k, v in {
        "doc_type":        "diamond_record",
        "supplier":        safe_str(row.get("supplier")),
        "lab":             safe_str(row.get("lab")),
        "shape":           safe_str(row.get("shape")),
        "carat":           safe_float(row.get("carat")),
        "color":           safe_str(row.get("color")),
        "clarity":         safe_str(row.get("clarity")),
        "cut":             safe_str(row.get("cut")),
        "polish":          safe_str(row.get("polish")),
        "symmetry":        safe_str(row.get("symmetry")),
        "fluorescence":    safe_str(row.get("fluorescence")),
        "price_per_carat": safe_float(row.get("price_per_carat")),
        "price":           safe_float(row.get("price")),
        "rap_discount":    safe_float(row.get("rap_discount")),
        "location":        safe_str(row.get("location")),
        "availability":    safe_str(row.get("availability")),
        "origin":          safe_str(row.get("origin")),
        "stone_id":        val(row.get("stone_id")) or None,
    }.items() if v is not None}


# =============================================================================
# domain knowledge → chunked documents
# =============================================================================

def chunk_markdown(filepath: Path) -> list[dict]:
    """Split a markdown file into one document per ## section."""
    text = filepath.read_text(encoding="utf-8")
    # Split on ## headings
    chunks = re.split(r"(?m)^(## .+)", text)

    documents = []
    topic = filepath.stem  # e.g. "01_grading_4cs"

    # First chunk = content before first ## (the file-level intro)
    intro = chunks[0].strip()
    if intro:
        # Use the # title as the section name
        title_match = re.match(r"^# (.+)", intro, re.MULTILINE)
        section_name = title_match.group(1) if title_match else topic
        documents.append({
            "text": intro,
            "section": section_name,
        })

    # Remaining chunks come in pairs: heading, body
    for i in range(1, len(chunks) - 1, 2):
        heading = chunks[i].strip()
        body    = chunks[i + 1].strip() if i + 1 < len(chunks) else ""
        full_text = f"{heading}\n\n{body}".strip()
        if full_text:
            section_name = heading.lstrip("#").strip()
            documents.append({
                "text": full_text,
                "section": section_name,
            })

    return documents


def load_domain_knowledge() -> list[dict]:
    if not KNOWLEDGE_DIR.exists():
        print(f"  WARNING: knowledge/ directory not found at {KNOWLEDGE_DIR}")
        return []

    md_files = sorted(KNOWLEDGE_DIR.glob("*.md"))
    if not md_files:
        print(f"  WARNING: no .md files found in {KNOWLEDGE_DIR}")
        return []

    all_docs = []
    for filepath in md_files:
        chunks = chunk_markdown(filepath)
        topic = re.sub(r"^\d+_", "", filepath.stem)  # "01_grading_4cs" → "grading_4cs"
        for chunk in chunks:
            all_docs.append({
                "source_file": filepath.name,
                "topic":       topic,
                "section":     chunk["section"],
                "text":        chunk["text"],
            })
        print(f"  {filepath.name}: {len(chunks)} chunks")

    return all_docs


# =============================================================================
# main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Prepare knowledge base documents for RAG embedding.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="Excel source file (default: data/combined_mapped.xlsx)")
    parser.add_argument("--sheet",  default=None, help="Sheet name to read. If omitted, all non-mapping sheets are processed.")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output JSONL file path.")
    parser.add_argument("--dry-run", action="store_true", help="Count documents without writing.")
    args = parser.parse_args()

    source_path = Path(args.source)
    output_path = Path(args.output)

    if not source_path.exists():
        print(f"ERROR: Source file not found: {source_path}")
        raise SystemExit(1)

    documents = []

    # ── 1. Diamond records ────────────────────────────────────────────────────
    print(f"\nLoading diamond records from: {source_path.name}")
    xl = pd.ExcelFile(source_path)

    if args.sheet:
        sheets_to_process = [args.sheet]
    else:
        sheets_to_process = [s for s in xl.sheet_names if s not in SKIP_SHEETS]

    record_count = 0
    for sheet_name in sheets_to_process:
        df = pd.read_excel(source_path, sheet_name=sheet_name)
        df = df.dropna(how="all")

        # Skip sheets that are effectively empty
        if len(df) == 0 or (len(df.columns) <= 1 and "supplier" in df.columns):
            print(f"  Skipping empty sheet: {sheet_name}")
            continue

        print(f"  Sheet '{sheet_name}': {len(df)} rows")

        for idx, row in df.iterrows():
            doc_id   = f"diamond_{sheet_name}_{idx}"
            text     = row_to_text(row)
            metadata = row_to_metadata(row)
            metadata["source_sheet"] = sheet_name

            documents.append({"id": doc_id, "text": text, "metadata": metadata})
            record_count += 1

    print(f"  Total diamond records: {record_count}")

    # ── 2. Domain knowledge ───────────────────────────────────────────────────
    print(f"\nLoading domain knowledge from: {KNOWLEDGE_DIR}/")
    domain_docs = load_domain_knowledge()

    for i, doc in enumerate(domain_docs):
        doc_id = f"domain_{doc['topic']}_{i:04d}"
        metadata = {
            "doc_type":    "domain_knowledge",
            "topic":       doc["topic"],
            "section":     doc["section"],
            "source_file": doc["source_file"],
        }
        documents.append({"id": doc_id, "text": doc["text"], "metadata": metadata})

    print(f"  Total domain knowledge chunks: {len(domain_docs)}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\nTotal documents to embed: {len(documents)}")
    print(f"  diamond_record:    {sum(1 for d in documents if d['metadata'].get('doc_type') == 'diamond_record')}")
    print(f"  domain_knowledge:  {sum(1 for d in documents if d['metadata'].get('doc_type') == 'domain_knowledge')}")

    if args.dry_run:
        print("\nDry run — no file written.")
        return

    # ── Write JSONL ───────────────────────────────────────────────────────────
    with open(output_path, "w", encoding="utf-8") as fh:
        for doc in documents:
            fh.write(json.dumps(doc, ensure_ascii=False) + "\n")

    print(f"\nDone. Written to: {output_path}")
    print(f"  {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
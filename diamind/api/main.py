"""
api/main.py
-----------
FastAPI server for the Diamond RAG agent.

Start:
    pip install fastapi uvicorn[standard]
    uvicorn api.main:app --reload --port 8000

Endpoints:
    POST /query            — ask the agent a question
    GET  /health           — liveness / readiness check
    GET  /index/stats      — Pinecone index statistics
    POST /index/refresh    — re-build KB and re-upsert all vectors
"""

import os
import sys
import subprocess
import threading
import json
import uuid
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# ── Path setup ─────────────────────────────────────────────────────────────────
# api/ sits inside the project root; add root to sys.path so we can import
# query_agent, prepare_kb, and embed_and_upsert from the parent directory.
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from query_agent import DiamondAgentWithTexts, verify_input_guardrail, verify_output_guardrail          # noqa: E402
from api.models import (                               # noqa: E402
    QueryRequest, QueryResponse, SourceDocument,
    IndexStats, RefreshResponse, HealthResponse,
    DemandRaiseRequest, DemandItem, NotificationLog, DemandListResponse,
)

# ── CORS origins ───────────────────────────────────────────────────────────────
# Comma-separated list in CORS_ORIGINS env var, or defaults to Next.js dev port.
_raw_origins = os.environ.get("CORS_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

# ── Shared state ───────────────────────────────────────────────────────────────
_refresh_lock   = threading.Lock()
_refresh_status = {"status": "idle", "message": "No refresh has run yet.", "docs_indexed": None}

# ── Agent singleton ────────────────────────────────────────────────────────────
agent: DiamondAgentWithTexts | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    print("Loading Diamond RAG agent...")
    agent = DiamondAgentWithTexts()
    print("Agent ready.")
    yield
    # nothing to tear down


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Diamond RAG API",
    description="Agentic retrieval-augmented generation over diamond inventory and industry knowledge.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── POST /query ────────────────────────────────────────────────────────────────

@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialised.")

    # 1. Run Input Guardrails
    guardrail_msg = verify_input_guardrail(req.question, agent.groq)
    if guardrail_msg:
        return QueryResponse(
            answer = guardrail_msg,
            sources = [],
            filters_applied = {},
            demand_raisable = False,
            recommended_criteria = None
        )

    # Run the two-stage pipeline
    extracted       = agent.extract_filters(req.question) if req.use_filters else {}
    pinecone_filter = agent.build_pinecone_filter(extracted)
    matches         = agent.retrieve(req.question, pinecone_filter)

    # Load behavior & news mocks
    user_behavior = ""
    market_news = ""
    behavior_path = ROOT / "data" / "user_behavior.json"
    news_path = ROOT / "data" / "market_news.json"
    if behavior_path.exists():
        try:
            with open(behavior_path, encoding="utf-8") as f:
                user_behavior = json.dumps(json.load(f))
        except Exception as e:
            print(f"Error loading behavior in api: {e}")
    if news_path.exists():
        try:
            with open(news_path, encoding="utf-8") as f:
                market_news = json.dumps(json.load(f))
        except Exception as e:
            print(f"Error loading news in api: {e}")

    # Generate answer with behavioral + news context
    answer          = agent.answer(req.question, matches, user_behavior, market_news)
    answer          = verify_output_guardrail(answer)

    # Build source list from match objects
    sources: list[SourceDocument] = []
    for m in matches:
        md       = m.metadata or {}
        doc_type = md.get("doc_type", "unknown")

        sources.append(SourceDocument(
            id          = m.id,
            score       = round(m.score, 4),
            doc_type    = doc_type,
            supplier    = md.get("supplier"),
            stone_id    = md.get("stone_id"),
            shape       = md.get("shape"),
            carat       = md.get("carat"),
            color       = md.get("color"),
            clarity     = md.get("clarity"),
            cut         = md.get("cut"),
            price_per_carat = md.get("price_per_carat"),
            price       = md.get("price"),
            topic       = md.get("topic"),
            section     = md.get("section"),
        ))

    # Inventory check to raise demand if zero diamond records match
    is_inventory_query = (
        extracted.get("doc_type") == "diamond_record" or 
        any(k in extracted for k in ["shape", "color", "clarity", "carat_min", "carat_max", "price_min", "price_max", "ppc_min", "ppc_max", "supplier"])
    )
    has_diamond_matches = any(m.metadata.get("doc_type") == "diamond_record" for m in matches if m.metadata)
    demand_raisable = is_inventory_query and not has_diamond_matches

    # Only include filters in recommended_criteria that are not null/empty
    recommended_criteria = {k: v for k, v in extracted.items() if v is not None} if demand_raisable else None

    return QueryResponse(
        answer          = answer,
        sources         = sources,
        filters_applied = pinecone_filter,
        demand_raisable = demand_raisable,
        recommended_criteria = recommended_criteria,
    )


# ── GET /health ────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health():
    pinecone_status = "error"
    index_name      = os.environ.get("PINECONE_INDEX", "diamond-kb")
    api_key         = os.environ.get("PINECONE_API_KEY", "")

    if api_key:
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=api_key)
            pc.Index(index_name).describe_index_stats()
            pinecone_status = "connected"
        except Exception:
            pass

    model_status = "loaded" if agent is not None else "error"
    overall      = "ok" if pinecone_status == "connected" and model_status == "loaded" else "degraded"

    return HealthResponse(
        status     = overall,
        pinecone   = pinecone_status,
        model      = model_status,
        index_name = index_name,
    )


# ── GET /index/stats ───────────────────────────────────────────────────────────

@app.get("/index/stats", response_model=IndexStats)
def index_stats():
    index_name = os.environ.get("PINECONE_INDEX", "diamond-kb")
    api_key    = os.environ.get("PINECONE_API_KEY", "")
    
    total_vectors = 0
    dimension = 768
    
    if api_key:
        try:
            from pinecone import Pinecone
            pc    = Pinecone(api_key=api_key)
            stats = pc.Index(index_name).describe_index_stats()
            total_vectors = stats.get("total_vector_count", 0)
            dimension = stats.get("dimension", 768)
        except Exception as e:
            print(f"Pinecone describe_index_stats failed: {e}")

    # Count doc types from local JSONL (fast, avoids full Pinecone scan)
    import json
    kb_path        = ROOT / "kb_documents.jsonl"
    diamond_count  = 0
    domain_count   = 0
    if kb_path.exists():
        try:
            with open(kb_path, encoding="utf-8") as fh:
                for line in fh:
                    doc = json.loads(line)
                    if doc["metadata"].get("doc_type") == "diamond_record":
                        diamond_count += 1
                    else:
                        domain_count += 1
        except Exception as e:
            print(f"Error reading local kb_documents.jsonl: {e}")

    return IndexStats(
        index_name      = index_name,
        total_vectors   = total_vectors,
        dimension       = dimension,
        diamond_records = diamond_count,
        domain_chunks   = domain_count,
    )


# ── POST /index/refresh ────────────────────────────────────────────────────────

def _run_refresh():
    """Runs in a background thread: prepare_kb → embed_and_upsert."""
    global agent
    import json

    _refresh_status.update({"status": "running", "message": "Building knowledge base..."})

    try:
        # Step 1 — rebuild kb_documents.jsonl
        result = subprocess.run(
            [sys.executable, str(ROOT / "prepare_kb.py")],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        if result.returncode != 0:
            raise RuntimeError(f"prepare_kb.py failed:\n{result.stderr}")

        _refresh_status["message"] = "Embedding and upserting vectors..."

        # Step 2 — re-embed and upsert
        result = subprocess.run(
            [sys.executable, str(ROOT / "embed_and_upsert.py")],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        if result.returncode != 0:
            raise RuntimeError(f"embed_and_upsert.py failed:\n{result.stderr}")

        # Step 3 — count docs
        kb_path = ROOT / "kb_documents.jsonl"
        doc_count = sum(1 for _ in open(kb_path, encoding="utf-8"))

        # Step 4 — reload agent so it picks up new document texts
        agent = DiamondAgentWithTexts()

        _refresh_status.update({
            "status":       "done",
            "message":      "Refresh complete.",
            "docs_indexed": doc_count,
        })

    except Exception as e:
        _refresh_status.update({
            "status":  "error",
            "message": str(e),
        })


@app.post("/index/refresh", response_model=RefreshResponse)
def index_refresh():
    if not _refresh_lock.acquire(blocking=False):
        return RefreshResponse(
            status  = "running",
            message = "A refresh is already in progress.",
        )

    def run_and_release():
        try:
            _run_refresh()
        finally:
            _refresh_lock.release()

    thread = threading.Thread(target=run_and_release, daemon=True)
    thread.start()

    return RefreshResponse(
        status  = "started",
        message = "Refresh started in background. Poll GET /index/stats to see updated vector count.",
    )


@app.get("/index/refresh/status", response_model=RefreshResponse)
def refresh_status():
    return RefreshResponse(**_refresh_status)


# ── POST /demand/raise and GET /demand/list ────────────────────────────────────

DEMANDS_FILE = ROOT / "data" / "demands.json"

def _load_demands_data() -> dict:
    if DEMANDS_FILE.exists():
        try:
            with open(DEMANDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"demands": [], "notifications": []}

def _save_demands_data(data: dict):
    DEMANDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DEMANDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.post("/demand/raise")
def raise_demand(req: DemandRaiseRequest):
    data = _load_demands_data()
    
    # Create new demand item
    demand_id = f"dem-{uuid.uuid4().hex[:8]}"
    created_at = datetime.now().isoformat()
    new_demand = {
        "id": demand_id,
        "specs": req.specs,
        "contact_email": req.contact_email,
        "contact_phone": req.contact_phone,
        "created_at": created_at,
        "status": "pending"
    }
    data["demands"].append(new_demand)
    
    # Trigger simulated notifications (Procurement alert, supplier email, SMS log)
    specs_desc = ", ".join(f"{k}: {v}" for k, v in req.specs.items() if v)
    
    notifications = [
        {
            "id": f"notif-email-{uuid.uuid4().hex[:6]}",
            "demand_id": demand_id,
            "channel": "Email",
            "recipient": "procurement-team@diamind.com",
            "message": f"ALERT: New inventory demand raised for specifications: {specs_desc}. Requested by {req.contact_email}.",
            "sent_at": datetime.now().isoformat()
        },
        {
            "id": f"notif-sms-{uuid.uuid4().hex[:6]}",
            "demand_id": demand_id,
            "channel": "SMS",
            "recipient": req.contact_phone if req.contact_phone else "+15550199222 (Admin)",
            "message": f"Diamind Procurement: Match request registered for {req.specs.get('carat_min', '1.0')}-{req.specs.get('carat_max', '2.0')}ct {req.specs.get('shape', 'Diamond')}. Status: Pending supplier review.",
            "sent_at": datetime.now().isoformat()
        },
        {
            "id": f"notif-proc-{uuid.uuid4().hex[:6]}",
            "demand_id": demand_id,
            "channel": "Procurement Alert",
            "recipient": "GLOWSTAR, RATNAKALA, VAIBHAV, ZHAVERI",
            "message": f"B2B Broadcast: Supplier catalogs scanned for {specs_desc} - zero matches. Demand broadcasted to all supplier channels.",
            "sent_at": datetime.now().isoformat()
        }
    ]
    data["notifications"].extend(notifications)
    _save_demands_data(data)
    
    return {"status": "success", "message": "Demand successfully raised and dispatched to notification engine.", "demand_id": demand_id}


@app.get("/demand/list", response_model=DemandListResponse)
def list_demands():
    data = _load_demands_data()
    # Return demands and notifications sorted by date (newest first)
    sorted_demands = sorted(data.get("demands", []), key=lambda x: x["created_at"], reverse=True)
    sorted_notifications = sorted(data.get("notifications", []), key=lambda x: x["sent_at"], reverse=True)
    return DemandListResponse(demands=sorted_demands, notifications=sorted_notifications)
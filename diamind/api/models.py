from pydantic import BaseModel, Field
from typing import Any


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    use_filters: bool = True


class SourceDocument(BaseModel):
    id: str
    score: float
    doc_type: str
    # diamond_record fields (only present when doc_type == "diamond_record")
    supplier: str | None = None
    stone_id: str | None = None
    shape: str | None = None
    carat: float | None = None
    color: str | None = None
    clarity: str | None = None
    cut: str | None = None
    price_per_carat: float | None = None
    price: float | None = None
    # domain_knowledge fields
    topic: str | None = None
    section: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]
    filters_applied: dict[str, Any]
    demand_raisable: bool = False
    recommended_criteria: dict[str, Any] | None = None


class IndexStats(BaseModel):
    index_name: str
    total_vectors: int
    dimension: int
    diamond_records: int
    domain_chunks: int


class RefreshResponse(BaseModel):
    status: str        # "started" | "running" | "done" | "error"
    message: str
    docs_indexed: int | None = None


class HealthResponse(BaseModel):
    status: str        # "ok" | "degraded"
    pinecone: str      # "connected" | "error"
    model: str         # "loaded" | "error"
    index_name: str


class DemandRaiseRequest(BaseModel):
    specs: dict[str, Any] = Field(..., description="The parameters extracted from user query")
    contact_email: str = Field(..., description="User's contact email")
    contact_phone: str | None = None


class DemandItem(BaseModel):
    id: str
    specs: dict[str, Any]
    contact_email: str
    contact_phone: str | None = None
    created_at: str
    status: str = "pending"


class NotificationLog(BaseModel):
    id: str
    demand_id: str
    channel: str # "SMS" | "Email" | "Procurement Alert"
    recipient: str
    message: str
    sent_at: str


class DemandListResponse(BaseModel):
    demands: list[DemandItem]
    notifications: list[NotificationLog]
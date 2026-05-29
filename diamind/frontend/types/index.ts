export interface SourceDocument {
  id: string;
  score: number;
  doc_type: "diamond_record" | "domain_knowledge";
  // diamond_record
  supplier?: string;
  stone_id?: string;
  shape?: string;
  carat?: number;
  color?: string;
  clarity?: string;
  cut?: string;
  price_per_carat?: number;
  price?: number;
  // domain_knowledge
  topic?: string;
  section?: string;
}

export interface QueryResponse {
  answer: string;
  sources: SourceDocument[];
  filters_applied: Record<string, unknown>;
  demand_raisable?: boolean;
  recommended_criteria?: Record<string, unknown> | null;
}

export interface IndexStats {
  index_name: string;
  total_vectors: number;
  dimension: number;
  diamond_records: number;
  domain_chunks: number;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  pinecone: string;
  model: string;
  index_name: string;
}

export interface RefreshResponse {
  status: "started" | "running" | "done" | "error" | "idle";
  message: string;
  docs_indexed?: number;
}

export type MessageRole = "user" | "assistant";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  sources?: SourceDocument[];
  filters?: Record<string, unknown>;
  timestamp: Date;
  demand_raisable?: boolean;
  recommended_criteria?: Record<string, unknown> | null;
}

export interface DemandItem {
  id: string;
  specs: Record<string, any>;
  contact_email: string;
  contact_phone?: string;
  created_at: string;
  status: string;
}

export interface NotificationLog {
  id: string;
  demand_id: string;
  channel: string;
  recipient: string;
  message: string;
  sent_at: string;
}

export interface DemandListResponse {
  demands: DemandItem[];
  notifications: NotificationLog[];
}
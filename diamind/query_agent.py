"""
query_agent.py
--------------
Agentic RAG for the diamond knowledge base.

Two-stage pipeline per query:
  1. Filter extraction  — Groq LLM reads the query and outputs structured
                          Pinecone metadata filters (shape, color, carat
                          range, price ceiling, etc.)
  2. Retrieve + Answer  — embed the query, hit Pinecone with those filters,
                          pass the top-k chunks to Groq to generate the answer

Usage
-----
    python query_agent.py                        # interactive CLI
    python query_agent.py -q "your question"     # single shot
    python query_agent.py --no-filter            # skip filter extraction (debug)
"""

import json
import os
import re
import argparse
from pathlib import Path

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from groq import Groq

# ── Config ─────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
load_dotenv(SCRIPT_DIR / ".env", override=True)

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")
INDEX_NAME       = os.environ.get("PINECONE_INDEX", "diamond-kb")
GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")

EMBED_MODEL      = "BAAI/bge-base-en-v1.5"
# Prefix required by BGE on queries (NOT on documents at index time)
QUERY_PREFIX     = "Represent this sentence for searching relevant passages: "

GROQ_MODEL       = "llama-3.3-70b-versatile"
TOP_K            = 8       # chunks returned from Pinecone
TOP_K_FALLBACK   = 12      # used when filters eliminate too many results


# ── System prompts ─────────────────────────────────────────────────────────────

FILTER_SYSTEM = """\
You are a diamond inventory assistant. Extract structured search filters from the user's query.

Return a JSON object with any of these keys that are clearly stated or implied by the query.
Omit keys that are not mentioned. Do not guess.

{
  "doc_type":        "diamond_record" | "domain_knowledge" | null,
  "supplier":        "GLOWSTAR" | "RATNAKALA" | "VAIBHAV" | "ZHAVERI",
  "shape":           "RBC" | "ROUND" | "EM" | "PR" | "OV" | "MQ" | "PS" | "CU" | "AS" | "HT",
  "color":           single grade string e.g. "G", or list e.g. ["G","H"],
  "clarity":         single grade string e.g. "VS1", or list,
  "cut":             "EX" | "VG" | "GD",
  "polish":          "EX" | "VG" | "GD",
  "symmetry":        "EX" | "VG" | "GD",
  "fluorescence":    "NONE" | "NON" | "FNT" | "MED" | "STG",
  "lab":             "GIA" | "IGI" | "HRD",
  "carat_min":       number,
  "carat_max":       number,
  "price_min":       number,
  "price_max":       number,
  "ppc_min":         number,
  "ppc_max":         number,
  "availability":    "AV",
  "origin":          string,
  "location":        string
}

Rules:
- For grading/education questions ("what is SI2", "explain fluorescence") → set doc_type = "domain_knowledge"
- For inventory/pricing questions → set doc_type = "diamond_record"
- For mixed or comparison questions → omit doc_type to search both
- "triple excellent" or "EX/EX/EX" or "3EX" → set cut, polish, symmetry all to "EX"
- "no fluorescence" → fluorescence = "NONE"
- "round" maps to shape "RBC"
- Respond with ONLY valid JSON, no explanation.
"""

ANSWER_SYSTEM = """\
You are an expert diamond industry assistant with access to a live inventory and comprehensive \
grading knowledge. Answer the user's question using the retrieved context, and the provided User Behavior, Market News, and Business Rules.

Recommendations Guidelines:
- If recommending diamonds from the inventory, you MUST ONLY recommend the TOP 3 best matching stones. Do not recommend or list more than 3.
- For each recommended stone, include the Stone ID, Supplier, Carat, Color, Clarity, Cut, and Price details.
- For each stone, write a crisp justification (exactly 3-4 lines) explaining WHY the user should buy it.
  This justification MUST weave together:
  a) The diamond's specific attributes (e.g., Triple Excellent cut, clean table).
  b) The User's Behavior Data (e.g., matching their budget, preferred shapes, or high-cut interest).
  c) The Market News (e.g., capitalizing on stable prices, avoiding restricted origins, or BGM discounts).
  Be persuasive, crisp, and direct.

General Guidelines:
- For grading/industry questions: give a clear, expert explanation.
- For comparison questions: compare concisely and recommend.
- If the context does not contain enough information to answer, say so clearly.
- Use dollar signs and format prices with commas. Show rap discount as a percentage.
- Keep answers focused and practical — this is a B2B diamond trading tool.
"""


# ── Guardrails ─────────────────────────────────────────────────────────────────

ABUSIVE_KEYWORDS = [
    # English
    r"\bfuck(ing|er|ed)?\b", r"\bshit(ty)?\b", r"\basshole\b", r"\bbitch(es)?\b", r"\bcunt\b", 
    r"\bbastard\b", r"\bdick\b", r"\bpussy\b", r"\bfaggot\b", r"\bmotherfucker\b",
    # Hindi/Hinglish
    r"\bchutiya\b", r"\bbhadwa\b", r"\bharami\b", r"\bmadarchod\b", r"\bbehenchod\b", 
    r"\bbhenchod\b", r"\bsaala\b", r"\bsala\b", r"\bkamina\b", r"\brandi\b",
    r"\bgandu\b", r"\bbsdk\b", r"\bbhosdike\b", r"\bchut\b", r"\blaund\b", 
    r"\blauda\b", r"\bloda\b", r"\bkutta\b", r"\bkamine\b"
]

SELF_HARM_KEYWORDS = [
    r"\bsuicide\b", r"\bsuicidal\b", r"\bkill myself\b", r"\bend my life\b", 
    r"\bwant to die\b", r"\bhurt myself\b", r"\bcut myself\b", r"\batmanhatya\b", 
    r"\bjaan de dunga\b", r"\bmarne ja raha\b", r"\bmar jana\b", r"\bdie\b"
]

def verify_input_guardrail(query: str, groq_client = None) -> str | None:
    q_lower = query.lower()
    
    # 1. Check self harm
    for pattern in SELF_HARM_KEYWORDS:
        if re.search(pattern, q_lower):
            return (
                "If you are feeling overwhelmed and considering self-harm, please know that you are not alone. "
                "Please reach out to a support service, such as a national suicide helpline or the AASRA helpline "
                "at +91-9820466726, or dial 112 or 988 for immediate help."
            )
            
    # 2. Check abusive content
    for pattern in ABUSIVE_KEYWORDS:
        if re.search(pattern, q_lower):
            return "I cannot process queries containing inappropriate or abusive language. Please reformulate your request professionally."
            
    if not groq_client:
        # Check context locally using simple keyword heuristics
        diamond_context_keywords = [
            "diamond", "heera", "stone", "jewel", "gem", "price", "carat", "color", "clarity", "cut",
            "polish", "symmetry", "fluorescence", "lab", "gia", "igi", "hrd", "glowstar", "ratnakala",
            "vaibhav", "zhaveri", "karigar", "discount", "rapaport", "rap", "table", "depth", "crown",
            "pavilion", "girdle", "culet", "hna", "milky", "shade", "bgm", "natt", "inclusion", "origin",
            "location", "availability", "inventory", "buy", "purchase", "demand", "recommend", "cert", 
            "supplier", "hello", "hi", "hey", "help", "who", "what", "ready", "status"
        ]
        has_context = any(kw in q_lower for kw in diamond_context_keywords)
        if not has_context:
            return "I am a specialized Diamond Intelligence Assistant and can only answer questions related to diamond inventory, grading, pricing, and domain knowledge."
        return None

    system_prompt = (
        "You are a guardrail assistant for a B2B Diamond intelligence system.\n"
        "Determine if the user query is related to diamonds, gems, jewelry, trade, diamond suppliers "
        "(like Glowstar, Ratnakala, Vaibhav, Zhaveri), grading reports (GIA, IGI, HRD), 4Cs, or general business "
        "interaction (greetings, system status, general help requests).\n"
        "Return ONLY 'true' if the query is relevant and should be allowed, or 'false' if it is completely "
        "off-topic (e.g. asking for programming code, recipes, political discussions, unrelated stories).\n"
        "Do not explain, just return the word 'true' or 'false'."
    )
    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=10,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        )
        content = resp.choices[0].message.content.strip().lower()
        if "false" in content:
            return "I am a specialized Diamond Intelligence Assistant and can only answer questions related to diamond inventory, grading, pricing, and domain knowledge."
    except Exception as e:
        print(f"Error checking guardrails via LLM: {e}")
        
    return None

def verify_output_guardrail(answer: str) -> str:
    # Basic output sanity checks: ensure no leaked system instructions or bad words
    for pattern in ABUSIVE_KEYWORDS:
        if re.search(pattern, answer.lower()):
            return "Generated response failed output safety checks. Please try a different query."
    return answer


# ── DiamondAgent ──────────────────────────────────────────────────────────────

class DiamondAgent:

    def __init__(self):
        print("Loading embedding model...")
        self.embedder = SentenceTransformer(EMBED_MODEL)
        
        self.index = None
        if PINECONE_API_KEY:
            try:
                self.index = Pinecone(api_key=PINECONE_API_KEY).Index(INDEX_NAME)
            except Exception as e:
                print(f"Error connecting to Pinecone: {e}")
        else:
            print("Warning: PINECONE_API_KEY is empty. Vector search will be unavailable.")
            
        self.groq = None
        if GROQ_API_KEY:
            try:
                self.groq = Groq(api_key=GROQ_API_KEY)
            except Exception as e:
                print(f"Error initializing Groq: {e}")
        else:
            print("Warning: GROQ_API_KEY is empty. LLM features will be unavailable.")
            
        print("Ready.\n")

    # ── Embedding ──────────────────────────────────────────────────────────────

    def embed(self, text: str) -> list[float]:
        vec = self.embedder.encode(
            QUERY_PREFIX + text,
            normalize_embeddings=True,
        )
        return vec.tolist()

    # ── Filter extraction ──────────────────────────────────────────────────────

    def extract_filters(self, query: str) -> dict:
        """Ask Groq to pull structured filters out of the natural-language query."""
        if not self.groq:
            return {}
        resp = self.groq.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0,
            messages=[
                {"role": "system",  "content": FILTER_SYSTEM},
                {"role": "user",    "content": query},
            ],
        )
        raw = resp.choices[0].message.content.strip()

        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    # ── Build Pinecone filter ──────────────────────────────────────────────────

    @staticmethod
    def build_pinecone_filter(extracted: dict) -> dict:
        """Convert the LLM's extracted params into a Pinecone metadata filter."""
        f = {}

        # doc_type
        if "doc_type" in extracted:
            f["doc_type"] = {"$eq": extracted["doc_type"]}

        # Exact-match string fields
        for field in ("supplier", "lab", "cut", "polish", "symmetry",
                      "fluorescence", "availability", "origin", "location"):
            if field in extracted:
                f[field] = {"$eq": extracted[field].upper()}

        # Color / clarity — allow single value or list
        for field in ("color", "clarity", "shape"):
            if field in extracted:
                val = extracted[field]
                if isinstance(val, list):
                    f[field] = {"$in": [v.upper() for v in val]}
                else:
                    f[field] = {"$eq": val.upper()}

        # Numeric ranges
        carat_filter = {}
        if "carat_min" in extracted:
            carat_filter["$gte"] = float(extracted["carat_min"])
        if "carat_max" in extracted:
            carat_filter["$lte"] = float(extracted["carat_max"])
        if carat_filter:
            f["carat"] = carat_filter

        ppc_filter = {}
        if "ppc_min" in extracted:
            ppc_filter["$gte"] = float(extracted["ppc_min"])
        if "ppc_max" in extracted:
            ppc_filter["$lte"] = float(extracted["ppc_max"])
        if ppc_filter:
            f["price_per_carat"] = ppc_filter

        price_filter = {}
        if "price_min" in extracted:
            price_filter["$gte"] = float(extracted["price_min"])
        if "price_max" in extracted:
            price_filter["$lte"] = float(extracted["price_max"])
        if price_filter:
            f["price"] = price_filter

        return f

    # ── Retrieval ──────────────────────────────────────────────────────────────

    def retrieve(self, query: str, pinecone_filter: dict, top_k: int = TOP_K) -> list:
        vec = self.embed(query)
        if not self.index:
            print("Warning: Pinecone index is not initialized. Returning empty results.")
            return []

        results = self.index.query(
            vector=vec,
            top_k=top_k,
            filter=pinecone_filter if pinecone_filter else None,
            include_metadata=True,
        )
        matches = results.matches

        # If filters were too restrictive and returned nothing, fall back without them
        if not matches and pinecone_filter:
            print("  (No results with filters — retrying without metadata filters)")
            results = self.index.query(
                vector=vec,
                top_k=TOP_K_FALLBACK,
                include_metadata=True,
            )
            matches = results.matches

        return matches

    # ── Answer generation ──────────────────────────────────────────────────────

    def answer(self, query: str, matches: list, user_behavior: str = "", market_news: str = "") -> str:
        if not self.groq:
            return "Groq client is not initialized. Please set GROQ_API_KEY in your environment to use LLM answering."
        if not matches:
            return "No relevant documents found in the knowledge base for that query."

        context_parts = []
        for i, m in enumerate(matches, 1):
            score    = m.score
            metadata = m.metadata or {}
            text     = metadata.get("text", "")

            doc_type = metadata.get("doc_type", "unknown")
            header   = f"[{i}] {doc_type.upper()} (score: {score:.3f})"
            context_parts.append(f"{header}\n{text}")

        context = "\n\n---\n\n".join(context_parts)

        # Dynamic business rules loading
        business_rules = ""
        rules_path = SCRIPT_DIR / "business_rules.txt"
        if rules_path.exists():
            try:
                business_rules = rules_path.read_text(encoding="utf-8").strip()
            except Exception as e:
                print(f"Error loading business rules: {e}")

        system_message = ANSWER_SYSTEM
        if business_rules:
            system_message += f"\n\nBUSINESS RULES TO ENFORCE:\n{business_rules}"

        user_content = f"Context:\n{context}\n\n"
        if user_behavior:
            user_content += f"User Behavior / Profile Data:\n{user_behavior}\n\n"
        if market_news:
            user_content += f"Market News & Trends:\n{market_news}\n\n"
        user_content += f"Question: {query}"

        resp = self.groq.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0.2,
            messages=[
                {"role": "system",  "content": system_message},
                {"role": "user",    "content": user_content},
            ],
        )
        return resp.choices[0].message.content.strip()

    # ── Full pipeline ──────────────────────────────────────────────────────────

    def query(self, user_query: str, use_filters: bool = True, verbose: bool = False, user_behavior: str = "", market_news: str = "") -> str:
        # Apply input guardrails
        guardrail_msg = verify_input_guardrail(user_query, self.groq)
        if guardrail_msg:
            return guardrail_msg

        extracted      = {}
        pinecone_filter = {}

        if use_filters:
            extracted       = self.extract_filters(user_query)
            pinecone_filter = self.build_pinecone_filter(extracted)

        if verbose:
            print(f"  Extracted filters : {json.dumps(extracted, indent=2)}")
            print(f"  Pinecone filter   : {json.dumps(pinecone_filter, indent=2)}")

        matches = self.retrieve(user_query, pinecone_filter)

        if verbose:
            print(f"  Retrieved {len(matches)} chunks")
            for m in matches:
                md = m.metadata or {}
                print(f"    [{m.score:.3f}] {m.id}  ({md.get('doc_type','?')})")

        ans = self.answer(user_query, matches, user_behavior, market_news)
        return verify_output_guardrail(ans)


# ── Text needs to be stored retrievably ───────────────────────────────────────
# Pinecone does not return the original vector text by default — we need to
# re-attach it from the local JSONL file so the LLM gets the full document.

def attach_texts(matches: list, id_to_text: dict[str, str]) -> list:
    for m in matches:
        doc_id = m.id
        if doc_id in id_to_text:
            if m.metadata is None:
                m.metadata = {}
            m.metadata["text"] = id_to_text[doc_id]
    return matches


def load_id_to_text(kb_path: Path) -> dict[str, str]:
    mapping = {}
    if kb_path.exists():
        with open(kb_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    doc = json.loads(line)
                    mapping[doc["id"]] = doc["text"]
    return mapping


# ── Patch agent to attach texts ────────────────────────────────────────────────

class DiamondAgentWithTexts(DiamondAgent):

    def __init__(self):
        super().__init__()
        kb_path = SCRIPT_DIR / "kb_documents.jsonl"
        print(f"Loading document texts from {kb_path.name}...")
        self.id_to_text = load_id_to_text(kb_path)
        print(f"  {len(self.id_to_text)} documents indexed.\n")

    def retrieve(self, query: str, pinecone_filter: dict, top_k: int = TOP_K) -> list[dict]:
        matches = super().retrieve(query, pinecone_filter, top_k)
        return attach_texts(matches, self.id_to_text)


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Diamond RAG agent.")
    parser.add_argument("-q", "--query",     help="Single query (non-interactive mode).")
    parser.add_argument("--no-filter",  action="store_true", help="Disable filter extraction.")
    parser.add_argument("--verbose",    action="store_true", help="Show filters and retrieved chunks.")
    args = parser.parse_args()

    agent = DiamondAgentWithTexts()
    use_filters = not args.no_filter

    # Load mock profile & news if they exist
    user_behavior = ""
    market_news = ""
    
    behavior_path = SCRIPT_DIR / "data" / "user_behavior.json"
    news_path = SCRIPT_DIR / "data" / "market_news.json"
    
    if behavior_path.exists():
        try:
            with open(behavior_path, encoding="utf-8") as f:
                user_behavior = json.dumps(json.load(f), indent=2)
        except Exception as e:
            print(f"Warning: could not load user behavior: {e}")
            
    if news_path.exists():
        try:
            with open(news_path, encoding="utf-8") as f:
                market_news = json.dumps(json.load(f), indent=2)
        except Exception as e:
            print(f"Warning: could not load market news: {e}")

    if args.query:
        print(f"Q: {args.query}\n")
        answer = agent.query(args.query, use_filters=use_filters, verbose=args.verbose, user_behavior=user_behavior, market_news=market_news)
        print(answer)
        return

    # Interactive loop
    print("Diamond RAG Agent — type your question, or 'quit' to exit.")
    print("Flags: prefix with '!v' for verbose, '!nf' to skip filters.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            break

        verbose    = "!v"  in user_input
        no_filters = "!nf" in user_input
        clean_q    = user_input.replace("!v", "").replace("!nf", "").strip()

        print()
        answer = agent.query(
            clean_q,
            use_filters=not no_filters and use_filters,
            verbose=verbose,
            user_behavior=user_behavior,
            market_news=market_news,
        )
        print(f"\nAgent: {answer}\n")


if __name__ == "__main__":
    main()
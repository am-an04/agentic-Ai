"""
RAG / Knowledge Layer for DataPilot Agentic AI System.
Provides vector-based document retrieval, chunking, data dictionaries,
and past session indexing with source metadata for grounded citations.
"""

import os
import glob
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class Chunk(BaseModel):
    chunk_id: str
    text: str
    source: str
    topic: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None

# Backward-compatible static dictionary
ANALYTICAL_KNOWLEDGE_BASE = {
    "statistical_guidelines": {
        "p_value_threshold": 0.05,
        "sample_size_minimum": 30,
        "ttest_rule": "Use independent 2-sample t-test when comparing continuous metric across 2 categorical groups.",
        "anova_rule": "Use 1-way ANOVA when comparing continuous metric across 3+ categorical groups.",
        "chi_square_rule": "Use Chi-Square test when evaluating association between 2 categorical variables.",
        "correlation_vs_causation": "Always state linear association rather than causal direction unless controlled experiment design is confirmed."
    },
    "ml_guidelines": {
        "regression_metrics": ["MAE", "RMSE", "R2_score"],
        "classification_metrics": ["Accuracy", "Precision", "Recall", "F1_score", "Confusion Matrix"],
        "clustering_metrics": ["Silhouette Score"],
        "overfitting_rule": "Always evaluate models on a 20% holdout test set with random state reproducibility."
    },
    "visualization_guidelines": {
        "trend": "Use Line Chart for continuous time series (dates/quarters).",
        "category_comparison": "Use Bar Chart for comparing aggregated values across categories.",
        "relationship": "Use Scatter Plot for bivariate continuous variable relationships.",
        "distribution": "Use Box Plot or Histogram for spread, quartiles, and outliers."
    },
    "reporting_guidelines": {
        "transparency": "Every finding must be supported by an empirical tool observation.",
        "actionability": "Recommendations must directly reference findings and statistical metrics."
    }
}

def chunk_markdown_text(text: str, source_name: str, target_chunk_size: int = 400, overlap: int = 50) -> List[Chunk]:
    """
    Chunks a Markdown document into semantic sections based on headers or paragraphs,
    targeting approximately 300-500 words with overlap.
    """
    chunks: List[Chunk] = []
    # Determine topic from filename
    topic = "general"
    if "stat" in source_name.lower():
        topic = "statistics"
    elif "ml" in source_name.lower():
        topic = "machine_learning"
    elif "viz" in source_name.lower():
        topic = "visualization"
    elif "report" in source_name.lower():
        topic = "reporting"

    # Split by markdown headers
    sections = re.split(r'\n(?=#{1,3}\s)', text)
    chunk_index = 0

    for section in sections:
        section = section.strip()
        if not section:
            continue

        words = section.split()
        if len(words) <= target_chunk_size:
            chunk_index += 1
            chunks.append(Chunk(
                chunk_id=f"{source_name}#chunk-{chunk_index}",
                text=section,
                source=source_name,
                topic=topic,
                metadata={"word_count": len(words), "section_header": words[0] if words else ""}
            ))
        else:
            # Sub-chunk with overlap
            for start in range(0, len(words), target_chunk_size - overlap):
                sub_words = words[start:start + target_chunk_size]
                chunk_index += 1
                chunks.append(Chunk(
                    chunk_id=f"{source_name}#chunk-{chunk_index}",
                    text=" ".join(sub_words),
                    source=source_name,
                    topic=topic,
                    metadata={"word_count": len(sub_words)}
                ))

    return chunks

class KnowledgeStore:
    """Vector database manager for methodology docs, data dictionaries, and session summaries."""

    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self._init_chroma()
        # In-memory data dictionary store per dataset
        self.data_dictionaries: Dict[str, Dict[str, str]] = {}
        # Ensure knowledge base is indexed
        self.index_knowledge_docs()

    def _init_chroma(self):
        try:
            import chromadb
            from chromadb.config import Settings
            self.chroma_client = chromadb.PersistentClient(path=self.persist_dir)
            self.doc_collection = self.chroma_client.get_or_create_collection("knowledge_docs")
            self.dict_collection = self.chroma_client.get_or_create_collection("data_dictionaries")
            self.sessions_collection = self.chroma_client.get_or_create_collection("past_sessions")
            self.use_chroma = True
        except Exception:
            # Fallback to in-memory store if Chroma initialization is unavailable
            self.use_chroma = False
            self._fallback_docs: List[Chunk] = []
            self._fallback_sessions: List[Chunk] = []

    def index_knowledge_docs(self, docs_dir: Optional[str] = None):
        """Indexes all markdown files in knowledge_docs directory into the vector store."""
        if not docs_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            docs_dir = os.path.join(base_dir, "knowledge_docs")

        if not os.path.exists(docs_dir):
            return

        md_files = glob.glob(os.path.join(docs_dir, "*.md"))
        all_chunks: List[Chunk] = []

        for fpath in md_files:
            fname = os.path.basename(fpath)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                chunks = chunk_markdown_text(content, source_name=fname)
                all_chunks.extend(chunks)
            except Exception:
                continue

        if not all_chunks:
            return

        if self.use_chroma:
            # Upsert into Chroma
            ids = [c.chunk_id for c in all_chunks]
            documents = [c.text for c in all_chunks]
            metadatas = [{"source": c.source, "topic": c.topic} for c in all_chunks]
            self.doc_collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        else:
            self._fallback_docs = all_chunks

    def retrieve(
        self,
        query: str,
        k: int = 4,
        filters: Optional[Dict[str, Any]] = None,
        collection_name: str = "knowledge_docs"
    ) -> List[Chunk]:
        """
        Retrieves top-k relevant knowledge chunks matching the analytical query.
        Returns a list of Chunk objects with text and source citations.
        """
        if self.use_chroma:
            coll = {
                "knowledge_docs": self.doc_collection,
                "data_dictionaries": self.dict_collection,
                "past_sessions": self.sessions_collection
            }.get(collection_name, self.doc_collection)

            try:
                results = coll.query(
                    query_texts=[query],
                    n_results=min(k, max(1, coll.count())),
                    where=filters
                )
                chunks: List[Chunk] = []
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"][0]
                    ids = results["ids"][0]
                    metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
                    distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(docs)

                    for c_id, text, meta, dist in zip(ids, docs, metas, distances):
                        chunks.append(Chunk(
                            chunk_id=c_id,
                            text=text,
                            source=meta.get("source", "knowledge_doc"),
                            topic=meta.get("topic", "general"),
                            metadata=meta,
                            score=float(dist)
                        ))
                return chunks
            except Exception:
                pass

        # Fallback keyword ranking if Chroma query fails or in fallback mode
        q_terms = set(re.findall(r'\w+', query.lower()))
        pool = self._fallback_sessions if collection_name == "past_sessions" else getattr(self, "_fallback_docs", [])
        scored = []
        for c in pool:
            score = sum(1 for w in q_terms if w in c.text.lower())
            if score > 0:
                scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:k]]

    def set_data_dictionary(self, dataset_id: str, definitions: Dict[str, str]):
        """Stores business definitions for dataset columns to clarify terms for the planner."""
        self.data_dictionaries[dataset_id] = definitions
        if self.use_chroma:
            for col_name, definition in definitions.items():
                chunk_id = f"dict_{dataset_id}_{col_name}"
                doc_text = f"Dataset Column '{col_name}': {definition}"
                self.dict_collection.upsert(
                    ids=[chunk_id],
                    documents=[doc_text],
                    metadatas=[{"dataset_id": dataset_id, "column": col_name, "source": "data_dictionary"}]
                )

    def get_data_dictionary(self, dataset_id: str) -> Dict[str, str]:
        """Returns the data dictionary mapping for a given dataset."""
        return self.data_dictionaries.get(dataset_id, {})

    def index_past_session(self, session_id: str, user_question: str, final_report: Dict[str, Any]):
        """Indexes key findings from past completed sessions for cross-session retrieval."""
        summary = final_report.get("executive_summary", "")
        findings = "; ".join(final_report.get("key_findings", []))
        doc_text = f"Session Question: '{user_question}'. Executive Summary: {summary}. Key Findings: {findings}"

        if self.use_chroma:
            self.sessions_collection.upsert(
                ids=[f"session_{session_id}"],
                documents=[doc_text],
                metadatas=[{"session_id": session_id, "user_question": user_question, "source": "past_session"}]
            )
        else:
            if not hasattr(self, "_fallback_sessions"):
                self._fallback_sessions = []
            self._fallback_sessions.append(Chunk(
                chunk_id=f"session_{session_id}",
                text=doc_text,
                source="past_session",
                topic="historical_analysis",
                metadata={"session_id": session_id}
            ))

# Global singleton
_KNOWLEDGE_STORE: Optional[KnowledgeStore] = None

def get_knowledge_store() -> KnowledgeStore:
    global _KNOWLEDGE_STORE
    if _KNOWLEDGE_STORE is None:
        _KNOWLEDGE_STORE = KnowledgeStore()
    return _KNOWLEDGE_STORE

def retrieve(query: str, k: int = 4, filters: Optional[Dict[str, Any]] = None) -> List[Chunk]:
    """Public helper to retrieve top-k knowledge chunks with source citations."""
    store = get_knowledge_store()
    return store.retrieve(query, k=k, filters=filters)

def retrieve_guidance_for_query(query: str, k: int = 4) -> tuple[str, List[str]]:
    """
    Retrieves knowledge chunks for a query and formats them as a prompt-ready guidance block
    and a list of unique source filenames for citation.
    """
    chunks = retrieve(query, k=k)
    if not chunks:
        return "", []

    text_blocks = []
    sources = set()
    for c in chunks:
        text_blocks.append(f"[{c.source}]: {c.text}")
        sources.add(c.source)

    guidance = "\n\n".join(text_blocks)
    return guidance, sorted(list(sources))

def get_methodology_guidance(topic: str) -> str:
    """Backward-compatible function retrieving guidance for legacy callers."""
    if topic in ANALYTICAL_KNOWLEDGE_BASE:
        return str(ANALYTICAL_KNOWLEDGE_BASE[topic])
    # Search RAG
    chunks = retrieve(topic, k=2)
    if chunks:
        return "\n\n".join([c.text for c in chunks])
    return str(ANALYTICAL_KNOWLEDGE_BASE)

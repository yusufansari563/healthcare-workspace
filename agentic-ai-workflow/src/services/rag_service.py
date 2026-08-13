import os
import glob
import logging
from typing import List, Dict, Any
from src.config import settings
from src.utils.token_optimizer import TokenOptimizer

logger = logging.getLogger(__name__)

class RAGService:
    """
    Local RAG vector store for indexing codebase and docs,
    allowing low-cost token-efficient context retrieval.
    """

    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.in_memory_docs: List[Dict[str, str]] = []
        self._init_vector_store()

    def _init_vector_store(self):
        try:
            import chromadb
            os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
            self.collection = self.chroma_client.get_or_create_collection(
                name="workspace_knowledge",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB persistent vector collection successfully initialized.")
        except Exception as e:
            logger.warning(f"Could not initialize ChromaDB ({e}). Using in-memory fallback RAG store.")

    def index_directory(self, root_dir: str, file_extensions: List[str] = [".py", ".md", ".json", ".txt", ".yml"]) -> Dict[str, Any]:
        """
        Scans and indexes files from root_dir into vector store.
        """
        indexed_count = 0
        documents = []
        metadatas = []
        ids = []

        for ext in file_extensions:
            pattern = os.path.join(root_dir, "**", f"*{ext}")
            for filepath in glob.glob(pattern, recursive=True):
                # Ignore venvs, git, node_modules
                if any(ignored in filepath for ignored in [".venv", "node_modules", ".git", "chroma_db", "__pycache__"]):
                    continue
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    
                    if not content.strip():
                        continue

                    # Chunk content if large
                    lines = content.splitlines()
                    chunk_size = 50
                    for i in range(0, len(lines), chunk_size):
                        chunk = "\n".join(lines[i:i+chunk_size])
                        rel_path = os.path.relpath(filepath, root_dir)
                        doc_id = f"{rel_path}_chunk_{i}"
                        
                        meta = {"file": rel_path, "start_line": i + 1}
                        
                        documents.append(chunk)
                        metadatas.append(meta)
                        ids.append(doc_id)
                        
                        self.in_memory_docs.append({"content": chunk, "file": rel_path})
                        indexed_count += 1
                except Exception as e:
                    logger.warning(f"Error reading file {filepath} for RAG: {e}")

        if self.collection and documents:
            try:
                # Upsert into ChromaDB in batches
                batch_size = 100
                for i in range(0, len(documents), batch_size):
                    self.collection.upsert(
                        documents=documents[i:i+batch_size],
                        metadatas=metadatas[i:i+batch_size],
                        ids=ids[i:i+batch_size]
                    )
                logger.info(f"Indexed {len(documents)} document chunks into ChromaDB.")
            except Exception as e:
                logger.warning(f"ChromaDB batch insertion failed ({e}), relying on in-memory store.")

        return {"status": "success", "chunks_indexed": indexed_count}

    def query_context(self, query: str, top_k: int = 3, max_tokens: int = 1000) -> str:
        """
        Retrieves relevant codebase context matching query and trims tokens.
        """
        retrieved_chunks = []

        if self.collection and self.collection.count() > 0:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=min(top_k, self.collection.count())
                )
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if "metadatas" in results else []
                    for d, m in zip(docs, metas):
                        file_name = m.get("file", "unknown") if isinstance(m, dict) else "unknown"
                        retrieved_chunks.append(f"--- File: {file_name} ---\n{d}")
            except Exception as e:
                logger.warning(f"ChromaDB query failed: {e}")

        # Fallback simple keyword search on in-memory docs if vector store returned empty
        if not retrieved_chunks and self.in_memory_docs:
            query_words = set(query.lower().split())
            matched = []
            for item in self.in_memory_docs:
                score = sum(1 for w in query_words if w in item["content"].lower())
                if score > 0:
                    matched.append((score, item))
            matched.sort(key=lambda x: x[0], reverse=True)
            for _, item in matched[:top_k]:
                retrieved_chunks.append(f"--- File: {item['file']} ---\n{item['content']}")

        combined_context = "\n\n".join(retrieved_chunks)
        if not combined_context:
            return "No specific codebase context found for this instruction."

        return TokenOptimizer.trim_context_window(combined_context, max_tokens=max_tokens)

# Global singleton
rag_service = RAGService()

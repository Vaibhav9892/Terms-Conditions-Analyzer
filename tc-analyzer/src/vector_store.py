"""
vector_store.py
Supports two embedding backends:
  - "openai"       → OpenAI text-embedding-3-small (paid)
  - "huggingface"  → all-MiniLM-L6-v2 (FREE, runs locally, no API key needed)
"""
from typing import List, Tuple, Literal
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


def _get_embeddings(provider: str, api_key: str = ""):
    if provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings
        # Downloads ~90MB model on first run, cached after that
        return HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
    else:  # openai
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)


class VectorStore:
    def __init__(self, provider: str = "huggingface", api_key: str = ""):
        self.embeddings = _get_embeddings(provider, api_key)
        self.db: FAISS | None = None

    def build(self, documents: List[Document]) -> None:
        self.db = FAISS.from_documents(documents, self.embeddings)

    def search(self, query: str, k: int = 5) -> List[Document]:
        if not self.db:
            raise RuntimeError("Vector store not built. Call build() first.")
        return self.db.similarity_search(query, k=k)

    def search_with_score(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        if not self.db:
            raise RuntimeError("Vector store not built.")
        return self.db.similarity_search_with_score(query, k=k)

    def get_context(self, query: str, k: int = 5) -> str:
        docs = self.search(query, k=k)
        return "\n\n---\n\n".join(d.page_content for d in docs)

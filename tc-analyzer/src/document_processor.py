"""
document_processor.py
Handles PDF/text loading and semantic chunking.
Compatible with LangChain v0.2+
"""
import io
from typing import List, Tuple
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter   # moved in v0.2
from langchain_core.documents import Document                          # moved in v0.2


class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
            length_function=len,
        )

    def load_pdf(self, file_bytes: bytes) -> str:
        text = ""
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n[Page {i+1}]\n{page_text}\n"
        return text.strip()

    def load_text(self, raw_text: str) -> str:
        return raw_text.strip()

    def chunk(self, text: str, source: str = "document") -> List[Document]:
        docs = [Document(page_content=text, metadata={"source": source, "total_length": len(text)})]
        chunks = self.text_splitter.split_documents(docs)
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["chunk_count"] = len(chunks)
        return chunks

    def process(
        self, content, source: str = "document", file_type: str = "text"
    ) -> Tuple[List[Document], str]:
        if file_type == "pdf":
            text = self.load_pdf(content)
        else:
            text = self.load_text(content)
        chunks = self.chunk(text, source)
        return chunks, text

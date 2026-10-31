import re
import pypdf
from pathlib import Path
from typing import List
from src.config import DATA_DIR

class PolicyRAG:

    def __init__(self, pdf_path: Path = DATA_DIR / "políticas_da_loja.pdf"):
        self.pdf_path = pdf_path
        self.chunks: List[str] = []
        self._load_and_chunk_pdf()

    def _load_and_chunk_pdf(self) -> None:
        if not self.pdf_path.exists():
            return

        reader = pypdf.PdfReader(self.pdf_path)
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

        normalized_text = " ".join(full_text.split())
        sections = re.split(r"(?=\b\d+\.\d+\s+[A-Z])", normalized_text)
        self.chunks = []

        for section in sections:
            section = section.strip()
            while len(section) > 1000:
                split_at = section.rfind(" ", 0, 1000)
                if split_at <= 0:
                    split_at = 1000
                self.chunks.append(section[:split_at].strip())
                section = section[split_at:].strip()

            if section:
                self.chunks.append(section)

    def search_policies(self, query: str, top_k: int = 3) -> str:
        query_terms = query.lower().split()
        scored_chunks = []

        for chunk in self.chunks:
            score = sum(1 for term in query_terms if term in chunk.lower())
            if score > 0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        results = [chunk for _, chunk in scored_chunks[:top_k]]

        if not results:
            return "No specific store policy found regarding this query."

        return "\n---\n".join(results)
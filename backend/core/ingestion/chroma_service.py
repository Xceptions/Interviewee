import uuid
import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
from core.config import settings


class ChromaService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_db_path)
        self.collection_name = settings.chroma_collection_name
        
        self.ollama_ef = OllamaEmbeddingFunction(
            url = settings.ollama_url,
            model_name = settings.ollama_model
        )
        
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.ollama_ef
        )

    def _chunk_text(self, text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> list[str]:
        """
        Splits raw text into sliding window chunks to preserve context sentences.
        """
        # Defensive check to prevent an accidental infinite loop if misconfigured
        if chunk_overlap >= chunk_size:
            chunk_overlap = chunk_size // 2

        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            chunks.append(text[start:end])
            start += (chunk_size - chunk_overlap)
            
        return chunks

    def ingest_resume(self, file_text: str, filename: str) -> str:
        """
        Chunks the text, assigns a unique candidate_id, stamps metadata, 
        and stores the vectors persistently.
        """
        # Unique candidate ID to prevent collisions across similar names
        clean_name = "".join([c if c.isalnum() else "_" for c in filename.split(".")[0]])
        candidate_id = f"{clean_name}_{uuid.uuid4().hex[:8]}"
        
        chunks = self._chunk_text(file_text)
        
        if not chunks:
            return candidate_id

        ids = [f"{candidate_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"candidate_id": candidate_id, "source_file": filename} for _ in chunks]
        
        self.collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )
        
        return candidate_id

    def query_resume_context(self, question: str, candidate_id: str, max_results: int = 3) -> list[str]:
        """
        Queries Chroma DB using metadata filtering to isolate exactly ONE resume.
        """
        results = self.collection.query(
            query_texts=[question],
            n_results=max_results,
            where={"candidate_id": candidate_id}
        )

        if results and "documents" in results and results["documents"]:
            return results["documents"][0]
            
        return []


chroma_service = ChromaService()

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import Optional, List, Tuple
import hashlib

from app.config import settings


class VectorStore:
    def __init__(self):
        self.client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="articles",
            metadata={"hnsw:space": "cosine"}
        )
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def generate_embedding(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()
    
    def generate_id(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()
    
    def check_duplicate(self, title: str, content: str) -> Tuple[bool, Optional[str], Optional[float]]:
        """Check if similar content exists. Returns (is_duplicate, existing_id, similarity_score)"""
        combined_text = f"{title} {content[:500]}"
        embedding = self.generate_embedding(combined_text)
        
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=1
        )
        
        if not results['ids'][0]:
            return False, None, None
        
        # ChromaDB returns distances, convert to similarity
        distance = results['distances'][0][0] if results['distances'][0] else 1.0
        similarity = 1 - distance  # Cosine similarity
        
        if similarity >= settings.similarity_threshold:
            return True, results['ids'][0][0], similarity
        
        return False, None, similarity
    
    def add_article(self, article_id: str, title: str, content: str, metadata: dict = None) -> str:
        """Add article to vector store"""
        combined_text = f"{title} {content[:500]}"
        embedding = self.generate_embedding(combined_text)
        
        self.collection.add(
            ids=[article_id],
            embeddings=[embedding],
            metadatas=[metadata or {}],
            documents=[combined_text]
        )
        
        return article_id
    
    def delete_article(self, article_id: str) -> bool:
        """Remove article from vector store"""
        try:
            self.collection.delete(ids=[article_id])
            return True
        except Exception:
            return False


vector_store = VectorStore()

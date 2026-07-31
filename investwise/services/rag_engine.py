"""
RAG Engine Service for InvestWise AI 3.0.
Manages ChromaDB vector store and semantic search capabilities.
"""

import logging
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from django.conf import settings

logger = logging.getLogger('investwise')

_CHROMA_CLIENT = None

def get_chroma_client() -> chromadb.PersistentClient:
    """
    Get or create a singleton ChromaDB PersistentClient.
    """
    global _CHROMA_CLIENT
    if _CHROMA_CLIENT is None:
        try:
            persist_dir = getattr(settings, 'CHROMADB_PERSIST_DIR', './chroma_db')
            logger.info(f"Initializing ChromaDB client at {persist_dir}")
            _CHROMA_CLIENT = chromadb.PersistentClient(path=persist_dir)
        except Exception as e:
            logger.error(f"Error initializing ChromaDB client: {e}")
            raise e
    return _CHROMA_CLIENT

def _get_embedding_function():
    """
    Get the sentence-transformers embedding function.
    """
    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

def get_or_create_collection(name: str) -> chromadb.Collection:
    """
    Get or create a named collection.
    """
    client = get_chroma_client()
    try:
        collection = client.get_or_create_collection(
            name=name,
            embedding_function=_get_embedding_function()
        )
        return collection
    except Exception as e:
        logger.error(f"Error creating/getting collection {name}: {e}")
        raise e

def ingest_document(text_chunks: list[str], metadata: dict, collection_name: str) -> int:
    """
    Embed chunks and upsert to ChromaDB. Returns the number of chunks ingested.
    """
    if not text_chunks:
        return 0
        
    try:
        collection = get_or_create_collection(collection_name)
        
        ids = [f"{metadata.get('doc_id', 'doc')}_chunk_{i}" for i in range(len(text_chunks))]
        metadatas = [metadata for _ in range(len(text_chunks))]
        
        collection.upsert(
            documents=text_chunks,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Successfully ingested {len(text_chunks)} chunks into {collection_name}")
        return len(text_chunks)
    except Exception as e:
        logger.error(f"Error ingesting document into {collection_name}: {e}")
        return 0

def query_documents(query: str, collection_name: str, n_results: int = 5, where_filter: dict = None) -> list[dict]:
    """
    Semantic search with optional metadata filtering.
    """
    try:
        collection = get_or_create_collection(collection_name)
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )
        
        formatted_results = []
        if results and results.get('documents') and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results.get('metadatas') else {},
                    "distance": results['distances'][0][i] if results.get('distances') else None,
                    "id": results['ids'][0][i] if results.get('ids') else None
                })
                
        return formatted_results
    except Exception as e:
        logger.error(f"Error querying collection {collection_name}: {e}")
        return []

def delete_collection(name: str) -> bool:
    """
    Remove a collection.
    """
    client = get_chroma_client()
    try:
        client.delete_collection(name=name)
        logger.info(f"Deleted collection {name}")
        return True
    except Exception as e:
        logger.error(f"Error deleting collection {name}: {e}")
        return False

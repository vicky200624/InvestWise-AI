"""
RAG Engine Service for InvestWise AI 3.0.
Manages ChromaDB vector store and semantic search capabilities.
"""

import logging
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional

logger = logging.getLogger('investwise.ai.rag_engine')

_CHROMA_CLIENT = None
_PERSIST_DIR = None

def get_chroma_client(persist_dir: str = './chroma_db') -> chromadb.PersistentClient:
    """
    Get or create a singleton ChromaDB PersistentClient.
    """
    global _CHROMA_CLIENT
    global _PERSIST_DIR
    if _CHROMA_CLIENT is None or _PERSIST_DIR != persist_dir:
        try:
            logger.info(f"Initializing ChromaDB client at {persist_dir}")
            _CHROMA_CLIENT = chromadb.PersistentClient(path=persist_dir)
            _PERSIST_DIR = persist_dir
        except Exception as e:
            logger.error(f"Error initializing ChromaDB client: {e}")
            raise e
    return _CHROMA_CLIENT

def _get_embedding_function():
    """
    Get the sentence-transformers embedding function.
    """
    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

def get_or_create_collection(name: str, persist_dir: str = './chroma_db') -> chromadb.Collection:
    """
    Get or create a named collection.
    """
    client = get_chroma_client(persist_dir)
    try:
        collection = client.get_or_create_collection(
            name=name,
            embedding_function=_get_embedding_function()
        )
        return collection
    except Exception as e:
        logger.error(f"Error creating/getting collection {name}: {e}")
        raise e

def ingest_document(text_chunks: List[str], metadata: Dict[str, Any], collection_name: str, persist_dir: str = './chroma_db') -> int:
    """
    Embed chunks and upsert to ChromaDB. Returns the number of chunks ingested.
    """
    if not text_chunks:
        return 0
        
    try:
        collection = get_or_create_collection(collection_name, persist_dir)
        
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

def query_documents(query: str, collection_name: str, n_results: int = 5, where_filter: Optional[Dict[str, Any]] = None, persist_dir: str = './chroma_db') -> List[Dict[str, Any]]:
    """
    Semantic search with optional metadata filtering, relevance ranking, and chunk deduplication.
    Supports future migration to Pinecone/Weaviate/Milvus interfaces.
    """
    try:
        collection = get_or_create_collection(collection_name, persist_dir)
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results * 2,  # Query extra for deduplication
            where=where_filter
        )
        
        formatted_results = []
        seen_texts = set()
        if results and results.get('documents') and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                doc_text = results['documents'][0][i]
                # Remove duplicate chunks
                doc_hash = doc_text.strip()[:150]
                if doc_hash in seen_texts:
                    continue
                seen_texts.add(doc_hash)

                formatted_results.append({
                    "document": doc_text,
                    "metadata": results['metadatas'][0][i] if results.get('metadatas') else {},
                    "distance": results['distances'][0][i] if results.get('distances') else None,
                    "id": results['ids'][0][i] if results.get('ids') else None
                })
                if len(formatted_results) >= n_results:
                    break
                
        # Rank by distance (relevance ascending for distance)
        formatted_results.sort(key=lambda x: x['distance'] if x['distance'] is not None else 999.0)
        return formatted_results
    except Exception as e:
        logger.error(f"Error querying collection {collection_name}: {e}")
        return []

def delete_collection(name: str, persist_dir: str = './chroma_db') -> bool:
    """
    Remove a collection.
    """
    client = get_chroma_client(persist_dir)
    try:
        client.delete_collection(name=name)
        logger.info(f"Deleted collection {name}")
        return True
    except Exception as e:
        logger.error(f"Error deleting collection {name}: {e}")
        return False

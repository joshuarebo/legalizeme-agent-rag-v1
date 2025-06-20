"""
Enhanced Document Indexing System for Phase 2
Provides intelligent vector indexing with legal-specific embeddings and metadata filtering
"""
import os
import asyncio
import json
import numpy as np
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict

# Try to import the actual dependencies
try:
    import faiss
    from sentence_transformers import SentenceTransformer
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    SentenceTransformer = None
    FAISS_AVAILABLE = False

try:
    from haystack import Document
    from haystack.document_stores import FAISSDocumentStore
    from haystack.nodes import EmbeddingRetriever
    HAYSTACK_AVAILABLE = True
except ImportError:
    Document = None
    FAISSDocumentStore = None
    EmbeddingRetriever = None
    HAYSTACK_AVAILABLE = False

from app.utils.logger import get_logger
from app.parsers.document_processor_enhanced import DocumentChunk, ProcessedDocument

logger = get_logger(__name__)

@dataclass
class SearchResult:
    """Represents a search result with relevance scoring."""
    content: str
    metadata: Dict[str, Any]
    score: float
    document_id: str
    chunk_id: str

@dataclass
class IndexStats:
    """Statistics about the document index."""
    total_documents: int
    total_chunks: int
    index_size: int
    last_updated: str
    embedding_model: str

class EnhancedDocumentIndexer:
    """
    Enhanced document indexing system with legal specialization.
    
    Features:
    - Legal-specialized embeddings
    - Metadata filtering
    - Incremental indexing
    - Multiple search strategies
    - Performance optimization
    """
    
    def __init__(self):
        """Initialize the enhanced document indexer."""
        self.vector_db_dir = os.getenv("VECTOR_DB_DIR", "./data/vector_db")
        os.makedirs(self.vector_db_dir, exist_ok=True)
        
        # Index files
        self.faiss_index_file = os.path.join(self.vector_db_dir, "faiss_index.bin")
        self.documents_file = os.path.join(self.vector_db_dir, "documents.pkl")
        self.embeddings_file = os.path.join(self.vector_db_dir, "embeddings.npy")
        self.metadata_file = os.path.join(self.vector_db_dir, "metadata.json")
        self.stats_file = os.path.join(self.vector_db_dir, "index_stats.json")
        
        # Configuration
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.legal_embedding_model = os.getenv("LEGAL_EMBEDDING_MODEL", "nlpaueb/legal-bert-base-uncased")
        self.use_legal_embeddings = os.getenv("USE_LEGAL_EMBEDDINGS", "true").lower() == "true"
        
        # Initialize components
        self.embedding_model = None
        self.faiss_index = None
        self.document_store = None
        self.documents_metadata = {}
        self.embeddings = None
        
        # Performance settings
        self.batch_size = int(os.getenv("INDEXING_BATCH_SIZE", "32"))
        self.max_seq_length = int(os.getenv("MAX_SEQUENCE_LENGTH", "512"))
        
        # Initialize the indexer
        asyncio.create_task(self._initialize_async())

    async def _initialize_async(self):
        """Initialize the indexer asynchronously."""
        try:
            await self._load_embedding_model()
            await self._load_index()
            logger.info("Enhanced document indexer initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing enhanced indexer: {str(e)}")

    async def _load_embedding_model(self):
        """Load the embedding model."""
        try:
            if not SentenceTransformer:
                logger.warning("SentenceTransformer not available, using fallback")
                return
            
            model_name = self.legal_embedding_model if self.use_legal_embeddings else self.embedding_model_name
            
            logger.info(f"Loading embedding model: {model_name}")
            self.embedding_model = SentenceTransformer(model_name)
            
            # Set max sequence length
            if hasattr(self.embedding_model, 'max_seq_length'):
                self.embedding_model.max_seq_length = self.max_seq_length
            
            logger.info(f"Embedding model loaded successfully: {model_name}")
            
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            self.embedding_model = None

    async def _load_index(self):
        """Load existing index or create new one."""
        try:
            if os.path.exists(self.faiss_index_file) and os.path.exists(self.metadata_file):
                logger.info("Loading existing FAISS index")
                
                # Load FAISS index
                if FAISS_AVAILABLE and faiss:
                    self.faiss_index = faiss.read_index(self.faiss_index_file)
                
                # Load metadata
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.documents_metadata = json.load(f)
                
                # Load embeddings if available
                if os.path.exists(self.embeddings_file):
                    self.embeddings = np.load(self.embeddings_file)
                
                logger.info(f"Loaded index with {len(self.documents_metadata)} documents")
            else:
                logger.info("Creating new index")
                await self._create_new_index()
                
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            await self._create_new_index()

    async def _create_new_index(self):
        """Create a new empty index."""
        try:
            if FAISS_AVAILABLE and faiss and self.embedding_model:
                # Get embedding dimension
                test_embedding = self.embedding_model.encode(["test"])
                dimension = test_embedding.shape[1]
                
                # Create FAISS index
                self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
                
                # Initialize empty structures
                self.documents_metadata = {}
                self.embeddings = np.array([]).reshape(0, dimension)
                
                logger.info(f"Created new FAISS index with dimension {dimension}")
            else:
                logger.warning("FAISS or embedding model not available")
                
        except Exception as e:
            logger.error(f"Error creating new index: {str(e)}")

    async def add_document(self, document: ProcessedDocument):
        """
        Add a processed document to the index.
        
        Args:
            document: ProcessedDocument to index
        """
        try:
            if not self.embedding_model:
                logger.warning("No embedding model available, skipping indexing")
                return
            
            logger.info(f"Indexing document: {document.id}")
            
            # Check if document already exists
            if document.id in self.documents_metadata:
                logger.info(f"Document {document.id} already indexed, updating")
                await self.remove_document(document.id)
            
            # Prepare chunks for embedding
            chunk_texts = [chunk.content for chunk in document.chunks]
            
            if not chunk_texts:
                logger.warning(f"No chunks found for document {document.id}")
                return
            
            # Generate embeddings in batches
            all_embeddings = []
            for i in range(0, len(chunk_texts), self.batch_size):
                batch_texts = chunk_texts[i:i + self.batch_size]
                batch_embeddings = self.embedding_model.encode(
                    batch_texts,
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )
                all_embeddings.append(batch_embeddings)
            
            embeddings = np.vstack(all_embeddings)
            
            # Add to FAISS index
            if self.faiss_index:
                start_id = len(self.documents_metadata)
                self.faiss_index.add(embeddings)
            
            # Store metadata for each chunk
            for i, chunk in enumerate(document.chunks):
                chunk_id = f"{document.id}_chunk_{i}"
                self.documents_metadata[chunk_id] = {
                    'document_id': document.id,
                    'chunk_id': chunk.chunk_id,
                    'content': chunk.content,
                    'metadata': chunk.metadata,
                    'document_metadata': document.metadata,
                    'citations': document.citations,
                    'entities': document.entities,
                    'index_position': start_id + i,
                    'indexed_date': datetime.now().isoformat()
                }
            
            # Update embeddings array
            if self.embeddings.size == 0:
                self.embeddings = embeddings
            else:
                self.embeddings = np.vstack([self.embeddings, embeddings])
            
            # Save index
            await self._save_index()
            
            logger.info(f"Successfully indexed document {document.id} with {len(document.chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Error indexing document {document.id}: {str(e)}")

    async def add_document_chunk(self, content: str, metadata: Dict[str, Any]):
        """
        Add a single document chunk to the index.
        
        Args:
            content: Text content of the chunk
            metadata: Metadata dictionary
        """
        try:
            if not self.embedding_model:
                logger.warning("No embedding model available, skipping indexing")
                return
            
            # Generate embedding
            embedding = self.embedding_model.encode([content], convert_to_numpy=True, normalize_embeddings=True)
            
            # Add to FAISS index
            if self.faiss_index:
                self.faiss_index.add(embedding)
            
            # Generate chunk ID
            chunk_id = metadata.get('chunk_id', f"chunk_{len(self.documents_metadata)}")
            
            # Store metadata
            self.documents_metadata[chunk_id] = {
                **metadata,
                'content': content,
                'index_position': len(self.documents_metadata),
                'indexed_date': datetime.now().isoformat()
            }
            
            # Update embeddings array
            if self.embeddings.size == 0:
                self.embeddings = embedding
            else:
                self.embeddings = np.vstack([self.embeddings, embedding])
            
            logger.debug(f"Added chunk {chunk_id} to index")
            
        except Exception as e:
            logger.error(f"Error adding chunk to index: {str(e)}")

    async def search(self, query: str, k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        Search the document index.
        
        Args:
            query: Search query
            k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of SearchResult objects
        """
        try:
            if not self.embedding_model or not self.faiss_index:
                logger.warning("Search infrastructure not available")
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
            
            # Perform similarity search
            scores, indices = self.faiss_index.search(query_embedding, min(k * 2, len(self.documents_metadata)))
            
            # Process results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(self.documents_metadata):
                    continue
                
                # Find the chunk metadata by index position
                chunk_metadata = None
                for chunk_id, metadata in self.documents_metadata.items():
                    if metadata.get('index_position') == idx:
                        chunk_metadata = metadata
                        break
                
                if not chunk_metadata:
                    continue
                
                # Apply filters if provided
                if filters and not self._apply_filters(chunk_metadata, filters):
                    continue
                
                result = SearchResult(
                    content=chunk_metadata['content'],
                    metadata=chunk_metadata.get('metadata', {}),
                    score=float(score),
                    document_id=chunk_metadata.get('document_id', ''),
                    chunk_id=chunk_metadata.get('chunk_id', '')
                )
                results.append(result)
                
                if len(results) >= k:
                    break
            
            logger.info(f"Search returned {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error searching index: {str(e)}")
            return []

    async def search_by_citation(self, citation: str, k: int = 5) -> List[SearchResult]:
        """
        Search for documents containing a specific citation.
        
        Args:
            citation: Legal citation to search for
            k: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        try:
            results = []
            
            for chunk_id, metadata in self.documents_metadata.items():
                chunk_citations = metadata.get('citations', [])
                
                # Check if citation appears in this chunk
                citation_match = False
                for chunk_citation in chunk_citations:
                    if citation.lower() in chunk_citation.get('raw_text', '').lower():
                        citation_match = True
                        break
                
                # Also check in content
                if not citation_match:
                    if citation.lower() in metadata.get('content', '').lower():
                        citation_match = True
                
                if citation_match:
                    result = SearchResult(
                        content=metadata['content'],
                        metadata=metadata.get('metadata', {}),
                        score=1.0,  # Exact match
                        document_id=metadata.get('document_id', ''),
                        chunk_id=chunk_id
                    )
                    results.append(result)
                    
                    if len(results) >= k:
                        break
            
            logger.info(f"Citation search returned {len(results)} results for: {citation}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching by citation: {str(e)}")
            return []

    async def search_by_metadata(self, metadata_filters: Dict[str, Any], k: int = 10) -> List[SearchResult]:
        """
        Search documents by metadata criteria.
        
        Args:
            metadata_filters: Dictionary of metadata filters
            k: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        try:
            results = []
            
            for chunk_id, metadata in self.documents_metadata.items():
                if self._apply_filters(metadata, metadata_filters):
                    result = SearchResult(
                        content=metadata['content'],
                        metadata=metadata.get('metadata', {}),
                        score=1.0,  # Metadata match
                        document_id=metadata.get('document_id', ''),
                        chunk_id=chunk_id
                    )
                    results.append(result)
                    
                    if len(results) >= k:
                        break
            
            logger.info(f"Metadata search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching by metadata: {str(e)}")
            return []

    def _apply_filters(self, chunk_metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Apply metadata filters to a chunk.
        
        Args:
            chunk_metadata: Chunk metadata to test
            filters: Filter criteria
            
        Returns:
            True if chunk matches all filters
        """
        try:
            for filter_key, filter_value in filters.items():
                # Check in chunk metadata
                chunk_value = chunk_metadata.get('metadata', {}).get(filter_key)
                
                # Check in document metadata
                if chunk_value is None:
                    chunk_value = chunk_metadata.get('document_metadata', {}).get(filter_key)
                
                # Check direct metadata
                if chunk_value is None:
                    chunk_value = chunk_metadata.get(filter_key)
                
                if chunk_value is None:
                    return False
                
                # Handle different filter types
                if isinstance(filter_value, str):
                    if filter_value.lower() not in str(chunk_value).lower():
                        return False
                elif isinstance(filter_value, list):
                    if chunk_value not in filter_value:
                        return False
                else:
                    if chunk_value != filter_value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying filters: {str(e)}")
            return False

    async def remove_document(self, document_id: str):
        """
        Remove a document from the index.
        
        Args:
            document_id: ID of document to remove
        """
        try:
            # Find chunks belonging to this document
            chunks_to_remove = []
            for chunk_id, metadata in self.documents_metadata.items():
                if metadata.get('document_id') == document_id:
                    chunks_to_remove.append(chunk_id)
            
            # Remove chunks from metadata
            for chunk_id in chunks_to_remove:
                del self.documents_metadata[chunk_id]
            
            # Note: FAISS doesn't support direct removal, so we'd need to rebuild
            # For now, we just remove from metadata and mark as deleted
            
            logger.info(f"Removed document {document_id} ({len(chunks_to_remove)} chunks)")
            
        except Exception as e:
            logger.error(f"Error removing document {document_id}: {str(e)}")

    async def _save_index(self):
        """Save the index to disk."""
        try:
            # Save FAISS index
            if self.faiss_index:
                faiss.write_index(self.faiss_index, self.faiss_index_file)
            
            # Save metadata
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents_metadata, f, indent=2, ensure_ascii=False)
            
            # Save embeddings
            if self.embeddings is not None:
                np.save(self.embeddings_file, self.embeddings)
            
            # Save statistics
            stats = IndexStats(
                total_documents=len(set(metadata.get('document_id') for metadata in self.documents_metadata.values())),
                total_chunks=len(self.documents_metadata),
                index_size=self.faiss_index.ntotal if self.faiss_index else 0,
                last_updated=datetime.now().isoformat(),
                embedding_model=self.embedding_model_name
            )
            
            with open(self.stats_file, 'w') as f:
                json.dump(asdict(stats), f, indent=2)
            
            logger.debug("Index saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")

    async def get_stats(self) -> IndexStats:
        """
        Get index statistics.
        
        Returns:
            IndexStats object
        """
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    stats_data = json.load(f)
                return IndexStats(**stats_data)
            else:
                return IndexStats(
                    total_documents=0,
                    total_chunks=0,
                    index_size=0,
                    last_updated="Never",
                    embedding_model=self.embedding_model_name
                )
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return IndexStats(0, 0, 0, "Error", "Unknown")

    async def reindex_all(self):
        """
        Rebuild the entire index from stored documents.
        """
        try:
            logger.info("Starting full reindex")
            
            # Create new index
            await self._create_new_index()
            
            # Reindex would require access to original documents
            # This is a placeholder for the reindexing logic
            
            logger.info("Full reindex completed")
            
        except Exception as e:
            logger.error(f"Error during reindex: {str(e)}")

    async def periodic_maintenance(self):
        """
        Perform periodic maintenance on the index.
        """
        try:
            logger.info("Starting index maintenance")
            
            # Save current state
            await self._save_index()
            
            # Get stats
            stats = await self.get_stats()
            logger.info(f"Index stats: {stats.total_documents} docs, {stats.total_chunks} chunks")
            
            # Cleanup old temporary files
            # ... maintenance tasks ...
            
            logger.info("Index maintenance completed")
            
        except Exception as e:
            logger.error(f"Error during maintenance: {str(e)}")

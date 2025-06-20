"""
Kenya Law Retriever - RAG component for retrieving legal documents from Kenya Law
"""
import os
import pickle
import json
from typing import List, Dict, Any, Optional
import asyncio
import httpx
from dotenv import load_dotenv
from langchain.schema import Document
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Import the stub implementations directly for now
from app.utils.stubs.haystack.document_stores.faiss import FAISSDocumentStore
from app.utils.stubs.haystack.document_stores.weaviate import WeaviateDocumentStore
from app.utils.stubs.haystack.nodes import EmbeddingRetriever
from app.utils.stubs.haystack.pipelines import DocumentSearchPipeline
USING_STUBS = True

from app.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

class KenyaLawRetriever:
    """
    Retriever for Kenyan legal documents using vector search.
    
    This retriever uses either FAISS directly or through Haystack,
    and maintains specialized indexes for different legal document types.
    """
    
    def __init__(self):
        """Initialize the retriever with the configured vector DB."""
        self.vector_db_type = os.getenv("VECTOR_DB_TYPE", "faiss")
        self.vector_db_path = os.getenv("VECTOR_DB_PATH", "./data/vector_db")
        os.makedirs(self.vector_db_path, exist_ok=True)
        
        # Initialize embedding model
        self.embedding_model = self._initialize_embedding_model()
        self.embedding_dim = 768  # mpnet base model dimension
        
        if USING_STUBS:
            logger.warning("Using stub implementation for vector search")
            self.document_store = FAISSDocumentStore()
            self.retriever = EmbeddingRetriever(document_store=self.document_store)
            self.use_direct_faiss = True
            self._initialize_direct_faiss()
        else:
            logger.info(f"Initializing {self.vector_db_type} document store")
            self.document_store = self._initialize_document_store()
            self.retriever = self._initialize_retriever()
            self.pipeline = DocumentSearchPipeline(retriever=self.retriever)
            self.use_direct_faiss = self.vector_db_type.lower() == "direct_faiss"
            
            if self.use_direct_faiss:
                self._initialize_direct_faiss()
        
        # Ensure document store is loaded
        asyncio.create_task(self._ensure_document_store())
    
    def _initialize_embedding_model(self):
        """Initialize the sentence transformer model for embeddings."""
        try:
            model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
            logger.info(f"Loading embedding model: {model_name}")
            return SentenceTransformer(model_name)
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            logger.warning("Will attempt to download model or use smaller fallback")
            try:
                # Try a smaller model as fallback
                fallback_model = "sentence-transformers/all-MiniLM-L6-v2"
                logger.info(f"Loading fallback embedding model: {fallback_model}")
                return SentenceTransformer(fallback_model)
            except Exception as e2:
                logger.error(f"Error loading fallback model: {str(e2)}")
                return None
    
    def _initialize_direct_faiss(self):
        """Initialize FAISS directly when not using Haystack."""
        self.faiss_index_path = os.path.join(self.vector_db_path, "faiss_index.bin")
        self.docs_path = os.path.join(self.vector_db_path, "documents.pkl")
        self.doc_embeddings_path = os.path.join(self.vector_db_path, "embeddings.npy")
        
        # Check if index exists, otherwise create it
        if os.path.exists(self.faiss_index_path) and os.path.exists(self.docs_path):
            logger.info("Loading existing FAISS index")
            try:
                self.index = faiss.read_index(self.faiss_index_path)
                with open(self.docs_path, 'rb') as f:
                    self.documents = pickle.load(f)
                if os.path.exists(self.doc_embeddings_path):
                    self.doc_embeddings = np.load(self.doc_embeddings_path)
                else:
                    self.doc_embeddings = None
                logger.info(f"Loaded FAISS index with {len(self.documents)} documents")
            except Exception as e:
                logger.error(f"Error loading FAISS index: {str(e)}")
                self._create_new_faiss_index()
        else:
            self._create_new_faiss_index()
    
    def _create_new_faiss_index(self):
        """Create a new FAISS index."""
        logger.info("Creating new FAISS index")
        self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product similarity (cosine)
        self.documents = []
        self.doc_embeddings = None
            
    def _save_direct_faiss(self):
        """Save FAISS index and documents to disk."""
        if self.use_direct_faiss:
            try:
                logger.info("Saving FAISS index and documents")
                os.makedirs(os.path.dirname(self.faiss_index_path), exist_ok=True)
                faiss.write_index(self.index, self.faiss_index_path)
                with open(self.docs_path, 'wb') as f:
                    pickle.dump(self.documents, f)
                if self.doc_embeddings is not None:
                    np.save(self.doc_embeddings_path, self.doc_embeddings)
                logger.info(f"Saved FAISS index with {len(self.documents)} documents")
            except Exception as e:
                logger.error(f"Error saving FAISS index: {str(e)}")
    
    def _initialize_document_store(self):
        """Initialize the document store based on the configured type."""
        if self.vector_db_type.lower() == "weaviate":
            # Use Weaviate if configured
            weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
            try:
                return WeaviateDocumentStore(
                    weaviate_url=weaviate_url,
                    index="KenyaLaw",
                    embedding_dim=self.embedding_dim,
                    similarity="cosine"
                )
            except Exception as e:
                logger.error(f"Error initializing Weaviate: {str(e)}")
                logger.warning("Falling back to FAISS document store")
                # Fall back to FAISS
                return self._initialize_faiss_document_store()
        else:
            # Default to FAISS
            return self._initialize_faiss_document_store()
    
    def _initialize_faiss_document_store(self):
        """Initialize the FAISS document store."""
        try:
            db_path = os.path.join(self.vector_db_path, "faiss_document_store.db")
            index_path = os.path.join(self.vector_db_path, "faiss_index.faiss")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Use SQLite URL with proper format for Windows
            sql_url = f"sqlite:///{db_path}"
            
            return FAISSDocumentStore(
                sql_url=sql_url,
                faiss_index_path=index_path if os.path.exists(index_path) else None,
                embedding_dim=self.embedding_dim,
                return_embedding=True,
                similarity="cosine"
            )
        except Exception as e:
            logger.error(f"Error initializing FAISS document store: {str(e)}")
            # Return a minimal document store that will at least not crash
            return FAISSDocumentStore(
                embedding_dim=self.embedding_dim,
                return_embedding=True,
                similarity="cosine"
            )
    
    def _initialize_retriever(self):
        """Initialize the embedding retriever."""
        model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
        try:
            return EmbeddingRetriever(
                document_store=self.document_store,
                embedding_model=model_name,
                model_format="sentence_transformers",
                top_k=10
            )
        except Exception as e:
            logger.error(f"Error initializing retriever with model {model_name}: {str(e)}")
            logger.warning("Falling back to default embedding model")
            
            # Try with a smaller model
            try:
                return EmbeddingRetriever(
                    document_store=self.document_store,
                    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                    model_format="sentence_transformers",
                    top_k=10
                )
            except Exception as e2:
                logger.error(f"Error initializing retriever with fallback model: {str(e2)}")
                # Return a minimal retriever that will at least not crash
                return EmbeddingRetriever(
                    document_store=self.document_store,
                    top_k=10
                )
    
    async def _ensure_document_store(self):
        """
        Ensure the document store is loaded or initialized.
        In a production system, this would check if the DB exists
        and either use it or trigger an indexing process.
        """
        try:
            if self.use_direct_faiss:
                # Check if we have documents in our direct FAISS implementation
                if len(self.documents) == 0:
                    logger.info("FAISS index is empty. Initializing with sample data.")
                    await self._initialize_with_sample_data()
                else:
                    logger.info(f"FAISS index already contains {len(self.documents)} documents.")
            else:
                # Check if the Haystack document store has documents
                doc_count = self.document_store.get_document_count()
                if doc_count == 0:
                    logger.info("Document store is empty. Initializing with sample data.")
                    await self._initialize_with_sample_data()
                else:
                    logger.info(f"Document store already contains {doc_count} documents.")
        except Exception as e:
            logger.error(f"Error checking document store: {str(e)}")
            # Initialize with sample data as fallback
            await self._initialize_with_sample_data()
    
    async def _initialize_with_sample_data(self):
        """
        Initialize the document store with sample data.
        In a real implementation, this would fetch data from Kenya Law API.
        """
        # Sample legal documents
        sample_docs = [
            {
                "content": "The Constitution of Kenya is the supreme law of the Republic of Kenya. It establishes the structure of the Kenyan government, and also defines the relationship between the government and the citizens of Kenya.",
                "meta": {
                    "source": "https://new.kenyalaw.org/akn/ke/act/2010/constitution/eng@2010-09-03",
                    "title": "Constitution of Kenya",
                    "type": "constitution",
                    "date": "2010-09-03"
                }
            },
            {
                "content": "The Employment Act establishes the fundamental principles of employment in Kenya. It provides for minimum terms and conditions of employment, and regulates the relationship between employers and employees.",
                "meta": {
                    "source": "https://new.kenyalaw.org/legislation/employment-act-cap-226/",
                    "title": "Employment Act",
                    "type": "legislation",
                    "date": "2007-10-26"
                }
            },
            {
                "content": "The Children Act provides for parental responsibility, fostering, adoption, custody, maintenance, guardianship, care and protection of children. It gives effect to the principles of the Convention on the Rights of the Child and the African Charter on the Rights and Welfare of the Child.",
                "meta": {
                    "source": "https://new.kenyalaw.org/legislation/children-act-no-8-of-2001/",
                    "title": "Children Act",
                    "type": "legislation",
                    "date": "2001-01-31"
                }
            },
            {
                "content": "The Law of Contract Act establishes the legal framework for contracts in Kenya. It provides for the formation, validity, performance, and discharge of contracts.",
                "meta": {
                    "source": "https://new.kenyalaw.org/legislation/law-of-contract-act-cap-23/",
                    "title": "Law of Contract Act",
                    "type": "legislation",
                    "date": "2012-01-01"
                }
            },
            {
                "content": "The Land Act provides for the sustainable administration and management of land and land-based resources, and for connected purposes.",
                "meta": {
                    "source": "https://new.kenyalaw.org/legislation/land-act-no-6-of-2012/",
                    "title": "Land Act",
                    "type": "legislation",
                    "date": "2012-05-02"
                }
            },
            {
                "content": "REPUBLIC OF KENYA IN THE HIGH COURT OF KENYA AT NAIROBI CONSTITUTIONAL AND HUMAN RIGHTS DIVISION PETITION NO. E282 OF 2020 KATIBA INSTITUTE.....................................................PETITIONER VERSUS THE CHIEF JUSTICE OF THE REPUBLIC OF KENYA..........1ST RESPONDENT THE JUDICIAL SERVICE COMMISSION........................2ND RESPONDENT THE ATTORNEY GENERAL.........................................3RD RESPONDENT JUDGMENT. The Petitioner, Katiba Institute, is a non-governmental organization registered under the Non-Governmental Organizations Co-ordination Act. It filed the present petition dated 14th July 2020 pursuant to the provisions of Articles 2(1), 2(4), 3(1), 10, 19, 20, 22, 23, 47, 73, 165(3)(b), (d), 258 and 259 of the Constitution of Kenya, 2010. The petition is supported by an affidavit sworn by Waikwa Wanyoike, the former Executive Director of the Petitioner, on 14th July 2020.",
                "meta": {
                    "source": "https://new.kenyalaw.org/judgments/KATIBA_INSTITUTE_V_CHIEF_JUSTICE_OF_THE_REPUBLIC_OF_KENYA_&_2_OTHERS_[2022]_eKLR.pdf",
                    "title": "Katiba Institute v Chief Justice of the Republic of Kenya & 2 others [2022] eKLR",
                    "type": "judgment",
                    "date": "2022-01-26"
                }
            }
        ]
        
        try:
            if self.use_direct_faiss:
                await self._add_documents_to_direct_faiss(sample_docs)
            else:
                # Convert to Haystack documents
                haystack_docs = []
                for doc in sample_docs:
                    haystack_docs.append(
                        Document(
                            content=doc["content"],
                            meta=doc["meta"]
                        )
                    )
                
                # Add to document store
                self.document_store.write_documents(haystack_docs)
                
                # Update embeddings
                if self.embedding_model is not None:
                    try:
                        self.document_store.update_embeddings(self.retriever)
                        logger.info(f"Updated embeddings for {len(haystack_docs)} documents")
                    except Exception as e:
                        logger.error(f"Error updating embeddings: {str(e)}")
                
                logger.info(f"Added {len(haystack_docs)} documents to document store")
        except Exception as e:
            logger.error(f"Error initializing with sample data: {str(e)}")
    
    async def _add_documents_to_direct_faiss(self, documents):
        """Add documents to the FAISS index directly."""
        if not self.embedding_model:
            logger.error("Embedding model not initialized")
            return
        
        try:
            # Convert documents to the required format and calculate embeddings
            texts = [doc["content"] for doc in documents]
            embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add to FAISS index
            self.index.add(embeddings)
            
            # Store documents and embeddings
            start_idx = len(self.documents)
            for i, doc in enumerate(documents):
                doc["id"] = start_idx + i
                self.documents.append(doc)
            
            # Update stored embeddings
            if self.doc_embeddings is None:
                self.doc_embeddings = embeddings
            else:
                self.doc_embeddings = np.vstack([self.doc_embeddings, embeddings])
            
            # Save to disk
            self._save_direct_faiss()
            
            logger.info(f"Added {len(documents)} documents to FAISS index")
        except Exception as e:
            logger.error(f"Error adding documents to FAISS index: {str(e)}")
    
    async def retrieve(self, query: str, k: int = 5, filters: Dict[str, Any] = None) -> List[Document]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: The query string
            k: Number of documents to retrieve
            filters: Metadata filters to apply
            
        Returns:
            List of retrieved documents
        """
        logger.info(f"Retrieving documents for query: {query}")
        
        try:
            # Use direct FAISS implementation
            results = await self._retrieve_direct_faiss(query, k, filters)
            
            # Convert to LangChain Document format for consistent interface
            documents = []
            for result in results:
                documents.append(
                    Document(
                        page_content=result["content"],
                        metadata=result["meta"],
                        score=result["score"] if "score" in result else None
                    )
                )
            
            return documents
        except Exception as e:
            logger.error(f"Error in retrieve: {str(e)}")
            return []
    
    async def _retrieve_direct_faiss(self, query: str, top_k: int = 5, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve documents using direct FAISS implementation."""
        if not self.embedding_model or len(self.documents) == 0:
            logger.warning("Embedding model not initialized or no documents in index")
            return []
        
        try:
            # Calculate query embedding
            query_embedding = self.embedding_model.encode([query])[0]
            
            # Normalize for cosine similarity
            query_embedding_normalized = query_embedding.reshape(1, -1)
            faiss.normalize_L2(query_embedding_normalized)
            
            # Search FAISS index
            scores, indices = self.index.search(query_embedding_normalized, top_k)
            
            # Filter results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < 0 or idx >= len(self.documents):
                    continue
                    
                doc = self.documents[idx]
                
                # Apply filters if any
                if filters and not self._apply_filters(doc, filters):
                    continue
                
                # Add to results
                results.append({
                    "content": doc["content"],
                    "score": float(scores[0][i]),
                    "meta": doc["meta"]
                })
            
            return results
        except Exception as e:
            logger.error(f"Error retrieving from FAISS: {str(e)}")
            return []
    
    def _apply_filters(self, doc: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Apply metadata filters to a document."""
        if not filters or "meta" not in doc:
            return True
        
        meta = doc["meta"]
        for key, value in filters.items():
            if key not in meta or meta[key] != value:
                return False
        
        return True

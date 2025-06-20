"""
Kenya Law Retriever - Enhanced RAG component with advanced retrieval strategies
"""
import os
import pickle
import json
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import httpx
import numpy as np
from dotenv import load_dotenv
from langchain.schema import Document
import numpy as np
import faiss
import hashlib
import time

try:
    from sentence_transformers import SentenceTransformer
    HAVE_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAVE_SENTENCE_TRANSFORMERS = False

# Import the stub implementations for backward compatibility
from app.utils.stubs.haystack.document_stores.faiss import FAISSDocumentStore
from app.utils.stubs.haystack.document_stores.weaviate import WeaviateDocumentStore
from app.utils.stubs.haystack.nodes import EmbeddingRetriever
from app.utils.stubs.haystack.pipelines import DocumentSearchPipeline
USING_STUBS = True

from app.utils.logger import get_logger
from app.utils.llm_factory import get_llm

load_dotenv()

logger = get_logger(__name__)

class KenyaLawRetriever:
    """
    Enhanced retriever for Kenyan legal documents using advanced vector search.
    
    Features:
    - Query expansion and rewrites
    - Hybrid retrieval (semantic + keyword)
    - Metadata filtering
    - Chunking optimization
    - Incremental indexing
    """
    
    def __init__(self):
        """Initialize the retriever with the configured vector DB."""
        self.vector_db_type = os.getenv("VECTOR_DB_TYPE", "faiss")
        self.vector_db_path = os.getenv("VECTOR_DB_PATH", "./data/vector_db")
        os.makedirs(self.vector_db_path, exist_ok=True)
        # Initialize embedding model
        self.embedding_model = self._initialize_embedding_model()
        self.embedding_dim = 768  # Default embedding dimension
        
        # Initialize embeddings attribute for direct FAISS usage
        self.embeddings = self  # Use self as embeddings interface
        
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
          # Initialize LLM for query expansion
        self.query_expansion_llm = None
        self.llm_initialized = False
        
    async def _lazy_init_llm(self):
        """Lazy initialize LLM for query expansion."""
        if not self.llm_initialized:
            try:
                self.query_expansion_llm = get_llm("mixtral")
                self.llm_initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize LLM for query expansion: {str(e)}")
                self.query_expansion_llm = None
        return self.query_expansion_llm is not None
    
    def _initialize_embedding_model(self):
        """Initialize the sentence transformer model for embeddings."""
        if not HAVE_SENTENCE_TRANSFORMERS:
            logger.warning("SentenceTransformers not available, vector search will be limited")
            return None
            
        try:
            model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
            logger.info(f"Loading embedding model: {model_name}")
            model = SentenceTransformer(model_name)
            self.embedding_dim = model.get_sentence_embedding_dimension()
            return model
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            logger.warning("Will attempt to download model or use smaller fallback")
            try:
                # Try a smaller model as fallback
                fallback_model = "sentence-transformers/all-MiniLM-L6-v2"
                logger.info(f"Loading fallback embedding model: {fallback_model}")
                model = SentenceTransformer(fallback_model)
                self.embedding_dim = model.get_sentence_embedding_dimension()
                return model
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
                    loaded_docs = pickle.load(f)
                    # Convert any dict objects to Document objects
                    self.documents = []
                    for doc in loaded_docs:
                        if isinstance(doc, dict):
                            content = doc.get("content", "")
                            meta = doc.get("meta", {})
                            self.documents.append(Document(page_content=content, metadata=meta))
                        else:
                            self.documents.append(doc)
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
                self.document_store.write_documents(haystack_docs)                # Update embeddings
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
                meta = doc.get("meta", {})
                if isinstance(meta, dict):
                    meta = dict(meta)  # ensure mutable
                else:
                    meta = {}
                meta["id"] = start_idx + i
                # Store as Document object
                self.documents.append(Document(page_content=doc["content"], metadata=meta))                # Update stored embeddings
            if self.doc_embeddings is None:
                self.doc_embeddings = embeddings
            else:
                self.doc_embeddings = np.vstack([self.doc_embeddings, embeddings])
            
            # Save to disk
            self._save_direct_faiss()
            
            logger.info(f"Added {len(documents)} documents to FAISS index")
        except Exception as e:
            logger.error(f"Error adding documents to FAISS index: {str(e)}")
    
    async def retrieve(self, query: str, top_k: int = 5, filters: Dict[str, Any] = None) -> List[Document]:
        """
        Enhanced retrieve with query expansion and hybrid search.
        
        Args:
            query: The query string
            top_k: Number of documents to retrieve
            filters: Metadata filters to apply
            
        Returns:
            List of retrieved documents
        """
        logger.info(f"Retrieving documents for query: {query}")
        
        try:
            # Step 1: Perform query expansion
            expanded_queries = await self._expand_query(query)
            
            # Step 2: Perform retrieval for each expanded query
            all_results = []
            for expanded_query in expanded_queries:
                # Get semantic search results
                semantic_results = await self._retrieve_direct_faiss(
                    expanded_query, 
                    top_k=top_k, 
                    filters=filters
                )
                all_results.extend(semantic_results)
            
            # Convert all Document objects to dicts for consistent processing
            processed_results = []
            for doc in all_results:
                if isinstance(doc, Document):
                    # Convert Document to dict format for consistent processing
                    processed_results.append({
                        "content": doc.page_content,
                        "meta": doc.metadata,
                        "score": doc.metadata.get("score", 0.0),
                        "search_type": "semantic"
                    })
            
            # Step 3: Perform keyword search for hybrid retrieval
            keyword_results = await self._keyword_search(query, top_k=top_k, filters=filters)
            processed_results.extend(keyword_results)
            
            # Step 4: Remove duplicates and re-rank
            deduplicated_results = self._deduplicate_results(processed_results)
            final_results = self._rerank_results(deduplicated_results, query)
            
            # Step 5: Convert to LangChain Document format for consistent interface
            documents = []
            for i, result in enumerate(final_results[:top_k]):  # Limit to top_k
                score = result.get("score", 0.0)
                documents.append(
                    Document(
                        page_content=result["content"],
                        metadata={
                            **(result.get("meta", {})),
                            "relevance_score": score,
                            "rank": i + 1                        }
                    )
                )
            
            logger.info(f"Retrieved {len(documents)} documents with hybrid search")
            return documents
        except Exception as e:
            logger.error(f"Error in retrieve: {str(e)}")
            # Fallback to basic retrieval
            try:
                basic_results = await self._retrieve_direct_faiss(query, top_k, filters)
                return basic_results
            except Exception as e2:
                logger.error(f"Fallback retrieval also failed: {str(e2)}")
                return []
    
    async def _expand_query(self, query: str) -> List[str]:
        """
        Expand the query to improve retrieval.
        
        This can use several techniques:
        1. Legal term expansion (rule-based)
        2. LLM-based query expansion
        3. Synonym expansion
        """
        expanded_queries = [query]  # Always include original query
        
        # 1. Legal term expansion (rule-based)
        legal_expanded = await self._rule_based_expansion(query)
        if legal_expanded and legal_expanded != query:
            expanded_queries.append(legal_expanded)
        
        # 2. LLM-based query expansion if LLM is available
        if await self._lazy_init_llm():
            try:
                llm_expanded = await self._llm_based_expansion(query)
                if llm_expanded and llm_expanded != query:
                    expanded_queries.append(llm_expanded)
            except Exception as e:
                logger.error(f"LLM-based query expansion failed: {str(e)}")
        
        logger.info(f"Generated {len(expanded_queries)} query variations")
        return expanded_queries
    
    async def _rule_based_expansion(self, query: str) -> str:
        """Apply rule-based expansion of legal terms."""
        # Legal term dictionary
        legal_terms = {
            "constitution": "constitution of kenya constitutional rights fundamental freedoms",
            "employment": "employment act labor relations employer employee rights",
            "land": "land act property rights ownership title deed",
            "children": "children act minors rights welfare guardianship",
            "contract": "contract law agreement consideration offer acceptance",
            "divorce": "divorce matrimonial causes separation maintenance custody",
            "succession": "succession inheritance will estate probate administration",
            "criminal": "criminal penal code offense prosecution conviction sentencing",
            "company": "company corporate business entity registration shareholders"
        }
        
        expanded = query
        
        # Add legal context terms
        for term, expansion in legal_terms.items():
            if term.lower() in query.lower():
                expanded += f" {expansion}"
        
        # Add Kenyan legal system context if not present
        if "kenya" not in expanded.lower() and "kenyan" not in expanded.lower():
            expanded += " kenya kenyan law legal system"
            
        return expanded
    
    async def _llm_based_expansion(self, query: str) -> str:
        """Use LLM to expand the query with legal context."""
        if not self.query_expansion_llm:
            return query
            
        try:
            prompt = f"""As a legal expert, expand the following query with relevant legal terms to improve search results. Focus on Kenyan law.
            
            Original query: {query}
            
            Expanded query:"""
            
            response = await self.query_expansion_llm.invoke(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Error in LLM query expansion: {str(e)}")
            return query
    async def _keyword_search(self, query: str, top_k: int = 5, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Perform keyword-based search over documents."""
        # Basic keyword matching - in a real implementation, this would use BM25 or similar
        results = []
        
        if not self.documents:
            return results
            
        # Extract keywords from query (simple implementation)
        keywords = [word.lower() for word in query.split() if len(word) > 3]
        
        for doc in self.documents:
            # Handle Document objects properly
            if isinstance(doc, Document):
                content = doc.page_content.lower()
                meta = doc.metadata
            else:
                # Skip invalid documents
                continue
                
            # Apply filters if any
            if filters and not self._apply_filters(meta, filters):
                continue
            
            # Count keyword matches
            matches = sum(keyword in content for keyword in keywords)
            if matches > 0:
                # Calculate simple relevance score based on keyword density
                score = matches / len(keywords) if keywords else 0
                
                results.append({
                    "content": doc.page_content,
                    "meta": meta,
                    "score": score,
                    "search_type": "keyword"                })
        
        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]
    
    def _apply_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Apply metadata filters to a document.
        
        Args:
            metadata: Document metadata
            filters: Filter criteria as key-value pairs
            
        Returns:
            True if document passes all filters, False otherwise
        """
        if not filters:
            return True
            
        for key, value in filters.items():
            # Skip if the metadata doesn't have the key
            if key not in metadata:
                return False
                
            # Handle list values (OR condition)
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            # Handle exact match
            elif metadata[key] != value:
                return False
                
        return True
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on content."""
        unique_results = []
        seen_contents = set()
        
        for result in results:
            # Create a hash of the content for deduplication
            content_hash = hashlib.md5(result["content"].encode()).hexdigest()
            
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_results.append(result)
        
        return unique_results
    
    def _rerank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Re-rank results based on a combination of factors."""
        for result in results:
            # Start with the original score or 0 if not present
            base_score = result.get("score", 0.0)
            
            # Adjust score based on search type (prefer semantic over keyword)
            search_type = result.get("search_type", "semantic")
            type_boost = 1.2 if search_type == "semantic" else 1.0
            
            # Boost recent documents
            recency_boost = 1.0
            if "meta" in result and "date" in result["meta"]:
                try:
                    doc_date = result["meta"]["date"]
                    if isinstance(doc_date, str) and len(doc_date) >= 4:
                        year = int(doc_date[:4])
                        current_year = time.localtime().tm_year
                        years_old = max(0, current_year - year)
                        # Exponential decay based on age
                        recency_boost = 1.0 * (0.9 ** years_old)
                except (ValueError, TypeError):
                    pass
            
            # Calculate final score
            result["score"] = base_score * type_boost * recency_boost
            
        # Sort by final score
        results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return results
    
    async def _retrieve_direct_faiss(self, query: str, top_k: int = 5, filters: Dict[str, Any] = None) -> List[Document]:
        """
        Perform direct FAISS vector search.
        
        Args:
            query: The query string
            top_k: Number of documents to retrieve
            filters: Metadata filters to apply
            
        Returns:
            List of retrieved documents
        """
        try:
            # Generate embeddings for the query
            query_embedding = self.embeddings.embed_query(query)
            
            # Search FAISS index
            if self.index is not None:            # Convert to numpy array
                query_embedding_np = np.array([query_embedding], dtype=np.float32)
                
                # Perform the search
                D, I = self.index.search(query_embedding_np, k=min(top_k, self.index.ntotal))
                
                # Get the documents
                results = []
                for i, idx in enumerate(I[0]):
                    if idx != -1 and idx < len(self.documents):
                        doc = self.documents[idx]
                        # Add score from FAISS
                        doc.metadata["score"] = float(D[0][i])
                        results.append(doc)
                
                logger.info(f"Retrieved {len(results)} documents from FAISS index")
                return results
            else:
                logger.warning("FAISS index not initialized")
                return []
        except Exception as e:
            logger.error(f"Error in FAISS retrieval: {str(e)}")
            # Use stub implementation as fallback
            return self._stub_retrieval(query, top_k)
    
    def _stub_retrieval(self, query: str, top_k: int = 5) -> List[Document]:
        """
        Stub implementation for retrieval when vector search fails.
        
        Args:
            query: The query string
            top_k: Number of documents to retrieve
            
        Returns:
            List of stub documents
        """
        from langchain.schema import Document
        
        # Create stub documents with relevant legal content
        stub_docs = []
        
        # Common legal topics in Kenya with sample content
        legal_topics = [
            {
                "title": "Constitution of Kenya",
                "content": "The Constitution of Kenya is the supreme law of the Republic of Kenya. It establishes the structure of the Kenyan government, and also defines the relationship between the government and the citizens of Kenya.",
                "source": "https://new.kenyalaw.org/akn/ke/act/2010/constitution/eng@2010-09-03",
                "score": 0.85,
                "type": "constitution"
            },
            {
                "title": "Employment Act",
                "content": "The Employment Act establishes the fundamental principles of employment in Kenya. It provides for minimum terms and conditions of employment, and regulates the relationship between employers and employees.",
                "source": "https://new.kenyalaw.org/legislation/employment-act-cap-226/",
                "score": 0.75,
                "type": "legislation"
            },
            {
                "title": "Children Act",
                "content": "The Children Act provides for parental responsibility, fostering, adoption, custody, maintenance, guardianship, care and protection of children. It gives effect to the principles of the Convention on the Rights of the Child.",
                "source": "https://new.kenyalaw.org/legislation/children-act-no-8-of-2001/",
                "score": 0.65,
                "type": "legislation"
            },
            {
                "title": "Land Act",
                "content": "The Land Act provides for the sustainable administration and management of land and land-based resources, and for connected purposes.",
                "source": "https://new.kenyalaw.org/legislation/land-act-no-6-of-2012/",
                "score": 0.60,
                "type": "legislation"
            },
            {
                "title": "Katiba Institute v Chief Justice of the Republic of Kenya",
                "content": "REPUBLIC OF KENYA IN THE HIGH COURT OF KENYA AT NAIROBI CONSTITUTIONAL AND HUMAN RIGHTS DIVISION PETITION NO. E282 OF 2020 KATIBA INSTITUTE.....................................................PETITIONER VERSUS THE CHIEF JUSTICE OF THE REPUBLIC OF KENYA..........1ST RESPONDENT",
                "source": "https://new.kenyalaw.org/judgments/KATIBA_INSTITUTE_V_CHIEF_JUSTICE_OF_THE_REPUBLIC_OF_KENYA_&_2_OTHERS_[2022]_eKLR.pdf",
                "score": 0.55,
                "type": "judgment"
            }
        ]
        
        # Return a subset of documents based on top_k
        for i in range(min(top_k, len(legal_topics))):
            topic = legal_topics[i]
            
            # Create metadata
            metadata = {
                "source": topic["source"],
                "title": topic["title"],
                "type": topic["type"],
                "score": topic["score"]
            }            # Create a Document object
            doc = Document(page_content=topic["content"], metadata=metadata)
            stub_docs.append(doc)
        
        logger.warning(f"Returning {len(stub_docs)} stub documents for query: {query}")
        return stub_docs
    
    def embed_query(self, query: str) -> List[float]:
        """
        Embeds a query string into a vector representation.
        
        Args:
            query: The query text to embed
            
        Returns:
            Vector representation of the query
        """
        if not self.embedding_model:
            logger.error("Embedding model not initialized for query embedding")
            # Return a zero vector of the correct dimension as fallback
            return [0.0] * self.embedding_dim
            
        try:
            # Use the sentence transformer model to encode the query
            vector = self.embedding_model.encode(query)
            return vector.tolist() if isinstance(vector, np.ndarray) else vector
        except Exception as e:
            logger.error(f"Error encoding query: {str(e)}")
            # Return a zero vector of the correct dimension as fallback
            return [0.0] * self.embedding_dim





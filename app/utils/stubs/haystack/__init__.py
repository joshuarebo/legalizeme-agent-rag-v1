# Stub implementation for haystack module package

# Create a package layout that matches the real haystack package
# so imports like haystack.document_stores.faiss will work

import sys

# Define base modules and classes
class Document:
    def __init__(self, content=None, meta=None, id=None, score=None, embedding=None, page_content=None):
        # Support both content and page_content for compatibility with different versions
        if content is not None:
            self.content = content
            self.page_content = content  # For langchain compatibility
        elif page_content is not None:
            self.content = page_content
            self.page_content = page_content
        else:
            self.content = ""
            self.page_content = ""
            
        self.meta = meta or {}
        self.id = id
        self.score = score
        self.embedding = embedding
    
    def to_dict(self):
        return {"content": self.content, "meta": self.meta}

# Document store classes for direct import from haystack
class FAISSDocumentStore:
    def __init__(self, *args, **kwargs):
        self._documents = []
        self.sql_url = kwargs.get("sql_url", "sqlite:///faiss_document_store.db")
        self.faiss_index_path = kwargs.get("faiss_index_path", "faiss_index.faiss")
        self.embedding_dim = kwargs.get("embedding_dim", 768)
        self.similarity = kwargs.get("similarity", "cosine")
        self.return_embedding = kwargs.get("return_embedding", False)
        self.index = kwargs.get("index", "document")
    
    def write_documents(self, documents, *args, **kwargs):
        self._documents.extend(documents)
        return {"documents_written": len(documents)}
    
    def update_embeddings(self, retriever, *args, **kwargs):
        # Stub for update_embeddings
        return {"embeddings_updated": len(self._documents)}
    
    def get_all_documents(self, *args, **kwargs):
        return self._documents
    
    def query_by_embedding(self, *args, **kwargs):
        return []
    
    def get_document_count(self):
        return len(self._documents)

class WeaviateDocumentStore:
    def __init__(self, *args, **kwargs):
        self._documents = []
        self.weaviate_url = kwargs.get("weaviate_url", "http://localhost:8080")
        self.embedding_dim = kwargs.get("embedding_dim", 768)
        self.similarity = kwargs.get("similarity", "cosine")
        self.index = kwargs.get("index", "Document")
    
    def write_documents(self, documents, *args, **kwargs):
        self._documents.extend(documents)
        return {"documents_written": len(documents)}
    
    def update_embeddings(self, retriever, *args, **kwargs):
        # Stub for update_embeddings
        return {"embeddings_updated": len(self._documents)}
    
    def get_all_documents(self, *args, **kwargs):
        return self._documents
    
    def query_by_embedding(self, *args, **kwargs):
        return []
    
    def get_document_count(self):
        return len(self._documents)

# Make these available for import from haystack
__all__ = ["Document", "FAISSDocumentStore", "WeaviateDocumentStore"]

# EmbeddingRetriever implementation
class EmbeddingRetriever:
    def __init__(self, *args, **kwargs):
        self.document_store = kwargs.get("document_store", None)
        self.embedding_model = kwargs.get("embedding_model", "default-model")
        self.model_format = kwargs.get("model_format", "sentence_transformers")
        self.top_k = kwargs.get("top_k", 10)
    
    def retrieve(self, *args, **kwargs):
        # Return empty list as this is a stub
        return []
    
    def embed_passages(self, passages):
        # Stub for embedding passages
        import numpy as np
        return [np.zeros(768) for _ in passages]
    
    def embed_queries(self, queries):
        # Stub for embedding queries
        import numpy as np
        return [np.zeros(768) for _ in queries]

# DocumentSearchPipeline implementation
class DocumentSearchPipeline:
    def __init__(self, retriever=None, *args, **kwargs):
        self.retriever = retriever
    
    def run(self, query=None, params=None, **kwargs):
        """Stub for running the pipeline"""
        if self.retriever is None:
            return {"documents": []}
        
        try:
            # Try to use the retriever's retrieve method directly
            if hasattr(self.retriever, 'retrieve') and callable(self.retriever.retrieve):
                documents = self.retriever.retrieve(query=query, **kwargs)
                return {"documents": documents}
        except Exception as e:
            print(f"Error in DocumentSearchPipeline: {str(e)}")
        
        # Default empty response
        return {"documents": []}

# Set up the module structure
# Create the document_stores package
document_stores_module = type('document_stores', (), {})
sys.modules['haystack.document_stores'] = document_stores_module

# Create document_stores.faiss
faiss_module = type('faiss', (), {'FAISSDocumentStore': FAISSDocumentStore})
sys.modules['haystack.document_stores.faiss'] = faiss_module

# Create document_stores.weaviate
weaviate_module = type('weaviate', (), {'WeaviateDocumentStore': WeaviateDocumentStore})
sys.modules['haystack.document_stores.weaviate'] = weaviate_module

# Create nodes module
nodes_module = type('nodes', (), {'EmbeddingRetriever': EmbeddingRetriever})
sys.modules['haystack.nodes'] = nodes_module

# Create pipelines module
pipelines_module = type('pipelines', (), {'DocumentSearchPipeline': DocumentSearchPipeline})
sys.modules['haystack.pipelines'] = pipelines_module

# Schema module
schema_module = type('schema', (), {'Document': Document})
sys.modules['haystack.schema'] = schema_module

# Add them to this module for direct imports
document_stores = document_stores_module
nodes = nodes_module
pipelines = pipelines_module
schema = schema_module

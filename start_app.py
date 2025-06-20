import sys
import os
import importlib.util

# Add the app directory to the Python path
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Import stubs module first
from app.utils.stubs import langgraph
from app.utils.stubs import haystack
import app.utils.stubs.unstructured
import app.utils.stubs.fitz

# Create necessary directories if they don't exist
required_dirs = [
    os.path.join(app_dir, "data"),
    os.path.join(app_dir, "data", "vector_db"),
    os.path.join(app_dir, "data", "model_cache"),
    os.path.join(app_dir, "data", "temp_pdfs"),
    os.path.join(app_dir, "data", "llm_config"),
    os.path.join(app_dir, "logs"),
]

for directory in required_dirs:
    os.makedirs(directory, exist_ok=True)
    print(f"Ensured directory exists: {directory}")

# Import torch as a stub if it's not available
try:
    import torch
    print("Successfully imported torch")
except ImportError:
    print("Creating stub for torch")
    import sys
    class TorchStub:
        def __init__(self):
            self.cuda = self
            self.device = "cpu"
        
        def is_available(self):
            return False
        
        def __getattr__(self, name):
            # Return a callable for any method
            def stub_callable(*args, **kwargs):
                return None
            return stub_callable
    
    sys.modules['torch'] = TorchStub()

# Files to patch imports in
files_to_patch = [
    ('app/agents/counsel_agent.py', [
        ('from langgraph.graph import StateGraph, END', 'from app.utils.stubs.langgraph import StateGraph, END'),
        ('from langgraph.prebuilt import ToolNode', 'from app.utils.stubs.langgraph import ToolNode'),
        ('import langgraph', 'import app.utils.stubs.langgraph as langgraph')
    ]),
    ('app/rag/retriever.py', [
        ('from haystack.document_stores.faiss import FAISSDocumentStore', 'from app.utils.stubs.haystack.document_stores.faiss import FAISSDocumentStore'),
        ('from haystack.document_stores.weaviate import WeaviateDocumentStore', 'from app.utils.stubs.haystack.document_stores.weaviate import WeaviateDocumentStore'),
        ('from haystack.nodes import EmbeddingRetriever', 'from app.utils.stubs.haystack.nodes import EmbeddingRetriever'),
        ('from haystack.pipelines import DocumentSearchPipeline', 'from app.utils.stubs.haystack.pipelines import DocumentSearchPipeline'),
        ('from langchain.schema import Document', 'from langchain.schema import Document')
    ]),
    ('app/parsers/document_parser.py', [
        ('from unstructured.partition.pdf import partition', 'from app.utils.stubs.unstructured.partition.pdf import partition_pdf'),
        ('from unstructured.partition.html import partition', 'from app.utils.stubs.unstructured.partition.html import partition_html'),
        ('from unstructured.partition.text import partition', 'from app.utils.stubs.unstructured.partition.text import partition_text'),
        ('import fitz', 'import app.utils.stubs.fitz as fitz')
    ]),
    ('app/parsers/web_parser.py', [
        ('from unstructured.partition.html import partition', 'from app.utils.stubs.unstructured.partition.html import partition_html')
    ])
]

# Apply patches
for file_path, replacements in files_to_patch:
    full_path = os.path.join(app_dir, file_path)
    if os.path.exists(full_path):
        with open(full_path, 'r') as f:
            content = f.read()
        
        # Apply all replacements
        for old_str, new_str in replacements:
            if old_str in content:
                content = content.replace(old_str, new_str)
        
        # Write the changes back
        with open(full_path, 'w') as f:
            f.write(content)
        print(f"Patched imports in {full_path}")

# Patch the retriever.py to use the enhanced Document class
retriever_path = os.path.join(app_dir, 'app', 'rag', 'retriever.py')
if os.path.exists(retriever_path):
    with open(retriever_path, 'r') as f:
        content = f.read()
    
    if 'from langchain.schema import Document' in content:
        # Use it directly to avoid conflicts
        print(f"Found Document import in {retriever_path}")
    
    # Write the changes back
    with open(retriever_path, 'w') as f:
        f.write(content)

# Then run the application with uvicorn
print("Starting the application with uvicorn...")
import uvicorn
uvicorn.run('app.api.main:app', host='0.0.0.0', port=8000)

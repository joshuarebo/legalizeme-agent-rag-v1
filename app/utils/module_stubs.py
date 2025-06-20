# Additional patches for missing modules
# This script will add stubs or mocks for problematic or missing packages

import sys
import os

# Get the app base directory
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the stubs directory to the Python path
stubs_dir = os.path.join(base_dir, 'utils', 'stubs')
if stubs_dir not in sys.path:
    sys.path.insert(0, stubs_dir)

# Create stubs for problematic modules at runtime
def create_module_stub(name):
    """Dynamically create a stub module at runtime"""
    class StubModule:
        def __init__(self, name):
            self.__name__ = name
            self.__all__ = []
        
        def __getattr__(self, attr):
            # Return a callable for any method
            if attr.startswith('__'):
                raise AttributeError(f"{self.__name__} has no attribute {attr}")
            
            # Create a stub callable that returns None
            def stub_callable(*args, **kwargs):
                return None
            
            # Also make the callable itself able to handle attribute access
            stub_callable.__name__ = attr
            stub_callable.__module__ = self.__name__
            
            # Allow method chaining by returning the stub_callable for any attribute
            def get_subattr(subattr):
                if subattr.startswith('__'):
                    raise AttributeError(f"{attr} has no attribute {subattr}")
                return stub_callable
            stub_callable.__getattr__ = get_subattr
            
            return stub_callable
    
    # Create and register the stub module
    stub = StubModule(name)
    sys.modules[name] = stub
    
    # If it's a package with submodules, handle those too
    parts = name.split('.')
    for i in range(1, len(parts)):
        parent = '.'.join(parts[:i])
        if parent not in sys.modules:
            sys.modules[parent] = StubModule(parent)
    
    return stub

# List of modules to stub if they can't be imported
modules_to_stub = [
    'langgraph',
    'langgraph.graph',
    'langgraph.prebuilt',
    'smol_agent',
    'haystack',
    'haystack.document_stores',
    'haystack.nodes'
]

# Try to import each module, and if it fails, create a stub
for module_name in modules_to_stub:
    try:
        __import__(module_name)
        print(f"Successfully imported {module_name}")
    except ImportError:
        print(f"Creating stub for missing module: {module_name}")
        create_module_stub(module_name)

# Special handling for ToolNode since it's used directly
try:
    from langgraph.prebuilt import ToolNode
    print("Successfully imported ToolNode from langgraph.prebuilt")
except ImportError:
    # Create a ToolNode class
    class ToolNode:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *args, **kwargs):
            return None
    
    # Add it to sys.modules
    if 'langgraph.prebuilt' not in sys.modules:
        class StubPrebuilt:
            ToolNode = ToolNode
        sys.modules['langgraph.prebuilt'] = StubPrebuilt()
    else:
        sys.modules['langgraph.prebuilt'].ToolNode = ToolNode

# Special handling for haystack
try:
    import haystack
    print("Successfully imported haystack")
except ImportError:
    # Create a haystack module with document_stores, nodes, etc.
    sys.modules['haystack'] = type('haystack', (), {})
    
    # document_stores
    document_stores = type('document_stores', (), {})
    
    # document_stores.faiss
    faiss = type('faiss', (), {})
    
    class FAISSDocumentStore:
        def __init__(self, *args, **kwargs):
            pass
        def write_documents(self, *args, **kwargs):
            return {"documents_written": 0}
        def get_all_documents(self, *args, **kwargs):
            return []
        def query_by_embedding(self, *args, **kwargs):
            return []
    
    faiss.FAISSDocumentStore = FAISSDocumentStore
    document_stores.faiss = faiss
    
    # document_stores.weaviate
    weaviate = type('weaviate', (), {})
    
    class WeaviateDocumentStore:
        def __init__(self, *args, **kwargs):
            pass
        def write_documents(self, *args, **kwargs):
            return {"documents_written": 0}
        def get_all_documents(self, *args, **kwargs):
            return []
        def query_by_embedding(self, *args, **kwargs):
            return []
    
    weaviate.WeaviateDocumentStore = WeaviateDocumentStore
    document_stores.weaviate = weaviate
    
    # Set document_stores
    sys.modules['haystack'].document_stores = document_stores
    sys.modules['haystack.document_stores'] = document_stores
    sys.modules['haystack.document_stores.faiss'] = faiss
    sys.modules['haystack.document_stores.weaviate'] = weaviate
    
    # nodes
    nodes = type('nodes', (), {})
    
    class EmbeddingRetriever:
        def __init__(self, *args, **kwargs):
            pass
        def retrieve(self, *args, **kwargs):
            return []
    
    nodes.EmbeddingRetriever = EmbeddingRetriever
    sys.modules['haystack'].nodes = nodes
    sys.modules['haystack.nodes'] = nodes
    
    # pipelines
    pipelines = type('pipelines', (), {})
    
    class DocumentSearchPipeline:
        def __init__(self, *args, **kwargs):
            pass
        def run(self, *args, **kwargs):
            return {"documents": []}

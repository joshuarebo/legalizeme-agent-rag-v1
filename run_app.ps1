# Setup and run script for Counsel Legal AI
# This script creates a virtual environment, installs dependencies, and runs the application

# Create a virtual environment if it doesn't exist
if (-not (Test-Path -Path ".\venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

# Activate the virtual environment
Write-Host "Activating virtual environment..."
.\venv\Scripts\Activate.ps1

# Install or update dependencies
Write-Host "Installing dependencies..."
# First, install core packages
pip install fastapi uvicorn python-dotenv
pip install langchain
pip install faiss-cpu
pip install transformers

# Try to install packages that might have issues
try {
    pip install langgraph
    # Check if langgraph is actually importable
    $testImport = python -c @"
try:
    import langgraph
    print('langgraph imported successfully')
except ImportError as e:
    print('langgraph failed to import: ' + str(e))
"@
    if ($testImport -notmatch "successfully") {
        throw "langgraph installed but cannot be imported"
    }
} catch {
    Write-Host "Warning: Could not install or import langgraph. Using stub implementation."
    # Create a stub for langgraph if it fails to install
    New-Item -ItemType Directory -Force -Path ".\app\utils\stubs" | Out-Null
    $stubContent = @"
# Stub implementation for langgraph
class StateGraph:
    def __init__(self, *args, **kwargs):
        pass
    
    def add_node(self, *args, **kwargs):
        return self
    
    def add_edge(self, *args, **kwargs):
        return self
    
    def set_entry_point(self, *args, **kwargs):
        return self
    
    def compile(self, *args, **kwargs):
        return self

class ToolNode:
    def __init__(self, *args, **kwargs):
        pass

END = "END"

# Add prebuilt module with ToolNode
class prebuilt:
    class ToolNode:
        def __init__(self, *args, **kwargs):
            pass
"@
    Set-Content -Path ".\app\utils\stubs\langgraph.py" -Value $stubContent
    New-Item -Path ".\app\utils\stubs\__init__.py" -Force | Out-Null
}

# Skip problematic packages
Write-Host "Skipping problematic packages and continuing with installation..."
$requirements = Get-Content -Path "requirements.txt" | Where-Object {
    -not ($_ -match "smol-agent" -or $_ -match "weaviate-client" -or $_ -match "flash-attn" -or $_ -match "langgraph" -or $_ -match "llama-index")
}
$requirements | Out-File -FilePath "requirements-filtered.txt"
pip install -r requirements-filtered.txt

# Try to install haystack
try {
    pip install haystack-ai
    # Check if it's importable
    $testHaystack = python -c @"
try:
    import haystack
    print('haystack imported successfully')
except ImportError as e:
    print('haystack failed to import: ' + str(e))
"@
    if ($testHaystack -notmatch "successfully") {
        throw "haystack installed but cannot be imported"
    }
} catch {
    Write-Host "Warning: Could not install or import haystack. Will use stub implementation."
}

# Create stub for smol-agent if needed
New-Item -ItemType Directory -Force -Path ".\app\utils\stubs\smol_agent" | Out-Null
$smolAgentStubContent = @"
# Stub implementation for smol-agent
class SmolAgentManager:
    def __init__(self, *args, **kwargs):
        pass
    
    def execute(self, *args, **kwargs):
        return {"result": "SmolAgent is not available. This is a stub implementation."}
"@
Set-Content -Path ".\app\utils\stubs\smol_agent\__init__.py" -Value $smolAgentStubContent

# Create necessary directories
Write-Host "Creating necessary directories..."
New-Item -ItemType Directory -Force -Path ".\data\vector_db" | Out-Null
New-Item -ItemType Directory -Force -Path ".\data\model_cache" | Out-Null
New-Item -ItemType Directory -Force -Path ".\data\temp_pdfs" | Out-Null
New-Item -ItemType Directory -Force -Path ".\data\llm_config" | Out-Null
New-Item -ItemType Directory -Force -Path ".\logs" | Out-Null

# Apply patches for missing modules if needed
Write-Host "Applying patches for missing modules..."

# First run the module_stubs.py to create stubs for missing modules
$moduleStubsPath = ".\app\utils\module_stubs.py"
if (Test-Path -Path $moduleStubsPath) {
    Write-Host "Running module stubs..."
    python -c "import app.utils.module_stubs"
} else {
    Write-Host "Module stubs script not found. Creating basic stubs instead."
    # Create a minimal module_stubs.py if it doesn't exist
    $basicStubsContent = @"
# Basic stubs for missing modules
import sys
import os

def create_module_stub(name):
    """Dynamically create a stub module at runtime"""
    class StubModule:
        def __init__(self, name):
            self.__name__ = name
        
        def __getattr__(self, attr):
            # Return a callable for any method
            def stub_callable(*args, **kwargs):
                return None
            return stub_callable
    
    # Create and register the stub module
    stub = StubModule(name)
    sys.modules[name] = stub
    return stub

# Stub important modules if they're missing
for module_name in ['langgraph', 'haystack', 'unstructured', 'smol_agent']:
    try:
        __import__(module_name)
        print(f"Successfully imported {module_name}")
    except ImportError:
        print(f"Creating stub for missing module: {module_name}")
        create_module_stub(module_name)
"@
    New-Item -ItemType Directory -Force -Path ".\app\utils" | Out-Null
    Set-Content -Path $moduleStubsPath -Value $basicStubsContent
    python -c "import app.utils.module_stubs"
}

# Then use the patch script for consistent patching of import statements
python -m app.utils.patch_imports

# Run the application
Write-Host "Starting Counsel Legal AI application..."
try {
    # Create a custom startup script to ensure our stubs are loaded first
    $startupScript = @"
import sys
import os

# Add the app directory to the Python path
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Import stubs module first
from app.utils.stubs import langgraph
from app.utils.stubs import haystack
import app.utils.stubs.unstructured
import app.utils.stubs.fitz

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

# Fix imports in counsel_agent.py manually
counsel_agent_path = os.path.join(app_dir, 'app', 'agents', 'counsel_agent.py')
if os.path.exists(counsel_agent_path):
    with open(counsel_agent_path, 'r') as f:
        content = f.read()
    
    # Replace imports
    if 'from langgraph.graph import StateGraph, END' in content:
        content = content.replace(
            'from langgraph.graph import StateGraph, END',
            'from app.utils.stubs.langgraph import StateGraph, END'
        )
    
    if 'from langgraph.prebuilt import ToolNode' in content:
        content = content.replace(
            'from langgraph.prebuilt import ToolNode',
            'from app.utils.stubs.langgraph import ToolNode'
        )
    
    # Write the changes back
    with open(counsel_agent_path, 'w') as f:
        f.write(content)
    print(f"Patched imports in {counsel_agent_path}")

# Then run the application with uvicorn
import uvicorn
uvicorn.run('app.api.main:app', host='0.0.0.0', port=8000)
"@
    Set-Content -Path ".\start_app.py" -Value $startupScript

    # Run the custom startup script
    python .\start_app.py
} catch {
    Write-Host "Error starting the application: $_"
    Write-Host "Please check the logs for more details."
}

# Keep the window open after execution
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

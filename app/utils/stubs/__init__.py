# Stubs package for missing dependencies
"""
This package contains stub implementations of external dependencies that might be
missing in the environment. This allows the application to run with reduced functionality
when some dependencies cannot be installed.
"""

# Export key components
from . import langgraph
try:
    from .langgraph import StateGraph, END
    # Use prebuilt attribute from the langgraph module
    ToolNode = langgraph.prebuilt.ToolNode
except (ImportError, AttributeError):
    # Define them directly if module structure doesn't match
    from .langgraph import StateGraph, END, ToolNode

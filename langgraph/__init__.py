"""
Top-level stub implementation of the 'langgraph' package so that imports
`from langgraph.graph import StateGraph, END` resolve even if the real package
is not installed. This file lives in the project root, which is on PYTHONPATH
inside the Docker container.
"""
from importlib import import_module as _import_module

# Re-export objects from the internal stub graph implementation
from .graph import StateGraph, END  # noqa: F401

# Make langgraph.graph importable
import sys as _sys
_sys.modules.setdefault(__name__ + '.graph', _import_module(__name__ + '.graph'))

__all__ = [
    'StateGraph',
    'END',
] 
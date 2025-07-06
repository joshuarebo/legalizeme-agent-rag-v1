"""
Stub implementation of langgraph.graph used in CI when the real package is
unavailable. It provides just enough functionality for the application to
import and construct graphs without executing real workflows.
"""
from typing import Any, Dict, Callable, Union

class END:
    """Sentinel to denote the end of a StateGraph."""
    pass

class StateGraph:
    """Very small subset of the real StateGraph API used by the app."""

    def __init__(self, state_type: Any):
        self.state_type = state_type
        self._nodes: Dict[str, Callable] = {}
        self._edges: Dict[str, Union[str, Callable, END]] = {}
        self._cond_edges: Dict[str, tuple[Callable, Dict[Any, str]]] = {}
        self._entry: str | None = None

    # --- Graph construction helpers -------------------------------------------------

    def add_node(self, name: str, handler: Callable):
        self._nodes[name] = handler

    def add_edge(self, from_node: str, to_node: Union[str, Callable, END]):
        self._edges[from_node] = to_node

    def add_conditional_edges(
        self,
        from_node: str,
        condition: Callable[[Any], Any],
        edges: Dict[Any, str],
    ):
        self._cond_edges[from_node] = (condition, edges)

    def set_entry_point(self, name: str):
        self._entry = name

    # --- Execution helpers -----------------------------------------------------------

    async def arun(self, state: Any):
        current = self._entry
        while current and current is not END:
            handler = self._nodes.get(current)
            if handler is None:
                break
            state = await handler(state) if callable(handler) else state

            # conditional edges take priority
            if current in self._cond_edges:
                cond_fn, mapping = self._cond_edges[current]
                nxt = mapping.get(cond_fn(state))
            else:
                nxt = self._edges.get(current)
            current = nxt
        return state

    def run(self, state: Any):
        import asyncio
        return asyncio.run(self.arun(state)) 
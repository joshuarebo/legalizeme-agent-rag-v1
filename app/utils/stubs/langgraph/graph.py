"""
Stub implementation of langgraph.graph module
"""
from typing import Any, Dict, List, Optional, Callable, Union

class END:
    """Stub for END marker"""
    pass

class StateGraph:
    """
    Stub implementation of StateGraph that mimics the basic functionality
    """
    def __init__(self, state_type: Any):
        self.state_type = state_type
        self.nodes = {}
        self.edges = {}
        self.conditional_edges = {}
        self.entry_point = None

    def add_node(self, name: str, handler: Callable) -> None:
        """Add a node to the graph"""
        self.nodes[name] = handler

    def add_edge(self, from_node: str, to_node: Union[str, Callable, END]) -> None:
        """Add an edge between nodes"""
        self.edges[from_node] = to_node

    def add_conditional_edges(self, from_node: str, condition: Callable, edges: Dict[Any, str]) -> None:
        """Add conditional edges from a node"""
        self.conditional_edges[from_node] = (condition, edges)

    def set_entry_point(self, node: str) -> None:
        """Set the entry point of the graph"""
        self.entry_point = node

    async def arun(self, state: Any) -> Any:
        """Run the graph with the given state"""
        current_node = self.entry_point
        while current_node is not None and current_node is not END:
            # Get the handler for the current node
            handler = self.nodes.get(current_node)
            if handler:
                # Execute the handler
                state = await handler(state)

            # Check conditional edges first
            if current_node in self.conditional_edges:
                condition_func, edge_map = self.conditional_edges[current_node]
                condition_result = condition_func(state)
                current_node = edge_map.get(condition_result)
            else:
                # Use regular edges
                current_node = self.edges.get(current_node)

        return state

    def run(self, state: Any) -> Any:
        """Synchronous version of arun"""
        import asyncio
        return asyncio.run(self.arun(state)) 
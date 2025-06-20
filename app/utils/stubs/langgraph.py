# Stub implementation for langgraph
import sys

# Define the main components as attributes of this module
class StateGraph:
    def __init__(self, *args, **kwargs):
        self.nodes = {}
        self.edges = {}
        self.conditional_edges = {}
        self.entry_point = None
    
    def add_node(self, node_name, node_func):
        self.nodes[node_name] = node_func
        return self
    
    def add_edge(self, start_node, end_node):
        if start_node not in self.edges:
            self.edges[start_node] = []
        self.edges[start_node].append(end_node)
        return self
    
    def add_conditional_edges(self, source, condition_func, destinations):
        self.conditional_edges[source] = (condition_func, destinations)
        return self
    
    def set_entry_point(self, entry_point):
        self.entry_point = entry_point
        return self
    
    def compile(self, *args, **kwargs):
        return self
    
    async def ainvoke(self, state, *args, **kwargs):
        # Simply return a modified state with a fake response
        if hasattr(state, 'query'):
            state.response = f"Simulated response for: {state.query}"
        else:
            state.response = "Simulated response"
        
        state.error = None
        return state

class ToolNode:
    def __init__(self, *args, **kwargs):
        pass
    
    def __call__(self, *args, **kwargs):
        return None

END = "END"

# Define prebuilt as an attribute of this module, not a class
class _PrebuiltModule:
    def __init__(self):
        self.ToolNode = ToolNode

prebuilt = _PrebuiltModule()

# Make this module look more like the real langgraph
__all__ = ["StateGraph", "END", "prebuilt", "ToolNode"]

# Register the module in sys.modules so it can be imported correctly
module_name = "langgraph"
sys.modules[module_name] = sys.modules[__name__]
sys.modules[f"{module_name}.graph"] = type("graph", (), {"StateGraph": StateGraph, "END": END})
sys.modules[f"{module_name}.prebuilt"] = type("prebuilt", (), {"ToolNode": ToolNode})

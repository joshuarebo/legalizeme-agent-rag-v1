# Haystack pipelines module

class DocumentSearchPipeline:
    def __init__(self, *args, **kwargs):
        pass
    
    def run(self, *args, **kwargs):
        return {"documents": []}
    
    def add_node(self, *args, **kwargs):
        return self

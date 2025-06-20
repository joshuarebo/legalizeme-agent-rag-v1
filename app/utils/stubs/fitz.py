# Stub for fitz (PyMuPDF) package
import sys

class Document:
    def __init__(self, file_path):
        self.file_path = file_path
        self.page_count = 1
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def __len__(self):
        return self.page_count
    
    def __getitem__(self, idx):
        return Page()
    
    def load_page(self, page_idx):
        return Page()
    
    def close(self):
        pass

class Page:
    def __init__(self):
        self.mediabox = [0, 0, 612, 792]  # Standard letter size
    
    def get_text(self, opt="text"):
        return "[Stub PDF page content]"
    
    def get_textpage(self):
        return TextPage()
    
    def search_for(self, text):
        return []

class TextPage:
    def __init__(self):
        pass
    
    def extractWORDS(self):
        return []
    
    def extractBLOCKS(self):
        return []

class Rect:
    def __init__(self, x0=0, y0=0, x1=612, y1=792):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

# Register the module and all necessary components
sys.modules['fitz'] = sys.modules[__name__]
sys.modules['fitz.fitz'] = sys.modules[__name__]

# Export public classes
__all__ = ['Document', 'Page', 'TextPage', 'Rect']

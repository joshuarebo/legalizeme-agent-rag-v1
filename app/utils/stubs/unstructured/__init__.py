# Stub implementation for unstructured module
import sys

# Base unstructured module
class UnstructuredStub:
    pass

sys.modules['unstructured'] = UnstructuredStub()

# Create partition submodule
class PartitionStub:
    pass

sys.modules['unstructured.partition'] = PartitionStub()

# Create PDF partition submodule
class PdfPartitionStub:
    @staticmethod
    def partition(file_path, **kwargs):
        """Stub for PDF partitioning"""
        return [{"type": "Text", "text": f"[Stub PDF content from {file_path}]"}]

sys.modules['unstructured.partition.pdf'] = PdfPartitionStub()

# Create HTML partition submodule
class HtmlPartitionStub:
    @staticmethod
    def partition(html_content, **kwargs):
        """Stub for HTML partitioning"""
        return [{"type": "Text", "text": "[Stub HTML content]"}]

sys.modules['unstructured.partition.html'] = HtmlPartitionStub()

# Create Text partition submodule
class TextPartitionStub:
    @staticmethod
    def partition(text, **kwargs):
        """Stub for text partitioning"""
        return [{"type": "Text", "text": text[:500] + "..." if len(text) > 500 else text}]

sys.modules['unstructured.partition.text'] = TextPartitionStub()

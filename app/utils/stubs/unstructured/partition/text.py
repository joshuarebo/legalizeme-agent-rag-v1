# Stub for unstructured.partition.text
def partition(text, **kwargs):
    """Stub for text partitioning"""
    return [{"type": "Text", "text": text[:500] + "..." if len(text) > 500 else text}]

# For compatibility with different function names
partition_text = partition

# Patch importer script
# This script will patch imports in Python files to use stub implementations where necessary

import os
import re
import sys
import importlib
import logging

logger = logging.getLogger(__name__)

def is_package_installed(package_name):
    """
    Check if a package is installed by attempting to import it
    """
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def patch_file(file_path, replacements):
    """
    Apply regex replacements to a file
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            logger.info(f"Patched: {file_path}")
            return True
        else:
            logger.info(f"No changes needed for: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Error patching {file_path}: {str(e)}")
        return False

def restore_original_imports(file_path, package_name, stub_package):
    """
    Restore original imports for a file when the real package is available
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Pattern to match imports from the stub package
        pattern = f"from {re.escape(stub_package)}"
        replacement = f"from {package_name}"
        
        # Replace stub imports with real imports
        original_content = content
        content = re.sub(pattern, replacement, content)
        
        # Also handle import X as Y patterns
        pattern_import = f"import {re.escape(stub_package)}"
        replacement_import = f"import {package_name}"
        content = re.sub(pattern_import, replacement_import, content)
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            logger.info(f"Restored original imports in: {file_path}")
            return True
        else:
            logger.info(f"No changes needed for: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Error restoring imports in {file_path}: {str(e)}")
        return False

def main():
    # Define package mapping - these are the packages we might need to patch
    package_mapping = {
        "langgraph": "app.utils.stubs.langgraph",
        "haystack": "app.utils.stubs.haystack",
        "unstructured": "app.utils.stubs.unstructured",
        "fitz": "app.utils.stubs.fitz",
        "smol_agent": "app.utils.stubs.smol_agent"
    }
    
    # Check which packages need patching
    packages_to_patch = {}
    packages_to_restore = {}
    
    for package, stub in package_mapping.items():
        if not is_package_installed(package):
            logger.warning(f"Package {package} is not installed. Will use stub implementation.")
            packages_to_patch[package] = stub
        else:
            logger.info(f"Package {package} is installed. Using real implementation.")
            packages_to_restore[package] = stub
    
    # If all packages are installed, we don't need to patch anything
    if not packages_to_patch:
        logger.info("All required packages are installed. No patching needed.")
        
        # Instead, restore any previously patched files
        restore_files(packages_to_restore)
        return
    
    # Define the patches based on what needs to be patched
    patches = []
    
    # LangGraph patches
    if "langgraph" in packages_to_patch:
        patches.extend([
            (
                "agents/counsel_agent.py",
                [
                    (
                        r"from langgraph\.graph import StateGraph, END",
                        f"from {packages_to_patch['langgraph']} import StateGraph, END"
                    ),
                    (
                        r"from langgraph\.prebuilt import ToolNode",
                        f"from {packages_to_patch['langgraph']} import ToolNode"
                    ),
                    (
                        r"import langgraph",
                        f"import {packages_to_patch['langgraph']} as langgraph"
                    )
                ]
            ),
            (
                "agents/agent_tools.py",
                [
                    (
                        r"from langgraph\.graph import StateGraph, END",
                        f"from {packages_to_patch['langgraph']} import StateGraph, END"
                    ),
                    (
                        r"from langgraph\.prebuilt import ToolNode",
                        f"from {packages_to_patch['langgraph']} import ToolNode"
                    ),
                    (
                        r"import langgraph",
                        f"import {packages_to_patch['langgraph']} as langgraph"
                    )
                ]
            )
        ])
    
    # Haystack patches
    if "haystack" in packages_to_patch:
        patches.append(
            (
                "rag/retriever.py", 
                [
                    (
                        r"from haystack\.document_stores\.faiss import FAISSDocumentStore",
                        f"from {packages_to_patch['haystack']}.document_stores.faiss import FAISSDocumentStore"
                    ),
                    (
                        r"from haystack\.document_stores\.weaviate import WeaviateDocumentStore",
                        f"from {packages_to_patch['haystack']}.document_stores.weaviate import WeaviateDocumentStore"
                    ),
                    (
                        r"from haystack\.nodes import EmbeddingRetriever",
                        f"from {packages_to_patch['haystack']}.nodes import EmbeddingRetriever"
                    ),
                    (
                        r"from haystack\.pipelines import DocumentSearchPipeline",
                        f"from {packages_to_patch['haystack']}.pipelines import DocumentSearchPipeline"
                    )
                ]
            )
        )
    
    # Unstructured patches
    if "unstructured" in packages_to_patch:
        patches.extend([
            (
                "parsers/document_parser.py",
                [
                    (
                        r"from unstructured\.partition\.pdf import partition",
                        f"from {packages_to_patch['unstructured']}.partition.pdf import partition"
                    ),
                    (
                        r"from unstructured\.partition\.html import partition",
                        f"from {packages_to_patch['unstructured']}.partition.html import partition"
                    ),
                    (
                        r"from unstructured\.partition\.text import partition",
                        f"from {packages_to_patch['unstructured']}.partition.text import partition"
                    )
                ]
            ),
            (
                "parsers/web_parser.py",
                [
                    (
                        r"from unstructured\.partition\.html import partition",
                        f"from {packages_to_patch['unstructured']}.partition.html import partition"
                    )
                ]
            )
        ])
    
    # PyMuPDF (fitz) patches
    if "fitz" in packages_to_patch:
        patches.append(
            (
                "parsers/document_parser.py",
                [
                    (
                        r"import fitz",
                        f"import {packages_to_patch['fitz']} as fitz"
                    )
                ]
            )
        )
    
    # Apply patches
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for file_rel_path, replacements in patches:
        file_path = os.path.join(base_dir, file_rel_path)
        patch_file(file_path, replacements)
    
    logger.info("Patching complete.")

def restore_files(packages_to_restore):
    """Restore original imports for packages that are now available"""
    if not packages_to_restore:
        return
    
    logger.info("Restoring original imports for installed packages...")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Files that might have been patched
    files_to_check = {
        "langgraph": ["agents/counsel_agent.py", "agents/agent_tools.py"],
        "haystack": ["rag/retriever.py"],
        "unstructured": ["parsers/document_parser.py", "parsers/web_parser.py"],
        "fitz": ["parsers/document_parser.py"]
    }
    
    # Restore original imports
    for package, stub in packages_to_restore.items():
        if package in files_to_check:
            for file_rel_path in files_to_check[package]:
                file_path = os.path.join(base_dir, file_rel_path)
                restore_original_imports(file_path, package, stub)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()

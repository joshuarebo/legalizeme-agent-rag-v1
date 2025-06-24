"""
Document summarization module for legal-tech application.
Provides various summarization capabilities for legal documents.
"""
import os
import re
import json
import uuid
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from pydantic import BaseModel, Field

from app.utils.logger import get_logger
from app.utils.llm_factory import get_enhanced_llm, create_legal_prompt

logger = get_logger(__name__)

class SummarizedDocument(BaseModel):
    """Model for a summarized document."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_document_id: Optional[str] = None
    original_content: Optional[str] = None
    summary: str
    key_points: List[str]
    summary_type: str  # extractive, abstractive, hierarchical
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)

class DocumentComparison(BaseModel):
    """Model for document comparison results."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_ids: List[str]
    document_names: List[str]
    similarities: List[float]
    differences: List[Dict[str, Any]]
    common_points: List[str]
    unique_points: Dict[str, List[str]]
    created_at: datetime = Field(default_factory=datetime.now)

class SummarizationConfig(BaseModel):
    """Configuration for document summarization."""
    summary_type: str = "extractive"  # extractive, abstractive, hierarchical
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    focus_areas: Optional[List[str]] = None
    extraction_ratio: float = 0.3  # For extractive summarization
    detail_level: str = "medium"  # low, medium, high (for hierarchical)
    include_citations: bool = True
    simplify_language: bool = False

class DocumentSummarizer:
    """
    Provides document summarization capabilities using LLMs.
    """
    
    def __init__(self):
        """Initialize the document summarizer."""
        self.llm = get_enhanced_llm(llm_type="huggingface", use_case="legal_analysis")
    
    async def summarize_document(
        self, 
        document_content: str,
        config: SummarizationConfig = SummarizationConfig(),
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> SummarizedDocument:
        """
        Summarize a document based on the provided configuration.
        
        Args:
            document_content: The content of the document to summarize
            config: Summarization configuration
            document_metadata: Optional metadata about the document
            
        Returns:
            A summarized document
        """
        logger.info(f"Summarizing document with {config.summary_type} approach")
        
        if config.summary_type == "extractive":
            summary, key_points = await self._extractive_summarization(document_content, config)
        elif config.summary_type == "abstractive":
            summary, key_points = await self._abstractive_summarization(document_content, config)
        elif config.summary_type == "hierarchical":
            summary, key_points = await self._hierarchical_summarization(document_content, config)
        else:
            raise ValueError(f"Unsupported summarization type: {config.summary_type}")
        
        # Create a summarized document
        return SummarizedDocument(
            original_content=document_content,
            summary=summary,
            key_points=key_points,
            summary_type=config.summary_type,
            confidence_score=0.9,  # Placeholder, should be calculated
            metadata=document_metadata or {}
        )
    
    async def _extractive_summarization(
        self, 
        document_content: str,
        config: SummarizationConfig
    ) -> Tuple[str, List[str]]:
        """
        Perform extractive summarization by selecting important sentences.
        
        Args:
            document_content: The content to summarize
            config: Summarization configuration
            
        Returns:
            Summary text and key points
        """
        # Create a prompt for the LLM
        prompt = f"""
You are a legal document summarization expert. Create an extractive summary of the following legal document by selecting the most important sentences and passages.

DOCUMENT:
{document_content}

INSTRUCTIONS:
1. Extract the most important sentences and paragraphs that capture the key legal points
2. Maintain the original wording of the extracted sentences
3. Ensure the summary is approximately {int(config.extraction_ratio * 100)}% the length of the original
4. Include important legal terms, citations, and references
5. Organize the extracted content in a coherent manner
6. After the summary, list the 5-7 key points of the document

FORMAT:
SUMMARY:
[Your extractive summary here]

KEY POINTS:
- [Key point 1]
- [Key point 2]
- etc.
"""
        
        # Call the LLM
        response = await self.llm.invoke(prompt)
        
        # Extract summary and key points
        summary_pattern = r"SUMMARY:(.*?)(?:KEY POINTS:|$)"
        key_points_pattern = r"KEY POINTS:(.*?)$"
        
        summary_match = re.search(summary_pattern, response, re.DOTALL)
        key_points_match = re.search(key_points_pattern, response, re.DOTALL)
        
        summary = summary_match.group(1).strip() if summary_match else "Summary not found."
        
        key_points_text = key_points_match.group(1).strip() if key_points_match else ""
        key_points = [point.strip() for point in key_points_text.split('-') if point.strip()]
        
        return summary, key_points
    
    async def _abstractive_summarization(
        self, 
        document_content: str,
        config: SummarizationConfig
    ) -> Tuple[str, List[str]]:
        """
        Perform abstractive summarization by generating a new summary.
        
        Args:
            document_content: The content to summarize
            config: Summarization configuration
            
        Returns:
            Summary text and key points
        """
        # Create a prompt for the LLM
        length_constraint = ""
        if config.max_length:
            length_constraint = f"The summary should be no more than {config.max_length} words."
        
        prompt = f"""
You are a legal document summarization expert. Create an abstractive summary of the following legal document by generating a concise, coherent summary in your own words.

DOCUMENT:
{document_content}

INSTRUCTIONS:
1. Generate a concise summary that captures the key legal points and arguments
2. Use your own words to synthesize the information
3. Ensure legal accuracy and precision
4. {length_constraint}
5. Include references to important legal terms, citations, and precedents
6. After the summary, list the 5-7 key points of the document

FORMAT:
SUMMARY:
[Your abstractive summary here]

KEY POINTS:
- [Key point 1]
- [Key point 2]
- etc.
"""
        
        # Call the LLM
        response = await self.llm.invoke(prompt)
        
        # Extract summary and key points
        summary_pattern = r"SUMMARY:(.*?)(?:KEY POINTS:|$)"
        key_points_pattern = r"KEY POINTS:(.*?)$"
        
        summary_match = re.search(summary_pattern, response, re.DOTALL)
        key_points_match = re.search(key_points_pattern, response, re.DOTALL)
        
        summary = summary_match.group(1).strip() if summary_match else "Summary not found."
        
        key_points_text = key_points_match.group(1).strip() if key_points_match else ""
        key_points = [point.strip() for point in key_points_text.split('-') if point.strip()]
        
        return summary, key_points
    
    async def _hierarchical_summarization(
        self, 
        document_content: str,
        config: SummarizationConfig
    ) -> Tuple[str, List[str]]:
        """
        Perform hierarchical summarization at different levels of detail.
        
        Args:
            document_content: The content to summarize
            config: Summarization configuration
            
        Returns:
            Summary text and key points
        """
        # Create a prompt for the LLM
        detail_level_map = {
            "low": "Create a very brief overview with only the most essential points.",
            "medium": "Create a moderately detailed summary covering the main points and some supporting details.",
            "high": "Create a comprehensive summary that includes main points, supporting details, and nuanced arguments."
        }
        
        detail_instruction = detail_level_map.get(config.detail_level, detail_level_map["medium"])
        
        prompt = f"""
You are a legal document summarization expert. Create a hierarchical summary of the following legal document at multiple levels of detail.

DOCUMENT:
{document_content}

INSTRUCTIONS:
1. {detail_instruction}
2. Structure the summary hierarchically with main points and supporting details
3. Ensure legal accuracy and precision
4. Include references to important legal terms, citations, and precedents
5. After the summary, list the 5-7 key points of the document

FORMAT:
SUMMARY:
[Your hierarchical summary here]

KEY POINTS:
- [Key point 1]
- [Key point 2]
- etc.
"""
        
        # Call the LLM
        response = await self.llm.invoke(prompt)
        
        # Extract summary and key points
        summary_pattern = r"SUMMARY:(.*?)(?:KEY POINTS:|$)"
        key_points_pattern = r"KEY POINTS:(.*?)$"
        
        summary_match = re.search(summary_pattern, response, re.DOTALL)
        key_points_match = re.search(key_points_pattern, response, re.DOTALL)
        
        summary = summary_match.group(1).strip() if summary_match else "Summary not found."
        
        key_points_text = key_points_match.group(1).strip() if key_points_match else ""
        key_points = [point.strip() for point in key_points_text.split('-') if point.strip()]
        
        return summary, key_points
    
    async def extract_key_points(self, document_content: str, num_points: int = 5) -> List[str]:
        """
        Extract key points from a document.
        
        Args:
            document_content: The content to extract key points from
            num_points: Number of key points to extract
            
        Returns:
            List of key points
        """
        # Create a prompt for the LLM
        prompt = f"""
You are a legal document analysis expert. Extract the {num_points} most important key points from the following legal document.

DOCUMENT:
{document_content}

INSTRUCTIONS:
1. Identify the {num_points} most important legal points or arguments
2. Each point should be concise but capture a complete thought
3. Focus on substantive legal issues, not procedural details
4. Include citations or references where relevant
5. Ensure points are distinct from each other

FORMAT:
KEY POINTS:
- [Key point 1]
- [Key point 2]
- etc.
"""
        
        # Call the LLM
        response = await self.llm.invoke(prompt)
        
        # Extract key points
        key_points_pattern = r"KEY POINTS:(.*?)$"
        key_points_match = re.search(key_points_pattern, response, re.DOTALL)
        
        key_points_text = key_points_match.group(1).strip() if key_points_match else ""
        key_points = [point.strip() for point in key_points_text.split('-') if point.strip()]
        
        return key_points
    
    async def compare_documents(
        self, 
        documents: List[Tuple[str, str]]  # List of (document_id, content) tuples
    ) -> DocumentComparison:
        """
        Compare multiple documents and identify similarities and differences.
        
        Args:
            documents: List of (document_id, document_content) tuples
            
        Returns:
            Document comparison results
        """
        if len(documents) < 2:
            raise ValueError("At least 2 documents are required for comparison")
        
        # Extract document IDs and contents
        doc_ids = [doc_id for doc_id, _ in documents]
        doc_contents = [content for _, content in documents]
        # Precompute optional section for a third document to avoid backslash in f-string expression
        extra_doc_section = (
            "Document 3:\n- [Unique point 1]\n- [Unique point 2]\n- etc.\n"
            if len(documents) > 2 else ""
        )
        
        # Create a prompt for the LLM to compare documents
        docs_formatted = "\n\n".join([f"DOCUMENT {i+1}:\n{content}" for i, content in enumerate(doc_contents)])
        
        prompt = f"""
You are a legal document comparison expert. Compare the following legal documents and identify similarities and differences.

{docs_formatted}

INSTRUCTIONS:
1. Identify common themes, arguments, or legal points across all documents
2. Identify unique points or arguments in each document
3. Compare the legal reasoning and conclusions
4. Note any differences in citations or references
5. Assess the overall degree of similarity between documents

FORMAT:
SIMILARITIES:
- [Common point 1]
- [Common point 2]
- etc.

UNIQUE POINTS:
Document 1:
- [Unique point 1]
- [Unique point 2]
- etc.

Document 2:
- [Unique point 1]
- [Unique point 2]
- etc.

{extra_doc_section}

SIMILARITY ASSESSMENT:
[Your assessment of how similar the documents are, with a percentage estimate]
"""
        
        # Call the LLM
        response = await self.llm.invoke(prompt)
        
        # Extract similarities and differences
        similarities_pattern = r"SIMILARITIES:(.*?)(?:UNIQUE POINTS:|$)"
        unique_points_pattern = r"UNIQUE POINTS:(.*?)(?:SIMILARITY ASSESSMENT:|$)"
        assessment_pattern = r"SIMILARITY ASSESSMENT:(.*?)$"
        
        similarities_match = re.search(similarities_pattern, response, re.DOTALL)
        unique_points_match = re.search(unique_points_pattern, response, re.DOTALL)
        assessment_match = re.search(assessment_pattern, response, re.DOTALL)
        
        # Extract similarities
        similarities_text = similarities_match.group(1).strip() if similarities_match else ""
        common_points = [point.strip() for point in similarities_text.split('-') if point.strip()]
        
        # Extract unique points for each document
        unique_points_text = unique_points_match.group(1).strip() if unique_points_match else ""
        unique_points_dict = {}
        
        for i, doc_id in enumerate(doc_ids):
            doc_pattern = rf"Document {i+1}:(.*?)(?:Document {i+2}:|SIMILARITY ASSESSMENT:|$)"
            doc_match = re.search(doc_pattern, unique_points_text, re.DOTALL)
            
            if doc_match:
                doc_points_text = doc_match.group(1).strip()
                doc_points = [point.strip() for point in doc_points_text.split('-') if point.strip()]
                unique_points_dict[doc_id] = doc_points
            else:
                unique_points_dict[doc_id] = []
        
        # Extract similarity assessment and convert to percentages
        assessment_text = assessment_match.group(1).strip() if assessment_match else ""
        # Extract percentage values from the assessment text
        percentages = [float(p.strip('%')) / 100 for p in re.findall(r'(\d+(?:\.\d+)?)%', assessment_text)]
        
        # If no percentages found, use a default
        similarities = percentages if percentages else [0.5] * len(documents)
        
        # Create differences list
        differences = []
        for i, doc_id in enumerate(doc_ids):
            for point in unique_points_dict.get(doc_id, []):
                differences.append({
                    "document_id": doc_id,
                    "document_index": i,
                    "point": point
                })
        
        # Create document comparison
        return DocumentComparison(
            document_ids=doc_ids,
            document_names=[f"Document {i+1}" for i in range(len(documents))],
            similarities=similarities,
            differences=differences,
            common_points=common_points,
            unique_points=unique_points_dict
        )
    
    async def simplify_language(self, document_content: str, target_audience: str = "general") -> str:
        """
        Simplify legal language for non-expert audiences.
        
        Args:
            document_content: The content to simplify
            target_audience: The target audience (general, client, student)
            
        Returns:
            Simplified document content
        """
        # Create a prompt for the LLM
        audience_instruction = {
            "general": "the general public with no legal background",
            "client": "clients with basic understanding of their legal situation",
            "student": "law students with fundamental legal knowledge but limited expertise"
        }.get(target_audience, "the general public with no legal background")
        
        prompt = f"""
You are a legal communication expert. Simplify the following legal document for {audience_instruction}. 
Make it more accessible while preserving the important legal meaning.

DOCUMENT:
{document_content}

INSTRUCTIONS:
1. Replace complex legal jargon with plain language
2. Break down complex sentences into simpler ones
3. Explain legal concepts in straightforward terms
4. Use concrete examples where helpful
5. Maintain all important legal points and meanings
6. Preserve any citations or references but explain their significance

SIMPLIFIED DOCUMENT:
"""
        
        # Call the LLM
        simplified_content = await self.llm.invoke(prompt)
        return simplified_content

"""
Claude 4 Model Implementation via Amazon Bedrock
Supports Claude 4 and Claude 3.5 Sonnet through AWS Bedrock Runtime
"""
import os
import json
import asyncio
import time
from typing import Dict, Any, Optional, List
import logging
from functools import lru_cache

from app.utils.logger import get_logger

logger = get_logger(__name__)

class ClaudeModel:
    """
    Claude 4 model implementation using Amazon Bedrock
    """
    
    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize Claude model with AWS Bedrock client
        
        Args:
            region_name: AWS region for Bedrock service
        """
        self.region_name = region_name
        self.bedrock_client = None
        self.model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"  # Latest Claude 3.5 Sonnet
        self.fallback_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"  # Fallback to Claude 3 Sonnet
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Initialize the client
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the AWS Bedrock client"""
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            
            # Create the Bedrock runtime client
            self.bedrock_client = boto3.client(
                "bedrock-runtime",
                region_name=self.region_name
            )
            
            logger.info(f"Initialized Claude model with Bedrock client in {self.region_name}")
            
        except ImportError:
            logger.error("boto3 is required for Claude model. Install with: pip install boto3")
            raise ImportError("boto3 is required for Claude model")
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS credentials.")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {str(e)}")
            raise
    
    async def invoke(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Invoke Claude model via Bedrock
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        if self.bedrock_client is None:
            raise RuntimeError("Bedrock client not initialized")
        
        # Prepare the request
        request_body = self._prepare_request_body(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            system_prompt=system_prompt,
            **kwargs
        )
        
        # Try with primary model first, then fallback
        models_to_try = [self.model_id, self.fallback_model_id]
        
        for model_id in models_to_try:
            try:
                response = await self._invoke_with_retry(model_id, request_body)
                if response:
                    logger.info(f"Successfully generated response using {model_id}")
                    return response
            except Exception as e:
                logger.error(f"Failed to invoke {model_id}: {str(e)}")
                if model_id == models_to_try[-1]:  # Last model
                    raise
                continue
        
        raise RuntimeError("All Claude models failed to generate a response")
    
    async def _invoke_with_retry(self, model_id: str, request_body: Dict[str, Any]) -> str:
        """
        Invoke model with retry logic for throttling
        
        Args:
            model_id: The model ID to invoke
            request_body: Request body for the model
            
        Returns:
            Generated response
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Invoking {model_id} (attempt {attempt + 1}/{self.max_retries})")
                
                # Run the blocking call in a thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    self._invoke_bedrock_sync,
                    model_id,
                    request_body
                )
                
                return self._extract_response_text(response)
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
                # Check if it's a throttling error
                if self._is_throttling_error(e):
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.info(f"Throttling detected, retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                        continue
                
                # If not throttling or max retries reached, raise
                if attempt == self.max_retries - 1:
                    raise
        
        # Should not reach here, but just in case
        raise last_exception
    
    def _invoke_bedrock_sync(self, model_id: str, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous Bedrock invocation for executor
        
        Args:
            model_id: The model ID to invoke
            request_body: Request body for the model
            
        Returns:
            Raw response from Bedrock
        """
        try:
            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body),
                contentType="application/json"
            )
            
            return json.loads(response['body'].read().decode('utf-8'))
            
        except Exception as e:
            logger.error(f"Bedrock invocation failed: {str(e)}")
            raise
    
    def _prepare_request_body(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Prepare request body for Claude model
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Returns:
            Request body dictionary
        """
        # Format messages for Claude
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Prepare the request body
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "messages": messages
        }
        
        # Add system prompt if provided
        if system_prompt:
            request_body["system"] = system_prompt
        
        # Add additional parameters
        for key, value in kwargs.items():
            if key not in request_body and value is not None:
                request_body[key] = value
        
        return request_body
    
    def _extract_response_text(self, response: Dict[str, Any]) -> str:
        """
        Extract text from Claude response
        
        Args:
            response: Raw response from Bedrock
            
        Returns:
            Extracted text
        """
        try:
            # Claude returns content in specific format
            if "content" in response:
                content = response["content"]
                if isinstance(content, list) and len(content) > 0:
                    # Extract text from the first content item
                    first_content = content[0]
                    if isinstance(first_content, dict) and "text" in first_content:
                        return first_content["text"]
                    elif isinstance(first_content, str):
                        return first_content
                elif isinstance(content, str):
                    return content
            
            # Fallback extraction methods
            if "completion" in response:
                return response["completion"]
            
            if "text" in response:
                return response["text"]
            
            # If no recognizable format, return string representation
            logger.warning(f"Unexpected response format: {response}")
            return str(response)
            
        except Exception as e:
            logger.error(f"Error extracting response text: {str(e)}")
            return f"Error processing response: {str(e)}"
    
    def _is_throttling_error(self, exception: Exception) -> bool:
        """
        Check if the exception is a throttling error
        
        Args:
            exception: Exception to check
            
        Returns:
            True if it's a throttling error
        """
        try:
            import botocore.exceptions
            
            if isinstance(exception, botocore.exceptions.ClientError):
                error_code = exception.response.get('Error', {}).get('Code', '')
                return error_code in ['ThrottlingException', 'TooManyRequestsException', 'ServiceQuotaExceededException']
            
            # Check error message for throttling indicators
            error_message = str(exception).lower()
            throttling_indicators = [
                'throttling',
                'rate limit',
                'too many requests',
                'quota exceeded',
                'service quota'
            ]
            
            return any(indicator in error_message for indicator in throttling_indicators)
            
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the Claude model
        
        Returns:
            Model information dictionary
        """
        return {
            "name": "Claude-3.5-Sonnet",
            "provider": "Anthropic",
            "service": "Amazon Bedrock",
            "model_id": self.model_id,
            "fallback_model_id": self.fallback_model_id,
            "region": self.region_name,
            "context_length": 200000,
            "max_tokens": 8192,
            "strengths": ["reasoning", "analysis", "safety", "long_context"],
            "use_cases": ["legal_analysis", "document_analysis", "complex_reasoning"]
        }
    
    def is_available(self) -> bool:
        """
        Check if the Claude model is available
        
        Returns:
            True if available
        """
        try:
            # Simple check by attempting to initialize client
            if self.bedrock_client is None:
                return False
            
            # Could add a simple test call here if needed
            return True
            
        except Exception:
            return False
    
    async def stream_invoke(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """
        Stream invoke Claude model for real-time responses
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Yields:
            Chunks of generated text
        """
        if self.bedrock_client is None:
            raise RuntimeError("Bedrock client not initialized")
        
        # Prepare request body
        request_body = self._prepare_request_body(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            system_prompt=system_prompt,
            **kwargs
        )
        
        try:
            # Use invoke_model_with_response_stream for streaming
            loop = asyncio.get_event_loop()
            response_stream = await loop.run_in_executor(
                None,
                lambda: self.bedrock_client.invoke_model_with_response_stream(
                    modelId=self.model_id,
                    body=json.dumps(request_body),
                    contentType="application/json"
                )
            )
            
            # Process stream
            stream = response_stream.get('body')
            if stream:
                for event in stream:
                    chunk = event.get('chunk', {})
                    if chunk:
                        chunk_data = json.loads(chunk.get('bytes', b'{}').decode('utf-8'))
                        if 'delta' in chunk_data:
                            delta = chunk_data['delta']
                            if 'text' in delta:
                                yield delta['text']
                        elif 'content' in chunk_data:
                            # Handle different streaming formats
                            content = chunk_data['content']
                            if isinstance(content, list) and len(content) > 0:
                                if 'text' in content[0]:
                                    yield content[0]['text']
                                    
        except Exception as e:
            logger.error(f"Error in streaming invoke: {str(e)}")
            raise

# Convenience functions
async def create_claude_model(region_name: str = "us-east-1") -> ClaudeModel:
    """
    Create a new Claude model instance
    
    Args:
        region_name: AWS region for Bedrock service
        
    Returns:
        ClaudeModel instance
    """
    return ClaudeModel(region_name=region_name)

def get_claude_model(region_name: str = "us-east-1") -> ClaudeModel:
    """
    Get a Claude model instance
    
    Args:
        region_name: AWS region for Bedrock service
        
    Returns:
        ClaudeModel instance
    """
    return ClaudeModel(region_name=region_name)
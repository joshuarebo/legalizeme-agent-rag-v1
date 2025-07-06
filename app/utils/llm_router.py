"""
Multi-LLM Router - Dynamic routing and execution for multiple LLM backends
Supports Hunyuan-A13B, Claude 4 via Bedrock, and existing models
"""
import os
import time
import asyncio
from typing import Any, Dict, Optional, List, Union
from enum import Enum
from functools import lru_cache
import logging

from app.utils.logger import get_logger
from app.utils.llm_factory import get_llm, get_fallback_llm, CachingLLM

logger = get_logger(__name__)

class ModelType(Enum):
    """Supported model types for routing"""
    HUNYUAN_A13B = "hunyuan-a13b"
    CLAUDE_4 = "claude-4"
    FLAN_T5 = "flan-t5"
    MIXTRAL = "mixtral"
    LLAMA = "llama"
    MINIMAX = "minimax"

class LLMRouter:
    """
    Multi-LLM Router that handles dynamic model selection and routing
    """
    
    def __init__(self):
        """Initialize the router with supported models"""
        self.model_cache = {}
        self.supported_models = {
            ModelType.HUNYUAN_A13B.value: self._get_hunyuan_model,
            ModelType.CLAUDE_4.value: self._get_claude_model,
            ModelType.FLAN_T5.value: self._get_flan_model,
            ModelType.MIXTRAL.value: self._get_mixtral_model,
            ModelType.LLAMA.value: self._get_llama_model,
            ModelType.MINIMAX.value: self._get_minimax_model,
        }
        
        # Model capabilities and use cases
        self.model_capabilities = {
            ModelType.HUNYUAN_A13B.value: {
                "max_tokens": 4096,
                "context_length": 32768,
                "strengths": ["chinese_legal", "multilingual", "reasoning"],
                "use_cases": ["legal_analysis", "complex_reasoning", "multilingual_support"]
            },
            ModelType.CLAUDE_4.value: {
                "max_tokens": 4096,
                "context_length": 200000,
                "strengths": ["legal_reasoning", "document_analysis", "safety"],
                "use_cases": ["legal_analysis", "document_summarization", "ethical_reasoning"]
            },
            ModelType.FLAN_T5.value: {
                "max_tokens": 512,
                "context_length": 2048,
                "strengths": ["instruction_following", "summarization"],
                "use_cases": ["simple_qa", "summarization", "classification"]
            },
            ModelType.MIXTRAL.value: {
                "max_tokens": 2048,
                "context_length": 32768,
                "strengths": ["general_reasoning", "multilingual", "efficiency"],
                "use_cases": ["legal_analysis", "general_qa", "reasoning"]
            },
            ModelType.LLAMA.value: {
                "max_tokens": 2048,
                "context_length": 8192,
                "strengths": ["reasoning", "instruction_following"],
                "use_cases": ["legal_analysis", "reasoning", "general_qa"]
            },
            ModelType.MINIMAX.value: {
                "max_tokens": 2048,
                "context_length": 4096,
                "strengths": ["chinese_support", "efficiency"],
                "use_cases": ["general_qa", "chinese_legal", "efficiency"]
            }
        }
        
        # Default model fallback chain
        self.fallback_chain = [
            ModelType.CLAUDE_4.value,
            ModelType.MIXTRAL.value,
            ModelType.LLAMA.value,
            ModelType.FLAN_T5.value
        ]
    
    async def route_model(
        self,
        prompt: str,
        model_choice: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Route the prompt to the specified model with fallback support
        
        Args:
            prompt: The input prompt
            model_choice: The model to use (hunyuan-a13b, claude-4, flan-t5, etc.)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            **kwargs: Additional model-specific parameters
            
        Returns:
            Generated response from the model
        """
        logger.info(f"Routing request to model: {model_choice}")
        
        # Validate model choice
        if model_choice not in self.supported_models:
            logger.warning(f"Unsupported model: {model_choice}, using fallback")
            model_choice = self.fallback_chain[0]
        
        # Prepare the full prompt with system prompt if provided
        full_prompt = self._prepare_prompt(prompt, system_prompt)
        
        # Try the requested model
        try:
            response = await self._invoke_model(
                model_choice, 
                full_prompt, 
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            if response and len(response.strip()) > 0:
                logger.info(f"Successfully got response from {model_choice}")
                return response
            else:
                logger.warning(f"Empty response from {model_choice}, trying fallback")
                
        except Exception as e:
            logger.error(f"Error with {model_choice}: {str(e)}")
        
        # Try fallback models
        for fallback_model in self.fallback_chain:
            if fallback_model == model_choice:
                continue  # Skip the model we already tried
                
            try:
                logger.info(f"Trying fallback model: {fallback_model}")
                response = await self._invoke_model(
                    fallback_model,
                    full_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                if response and len(response.strip()) > 0:
                    logger.info(f"Successfully got response from fallback {fallback_model}")
                    return response
                    
            except Exception as e:
                logger.error(f"Fallback {fallback_model} also failed: {str(e)}")
                continue
        
        # If all models fail, return error message
        logger.error("All models failed, returning error message")
        return "I apologize, but I'm currently unable to process your request due to technical difficulties. Please try again later."
    
    def _prepare_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Prepare the full prompt with system instructions"""
        if system_prompt:
            return f"{system_prompt}\n\nHuman: {prompt}\n\nAssistant:"
        return prompt
    
    async def _invoke_model(
        self,
        model_choice: str,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        Invoke the specified model with the given prompt
        
        Args:
            model_choice: The model to invoke
            prompt: The prepared prompt
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        # Route to specific model handlers
        if model_choice == ModelType.HUNYUAN_A13B.value:
            return await self.invoke_hunyuan(prompt, temperature=temperature, max_tokens=max_tokens, **kwargs)
        elif model_choice == ModelType.CLAUDE_4.value:
            return await self.invoke_claude(prompt, temperature=temperature, max_tokens=max_tokens, **kwargs)
        elif model_choice == ModelType.FLAN_T5.value:
            return await self.invoke_flan(prompt, temperature=temperature, max_tokens=max_tokens, **kwargs)
        else:
            # Use existing factory for other models
            return await self._invoke_existing_model(model_choice, prompt, temperature=temperature, max_tokens=max_tokens, **kwargs)
    
    async def invoke_hunyuan(self, prompt: str, **kwargs) -> str:
        """
        Invoke Hunyuan-A13B model
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        try:
            # Get or create Hunyuan model
            if ModelType.HUNYUAN_A13B.value not in self.model_cache:
                self.model_cache[ModelType.HUNYUAN_A13B.value] = await self._get_hunyuan_model()
            
            model = self.model_cache[ModelType.HUNYUAN_A13B.value]
            
            # Handle model-specific parameters
            temperature = kwargs.get('temperature', 0.3)
            max_tokens = kwargs.get('max_tokens', 2048)
            
            # Generate response
            response = await model.generate(
                prompt,
                temperature=temperature,
                max_new_tokens=max_tokens,
                **kwargs
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error invoking Hunyuan model: {str(e)}")
            raise
    
    async def invoke_claude(self, prompt: str, **kwargs) -> str:
        """
        Invoke Claude 4 via Amazon Bedrock
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        try:
            # Get or create Claude model
            if ModelType.CLAUDE_4.value not in self.model_cache:
                self.model_cache[ModelType.CLAUDE_4.value] = await self._get_claude_model()
            
            model = self.model_cache[ModelType.CLAUDE_4.value]
            
            # Handle model-specific parameters
            temperature = kwargs.get('temperature', 0.3)
            max_tokens = kwargs.get('max_tokens', 2048)
            
            # Format prompt for Claude
            formatted_prompt = f"\n\nHuman: {prompt}\n\nAssistant:"
            
            # Generate response
            response = await model.invoke(
                formatted_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error invoking Claude model: {str(e)}")
            raise
    
    async def invoke_flan(self, prompt: str, **kwargs) -> str:
        """
        Invoke FLAN-T5 model (existing implementation)
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        try:
            # Get or create FLAN model
            if ModelType.FLAN_T5.value not in self.model_cache:
                self.model_cache[ModelType.FLAN_T5.value] = await self._get_flan_model()
            
            model = self.model_cache[ModelType.FLAN_T5.value]
            
            # Generate response
            response = await model.invoke(prompt, **kwargs)
            
            return response
            
        except Exception as e:
            logger.error(f"Error invoking FLAN model: {str(e)}")
            raise
    
    async def _invoke_existing_model(self, model_choice: str, prompt: str, **kwargs) -> str:
        """
        Invoke existing models through the factory
        
        Args:
            model_choice: The model to invoke
            prompt: The input prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        try:
            # Get or create model
            if model_choice not in self.model_cache:
                self.model_cache[model_choice] = get_llm(model_choice)
            
            model = self.model_cache[model_choice]
            
            # Generate response
            response = await model.invoke(prompt, **kwargs)
            
            return response
            
        except Exception as e:
            logger.error(f"Error invoking {model_choice} model: {str(e)}")
            raise
    
    async def _get_hunyuan_model(self):
        """Get Hunyuan-A13B model instance"""
        from app.utils.hunyuan_model import HunyuanModel
        return HunyuanModel()
    
    async def _get_claude_model(self):
        """Get Claude 4 model instance"""
        from app.utils.claude_model import ClaudeModel
        return ClaudeModel()
    
    async def _get_flan_model(self):
        """Get FLAN-T5 model instance"""
        return get_llm("flan-t5")
    
    async def _get_mixtral_model(self):
        """Get Mixtral model instance"""
        return get_llm("mixtral")
    
    async def _get_llama_model(self):
        """Get LLaMA model instance"""
        return get_llm("llama")
    
    async def _get_minimax_model(self):
        """Get MiniMax model instance"""
        return get_llm("minimax")
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported model names"""
        return list(self.supported_models.keys())
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        return self.model_capabilities.get(model_name, {})
    
    def get_all_models_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all supported models"""
        return self.model_capabilities

# Global router instance
_router_instance = None

def get_router() -> LLMRouter:
    """Get the global router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = LLMRouter()
    return _router_instance

# Convenience functions for backward compatibility
async def route_model(
    prompt: str,
    model_choice: str,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    system_prompt: Optional[str] = None,
    **kwargs
) -> str:
    """Convenience function to route a model request"""
    router = get_router()
    return await router.route_model(
        prompt=prompt,
        model_choice=model_choice,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
        **kwargs
    )
"""
Hunyuan-A13B Model Implementation
Supports 4-bit/8-bit quantization with bitsandbytes for efficient inference
"""
import os
import asyncio
from typing import Dict, Any, Optional, List
from functools import lru_cache
import logging

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Conditional import for heavy dependencies
try:
    import torch
    import transformers
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    import bitsandbytes
    import accelerate
    HEAVY_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Heavy ML dependencies not available: {e}")
    HEAVY_DEPENDENCIES_AVAILABLE = False
    torch = None
    transformers = None
    AutoTokenizer = None
    AutoModelForCausalLM = None
    BitsAndBytesConfig = None
    bitsandbytes = None
    accelerate = None

class HunyuanModel:
    """
    Hunyuan-A13B model implementation with quantization support
    """
    
    _instance = None
    _model = None
    _tokenizer = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern to ensure only one model instance"""
        if cls._instance is None:
            cls._instance = super(HunyuanModel, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the model if not already initialized"""
        if not self._initialized:
            self._initialize_model()
            self._initialized = True
    
    def _initialize_model(self):
        """Initialize the Hunyuan-A13B model with quantization"""
        try:
            logger.info("Initializing Hunyuan-A13B model...")
            
            # Check if required packages are available
            if not HEAVY_DEPENDENCIES_AVAILABLE:
                logger.error("Heavy ML dependencies not available - Hunyuan model will use stub responses")
                self._model = None
                self._tokenizer = None
                return
            
            # Model configuration
            model_name = "Tencent-Hunyuan/Hunyuan-A13B-Chat"
            cache_dir = os.getenv("MODEL_CACHE_DIR", "./data/hunyuan_cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            # Quantization configuration
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            
            # Check device availability
            device_map = "auto" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device map: {device_map}")
            
            # Initialize tokenizer
            logger.info("Loading Hunyuan tokenizer...")
            self._tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                trust_remote_code=True,
                use_fast=False
            )
            
            # Initialize model with quantization
            logger.info("Loading Hunyuan model with quantization...")
            self._model = AutoModelForCausalLM.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                device_map=device_map,
                quantization_config=quantization_config,
                trust_remote_code=True,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                low_cpu_mem_usage=True,
                use_flash_attention_2=False  # Disable flash attention for compatibility
            )
            
            # Set padding token if not present
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token
            
            logger.info("Hunyuan-A13B model initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Hunyuan model: {str(e)}")
            # Set to None to indicate failure
            self._model = None
            self._tokenizer = None
            raise
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_new_tokens: int = 2048,
        do_sample: bool = True,
        top_p: float = 0.8,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
        **kwargs
    ) -> str:
        """
        Generate text using Hunyuan-A13B model
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_new_tokens: Maximum tokens to generate
            do_sample: Whether to use sampling
            top_p: Top-p sampling parameter
            top_k: Top-k sampling parameter
            repetition_penalty: Repetition penalty
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        if self._model is None or self._tokenizer is None:
            # Return stub response when model is not available
            if not HEAVY_DEPENDENCIES_AVAILABLE:
                logger.warning("Hunyuan model not available - returning stub response")
                return self._get_stub_response(prompt)
            else:
                raise RuntimeError("Hunyuan model not properly initialized")
        
        try:
            # Format prompt for chat model
            formatted_prompt = self._format_chat_prompt(prompt)
            
            # Tokenize input
            inputs = self._tokenizer(
                formatted_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=self._get_max_input_length(),
                padding=False
            )
            
            # Move to device
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Generate response
            logger.info(f"Generating with Hunyuan, max_new_tokens: {max_new_tokens}")
            
            # Run generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            outputs = await loop.run_in_executor(
                None,
                self._generate_sync,
                inputs,
                temperature,
                max_new_tokens,
                do_sample,
                top_p,
                top_k,
                repetition_penalty,
                kwargs
            )
            
            # Decode response
            response = self._tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            )
            
            # Clean up response
            response = self._clean_response(response)
            
            logger.info(f"Hunyuan generation completed, response length: {len(response)}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating with Hunyuan: {str(e)}")
            raise
    
    def _generate_sync(
        self,
        inputs,
        temperature,
        max_new_tokens,
        do_sample,
        top_p,
        top_k,
        repetition_penalty,
        kwargs
    ):
        """Synchronous generation for executor"""
        with torch.no_grad():
            return self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=do_sample,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                pad_token_id=self._tokenizer.pad_token_id,
                eos_token_id=self._tokenizer.eos_token_id,
                **kwargs
            )
    
    def _format_chat_prompt(self, prompt: str) -> str:
        """Format prompt for Hunyuan chat model"""
        # Hunyuan uses a specific chat format
        return f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    
    def _clean_response(self, response: str) -> str:
        """Clean and format the generated response"""
        # Remove special tokens and extra whitespace
        response = response.strip()
        
        # Remove common artifacts
        artifacts = [
            "<|im_end|>",
            "<|endoftext|>",
            "<|im_start|>",
            "assistant\n",
            "user\n"
        ]
        
        for artifact in artifacts:
            response = response.replace(artifact, "")
        
        # Clean up whitespace
        response = response.strip()
        
        return response
    
    def _get_max_input_length(self) -> int:
        """Get maximum input length for the model"""
        # Hunyuan-A13B has 32k context length
        return 30000  # Leave some room for generation
    
    def _get_stub_response(self, prompt: str) -> str:
        """Get a stub response when the model is not available"""
        return f"""Based on your query: "{prompt[:100]}..."

I'm a legal AI assistant powered by Hunyuan-A13B. Currently, the full model is not available in this environment, but I can provide general guidance on Kenyan legal matters.

For comprehensive legal analysis, please ensure the full model dependencies are available or consider using alternative models like Claude-4 or the standard fallback options.

Key legal considerations for your query:
- Relevant Kenyan statutes and regulations
- Constitutional provisions that may apply
- Recent case law and precedents
- Procedural requirements and timelines

Please note: This is a simplified response. For detailed legal analysis, the full Hunyuan-A13B model would provide more comprehensive insights."""
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model"""
        return {
            "name": "Hunyuan-A13B-Chat",
            "provider": "Tencent",
            "context_length": 32768,
            "max_tokens": 4096,
            "quantization": "4-bit" if self._model is not None else "Not loaded",
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "initialized": self._initialized
        }
    
    def is_available(self) -> bool:
        """Check if the model is available and initialized"""
        return self._initialized and self._model is not None and self._tokenizer is not None

# Convenience functions
async def create_hunyuan_model() -> HunyuanModel:
    """Create a new Hunyuan model instance"""
    return HunyuanModel()

def get_hunyuan_model() -> HunyuanModel:
    """Get the global Hunyuan model instance"""
    return HunyuanModel()
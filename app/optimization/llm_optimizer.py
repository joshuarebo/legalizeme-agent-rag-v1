"""
LLM Optimizer - For optimizing LLM inference parameters
"""
import os
import time
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import threading
from app.utils.logger import get_logger

logger = get_logger(__name__)

class LLMOptimizer:
    """
    Optimizer for LLM inference parameters.
    
    This class provides methods to optimize LLM parameters for faster inference
    while maintaining output quality.
    """
    
    def __init__(self):
        """Initialize the LLM optimizer."""
        self.config_path = os.getenv("LLM_CONFIG_PATH", "./data/llm_config")
        os.makedirs(self.config_path, exist_ok=True)
        
        # Default optimization parameters
        self.model_params = {
            "mixtral": {
                "temperature": float(os.getenv("MIXTRAL_TEMPERATURE", "0.3")),
                "top_p": float(os.getenv("MIXTRAL_TOP_P", "0.95")),
                "repetition_penalty": float(os.getenv("MIXTRAL_REPETITION_PENALTY", "1.15")),
                "max_new_tokens": int(os.getenv("MIXTRAL_MAX_NEW_TOKENS", "1024")),
                "batch_size": int(os.getenv("MIXTRAL_BATCH_SIZE", "1")),
                "use_flash_attention": os.getenv("MIXTRAL_USE_FLASH_ATTENTION", "True").lower() in ("true", "1", "t"),
                "use_4bit": os.getenv("MIXTRAL_USE_4BIT", "True").lower() in ("true", "1", "t"),
                "use_cache": os.getenv("MIXTRAL_USE_CACHE", "True").lower() in ("true", "1", "t"),
                "use_kv_cache": os.getenv("MIXTRAL_USE_KV_CACHE", "True").lower() in ("true", "1", "t"),
                "optimized": False
            },
            "llama3": {
                "temperature": float(os.getenv("LLAMA3_TEMPERATURE", "0.3")),
                "top_p": float(os.getenv("LLAMA3_TOP_P", "0.95")),
                "repetition_penalty": float(os.getenv("LLAMA3_REPETITION_PENALTY", "1.15")),
                "max_new_tokens": int(os.getenv("LLAMA3_MAX_NEW_TOKENS", "1024")),
                "batch_size": int(os.getenv("LLAMA3_BATCH_SIZE", "1")),
                "use_flash_attention": os.getenv("LLAMA3_USE_FLASH_ATTENTION", "True").lower() in ("true", "1", "t"),
                "use_4bit": os.getenv("LLAMA3_USE_4BIT", "True").lower() in ("true", "1", "t"),
                "use_cache": os.getenv("LLAMA3_USE_CACHE", "True").lower() in ("true", "1", "t"),
                "use_kv_cache": os.getenv("LLAMA3_USE_KV_CACHE", "True").lower() in ("true", "1", "t"),
                "optimized": False
            },
            "minimax": {
                "temperature": float(os.getenv("MINIMAX_TEMPERATURE", "0.3")),
                "top_p": float(os.getenv("MINIMAX_TOP_P", "0.95")),
                "repetition_penalty": float(os.getenv("MINIMAX_REPETITION_PENALTY", "1.15")),
                "max_new_tokens": int(os.getenv("MINIMAX_MAX_NEW_TOKENS", "1024")),
                "batch_size": int(os.getenv("MINIMAX_BATCH_SIZE", "1")),
                "use_flash_attention": os.getenv("MINIMAX_USE_FLASH_ATTENTION", "True").lower() in ("true", "1", "t"),
                "use_4bit": os.getenv("MINIMAX_USE_4BIT", "True").lower() in ("true", "1", "t"),
                "use_cache": os.getenv("MINIMAX_USE_CACHE", "True").lower() in ("true", "1", "t"),
                "use_kv_cache": os.getenv("MINIMAX_USE_KV_CACHE", "True").lower() in ("true", "1", "t"),
                "optimized": False
            }
        }
        
        # Performance metrics
        self.performance_metrics = {
            "mixtral": {"avg_token_time": None, "avg_response_time": None},
            "llama3": {"avg_token_time": None, "avg_response_time": None},
            "minimax": {"avg_token_time": None, "avg_response_time": None}
        }
        
        # Load saved configurations and metrics
        self._load_config()
        
        # Optimization lock
        self.optimization_lock = threading.Lock()
    
    def _load_config(self):
        """Load saved LLM configurations and metrics."""
        try:
            config_file = f"{self.config_path}/llm_params.json"
            metrics_file = f"{self.config_path}/llm_metrics.json"
            
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    saved_params = json.load(f)
                    # Update only existing models to preserve structure
                    for model, params in saved_params.items():
                        if model in self.model_params:
                            self.model_params[model].update(params)
            
            if os.path.exists(metrics_file):
                with open(metrics_file, "r") as f:
                    saved_metrics = json.load(f)
                    # Update only existing models to preserve structure
                    for model, metrics in saved_metrics.items():
                        if model in self.performance_metrics:
                            self.performance_metrics[model].update(metrics)
                            
        except Exception as e:
            logger.error(f"Error loading LLM configurations: {str(e)}")
    
    def _save_config(self):
        """Save LLM configurations and metrics."""
        try:
            config_file = f"{self.config_path}/llm_params.json"
            metrics_file = f"{self.config_path}/llm_metrics.json"
            
            with open(config_file, "w") as f:
                json.dump(self.model_params, f, indent=2)
            
            with open(metrics_file, "w") as f:
                json.dump(self.performance_metrics, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving LLM configurations: {str(e)}")
    
    def get_optimal_parameters(self, model_type: str) -> Dict[str, Any]:
        """
        Get optimal parameters for a specific LLM model.
        
        Args:
            model_type: Type of the LLM model (mixtral, llama3, minimax)
            
        Returns:
            Dictionary with optimal parameters
        """
        model_type = model_type.lower()
        if model_type not in self.model_params:
            logger.warning(f"Unknown model type: {model_type}, using mixtral parameters")
            model_type = "mixtral"
        
        # Return a copy to avoid direct modification
        return dict(self.model_params[model_type])
    
    def update_performance_metrics(self, model_type: str, token_time: float, response_time: float):
        """
        Update performance metrics for a model.
        
        Args:
            model_type: Type of the LLM model
            token_time: Average time per token
            response_time: Total response time
        """
        model_type = model_type.lower()
        if model_type not in self.performance_metrics:
            return
        
        metrics = self.performance_metrics[model_type]
        
        # Update exponential moving average
        alpha = 0.2  # Weight for new observations
        
        if metrics["avg_token_time"] is None:
            metrics["avg_token_time"] = token_time
        else:
            metrics["avg_token_time"] = (1 - alpha) * metrics["avg_token_time"] + alpha * token_time
        
        if metrics["avg_response_time"] is None:
            metrics["avg_response_time"] = response_time
        else:
            metrics["avg_response_time"] = (1 - alpha) * metrics["avg_response_time"] + alpha * response_time
        
        # Save updated metrics
        self._save_config()
    
    def optimize_model_parameters(self, model_type: str) -> Dict[str, Any]:
        """
        Optimize parameters for a specific LLM model.
        
        Args:
            model_type: Type of the LLM model
            
        Returns:
            Dictionary with optimized parameters
        """
        model_type = model_type.lower()
        if model_type not in self.model_params:
            logger.warning(f"Unknown model type: {model_type}")
            return {}
        
        # Use lock to prevent concurrent optimization
        with self.optimization_lock:
            try:
                logger.info(f"Starting parameter optimization for {model_type}")
                
                # Get current parameters
                params = self.model_params[model_type]
                
                # Optimize for inference speed
                # These are empirically good settings for most use cases
                optimized_params = dict(params)
                
                # Adjust based on model type
                if model_type == "mixtral":
                    # Mixtral specific optimizations
                    optimized_params["temperature"] = 0.3  # Lower temperature for more deterministic outputs
                    optimized_params["top_p"] = 0.9  # Slightly lower top_p for faster sampling
                    optimized_params["use_4bit"] = True  # Use 4-bit quantization for memory efficiency
                    optimized_params["use_flash_attention"] = True  # Use flash attention for speed
                    optimized_params["use_kv_cache"] = True  # Use KV cache for faster generation
                    
                elif model_type == "llama3":
                    # LLaMA 3 specific optimizations
                    optimized_params["temperature"] = 0.3
                    optimized_params["top_p"] = 0.9
                    optimized_params["use_4bit"] = True
                    optimized_params["use_flash_attention"] = True
                    optimized_params["use_kv_cache"] = True
                    
                elif model_type == "minimax":
                    # MiniMax specific optimizations
                    optimized_params["temperature"] = 0.3
                    optimized_params["top_p"] = 0.9
                    optimized_params["use_4bit"] = True
                    optimized_params["use_flash_attention"] = True
                    optimized_params["use_kv_cache"] = True
                
                # Mark as optimized
                optimized_params["optimized"] = True
                
                # Update stored parameters
                self.model_params[model_type] = optimized_params
                
                # Save configurations
                self._save_config()
                
                logger.info(f"Parameter optimization completed for {model_type}")
                return optimized_params
                
            except Exception as e:
                logger.error(f"Error optimizing parameters for {model_type}: {str(e)}")
                return self.model_params[model_type]
    
    def optimize_all_models(self):
        """Optimize parameters for all models."""
        for model_type in self.model_params.keys():
            self.optimize_model_parameters(model_type)
    
    def get_performance_metrics(self, model_type: str = None) -> Dict[str, Any]:
        """
        Get performance metrics for models.
        
        Args:
            model_type: Type of the LLM model (optional)
            
        Returns:
            Dictionary with performance metrics
        """
        if model_type:
            model_type = model_type.lower()
            if model_type in self.performance_metrics:
                return {model_type: dict(self.performance_metrics[model_type])}
            return {}
        
        # Return all metrics
        return {k: dict(v) for k, v in self.performance_metrics.items()}

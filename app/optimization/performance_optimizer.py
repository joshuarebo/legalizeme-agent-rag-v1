"""
Performance Optimizer - Coordinates various optimization strategies
"""
import os
import time
import asyncio
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.optimization.vector_store_optimizer import VectorStoreOptimizer
from app.optimization.llm_optimizer import LLMOptimizer
from app.utils.logger import get_logger

logger = get_logger(__name__)

class PerformanceOptimizer:
    """
    Main performance optimizer that coordinates all optimization strategies.
    """
    
    def __init__(self):
        """Initialize the performance optimizer."""
        self.vector_optimizer = VectorStoreOptimizer()
        self.llm_optimizer = LLMOptimizer()
          # Optimization schedule settings
        self.auto_optimize = os.getenv("AUTO_OPTIMIZE", "True").lower() in ("true", "1", "t")
        
        try:
            interval_env = os.getenv("OPTIMIZATION_INTERVAL_HOURS", "24")
            self.optimization_interval_hours = int(interval_env.split('#')[0].strip())
        except (ValueError, AttributeError):
            logger.warning(f"Invalid OPTIMIZATION_INTERVAL_HOURS: {interval_env}, using default of 24")
            self.optimization_interval_hours = 24
        
        # Get time setting, removing any comments
        optimization_time_env = os.getenv("OPTIMIZATION_TIME", "03:00")
        self.optimization_time = optimization_time_env.split('#')[0].strip()
        
        # Thread for background optimization
        self.optimization_thread = None
        self.stop_optimization = threading.Event()
        
        # Response time tracking
        self.response_times = []
        self.max_response_samples = 100
        
        # Status tracking
        self.status = {
            "last_optimization": None,
            "next_optimization": None,
            "optimizations_performed": 0,
            "avg_response_time_ms": None,
            "vector_store_stats": {},
            "llm_stats": {}
        }
    
    def start(self):
        """Start the optimizer."""
        if self.auto_optimize and not self.optimization_thread:
            self.stop_optimization.clear()
            self.optimization_thread = threading.Thread(target=self._optimization_loop)
            self.optimization_thread.daemon = True
            self.optimization_thread.start()
            logger.info("Performance optimizer started")
    
    def stop(self):
        """Stop the optimizer."""
        if self.optimization_thread:
            self.stop_optimization.set()
            self.optimization_thread.join(timeout=1.0)
            self.optimization_thread = None
            logger.info("Performance optimizer stopped")
    
    def _optimization_loop(self):
        """Background thread for scheduled optimization."""
        while not self.stop_optimization.is_set():
            try:                # Check if it's time to optimize
                now = datetime.now()
                
                # Parse optimization time safely
                try:
                    time_parts = self.optimization_time.split(':')
                    if len(time_parts) == 2:
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    else:
                        # Default to 3 AM if format is invalid
                        logger.warning(f"Invalid optimization time format: {self.optimization_time}, defaulting to 03:00")
                        target_time = now.replace(hour=3, minute=0, second=0, microsecond=0)
                except ValueError:
                    logger.warning(f"Could not parse optimization time: {self.optimization_time}, defaulting to 03:00")
                    target_time = now.replace(hour=3, minute=0, second=0, microsecond=0)
                
                # If we've passed the target time, move to next day
                if now > target_time:
                    target_time = target_time + timedelta(days=1)
                
                # Calculate seconds until next optimization
                seconds_until_next = (target_time - now).total_seconds()
                
                # Update next optimization time
                self.status["next_optimization"] = target_time.isoformat()
                
                # Sleep until next optimization time, checking stop flag periodically
                sleep_interval = min(60, seconds_until_next)  # Check every minute or less
                
                while seconds_until_next > 0 and not self.stop_optimization.is_set():
                    time.sleep(min(sleep_interval, seconds_until_next))
                    seconds_until_next = (target_time - datetime.now()).total_seconds()
                
                # If we're stopping, exit the loop
                if self.stop_optimization.is_set():
                    break
                
                # Perform optimization
                self._perform_optimization()
                
                # Sleep briefly to prevent CPU hogging if something goes wrong with time calculation
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in optimization loop: {str(e)}")
                time.sleep(60)  # Sleep for a minute before retrying
    
    def _perform_optimization(self):
        """Perform all optimization tasks."""
        try:
            logger.info("Starting scheduled performance optimization")
            
            # First optimize the vector store
            if self.vector_optimizer.needs_optimization():
                logger.info("Optimizing vector store")
                self.vector_optimizer.optimize()
            
            # Then optimize LLM parameters
            logger.info("Optimizing LLM parameters")
            self.llm_optimizer.optimize_all_models()
            
            # Update status
            self.status["last_optimization"] = datetime.now().isoformat()
            self.status["optimizations_performed"] += 1
            self.status["vector_store_stats"] = self.vector_optimizer.get_optimization_stats()
            self.status["llm_stats"] = self.llm_optimizer.get_performance_metrics()
            
            logger.info("Performance optimization completed")
            
        except Exception as e:
            logger.error(f"Error performing optimization: {str(e)}")
    
    def optimize_now(self):
        """
        Manually trigger optimization.
        
        Returns:
            Dictionary with optimization results
        """
        try:
            start_time = time.time()
            
            # Perform optimization
            self._perform_optimization()
            
            # Compute duration
            duration = time.time() - start_time
            
            return {
                "status": "success",
                "duration_seconds": round(duration, 2),
                "vector_store": self.status["vector_store_stats"],
                "llm": self.status["llm_stats"]
            }
            
        except Exception as e:
            logger.error(f"Error in manual optimization: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def track_response_time(self, response_time_ms: float):
        """
        Track response time for performance monitoring.
        
        Args:
            response_time_ms: Response time in milliseconds
        """
        self.response_times.append(response_time_ms)
        
        # Keep only the most recent samples
        if len(self.response_times) > self.max_response_samples:
            self.response_times = self.response_times[-self.max_response_samples:]
        
        # Update average
        self.status["avg_response_time_ms"] = round(sum(self.response_times) / len(self.response_times), 2)
    
    def get_optimized_llm_params(self, model_type: str) -> Dict[str, Any]:
        """
        Get optimized parameters for a specific LLM model.
        
        Args:
            model_type: Type of the LLM model
            
        Returns:
            Dictionary with optimized parameters
        """
        return self.llm_optimizer.get_optimal_parameters(model_type)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get optimization status.
        
        Returns:
            Dictionary with optimization status
        """
        return self.status

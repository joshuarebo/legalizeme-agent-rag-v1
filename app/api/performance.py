"""
Performance API endpoints
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from typing import Dict, Any, Optional
from app.optimization.performance_optimizer import PerformanceOptimizer
from app.utils.logger import get_logger

router = APIRouter(
    prefix="/performance",
    tags=["performance"],
    responses={404: {"description": "Not found"}},
)

logger = get_logger(__name__)

# Singleton instance of the optimizer
_optimizer = None

def get_optimizer():
    """
    Get or create the performance optimizer singleton.
    """
    global _optimizer
    if _optimizer is None:
        _optimizer = PerformanceOptimizer()
    return _optimizer

@router.get("/status")
async def get_performance_status(
    optimizer: PerformanceOptimizer = Depends(get_optimizer)
):
    """
    Get the status of performance optimization.
    """
    return optimizer.get_status()

@router.post("/optimize")
async def trigger_optimization(
    background_tasks: BackgroundTasks,
    optimizer: PerformanceOptimizer = Depends(get_optimizer)
):
    """
    Manually trigger performance optimization.
    """
    # Use background tasks to avoid blocking the API call
    background_tasks.add_task(optimizer.optimize_now)
    return {"message": "Performance optimization triggered in the background"}

@router.post("/start")
async def start_optimizer(
    optimizer: PerformanceOptimizer = Depends(get_optimizer)
):
    """
    Start the performance optimizer scheduling.
    """
    optimizer.start()
    return {"message": "Performance optimizer started successfully"}

@router.post("/stop")
async def stop_optimizer(
    optimizer: PerformanceOptimizer = Depends(get_optimizer)
):
    """
    Stop the performance optimizer scheduling.
    """
    optimizer.stop()
    return {"message": "Performance optimizer stopped successfully"}

@router.get("/llm-params/{model_type}")
async def get_llm_params(
    model_type: str,
    optimizer: PerformanceOptimizer = Depends(get_optimizer)
):
    """
    Get optimized parameters for a specific LLM model.
    """
    params = optimizer.get_optimized_llm_params(model_type)
    return params

"""
Crawler API endpoints
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from typing import Dict, Any, Optional
from app.crawlers.scheduler import CrawlerScheduler
from app.utils.logger import get_logger

router = APIRouter(
    prefix="/crawler",
    tags=["crawler"],
    responses={404: {"description": "Not found"}},
)

logger = get_logger(__name__)

# Singleton instance of the scheduler
_scheduler = None

def get_scheduler():
    """
    Get or create the crawler scheduler singleton.
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = CrawlerScheduler()
    return _scheduler

@router.get("/status")
async def get_crawler_status(
    scheduler: CrawlerScheduler = Depends(get_scheduler)
):
    """
    Get the status of the crawler.
    """
    next_run_times = scheduler.get_next_run_times()
    crawl_stats = scheduler.crawler.get_crawl_stats()
    
    return {
        "status": "running" if scheduler.full_crawl_job else "stopped",
        "next_run_times": next_run_times,
        "crawl_stats": crawl_stats
    }

@router.post("/start")
async def start_crawler(
    scheduler: CrawlerScheduler = Depends(get_scheduler)
):
    """
    Start the crawler scheduler.
    """
    if scheduler.full_crawl_job:
        return {"message": "Crawler scheduler is already running"}
    
    await scheduler.start()
    return {"message": "Crawler scheduler started successfully"}

@router.post("/stop")
async def stop_crawler(
    scheduler: CrawlerScheduler = Depends(get_scheduler)
):
    """
    Stop the crawler scheduler.
    """
    if not scheduler.full_crawl_job:
        return {"message": "Crawler scheduler is not running"}
    
    await scheduler.stop()
    return {"message": "Crawler scheduler stopped successfully"}

@router.post("/trigger/full")
async def trigger_full_crawl(
    background_tasks: BackgroundTasks,
    scheduler: CrawlerScheduler = Depends(get_scheduler)
):
    """
    Manually trigger a full crawl.
    """
    # Use background tasks to avoid blocking the API call
    background_tasks.add_task(scheduler.run_full_crawl)
    return {"message": "Full crawl triggered in the background"}

@router.post("/trigger/quick")
async def trigger_quick_update(
    background_tasks: BackgroundTasks,
    scheduler: CrawlerScheduler = Depends(get_scheduler)
):
    """
    Manually trigger a quick update crawl.
    """
    # Use background tasks to avoid blocking the API call
    background_tasks.add_task(scheduler.run_quick_update)
    return {"message": "Quick update crawl triggered in the background"}

"""
Crawler Scheduler - Manages scheduling of the Kenya Law crawlers
"""
import os
import asyncio
import aiocron
from datetime import datetime
from dotenv import load_dotenv
from app.utils.logger import get_logger
from app.crawlers.kenya_law_crawler import KenyaLawCrawler

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

class CrawlerScheduler:
    """
    Scheduler for running the Kenya Law crawler at regular intervals.
    """
    def __init__(self):
        """Initialize the crawler scheduler."""
        self.crawler = KenyaLawCrawler()
        
        # Get schedule settings from environment
        daily_update_env = os.getenv("CRAWLER_DAILY_UPDATE_TIME", "02:00")
        try:
            # Extract just the time part, ignoring any comments
            self.daily_update_time = daily_update_env.split('#')[0].strip()
        except (ValueError, AttributeError):
            logger.warning(f"Invalid CRAWLER_DAILY_UPDATE_TIME value: {daily_update_env}, using default of 02:00")
            self.daily_update_time = "02:00"
        
        quick_update_env = os.getenv("CRAWLER_QUICK_UPDATE_HOURS", "6")
        try:
            self.quick_update_interval = int(quick_update_env.split('#')[0].strip())
        except (ValueError, AttributeError):
            logger.warning(f"Invalid CRAWLER_QUICK_UPDATE_HOURS value: {quick_update_env}, using default of 6")
            self.quick_update_interval = 6
        
        # Initialize cron jobs
        self.full_crawl_job = None
        self.quick_update_job = None
        
        # Track if initial crawl has been done
        self.initial_crawl_completed = False
    
    async def start(self):
        """Start the crawler scheduler."""
        logger.info("Starting crawler scheduler")
        
        # Schedule the daily full crawl
        self.full_crawl_job = aiocron.crontab(
            f"0 {self.daily_update_time.split(':')[0]} * * *",  # Run at specified hour daily
            func=self.run_full_crawl,
            start=True
        )
        
        # Schedule quick updates
        quick_cron_expr = f"0 */{self.quick_update_interval} * * *"  # Every X hours
        self.quick_update_job = aiocron.crontab(
            quick_cron_expr,
            func=self.run_quick_update,
            start=True
        )
        
        logger.info(f"Scheduled full crawl daily at {self.daily_update_time}")
        logger.info(f"Scheduled quick updates every {self.quick_update_interval} hours")
        
        # Run an initial crawl if the document store is empty
        doc_count = self.crawler.retriever.document_store.get_document_count()
        if doc_count == 0:
            logger.info("Document store is empty, running initial crawl")
            await self.run_initial_crawl()
    
    async def stop(self):
        """Stop the crawler scheduler."""
        logger.info("Stopping crawler scheduler")
        
        if self.full_crawl_job:
            self.full_crawl_job.stop()
        
        if self.quick_update_job:
            self.quick_update_job.stop()
    
    async def run_initial_crawl(self):
        """Run an initial crawl to populate the document store."""
        logger.info("Running initial crawl")
        
        try:
            # Run with a smaller page limit for faster initial setup
            original_limit = self.crawler.max_pages_per_section
            self.crawler.max_pages_per_section = 2
            
            await self.crawler.crawl_all_sections()
            
            # Restore original limit
            self.crawler.max_pages_per_section = original_limit
            
            self.initial_crawl_completed = True
            logger.info("Initial crawl completed")
            
        except Exception as e:
            logger.error(f"Error during initial crawl: {str(e)}")
    
    async def run_full_crawl(self):
        """Run a full crawl of all sections."""
        logger.info("Running scheduled full crawl")
        
        try:
            await self.crawler.crawl_all_sections()
            logger.info("Scheduled full crawl completed")
            
        except Exception as e:
            logger.error(f"Error during scheduled full crawl: {str(e)}")
    
    async def run_quick_update(self):
        """Run a quick update crawl (only recent content)."""
        logger.info("Running quick update crawl")
        
        try:
            # Skip if initial crawl hasn't been done yet
            if not self.initial_crawl_completed:
                logger.info("Skipping quick update - initial crawl not yet completed")
                return
            
            await self.crawler.crawl_recent_updates()
            logger.info("Quick update crawl completed")
            
        except Exception as e:
            logger.error(f"Error during quick update crawl: {str(e)}")
    
    def get_next_run_times(self):
        """
        Get the next scheduled run times.
        
        Returns:
            Dictionary with next run times
        """
        next_full = self.full_crawl_job.next() if self.full_crawl_job else None
        next_quick = self.quick_update_job.next() if self.quick_update_job else None
        
        return {
            "next_full_crawl": next_full.strftime("%Y-%m-%d %H:%M:%S") if next_full else None,
            "next_quick_update": next_quick.strftime("%Y-%m-%d %H:%M:%S") if next_quick else None,
            "initial_crawl_completed": self.initial_crawl_completed
        }

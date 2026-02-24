"""Task scheduler for background jobs."""
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import SessionLocal
from app.services.webhook_notifier import check_and_notify_overdue_orders

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scheduled_order_check():
    """Scheduled task to check for overdue orders."""
    logger.info("Running scheduled order check")
    db = SessionLocal()
    try:
        await check_and_notify_overdue_orders(db)
    except Exception as e:
        logger.error(f"Error in scheduled order check: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start the scheduler with all scheduled jobs."""
    scheduler.add_job(
        scheduled_order_check,
        trigger="cron",
        hour=9,
        minute=0,
        id="order_check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started successfully")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown successfully")


@asynccontextmanager
async def scheduler_lifespan():
    """Context manager for scheduler lifecycle."""
    start_scheduler()
    try:
        yield
    finally:
        shutdown_scheduler()

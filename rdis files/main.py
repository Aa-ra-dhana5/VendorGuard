from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.Routes.routes import event_route
from src.Routes.admin_routes import admin_route, set_scheduler
from src.Worker.scheduled_decision_worker import process_scheduled_decisions
from src.config.logger_config import get_scheduler_logger
from .redis_lock import init_redis, close_redis  


logger = get_scheduler_logger()

# Global scheduler instance
scheduler = None

version = 'v1'


async def startup_event():
    global scheduler
    
    try:
        await init_redis("redis://localhost:6379")  
        logger.info("Redis client initialized successfully")
        
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            process_scheduled_decisions,
            'interval',
            minutes=5,
            id='process_scheduled_decisions',
            name='Process pending scheduled payout decisions'
        )
        scheduler.start()
        set_scheduler(scheduler)
        logger.info("="*80)
        logger.info("SCHEDULER INITIALIZED SUCCESSFULLY")
        logger.info("="*80)
        logger.info("Job: Process Pending Scheduled Payout Decisions")
        logger.info("Interval: Every 5 minutes")
        logger.info("Status: RUNNING")
        logger.info("="*80)
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        raise


async def shutdown_event():
    global scheduler
    
    await close_redis()  
    logger.info("Redis client closed successfully")
    
    if scheduler:
        scheduler.shutdown()
        logger.info("="*80)
        logger.info("SCHEDULER SHUT DOWN SUCCESSFULLY")
        logger.info("="*80)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_event()
    yield
    await shutdown_event()


app = FastAPI(
    title='Vender',
    description='A REST API for Vendor Settlement with scheduled payout processing',
    version=version,
    lifespan=lifespan
)

app.include_router(event_route, prefix=f'/api/{version}', tags=['event'])
app.include_router(admin_route, prefix=f'/api/{version}/admin', tags=['admin'])
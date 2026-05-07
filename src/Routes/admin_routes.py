from fastapi import APIRouter, status
from src.Worker.scheduled_decision_worker import process_scheduled_decisions
import logging

logger = logging.getLogger(__name__)

admin_route = APIRouter()

# Global scheduler reference
_scheduler = None


## Scheduler set up by main file
def set_scheduler(scheduler):
    global _scheduler
    _scheduler = scheduler

## Manually trigger processing of scheduled decisions.
@admin_route.post('/process-scheduled-decisions', status_code=status.HTTP_200_OK, summary="Manually trigger scheduled decision processing")
async def manual_process_scheduled_decisions():
    try:
        await process_scheduled_decisions()
        return {
            "status": "success",
            "message": "Scheduled decisions processed successfully"
        }
    except Exception as e:
        logger.error(f"Error processing scheduled decisions: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


##  Get the current status of the scheduler.
@admin_route.get('/scheduler-status', status_code=status.HTTP_200_OK,summary="Get scheduler status and pending jobs")
async def scheduler_status():
    if not _scheduler:
        return {
            "status": "not_running",
            "message": "Scheduler not initialized"
        }
    
    return {
        "scheduler_running": _scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time) if job.next_run_time else "Not scheduled"
            }
            for job in _scheduler.get_jobs()
        ]
    }

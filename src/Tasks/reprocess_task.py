from src.celery_app import celery_app
from src.DB.db import SessionLocal
from src.Service.reprocessing_service import handle_reprocess

@celery_app.task(name="reprocess_order",  queue="reprocess", bind=True, max_retries=3)
def reprocess_order_task(self, order_id: str):
    async def _reprocess():
        async with SessionLocal() as session:
            try:
                mode, decision = await handle_reprocess(session, order_id, commit=True)
                return {"status": "success", "mode": mode, "decision_id": str(decision.id) if decision else None}
            except Exception as e:
                await session.rollback()
                raise self.retry(exc=e)

    import asyncio
    return asyncio.run(_reprocess())
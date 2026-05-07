from src.celery_app import celery_app
from src.DB.db import SessionLocal
from src.Service.scheduler_service import SchedulerService
from src.Service.audit_service import AuditService
from src.Model.model import OrderState, StatusEnum
from sqlalchemy import select

@celery_app.task(name="process_scheduled_decisions", queue="scheduled", bind=True)
def process_scheduled_decisions_task(self):
    async def _process():
        async with SessionLocal() as session:
            try:
                pending_decisions = await SchedulerService.get_pending_scheduled_decisions(session)
                
                if not pending_decisions:
                    return {"status": "no_pending", "processed": 0}

                processed = 0
                failed = 0

                for decision in pending_decisions:
                    try:
                        order_id = decision.order_id
                        stmt = select(OrderState).where(OrderState.order_id == order_id)
                        result = await session.exec(stmt)
                        order_state = result.first()

                        if not order_state:
                            failed += 1
                            continue

                        if all([
                            order_state.delivery_status,
                            order_state.kyc_status,
                            order_state.invoice_status,
                            order_state.settlement_status
                        ]):
                            await SchedulerService.mark_decision_executed(
                                order_id,
                                StatusEnum.released,
                                session
                            )
                            
                            await AuditService.log(
                                order_id,
                                "SCHEDULED_PAYOUT_RELEASED",
                                StatusEnum.released,
                                "Scheduled payout released after delay",
                                session
                            )
                            
                            processed += 1
                        else:
                            failed += 1

                    except Exception as e:
                        failed += 1
                        continue

                return {"status": "completed", "processed": processed, "failed": failed}

            except Exception as e:
                return {"status": "error", "message": str(e)}

    import asyncio
    return asyncio.run(_process())
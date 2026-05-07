from src.Service.scheduler_service import SchedulerService
from src.Service.audit_service import AuditService
from src.DB.db import SessionLocal
from sqlmodel import select
from src.Model.model import OrderState
from src.config.logger_config import get_scheduler_logger, get_decision_logger, get_audit_logger
from datetime import datetime, timezone
from src.Model.model import StatusEnum


logger = get_scheduler_logger()
decision_logger = get_decision_logger()
audit_logger = get_audit_logger()


async def process_scheduled_decisions():
    async with SessionLocal() as session:
        try:
            start_time = datetime.now(timezone.utc)
            logger.info(f"{'='*80}")
            logger.info(f"STARTED: Scheduled Decision Processing | Time: {start_time.isoformat()} UTC")
            logger.info(f"{'='*80}")
            
            pending_decisions = await SchedulerService.get_pending_scheduled_decisions(session)
            
            if not pending_decisions:
                logger.info("No pending scheduled decisions to process")
                return
            
            logger.info(f"Processing {len(pending_decisions)} pending scheduled decisions...")
            processed_count = 0
            failed_count = 0
            
            for decision in pending_decisions:
                try:
                    order_id = decision.order_id
                    decision_logger.info(
                        f"PROCESSING DECISION - ID: {decision.id} | "
                        f"Order: {order_id} | "
                        f"Status: {decision.decision_status}"
                    )
                    
                    stmt = select(OrderState).where(
                        OrderState.order_id == order_id
                    )
                    result = await session.exec(stmt)
                    order_state = result.first()
                    
                    if not order_state:
                        logger.error(f"Order state not found for order_id: {order_id}")
                        decision_logger.error(f"Order state not found for order_id: {order_id}")
                        failed_count += 1
                        continue
                    
                    if order_state.delivery_status and order_state.kyc_status and order_state.invoice_status and order_state.settlement_status :
                        session.add(order_state)
                        await session.commit()
                        
                        audit_reason = f"Scheduled payout released after {decision.decision_status} delay"
                        
                        await AuditService.log(
                            order_id,
                            "SCHEDULED_PAYOUT_RELEASED",
                            decision.decision_status,
                            audit_reason,
                            session
                        )
                        
                        decision_logger.info(
                            f"PAYOUT RELEASED - Order: {order_id} | "
                            f"Delivery: {order_state.delivery_status} | "
                            f"KYC: {order_state.kyc_status} | "
                            f"Invoice: {order_state.invoice_status} | "
                            f"Settlement: {order_state.settlement_status}"
                        )
                        
                        audit_logger.info(
                            f"PAYOUT RELEASED AUDIT - Order: {order_id} | "
                            f"Action: SCHEDULED_PAYOUT_RELEASED | "
                            f"Decision Status: {decision.decision_status} | "
                            f"Reason: {audit_reason}"
                        )
                        
                        logger.info(f"Released payout for order: {order_id}")
                    else:
                        logger.warning(
                            f"Cannot release payout - Order: {order_id} | "
                            f"Delivery: {order_state.delivery_status} | "
                            f"KYC: {order_state.kyc_status} | "
                            f"Invoice: {order_state.invoice_status}"|
                            f"Settlement: {order_state.settlement_status}"
                        )
                        decision_logger.warning(
                            f"INCOMPLETE CONDITIONS - Order: {order_id} | "
                            f"Skipping payout release"
                        )
                        failed_count += 1
                        continue
                    
                    await SchedulerService.mark_decision_executed(order_id, StatusEnum.released, session)
                    logger.info(f"Marked decision {decision.id} as executed for order: {order_id}")
                    processed_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error processing decision {decision.id}: {str(e)}")
                    decision_logger.error(f"Error processing decision {decision.id}: {str(e)}")
                    await session.rollback()
                    continue
            
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"{'='*80}")
            logger.info(
                f"COMPLETED: Scheduled Decision Processing | "
                f"Processed: {processed_count} | "
                f"Failed: {failed_count} | "
                f"Duration: {duration:.2f}s"
            )
            logger.info(f"{'='*80}")
            
        except Exception as e:
            logger.error(f"Critical error in process_scheduled_decisions: {str(e)}")
            await session.rollback()
            raise

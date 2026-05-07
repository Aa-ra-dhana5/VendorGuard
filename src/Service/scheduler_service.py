from datetime import datetime, timezone, timedelta
from src.Model.model import OrderState, Payment_typeEnum, StatusEnum, Decision
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config.logger_config import get_scheduler_logger
from src.Service.decision_service import DecisionService

logger = get_scheduler_logger()
decision_service = DecisionService()

class SchedulerService:

    SCHEDULE_DELAYS = {
        Payment_typeEnum.cod: timedelta(days=7),
        Payment_typeEnum.prepaid: timedelta(minutes=2),
    }

    @staticmethod
    async def schedule_decision( order_id: str,payment_method: Payment_typeEnum,session: AsyncSession) -> datetime:
        if payment_method not in SchedulerService.SCHEDULE_DELAYS:
            logger.warning(f"Unsupported payment method: {payment_method} for order {order_id}")
            return None
        
        delay = SchedulerService.SCHEDULE_DELAYS[payment_method]
        scheduled_at = datetime.now(timezone.utc) + delay
        
        logger.info(
            f"SCHEDULED DECISION - Order: {order_id} | "
            f"Payment Method: {payment_method} | "
            f"Delay: {delay.days} days | "
            f"Scheduled At: {scheduled_at.isoformat()} UTC"
        )
        
        return scheduled_at

    @staticmethod
    async def get_pending_scheduled_decisions(session: AsyncSession) -> list:
        now = datetime.now(timezone.utc)
         
        stmt = select(Decision).where(
            Decision.scheduled_at <= now,
            Decision.is_executed == False
        )
        
        result = await session.exec(stmt)
        pending_decisions = result.all()
        
        if pending_decisions:
            logger.info(
                f"PENDING DECISIONS FOUND - Count: {len(pending_decisions)} | "
                f"Current Time: {now.isoformat()} UTC"
            )
            for decision in pending_decisions:
                logger.debug(
                    f"  Pending Decision - ID: {decision.id} | "
                    f"Order: {decision.order_id} | "
                    f"Status: {decision.decision_status} | "
                    f"Scheduled At: {decision.scheduled_at.isoformat()}"
                )
        else:
            logger.debug(f"No pending scheduled decisions at {now.isoformat()} UTC")
        
        return pending_decisions

    @staticmethod
    async def mark_decision_executed(
        order_id,
        decision_status,
        session: AsyncSession
    ):  
        # decision = await decision_service.save_decision(order_id, 'RELEASED', 'ALL CONDITION SAISFIED', session)
        statement = select(Decision).where(Decision.order_id == order_id,Decision.is_executed == False).order_by(Decision.created_at).limit(1)
        result = await session.exec(statement)
        decision = result.first()
        
        if decision:
            decision.is_executed = True
            decision.decision_status = decision_status
            decision.reason = 'SCHEDULED_PAYOUT_RELEASED'
            session.add(decision)
            await session.commit()
            await session.refresh(decision)
            
        logger.info(
                f"DECISION EXECUTED - ID: {decision.id} | "
                f"Order: {decision.order_id} | "
                f"Status: {decision.decision_status} | "
                f"Executed At: {datetime.now(timezone.utc).isoformat()} UTC"
            )
        
        return decision

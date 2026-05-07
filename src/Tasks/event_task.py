from src.celery_app import celery_app
from src.DB.db import SessionLocal
from src.Service.state_service import StateService
from src.Service.rule_engine import RuleEngine
from src.Service.decision_service import DecisionService
from src.Service.audit_service import AuditService
from src.Service.scheduler_service import SchedulerService
from src.Model.model import OrderState, StatusEnum, Payment_typeEnum
from sqlalchemy import select

state_service = StateService()
rule_engine = RuleEngine()

@celery_app.task(name="process_event", queue="events",bind=True, max_retries=3, default_retry_delay=60)
def process_event_task(self, event_data: dict):
    async def _process():
        async with SessionLocal() as session:
            try:
                # Get or create order state
                stmt = select(OrderState).where(OrderState.order_id == event_data['order_id'])
                result = await session.exec(stmt)
                existing_state = result.first()

                if existing_state:
                    state = await state_service.update_state(existing_state, event_data)
                else:
                    state = await state_service.build_state(event_data, session)
                
                await session.commit()

                # Process decision
                order_id = event_data['order_id']
                state_dict = state.model_dump()
                payment_method_enum = state_dict.get('payment_method')
                payment_method = getattr(payment_method_enum, "value", payment_method_enum) if payment_method_enum else None

                decision, reason = rule_engine.evaluate(state_dict)

                scheduled_at = None
                if payment_method and rule_engine.should_schedule_decision(str(payment_method)):
                    if payment_method_enum is None:
                        payment_method_enum = Payment_typeEnum(payment_method.upper())
                    scheduled_at = await SchedulerService.schedule_decision(order_id, payment_method_enum, session)

                if scheduled_at:
                    decision = StatusEnum.on_hold
                    reason = 'Decision is scheduled.'

                await DecisionService.save_decision(order_id, decision, reason, session, scheduled_at=scheduled_at)

                event_type = event_data.get('event_type', 'EVENT')
                audit_note = f"{reason}. Scheduled: {bool(scheduled_at)}"
                await AuditService.log(order_id, event_type, decision, audit_note, session)

            except Exception as e:
                await session.rollback()
                raise self.retry(exc=e)

    import asyncio
    asyncio.run(_process())
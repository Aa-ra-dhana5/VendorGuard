from src.Service.state_service import StateService
from src.Service.rule_engine import RuleEngine
from src.Service.audit_service import AuditService
from src.Service.decision_service import DecisionService
from src.Service.scheduler_service import SchedulerService
from src.DB.db import SessionLocal
from sqlmodel import select
from src.Model.model import OrderState
from src.Model.model import StatusEnum

state_service = StateService()
rule_engine = RuleEngine()

async def process_event_async(event_data: dict):

    async with SessionLocal() as session:
        try:
            stmt = select(OrderState).where(
                OrderState.order_id == event_data['order_id']
            )

            result = await session.exec(stmt)
            existing_state = result.first()

            if existing_state:
                print('existing state is ...', existing_state)
                state = await state_service.update_state(
                    existing_state, event_data
                )
            else:
                print('not existing state...')
                state = await state_service.build_state(
                    event_data, session
                )

            await session.commit()

        except Exception:
            await session.rollback()
            raise
        
        
        order_id = event_data['order_id']
        state_dict = state.model_dump()
        payment_method_enum = state_dict['payment_method']
        payment_method = getattr(payment_method_enum, "value", payment_method_enum)

        print("moving to take decision in decision engine.........:")
        
        decision, reason = rule_engine.evaluate(state_dict)
        
        print('scheduling requirements are getting checked ..........')
        print('payment method is .......' , payment_method)
        
        
        scheduled_at = None
        if rule_engine.should_schedule_decision(str(payment_method)):
            scheduled_at = await SchedulerService.schedule_decision(
                order_id, 
                payment_method, 
                session
            )
            print(f"Decision scheduled for {payment_method}: {scheduled_at}")
            
        if scheduled_at:
            decision = StatusEnum.on_hold  
            reason = 'Decision is scheduled.'
        else:
            decision
            
        await DecisionService.save_decision(
            order_id, 
            decision, 
            reason, 
            session,
            scheduled_at=scheduled_at
        )
        print("decision is saved and moving to audit save")

        event_type = event_data['event_type']
        audit_note = f"{reason}. Scheduled: {bool(scheduled_at)}"
        await AuditService.log(order_id, event_type, decision, audit_note, session)
        
        
    
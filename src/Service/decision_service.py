from src.Model.model import Decision 

class DecisionService:

    @staticmethod
    async def save_decision(order_id, decision, reason, session, scheduled_at=None):
        print("Decision saving.........:")
 
        if not (decision and reason):
            return None

        decision_data = Decision(
            order_id=order_id,
            decision_status=decision,
            reason=reason,
            scheduled_at=scheduled_at,
            is_executed=False if scheduled_at else True
        )
        
        session.add(decision_data)
        await session.commit()
        await session.refresh(decision_data)  
        print("Decision saved.........:")
        
        return decision_data
            

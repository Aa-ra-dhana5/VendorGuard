from src.Model.model import AuditLog

class AuditService:

    @staticmethod
    async def log(order_id, event : str, decision, reason ,session , commit: bool = True):
        print("Audit saving.........:")
        audit_data = AuditLog(
            order_id= order_id,
            action_type=event,
            performed_by="user",
            notes=reason                
        )
            
        session.add(audit_data)
        if commit:
            await session.commit()
            await session.refresh(audit_data)  
            print("Audit saved.........:")
            
        return audit_data
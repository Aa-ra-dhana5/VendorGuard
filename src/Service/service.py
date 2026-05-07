from sqlmodel.ext.asyncio.session import AsyncSession
from src.Model.model import Decision, StatusEnum
from sqlmodel import select, desc
from src.Service.decision_service import DecisionService
from src.Service.audit_service import AuditService

decision_service = DecisionService()
audit_service = AuditService()


class CommonService:
    async def get_decision(self, order_id:str , session: AsyncSession):
        # stmt  =select(Decision).where(Decision.order_id == order_id).order_by(desc(Decision.created_at)).limit(1)
        # result = await session.exec(stmt)
        # print('the secisons are......', result)
        # decision = result.first()
        # return decision
        
        stmt = (
        select(Decision)
        .where(Decision.order_id == order_id)
        .order_by(desc(Decision.created_at))
        )

        result = await session.exec(stmt)
        decisions = result.all()

        if not decisions:
            return None

        latest_time = decisions[0].created_at

        same_time_decisions = [
            d for d in decisions if d.created_at == latest_time
        ]

        return same_time_decisions[-1]  # last one from Python list
    
    async def get_decision_history(self, order_id:str , session: AsyncSession):
        stmt  =select(Decision).where(Decision.order_id == order_id)
        result = await session.exec(stmt)
        decisions = result.all() 
        return decisions
    

    async def get_review_cases(self, session: AsyncSession):
        stmt = select(Decision).where(
            Decision.decision_status.in_([StatusEnum.block, StatusEnum.manual_check])
        )
        result = await session.exec(stmt)
        return result.all()
    
    async def post_override_data(self, decision, event_name,session: AsyncSession):
       decision_dict_data = decision.model_dump()
       order_id = decision_dict_data['order_id']
       for status in StatusEnum:
           if status.value == decision_dict_data['decision_status']:               
                decision_status = status
                print('decision is ....' , decision_status)
       reason = decision_dict_data['reason']
       
       new_decision = await decision_service.save_decision(order_id, decision_status, reason, session)
       await audit_service.log(order_id, event_name ,decision_status, reason, session, commit=False,)
       

       return new_decision

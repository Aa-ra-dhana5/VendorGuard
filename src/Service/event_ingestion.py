from src.Model.model import Event 
from sqlmodel.ext.asyncio.session import AsyncSession
from src.Schema.schema import EventCreate , OrderState
from sqlmodel import select 
from src.Tasks.event_task import process_event_task


class EventService:

    async def process_event(self, event_data: EventCreate, session: AsyncSession):
        event_dict_data = event_data.model_dump()
        
        stmt = select(Event).where(Event.event_id == event_dict_data['event_id'])
        existing = await session.exec(stmt)
        existing = existing.first() 
        
        if existing:
            return None
        
        new_event = Event(**event_dict_data)
        session.add(new_event)
        await session.commit()
        await session.refresh(new_event)

        process_event_task.delay(new_event.model_dump())

        return new_event
    
    
    
    
    
    # from src.Worker.event_worker import process_event_async

    # async def process_event(self, event_data: EventCreate ,session : AsyncSession):
    #     event_dict_data = event_data.model_dump()
    #     # print('event informtation ----------- ',event_dict_data)
    #     new_event=Event(
    #         **event_dict_data
    #     )

    #     #Check duplicate
    #     stmt = select(Event).where(Event.event_id == new_event.event_id)
    #     existing = await session.exec(stmt)
    #     existing = existing.first() 
    #     # print('existing event -------',existing)
    #     if existing:
    #         return None
        
       
    #     session.add(new_event)
    #     await session.commit()
        

    #     #Trigger async worker
    #     print("process_event calling worker")
    #     await process_event_async(new_event.model_dump())
    #     print('process executed ')
        
        
    #     return new_event
    

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.Schema.schema import (
    Event,
    EventCreate,
    DecisionCreate,
    ReprocessRequest,
    ReprocessResponse,
)
from src.DB.db import get_session
from src.Service.event_ingestion import EventService
from src.Service.service import CommonService
from src.Tasks.reprocess_task import reprocess_order_task

_EVENT_OPENAPI_EXAMPLES = {
    "prepaid_scheduled": {
        "summary": "PREPAID — all gates OK (decision scheduled)",
        "description": "Use a **new** `event_id` each time you Send. Same `order_id` updates state.",
        "value": {
            "event_id": "demo-prepaid-001",
            "order_id": "ORD-DEMO-PREPAID-001",
            "event_type": "ORDER_UPDATE",
            "payload": {
                "payment_method": "PREPAID",
                "total_amount": 999.0,
                "paid_amount": 999.0,
                "refund_amount": 0,
                "delivery_status": True,
                "settlement_status": True,
                "kyc_status": True,
                "invoice_status": True,
                "fraud_flag": False,
            },
        },
    },
    "cod_on_hold": {
        "summary": "COD — invoice not satisfied (on hold + scheduled)",
        "description": "Change `event_id` per request.",
        "value": {
            "event_id": "demo-cod-001",
            "order_id": "ORD-DEMO-COD-001",
            "event_type": "ORDER_UPDATE",
            "payload": {
                "payment_method": "COD",
                "total_amount": 500.0,
                "paid_amount": 500.0,
                "refund_amount": 0,
                "delivery_status": True,
                "settlement_status": True,
                "kyc_status": True,
                "invoice_status": False,
                "fraud_flag": False,
            },
        },
    },
    "fraud_manual_check": {
        "summary": "PREPAID — fraud flag → MANUAL CHECK",
        "value": {
            "event_id": "demo-fraud-001",
            "order_id": "ORD-DEMO-FRAUD-001",
            "event_type": "RISK_UPDATE",
            "payload": {
                "payment_method": "PREPAID",
                "total_amount": 100.0,
                "paid_amount": 100.0,
                "refund_amount": 0,
                "delivery_status": True,
                "settlement_status": True,
                "kyc_status": True,
                "invoice_status": True,
                "fraud_flag": True,
            },
        },
    },
    "partial_refund": {
        "summary": "Refund amount → PARTIALLY RELEASED",
        "value": {
            "event_id": "demo-refund-001",
            "order_id": "ORD-DEMO-REFUND-001",
            "event_type": "ORDER_UPDATE",
            "payload": {
                "payment_method": "PREPAID",
                "total_amount": 200.0,
                "paid_amount": 200.0,
                "refund_amount": 50.0,
                "delivery_status": True,
                "settlement_status": True,
                "kyc_status": True,
                "invoice_status": True,
                "fraud_flag": False,
            },
        },
    },
}


event_route =APIRouter()
event_service =EventService()
app_service = CommonService()

@event_route.post('/event',status_code=status.HTTP_201_CREATED, response_model=Event)
async def create_event(
    event: EventCreate = Body(openapi_examples=_EVENT_OPENAPI_EXAMPLES),
    session: AsyncSession = Depends(get_session),
):
    new_event = await event_service.process_event(event , session) 
    if new_event:  
        return new_event 
    else:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Event already exist")
    

@event_route.get('/payout/{order_id}')
async def get_latest_decision_of_order(order_id : str, session : AsyncSession =Depends(get_session)):
    decision = await app_service.get_decision(order_id, session)    
    if decision:
        return decision
    else:
        raise HTTPException(status_code= status.HTTP_204_NO_CONTENT, detail='This order does not exist')


@event_route.get('/payout/{order_id}/history')
async def get_history_of_order(order_id : str, session : AsyncSession =Depends(get_session)):
    decisions = await app_service.get_decision_history(order_id, session)    
    if decisions:
        return decisions
    else:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail='This order does not exist')


@event_route.get('/review-cases')
async def review_cases(session : AsyncSession =Depends(get_session)):
    review_cases_data = await app_service.get_review_cases(session)
    
    print('review caseas data is ...', review_cases_data)
    if not review_cases_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,  # Use 404 for "not found" - more appropriate
                detail='No Blocked or Manual reviewed decisions'
        )    
    return review_cases_data

@event_route.post('/overrides')
async def override_data(decision :DecisionCreate , event_name: str ,session : AsyncSession =Depends(get_session)):
    new_decision_data = await app_service.post_override_data(decision,event_name, session)
    
    if new_decision_data:
        return new_decision_data
    else:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT , detail='Mismathced data')
    
 


@event_route.post("/reprocessing", response_model=ReprocessResponse)
async def reprocess_the_event(
    body: ReprocessRequest,
    session: AsyncSession = Depends(get_session),
):
    task = reprocess_order_task.delay(body.order_id)
    
    return ReprocessResponse(
        order_id=body.order_id,
        mode="queued",
        decision_id=None,
    )
    
    
    
# from src.Service.reprocessing_service import handle_reprocess
       
# @event_route.post("/reprocessing", response_model=ReprocessResponse)
# async def reprocess_the_event(
#     body: ReprocessRequest,
#     session: AsyncSession = Depends(get_session),
# ):
#     try:
#         mode, decision = await handle_reprocess(session, body.order_id, commit=True)
#     except ValueError as e:
#         if str(e) == "order_not_found":
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Order state not found for this order_id",
#             ) from e
#         raise
#     return ReprocessResponse(
#         order_id=body.order_id,
#         mode=mode,
#         decision_id=decision.id if decision else None,
#     )
from pydantic import BaseModel
import uuid
from datetime import datetime
from src.Model.model import StatusEnum, Payment_typeEnum

class Event(BaseModel):     
    id: uuid.UUID
    event_id: str
    order_id: str
    event_type : str
    payload: dict
    created_at : datetime 

class EventCreate(BaseModel):
    event_id: str
    order_id: str
    event_type : str
    payload: dict


class OrderState(BaseModel):    
    id: uuid.UUID
    order_id:str 
    total_amount :float 
    paid_amount :float
    refund_amount :float
    payment_method :Payment_typeEnum 
    delivery_status :bool
    settlement_status :bool
    kyc_status :bool
    fraud_flag: bool
    invoice_status :bool
    updated_at : datetime 
    created_at : datetime          
    
    
class Decision(BaseModel):    
        id: uuid.UUID
        order_id :str 
        decision_status:StatusEnum
        reason :str
        created_at : datetime    
              
class DecisionCreate(BaseModel):    
        order_id :str 
        decision_status:StatusEnum
        reason :str
         
class ReprocessRequest(BaseModel):
        order_id: str


class ReprocessResponse(BaseModel):
        order_id: str
        mode: str
        decision_id: uuid.UUID | None = None
             
class AuditLog(BaseModel):    
        id: uuid.UUID
        order_id :str
        action_type :str
        performed_by :str
        notes : str
        created_at : datetime
        updated_at : datetime 

   
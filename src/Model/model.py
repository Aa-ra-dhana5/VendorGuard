from sqlmodel import SQLModel , Field, Column, Relationship , JSON 
import uuid
import sqlalchemy.dialects.postgresql as pg
from datetime import datetime,timezone
from enum import Enum

class StatusEnum(str, Enum):
    released = "RELEASED"
    on_hold = "ON HOLD"
    partially_released = "PARTIALLY RELEASED"
    manual_check = "MANUAL CHECK"
    block = "BLOCK"
    cancelled = "CANCELLED"
    recovery = "RECOVERY"
    
class Payment_typeEnum(str, Enum):
    cod = "COD"
    prepaid = "PREPAID"



class Event(SQLModel, table=True):
    __tablename__ = 'event'
    __table_args__ = {"schema": "public"}
    
    id: uuid.UUID = Field(
        sa_column = Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4
            )
    )
    event_id: str = Field(
        sa_column=Column(
            pg.VARCHAR,
            unique=True,
            nullable=False
        )
    )
    order_id: str = Field(nullable=False)
    event_type: str = Field(nullable=False)
    payload: dict = Field(
        sa_column=Column(
            JSON,
            nullable=False
        )
    )
    created_at : datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=datetime.now(timezone.utc)))
    
    def __repr__(self):
        return f'<Event{Event.id}>'
    
    
class OrderState(SQLModel, table=True):
    __tablename__ ='orderstate'
    
    id: uuid.UUID= Field(
        sa_column = Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4
            )
    )
    order_id: str = Field(nullable=False, unique=True)
    total_amount: float = Field(default=0)
    paid_amount: float = Field(default=0)
    refund_amount: float = Field(default=0)
    payment_method: Payment_typeEnum = Field(nullable=True)
    delivery_status: bool = Field(default=False)
    settlement_status: bool = Field(default=False)
    kyc_status: bool = Field(default=False)
    fraud_flag: bool = Field(default=False)
    invoice_status: bool = Field(default=False)

    updated_at : datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=datetime.now(timezone.utc)))
    created_at : datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=datetime.now(timezone.utc)))
    
    # Relationships 
    decisions: list["Decision"] = Relationship(back_populates="orderstate", cascade_delete=True)
    audits: list["AuditLog"] = Relationship(back_populates="orderstate", cascade_delete=True)
    
    
    def __repr__(self):
         return f'<Order_state{OrderState.id}>'
    
    
class Decision(SQLModel, table=True):
    __tablename__ = 'decision'

    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4
        )
    )
    order_id: str = Field(foreign_key='orderstate.order_id', nullable=False)
    decision_status: StatusEnum = Field(nullable=False)
    reason: str = Field(nullable=False)
    scheduled_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=True), default=None)
    is_executed: bool = Field(default=False)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=datetime.now(timezone.utc)))
    orderstate: "OrderState" = Relationship(back_populates="decisions")

    def __repr__(self):
        return f'<Decision{Decision.id}>'
    
class AuditLog(SQLModel, table=True):
    __tablename__ = 'auditlog'

    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID,
            nullable=False,
            primary_key=True,
            default=uuid.uuid4
        )
    )
    order_id: str = Field(foreign_key='orderstate.order_id', nullable=False)
    action_type: str = Field(nullable=False)
    performed_by: str = Field(nullable=False)
    notes: str = Field(nullable=True)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=datetime.now(timezone.utc)))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=datetime.now(timezone.utc)))
    orderstate: "OrderState" = Relationship(back_populates="audits")

    def __repr__(self):
        return f'<AuditLog{AuditLog.id}>'

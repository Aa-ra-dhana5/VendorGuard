from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from sqlmodel import select, desc
from sqlmodel.ext.asyncio.session import AsyncSession

from src.Model.model import Decision, OrderState, StatusEnum, Payment_typeEnum
from src.DB.pg_locks import acquire_order_advisory_xact_lock
from src.Service.audit_service import AuditService
from src.Service.decision_service import DecisionService
from src.Service.rule_engine import RuleEngine
from src.Service.scheduler_service import SchedulerService

rule_engine = RuleEngine()

RECOVERY_REASON = "Reprocess after RELEASED payout; recovery requested"
CANCEL_PENDING_REASON = "Reprocess: pending scheduled payout cancelled"
RECOVERY_AUDIT_PREFIX = "reprocess_recovery"


def order_state_to_rule_dict(order_state: OrderState) -> dict:
    return order_state.model_dump()


async def _latest_decision(session: AsyncSession, order_id: str) -> Decision | None:
    stmt = (
        select(Decision)
        .where(Decision.order_id == order_id)
        .order_by(desc(Decision.created_at), desc(Decision.id))
        .limit(1)
    )
    res = await session.exec(stmt)
    return res.first()


async def _pending_scheduled_decisions(session: AsyncSession, order_id: str) -> list[Decision]:
    stmt = select(Decision).where(
        Decision.order_id == order_id,
        Decision.is_executed == False,
    )
    res = await session.exec(stmt)
    return [r for r in res.all() if r.scheduled_at is not None]


async def process_decision_after_event(
    session: AsyncSession,
    order_id: str,
    order_state: OrderState,
    event_type: str,
    *,
    commit: bool = True,
) -> Decision | None:
    state_dict = order_state_to_rule_dict(order_state)
    payment_method_enum = state_dict.get("payment_method")
    payment_method_str = (
        getattr(payment_method_enum, "value", payment_method_enum)
        if payment_method_enum is not None
        else ""
    )

    decision_status, reason = rule_engine.evaluate(state_dict)

    scheduled_at = None
    pm: Payment_typeEnum | None = None
    if isinstance(payment_method_enum, Payment_typeEnum):
        pm = payment_method_enum
    elif payment_method_str:
        try:
            pm = Payment_typeEnum(payment_method_str)
        except ValueError:
            pm = None

    if pm is not None and rule_engine.should_schedule_decision(str(payment_method_str)):
        scheduled_at = await SchedulerService.schedule_decision(order_id, pm, session)

    row = await DecisionService.save_decision(
        order_id,
        decision_status,
        reason,
        session,
        scheduled_at=scheduled_at,
       
    )
    audit_note = f"{reason}. Scheduled: {bool(scheduled_at)}"
    await AuditService.log(
        order_id, event_type, decision_status, audit_note, session ,commit=False
    )
    if commit:
        await session.commit()
        if row:
            await session.refresh(row)
    return row


async def try_execute_scheduled_decision(
    session: AsyncSession,
    pending: Decision,
    order_state: OrderState,
    *,
    commit: bool = True,
) -> bool:
    state_dict = order_state_to_rule_dict(order_state)
    decision_status, reason = rule_engine.evaluate(state_dict)

    if decision_status != StatusEnum.released:
        return False

    pending.is_executed = True
    pending.decision_status = StatusEnum.released
    pending.reason = reason + " (scheduled execution)"
    session.add(pending)

    await AuditService.log(
        order_state.order_id,
        "SCHEDULED_PAYOUT_RELEASED",
        StatusEnum.released,
        f"Scheduled payout released. {reason}",
        session,
        commit=False,
    )
    if commit:
        await session.commit()
        await session.refresh(pending)
    return True


async def handle_reprocess(
    session: AsyncSession,
    order_id: str,
    *,
    commit: bool = True,
) -> tuple[Literal["recovery", "cancelled_pending", "reevaluated"], Decision | None]:
    await acquire_order_advisory_xact_lock(session, order_id)

    stmt = select(OrderState).where(OrderState.order_id == order_id)
    res = await session.exec(stmt)
    order_state = res.first()
    if not order_state:
        raise ValueError("order_not_found")

    latest = await _latest_decision(session, order_id)

    if (
        latest
        and latest.is_executed
        and latest.decision_status == StatusEnum.released
    ):
        recovery = await DecisionService.save_decision(
            order_id,
            StatusEnum.recovery,
            RECOVERY_REASON,
            session,
            scheduled_at=None,
            
        )
        await AuditService.log(
            order_id,
            "REPROCESS",
            StatusEnum.recovery,
            f"{RECOVERY_AUDIT_PREFIX}: {RECOVERY_REASON}",
            session,
            commit=False,
        )
        if commit:
            await session.commit()
            if recovery:
                await session.refresh(recovery)
        return "recovery", recovery

    pending_rows = await _pending_scheduled_decisions(session, order_id)
    if pending_rows:
        now = datetime.now(timezone.utc)
        for row in pending_rows:
            row.is_executed = True
            row.decision_status = StatusEnum.cancelled
            row.reason = CANCEL_PENDING_REASON
            session.add(row)
        await AuditService.log(
            order_id,
            "REPROCESS",
            StatusEnum.cancelled,
            f"Cancelled {len(pending_rows)} pending scheduled payout(s) at {now.isoformat()}",
            session,
            commit=False,
        )

    row = await process_decision_after_event(
        session,
        order_id,
        order_state,
        "REPROCESS",
        commit=False,
    )
    if commit:
        await session.commit()
        if row:
            await session.refresh(row)

    mode: Literal["cancelled_pending", "reevaluated"] = (
        "cancelled_pending" if pending_rows else "reevaluated"
    )
    return mode, row

from src.Model.model import  OrderState as Statemodel
from src.Schema.schema import OrderState
from sqlmodel.ext.asyncio.session import AsyncSession


class StateService:

    fields = [
        "total_amount",
        "paid_amount",
        "refund_amount",
        "payment_method",
        "delivery_status",
        "settlement_status",
        "kyc_status",
        "invoice_status"
    ]

    async def build_state(self, event_dict_data: dict, session: AsyncSession):

        state = Statemodel(
            order_id=event_dict_data['order_id'],
            total_amount=0,
            paid_amount=0,
            refund_amount=0,
            payment_method=None,
            delivery_status=False,
            settlement_status=False,
            kyc_status=False,
            invoice_status=False
        )

        payload = event_dict_data.get("payload", {})

        for field in self.fields:
            value = payload.get(field)
            if value is not None:
                setattr(state, field, value)

        await self.create_state(state, session)
        return state

    @staticmethod
    async def create_state(state: OrderState, session: AsyncSession):
        print('state is creating in db.......')
        session.add(state)
        await session.flush()   
        await session.refresh(state)
        return state

    async def update_state(self, state: OrderState, event_dict_data: dict):

        payload = event_dict_data.get("payload", {})

        for field in self.fields:
            value = payload.get(field)
            if value is not None:
                setattr(state, field, value)

        print('state updated successfully !!')
        return state
from src.Model.model import StatusEnum, Payment_typeEnum


class RuleEngine:

    status_fields = [
        "delivery_status",
        "settlement_status",
        "kyc_status",
        "invoice_status"
    ]

    def evaluate(self, state: dict):

        for field in self.status_fields:
            value = state.get(field)
            if value is False or value is None:
                return StatusEnum.on_hold, f"{field} is not satisfied"

        if state.get("fraud_flag"):
            return StatusEnum.manual_check, "Fraud detected"
        
        if state.get("Complience"):
            return StatusEnum.block, "Seller Complience"

        if state.get("refund_amount", 0) > 0:
            return StatusEnum.partially_released, "Refund exists"

        if state.get("delivery_status") and state.get("settlement_status"):
            return StatusEnum.released, "All conditions met"

        return StatusEnum.on_hold, "Conditions not met"

    def should_schedule_decision(self, payment_method: str) -> bool:
        if not payment_method:
            raise ValueError("payment_method is required")

        normalized = payment_method.upper()
        print('scehduler payment method is ..........', normalized)
        valid_methods = {e.value.upper() for e in Payment_typeEnum}
        print('valid methods are .....', valid_methods)
        if normalized not in valid_methods:
            raise ValueError(f"Invalid payment_method: {payment_method}")

        return normalized in {
            Payment_typeEnum.cod.value.upper(),
            Payment_typeEnum.prepaid.value.upper()
        }
"""Transaction domain model and associated enumerations."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.domain.users import AppVersion, BankName

TransactionType = Literal["transfer", "wallet_funding", "bill_payment"]
TransactionStatus = Literal[
    "started", "submitted", "processing", "completed", "failed", "cancelled"
]
AmountBracket = Literal["<10k", "10k-50k", "50k-200k", ">=200k"]


def get_amount_bracket(amount_ngn: int) -> AmountBracket:
    """Derive standard amount bracket from amount in NGN."""
    if amount_ngn < 10_000:
        return "<10k"
    if amount_ngn < 50_000:
        return "10k-50k"
    if amount_ngn < 200_000:
        return "50k-200k"
    return ">=200k"


class Transaction(BaseModel):
    """Operational entity representing a monetary transaction attempt."""

    transaction_id: str = Field(..., pattern=r"^txn_[a-z0-9]{6}$")
    user_id: str = Field(..., pattern=r"^usr_[a-z0-9]{6}$")
    amount_ngn: int = Field(..., gt=0)
    amount_bracket: AmountBracket
    transaction_type: TransactionType
    destination_bank: BankName | None = None
    source_bank: BankName | None = None
    app_version: AppVersion
    timestamp: datetime
    status: TransactionStatus

    @model_validator(mode="after")
    def validate_banking_and_bracket(self) -> "Transaction":
        """Ensure banking properties align with transaction type and bracket aligns with amount."""
        expected_bracket = get_amount_bracket(self.amount_ngn)
        if self.amount_bracket != expected_bracket:
            raise ValueError(
                f"Amount {self.amount_ngn} corresponds to bracket '{expected_bracket}', "
                f"not '{self.amount_bracket}'"
            )

        if self.transaction_type == "transfer" and self.destination_bank is None:
            raise ValueError("Transfer transactions must specify destination_bank")
        if self.transaction_type == "wallet_funding" and self.source_bank is None:
            raise ValueError("Wallet funding transactions must specify source_bank")

        return self

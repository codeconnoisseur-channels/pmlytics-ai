"""User domain model and associated enumerations."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

UserType = Literal["student", "freelancer", "young_professional", "small_business"]
BankName = Literal["Bank A", "Bank B", "Bank C", "Bank D", "Bank E"]
AppVersion = Literal["2.3.0", "2.3.1", "2.4.0", "2.4.1"]


class User(BaseModel):
    """Operational entity representing a Pocket customer."""

    user_id: str = Field(..., pattern=r"^usr_[a-z0-9]{6}$")
    user_type: UserType
    primary_bank: BankName
    app_version: AppVersion
    signup_date: datetime

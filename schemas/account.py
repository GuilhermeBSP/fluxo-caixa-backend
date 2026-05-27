from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.account import AccountType


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: AccountType = AccountType.checking
    balance: float = 0.0
    description: Optional[str] = None


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[AccountType] = None
    balance: Optional[float] = None
    description: Optional[str] = None


class AccountOut(BaseModel):
    id: int
    name: str
    type: AccountType
    balance: float
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}

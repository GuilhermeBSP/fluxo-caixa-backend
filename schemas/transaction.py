from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from datetime import date as DateType
from models.transaction import TransactionType
from models.recurring import RecurringType


class TransactionCreate(BaseModel):
    account_id: int
    category_id: Optional[int] = None
    type: TransactionType
    amount: float = Field(..., gt=0)
    description: str = Field(..., min_length=1, max_length=255)
    date: DateType = Field(default_factory=DateType.today)


class TransactionOut(BaseModel):
    id: int
    account_id: int
    category_id: Optional[int]
    recurring_id: Optional[int]
    type: TransactionType
    amount: float
    description: str
    date: DateType
    created_at: datetime
    account_name: Optional[str] = None
    category_name: Optional[str] = None
    category_color: Optional[str] = None

    model_config = {"from_attributes": True}


class RecurringCreate(BaseModel):
    account_id: int
    category_id: Optional[int] = None
    type: RecurringType
    amount: float = Field(..., gt=0)
    description: str = Field(..., min_length=1, max_length=255)
    day_of_month: int = Field(..., ge=1, le=31)


class RecurringOut(BaseModel):
    id: int
    account_id: int
    category_id: Optional[int]
    type: RecurringType
    amount: float
    description: str
    day_of_month: int
    active: bool
    created_at: datetime
    account_name: Optional[str] = None
    category_name: Optional[str] = None

    model_config = {"from_attributes": True}

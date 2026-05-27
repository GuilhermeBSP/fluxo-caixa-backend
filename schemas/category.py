from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.category import CategoryType


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: CategoryType
    color: str = Field("#6c757d", pattern=r"^#[0-9a-fA-F]{6}$")


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")


class CategoryOut(BaseModel):
    id: int
    name: str
    type: CategoryType
    color: str
    created_at: datetime

    model_config = {"from_attributes": True}

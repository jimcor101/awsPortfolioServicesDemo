from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid


class PortfolioType(str, Enum):
    BROKERAGE = "Brokerage"
    IRA = "IRA"
    ROTH_IRA = "Roth IRA"
    TRADITIONAL_401K = "Traditional 401k"
    ROTH_401K = "Roth 401k"
    SAVINGS = "Savings"
    CHECKING = "Checking"
    OTHER = "Other"


class PortfolioBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: PortfolioType
    customer_id: str = Field(..., min_length=1)
    description: Optional[str] = Field(None, max_length=500)


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[PortfolioType] = None
    description: Optional[str] = Field(None, max_length=500)


class Portfolio(PortfolioBase):
    portfolio_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    total_value: float = Field(default=0.0)
    investment_count: int = Field(default=0)

    class Config:
        from_attributes = True


class PortfolioResponse(Portfolio):
    pass


class PortfolioSummary(BaseModel):
    portfolio_id: str
    name: str
    type: PortfolioType
    total_value: float
    investment_count: int
    created_at: datetime


class CustomerPortfolioSummary(BaseModel):
    customer_id: str
    portfolios: List[PortfolioSummary]
    total_portfolios: int
    total_value: float
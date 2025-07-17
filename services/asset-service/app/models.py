from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
import uuid


class InstrumentType(str, Enum):
    STOCK = "Stock"
    ETF = "ETF"
    BOND = "Bond"
    MUTUAL_FUND = "Mutual Fund"
    CRYPTOCURRENCY = "Cryptocurrency"
    COMMODITY = "Commodity"
    OPTION = "Option"
    FUTURE = "Future"
    OTHER = "Other"


class InstrumentBase(BaseModel):
    ticker_symbol: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    exchange: Optional[str] = Field(None, max_length=50)
    instrument_type: InstrumentType
    sector: Optional[str] = Field(None, max_length=100)
    currency: str = Field(default="USD", max_length=3)


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    exchange: Optional[str] = Field(None, max_length=50)
    instrument_type: Optional[InstrumentType] = None
    sector: Optional[str] = Field(None, max_length=100)
    currency: Optional[str] = Field(None, max_length=3)


class Instrument(InstrumentBase):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_price: Optional[float] = None
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssetPrice(BaseModel):
    ticker_symbol: str
    current_price: float
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "mock"


class InvestmentBase(BaseModel):
    portfolio_id: str = Field(..., min_length=1)
    ticker_symbol: str = Field(..., min_length=1, max_length=20)
    instrument_type: InstrumentType
    quantity: float = Field(..., gt=0)
    purchase_price: float = Field(..., gt=0)
    purchase_date: date


class InvestmentCreate(InvestmentBase):
    pass


class InvestmentUpdate(BaseModel):
    quantity: Optional[float] = Field(None, gt=0)
    purchase_price: Optional[float] = Field(None, gt=0)
    purchase_date: Optional[date] = None


class Investment(InvestmentBase):
    investment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    current_price: Optional[float] = None
    last_updated: Optional[datetime] = None
    current_value: float = Field(default=0.0)
    gain_loss: float = Field(default=0.0)
    gain_loss_percent: float = Field(default=0.0)

    class Config:
        from_attributes = True


class InvestmentResponse(Investment):
    pass


class PortfolioInvestmentSummary(BaseModel):
    portfolio_id: str
    investments: List[InvestmentResponse]
    total_investments: int
    total_value: float
    total_cost_basis: float
    total_gain_loss: float
    total_gain_loss_percent: float


class PriceUpdateRequest(BaseModel):
    ticker_symbols: List[str] = Field(..., min_items=1, max_items=100)


class PriceUpdateResponse(BaseModel):
    updated_prices: List[AssetPrice]
    updated_investments: int
    errors: List[str] = []
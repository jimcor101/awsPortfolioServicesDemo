from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    country: str


class CustomerBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    address: Address


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[Address] = None


class Customer(CustomerBase):
    customer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class CustomerResponse(Customer):
    pass
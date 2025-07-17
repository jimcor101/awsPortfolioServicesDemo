from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
from dotenv import load_dotenv

from .models import Customer, CustomerCreate, CustomerUpdate, CustomerResponse
from .database import db_service

load_dotenv()

app = FastAPI(
    title="Customer Service API",
    description="Investment Portfolio Tracker - Customer Management Service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Customer Service API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "customer-service"}


@app.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(customer: CustomerCreate):
    """Create a new customer"""
    try:
        # Check if customer with email already exists
        existing_customer = await db_service.get_customer_by_email(customer.email)
        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer with this email already exists"
            )
        
        new_customer = await db_service.create_customer(customer)
        return new_customer
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/customers", response_model=List[CustomerResponse])
async def get_customers(limit: int = 100):
    """Get all customers"""
    try:
        customers = await db_service.get_customers(limit=limit)
        return customers
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str):
    """Get customer by ID"""
    try:
        customer = await db_service.get_customer(customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        return customer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: str, customer_update: CustomerUpdate):
    """Update customer by ID"""
    try:
        updated_customer = await db_service.update_customer(customer_id, customer_update)
        if not updated_customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        return updated_customer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str):
    """Delete customer by ID"""
    try:
        deleted = await db_service.delete_customer(customer_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        return {"message": "Customer deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/customers/email/{email}", response_model=CustomerResponse)
async def get_customer_by_email(email: str):
    """Get customer by email"""
    try:
        customer = await db_service.get_customer_by_email(email)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        return customer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
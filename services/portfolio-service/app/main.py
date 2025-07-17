from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
from dotenv import load_dotenv

from .models import (
    Portfolio, PortfolioCreate, PortfolioUpdate, PortfolioResponse, 
    CustomerPortfolioSummary
)
from .database import db_service

load_dotenv()

app = FastAPI(
    title="Portfolio Service API",
    description="Investment Portfolio Tracker - Portfolio Management Service",
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
    return {"message": "Portfolio Service API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "portfolio-service"}


@app.post("/portfolios", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(portfolio: PortfolioCreate):
    """Create a new portfolio"""
    try:
        new_portfolio = await db_service.create_portfolio(portfolio)
        return new_portfolio
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/portfolios", response_model=List[PortfolioResponse])
async def get_portfolios(limit: int = 100):
    """Get all portfolios"""
    try:
        portfolios = await db_service.get_portfolios(limit=limit)
        return portfolios
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(portfolio_id: str):
    """Get portfolio by ID"""
    try:
        portfolio = await db_service.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        return portfolio
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.put("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(portfolio_id: str, portfolio_update: PortfolioUpdate):
    """Update portfolio by ID"""
    try:
        updated_portfolio = await db_service.update_portfolio(portfolio_id, portfolio_update)
        if not updated_portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        return updated_portfolio
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/portfolios/{portfolio_id}")
async def delete_portfolio(portfolio_id: str):
    """Delete portfolio by ID"""
    try:
        deleted = await db_service.delete_portfolio(portfolio_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        return {"message": "Portfolio deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/customers/{customer_id}/portfolios", response_model=List[PortfolioResponse])
async def get_customer_portfolios(customer_id: str):
    """Get all portfolios for a specific customer"""
    try:
        portfolios = await db_service.get_portfolios_by_customer(customer_id)
        return portfolios
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/customers/{customer_id}/portfolios/summary", response_model=CustomerPortfolioSummary)
async def get_customer_portfolio_summary(customer_id: str):
    """Get portfolio summary for a customer"""
    try:
        summary = await db_service.get_customer_portfolio_summary(customer_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.patch("/portfolios/{portfolio_id}/value")
async def update_portfolio_value(portfolio_id: str, total_value: float, investment_count: int):
    """Update portfolio total value and investment count (typically called by Investment Service)"""
    try:
        updated_portfolio = await db_service.update_portfolio_value(
            portfolio_id, total_value, investment_count
        )
        if not updated_portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        return {"message": "Portfolio value updated successfully", "portfolio": updated_portfolio}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
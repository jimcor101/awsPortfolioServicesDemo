from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
from dotenv import load_dotenv
import httpx

from .models import (
    Investment, InvestmentCreate, InvestmentUpdate, InvestmentResponse,
    AssetPrice, PriceUpdateRequest, PriceUpdateResponse,
    PortfolioInvestmentSummary
)
from .database import db_service
from .price_service import price_service
from .cache_service import cache_service

load_dotenv()

app = FastAPI(
    title="Asset Service API",
    description="Investment Portfolio Tracker - Asset & Investment Management Service",
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
    return {"message": "Asset Service API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "asset-service"}


# Investment CRUD endpoints
@app.post("/investments", response_model=InvestmentResponse, status_code=status.HTTP_201_CREATED)
async def create_investment(investment: InvestmentCreate):
    """Create a new investment"""
    try:
        new_investment = await db_service.create_investment(investment)
        return new_investment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/investments", response_model=List[InvestmentResponse])
async def get_investments(limit: int = 100):
    """Get all investments"""
    try:
        investments = await db_service.get_investments(limit=limit)
        return investments
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/investments/{investment_id}", response_model=InvestmentResponse)
async def get_investment(investment_id: str):
    """Get investment by ID"""
    try:
        investment = await db_service.get_investment(investment_id)
        if not investment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Investment not found"
            )
        return investment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.put("/investments/{investment_id}", response_model=InvestmentResponse)
async def update_investment(investment_id: str, investment_update: InvestmentUpdate):
    """Update investment by ID"""
    try:
        updated_investment = await db_service.update_investment(investment_id, investment_update)
        if not updated_investment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Investment not found"
            )
        return updated_investment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/investments/{investment_id}")
async def delete_investment(investment_id: str):
    """Delete investment by ID"""
    try:
        deleted = await db_service.delete_investment(investment_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Investment not found"
            )
        return {"message": "Investment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/portfolios/{portfolio_id}/investments", response_model=List[InvestmentResponse])
async def get_portfolio_investments(portfolio_id: str):
    """Get all investments for a specific portfolio"""
    try:
        investments = await db_service.get_investments_by_portfolio(portfolio_id)
        return investments
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/portfolios/{portfolio_id}/investments/summary", response_model=PortfolioInvestmentSummary)
async def get_portfolio_investment_summary(portfolio_id: str):
    """Get investment summary for a portfolio"""
    try:
        summary = await db_service.get_portfolio_investment_summary(portfolio_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Asset price endpoints
@app.get("/assets/{ticker_symbol}/price", response_model=AssetPrice)
async def get_asset_price(ticker_symbol: str, use_cache: bool = True):
    """Get current price for an asset"""
    try:
        ticker_symbol = ticker_symbol.upper()
        
        # Try cache first if enabled
        if use_cache:
            cached_price = await cache_service.get_price(ticker_symbol)
            if cached_price:
                return cached_price
        
        # Get fresh price from external service
        price = await price_service.get_price(ticker_symbol)
        if not price:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Price not found for {ticker_symbol}"
            )
        
        # Cache the result
        if use_cache:
            await cache_service.set_price(price)
        
        return price
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/assets/prices", response_model=List[AssetPrice])
async def get_asset_prices(request: PriceUpdateRequest, use_cache: bool = True):
    """Get current prices for multiple assets"""
    try:
        ticker_symbols = [t.upper() for t in request.ticker_symbols]
        
        # Try cache first if enabled
        cached_prices = {}
        if use_cache:
            cached_prices = await cache_service.get_prices(ticker_symbols)
        
        # Get missing prices from external service
        missing_tickers = [t for t in ticker_symbols if t not in cached_prices]
        fresh_prices = []
        
        if missing_tickers:
            fresh_prices = await price_service.get_prices(missing_tickers)
            
            # Cache fresh prices
            if use_cache and fresh_prices:
                await cache_service.set_prices(fresh_prices)
        
        # Combine cached and fresh prices
        all_prices = list(cached_prices.values()) + fresh_prices
        
        return all_prices
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


async def update_investment_prices_task(ticker_symbols: List[str]) -> PriceUpdateResponse:
    """Background task to update investment prices"""
    try:
        # Get fresh prices
        prices = await price_service.get_prices(ticker_symbols)
        updated_count = 0
        errors = []
        
        for price in prices:
            try:
                # Get all investments for this ticker
                investments = await db_service.get_investments_by_ticker(price.ticker_symbol)
                
                # Update each investment with new price
                for investment in investments:
                    await db_service.update_investment_price(
                        investment.investment_id, 
                        price.current_price
                    )
                    updated_count += 1
                
                # Cache the price
                await cache_service.set_price(price)
                
            except Exception as e:
                error_msg = f"Error updating {price.ticker_symbol}: {str(e)}"
                errors.append(error_msg)
                print(error_msg)
        
        return PriceUpdateResponse(
            updated_prices=prices,
            updated_investments=updated_count,
            errors=errors
        )
    except Exception as e:
        return PriceUpdateResponse(
            updated_prices=[],
            updated_investments=0,
            errors=[f"Task failed: {str(e)}"]
        )


@app.post("/investments/update-prices", response_model=PriceUpdateResponse)
async def update_investment_prices(
    background_tasks: BackgroundTasks,
    request: PriceUpdateRequest = None
):
    """Update prices for all investments or specified tickers"""
    try:
        if request and request.ticker_symbols:
            ticker_symbols = [t.upper() for t in request.ticker_symbols]
        else:
            # Get all unique tickers from investments
            ticker_symbols = await db_service.get_unique_tickers()
        
        if not ticker_symbols:
            return PriceUpdateResponse(
                updated_prices=[],
                updated_investments=0,
                errors=["No ticker symbols found"]
            )
        
        # For small requests, process immediately
        if len(ticker_symbols) <= 10:
            return await update_investment_prices_task(ticker_symbols)
        
        # For large requests, process in background
        background_tasks.add_task(update_investment_prices_task, ticker_symbols)
        
        return PriceUpdateResponse(
            updated_prices=[],
            updated_investments=0,
            errors=[f"Processing {len(ticker_symbols)} tickers in background"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/cache/prices")
async def clear_price_cache():
    """Clear all cached prices"""
    try:
        await cache_service.clear_all()
        return {"message": "Price cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


async def notify_portfolio_service(portfolio_id: str, total_value: float, investment_count: int):
    """Notify Portfolio Service of updated values"""
    try:
        portfolio_service_url = os.getenv("PORTFOLIO_SERVICE_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{portfolio_service_url}/portfolios/{portfolio_id}/value",
                params={
                    "total_value": total_value,
                    "investment_count": investment_count
                }
            )
            response.raise_for_status()
            print(f"Successfully updated portfolio {portfolio_id} with value {total_value}")
    except Exception as e:
        print(f"Failed to notify portfolio service: {e}")


@app.post("/portfolios/{portfolio_id}/sync-values")
async def sync_portfolio_values(portfolio_id: str):
    """Sync portfolio values with current investment data"""
    try:
        summary = await db_service.get_portfolio_investment_summary(portfolio_id)
        
        # Notify Portfolio Service
        await notify_portfolio_service(
            portfolio_id=portfolio_id,
            total_value=summary.total_value,
            investment_count=summary.total_investments
        )
        
        return {
            "message": "Portfolio values synced successfully",
            "portfolio_id": portfolio_id,
            "total_value": summary.total_value,
            "investment_count": summary.total_investments
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
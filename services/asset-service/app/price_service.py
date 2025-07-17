import httpx
import json
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import asyncio
import random
import os
from .models import AssetPrice


class MockPriceService:
    """Mock price service for development and testing"""
    
    def __init__(self):
        # Mock data for common stocks
        self.mock_prices = {
            "AAPL": {"price": 175.25, "change": 2.15, "volume": 50000000},
            "GOOGL": {"price": 2750.80, "change": -15.30, "volume": 25000000},
            "MSFT": {"price": 338.50, "change": 5.75, "volume": 35000000},
            "AMZN": {"price": 3285.04, "change": -22.15, "volume": 28000000},
            "TSLA": {"price": 850.25, "change": 18.90, "volume": 45000000},
            "NVDA": {"price": 450.75, "change": 12.30, "volume": 40000000},
            "META": {"price": 485.60, "change": -8.45, "volume": 30000000},
            "SPY": {"price": 445.20, "change": 1.85, "volume": 80000000},
            "QQQ": {"price": 375.30, "change": 3.25, "volume": 60000000},
            "VTI": {"price": 235.45, "change": 0.85, "volume": 15000000},
        }
    
    async def get_price(self, ticker_symbol: str) -> Optional[AssetPrice]:
        """Get current price for a single ticker"""
        try:
            # Simulate API delay
            await asyncio.sleep(0.1)
            
            if ticker_symbol in self.mock_prices:
                data = self.mock_prices[ticker_symbol]
                # Add some random variation
                base_price = data["price"]
                variation = random.uniform(-0.02, 0.02)  # ±2% variation
                current_price = base_price * (1 + variation)
                
                previous_close = current_price - data["change"]
                change_percent = (data["change"] / previous_close) * 100 if previous_close > 0 else 0
                
                return AssetPrice(
                    ticker_symbol=ticker_symbol,
                    current_price=round(current_price, 2),
                    previous_close=round(previous_close, 2),
                    change=data["change"],
                    change_percent=round(change_percent, 2),
                    volume=data["volume"],
                    timestamp=datetime.utcnow(),
                    source="mock"
                )
            else:
                # Generate random price for unknown tickers
                random_price = random.uniform(10, 500)
                random_change = random.uniform(-10, 10)
                previous_close = random_price - random_change
                change_percent = (random_change / previous_close) * 100 if previous_close > 0 else 0
                
                return AssetPrice(
                    ticker_symbol=ticker_symbol,
                    current_price=round(random_price, 2),
                    previous_close=round(previous_close, 2),
                    change=round(random_change, 2),
                    change_percent=round(change_percent, 2),
                    volume=random.randint(100000, 50000000),
                    timestamp=datetime.utcnow(),
                    source="mock"
                )
        except Exception as e:
            print(f"Error getting price for {ticker_symbol}: {e}")
            return None
    
    async def get_prices(self, ticker_symbols: List[str]) -> List[AssetPrice]:
        """Get current prices for multiple tickers"""
        prices = []
        
        # Process in batches to simulate real API limits
        batch_size = 10
        for i in range(0, len(ticker_symbols), batch_size):
            batch = ticker_symbols[i:i + batch_size]
            batch_tasks = [self.get_price(ticker) for ticker in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, AssetPrice):
                    prices.append(result)
                elif isinstance(result, Exception):
                    print(f"Error in batch processing: {result}")
        
        return prices


class AlphaVantagePriceService:
    """Alpha Vantage API integration for real market data"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        self.base_url = "https://www.alphavantage.co/query"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_price(self, ticker_symbol: str) -> Optional[AssetPrice]:
        """Get current price from Alpha Vantage API"""
        if not self.api_key:
            print("No Alpha Vantage API key provided, falling back to mock data")
            return None
        
        try:
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": ticker_symbol,
                "apikey": self.api_key
            }
            
            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "Global Quote" not in data:
                print(f"No data found for {ticker_symbol}")
                return None
            
            quote = data["Global Quote"]
            
            return AssetPrice(
                ticker_symbol=ticker_symbol,
                current_price=float(quote["05. price"]),
                previous_close=float(quote["08. previous close"]),
                change=float(quote["09. change"]),
                change_percent=float(quote["10. change percent"].rstrip("%")),
                volume=int(quote["06. volume"]) if quote["06. volume"] != "0" else None,
                timestamp=datetime.utcnow(),
                source="alphavantage"
            )
        
        except Exception as e:
            print(f"Error getting price from Alpha Vantage for {ticker_symbol}: {e}")
            return None
    
    async def get_prices(self, ticker_symbols: List[str]) -> List[AssetPrice]:
        """Get prices for multiple tickers (with rate limiting)"""
        prices = []
        
        # Alpha Vantage free tier: 5 requests per minute
        for ticker in ticker_symbols:
            price = await self.get_price(ticker)
            if price:
                prices.append(price)
            
            # Rate limiting - wait 12 seconds between requests for free tier
            if len(ticker_symbols) > 1:
                await asyncio.sleep(12)
        
        return prices


class PriceServiceFactory:
    """Factory to create the appropriate price service"""
    
    @staticmethod
    def create_price_service() -> "MockPriceService | AlphaVantagePriceService":
        """Create price service based on configuration"""
        alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        
        if alpha_vantage_key:
            print("Using Alpha Vantage price service")
            return AlphaVantagePriceService(alpha_vantage_key)
        else:
            print("Using mock price service (no Alpha Vantage API key found)")
            return MockPriceService()


# Global instance
price_service = PriceServiceFactory.create_price_service()
import json
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import os
from .models import AssetPrice

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class InMemoryCache:
    """Simple in-memory cache for development"""
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self.default_ttl = 300  # 5 minutes
    
    async def get_price(self, ticker_symbol: str) -> Optional[AssetPrice]:
        """Get cached price for a ticker"""
        try:
            cache_key = f"price:{ticker_symbol}"
            if cache_key in self._cache:
                cached_data = self._cache[cache_key]
                
                # Check if expired
                expires_at = datetime.fromisoformat(cached_data['expires_at'])
                if datetime.utcnow() > expires_at:
                    del self._cache[cache_key]
                    return None
                
                # Return cached price
                return AssetPrice(**cached_data['data'])
            return None
        except Exception as e:
            print(f"Error getting cached price for {ticker_symbol}: {e}")
            return None
    
    async def set_price(self, price: AssetPrice, ttl: int = None) -> bool:
        """Cache a price with TTL"""
        try:
            cache_key = f"price:{price.ticker_symbol}"
            expires_at = datetime.utcnow() + timedelta(seconds=ttl or self.default_ttl)
            
            self._cache[cache_key] = {
                'data': price.model_dump(),
                'expires_at': expires_at.isoformat()
            }
            return True
        except Exception as e:
            print(f"Error caching price for {price.ticker_symbol}: {e}")
            return False
    
    async def get_prices(self, ticker_symbols: List[str]) -> Dict[str, AssetPrice]:
        """Get multiple cached prices"""
        prices = {}
        for ticker in ticker_symbols:
            price = await self.get_price(ticker)
            if price:
                prices[ticker] = price
        return prices
    
    async def set_prices(self, prices: List[AssetPrice], ttl: int = None) -> int:
        """Cache multiple prices"""
        cached_count = 0
        for price in prices:
            if await self.set_price(price, ttl):
                cached_count += 1
        return cached_count
    
    async def delete_price(self, ticker_symbol: str) -> bool:
        """Delete cached price"""
        cache_key = f"price:{ticker_symbol}"
        if cache_key in self._cache:
            del self._cache[cache_key]
            return True
        return False
    
    async def clear_all(self) -> bool:
        """Clear all cached prices"""
        self._cache.clear()
        return True


class RedisCache:
    """Redis-based cache for production"""
    
    def __init__(self, redis_url: str = None):
        if not REDIS_AVAILABLE:
            raise ImportError("redis package not available")
        
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.default_ttl = 300  # 5 minutes
        self._redis = None
    
    async def _get_redis(self):
        """Get Redis connection (lazy initialization)"""
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
        return self._redis
    
    async def get_price(self, ticker_symbol: str) -> Optional[AssetPrice]:
        """Get cached price for a ticker"""
        try:
            redis_client = await self._get_redis()
            cache_key = f"price:{ticker_symbol}"
            
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                price_data = json.loads(cached_data)
                return AssetPrice(**price_data)
            return None
        except Exception as e:
            print(f"Error getting cached price for {ticker_symbol}: {e}")
            return None
    
    async def set_price(self, price: AssetPrice, ttl: int = None) -> bool:
        """Cache a price with TTL"""
        try:
            redis_client = await self._get_redis()
            cache_key = f"price:{price.ticker_symbol}"
            
            price_data = price.model_dump()
            # Convert datetime to string for JSON serialization
            price_data['timestamp'] = price_data['timestamp'].isoformat()
            
            await redis_client.setex(
                cache_key,
                ttl or self.default_ttl,
                json.dumps(price_data)
            )
            return True
        except Exception as e:
            print(f"Error caching price for {price.ticker_symbol}: {e}")
            return False
    
    async def get_prices(self, ticker_symbols: List[str]) -> Dict[str, AssetPrice]:
        """Get multiple cached prices using pipeline"""
        try:
            redis_client = await self._get_redis()
            
            # Use pipeline for efficient multi-get
            pipe = redis_client.pipeline()
            cache_keys = [f"price:{ticker}" for ticker in ticker_symbols]
            
            for key in cache_keys:
                pipe.get(key)
            
            results = await pipe.execute()
            
            prices = {}
            for i, result in enumerate(results):
                if result:
                    ticker = ticker_symbols[i]
                    price_data = json.loads(result)
                    # Convert timestamp back to datetime
                    price_data['timestamp'] = datetime.fromisoformat(price_data['timestamp'])
                    prices[ticker] = AssetPrice(**price_data)
            
            return prices
        except Exception as e:
            print(f"Error getting cached prices: {e}")
            return {}
    
    async def set_prices(self, prices: List[AssetPrice], ttl: int = None) -> int:
        """Cache multiple prices using pipeline"""
        try:
            redis_client = await self._get_redis()
            pipe = redis_client.pipeline()
            
            for price in prices:
                cache_key = f"price:{price.ticker_symbol}"
                price_data = price.model_dump()
                price_data['timestamp'] = price_data['timestamp'].isoformat()
                
                pipe.setex(
                    cache_key,
                    ttl or self.default_ttl,
                    json.dumps(price_data)
                )
            
            results = await pipe.execute()
            return len([r for r in results if r])
        except Exception as e:
            print(f"Error caching prices: {e}")
            return 0
    
    async def delete_price(self, ticker_symbol: str) -> bool:
        """Delete cached price"""
        try:
            redis_client = await self._get_redis()
            cache_key = f"price:{ticker_symbol}"
            result = await redis_client.delete(cache_key)
            return result > 0
        except Exception as e:
            print(f"Error deleting cached price for {ticker_symbol}: {e}")
            return False
    
    async def clear_all(self) -> bool:
        """Clear all cached prices"""
        try:
            redis_client = await self._get_redis()
            # Get all price keys
            keys = await redis_client.keys("price:*")
            if keys:
                await redis_client.delete(*keys)
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()


class CacheServiceFactory:
    """Factory to create appropriate cache service"""
    
    @staticmethod
    def create_cache_service():
        """Create cache service based on configuration"""
        redis_url = os.getenv("REDIS_URL")
        
        if redis_url and REDIS_AVAILABLE:
            try:
                print("Using Redis cache service")
                return RedisCache(redis_url)
            except Exception as e:
                print(f"Failed to initialize Redis cache: {e}")
                print("Falling back to in-memory cache")
                return InMemoryCache()
        else:
            print("Using in-memory cache service")
            return InMemoryCache()


# Global instance
cache_service = CacheServiceFactory.create_cache_service()
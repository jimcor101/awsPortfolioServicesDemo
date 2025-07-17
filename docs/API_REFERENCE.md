# API Reference Guide

## Overview

This document provides detailed API reference for the AWS Portfolio Services Demo. All services are accessible through the Application Load Balancer.

**Base URL**: `http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com`

## Authentication

Currently, the API does not require authentication. In a production environment, you would implement:
- JWT tokens
- API keys
- AWS IAM authentication
- OAuth 2.0

## Response Format

All APIs return JSON responses with the following structure:

### Success Response
```json
{
  "data": { ... },
  "message": "Operation successful",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": { ... }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Customer Service API

### Health Check

#### GET /health
Check service health status.

**Response**:
```json
{
  "status": "healthy",
  "service": "customer-service",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Customer Management

#### GET /customers
List all customers with pagination.

**Parameters**:
- `limit` (optional, default: 100): Number of customers to return

**Example Request**:
```bash
curl http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/customers?limit=50
```

**Response**:
```json
[
  {
    "customer_id": "cust-12345",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "address": "123 Main St, City, ST 12345",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

#### POST /customers
Create a new customer.

**Request Body**:
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1-555-0123",
  "address": "123 Main St, City, ST 12345"
}
```

**Example Request**:
```bash
curl -X POST http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "address": "123 Main St, City, ST 12345"
  }'
```

**Response** (201 Created):
```json
{
  "customer_id": "cust-12345",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1-555-0123",
  "address": "123 Main St, City, ST 12345",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### GET /customers/{customer_id}
Get customer by ID.

**Example Request**:
```bash
curl http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/customers/cust-12345
```

**Response**:
```json
{
  "customer_id": "cust-12345",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1-555-0123",
  "address": "123 Main St, City, ST 12345",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### PUT /customers/{customer_id}
Update customer information.

**Request Body**:
```json
{
  "name": "John Smith",
  "phone": "+1-555-9876"
}
```

**Example Request**:
```bash
curl -X PUT http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/customers/cust-12345 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "phone": "+1-555-9876"
  }'
```

#### DELETE /customers/{customer_id}
Delete a customer.

**Example Request**:
```bash
curl -X DELETE http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/customers/cust-12345
```

**Response**:
```json
{
  "message": "Customer deleted successfully"
}
```

#### GET /customers/email/{email}
Get customer by email address.

**Example Request**:
```bash
curl http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/customers/email/john@example.com
```

## Portfolio Service API

### Portfolio Management

#### GET /portfolios
List all portfolios.

**Parameters**:
- `limit` (optional, default: 100): Number of portfolios to return

**Example Request**:
```bash
curl http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/portfolios
```

**Response**:
```json
[
  {
    "portfolio_id": "port-12345",
    "customer_id": "cust-12345",
    "portfolio_name": "My Retirement Portfolio",
    "portfolio_type": "IRA",
    "total_value": 150000.00,
    "investment_count": 5,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

#### POST /portfolios
Create a new portfolio.

**Request Body**:
```json
{
  "customer_id": "cust-12345",
  "portfolio_name": "My Retirement Portfolio",
  "portfolio_type": "IRA"
}
```

**Portfolio Types**:
- `IRA` - Individual Retirement Account
- `ROTH_IRA` - Roth IRA
- `401K` - 401(k) Plan
- `BROKERAGE` - Taxable Brokerage Account
- `HSA` - Health Savings Account
- `529` - 529 Education Savings Plan

**Example Request**:
```bash
curl -X POST http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/portfolios \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust-12345",
    "portfolio_name": "My Retirement Portfolio",
    "portfolio_type": "IRA"
  }'
```

#### GET /portfolios/{portfolio_id}
Get portfolio by ID.

**Example Request**:
```bash
curl http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/portfolios/port-12345
```

#### PUT /portfolios/{portfolio_id}
Update portfolio information.

**Request Body**:
```json
{
  "portfolio_name": "Updated Portfolio Name",
  "portfolio_type": "ROTH_IRA"
}
```

#### DELETE /portfolios/{portfolio_id}
Delete a portfolio.

**Example Request**:
```bash
curl -X DELETE http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/portfolios/port-12345
```

#### GET /customers/{customer_id}/portfolios
Get all portfolios for a customer.

**Example Request**:
```bash
curl http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/customers/cust-12345/portfolios
```

#### GET /customers/{customer_id}/portfolios/summary
Get portfolio summary for a customer.

**Example Request**:
```bash
curl http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/customers/cust-12345/portfolios/summary
```

**Response**:
```json
{
  "customer_id": "cust-12345",
  "portfolios": [
    {
      "portfolio_id": "port-12345",
      "portfolio_name": "My Retirement Portfolio",
      "portfolio_type": "IRA",
      "total_value": 150000.00,
      "investment_count": 5
    }
  ],
  "total_portfolios": 1,
  "total_value": 150000.00,
  "total_investments": 5,
  "summary_date": "2024-01-15T10:30:00Z"
}
```

## Asset Service API

### Investment Management

#### GET /investments
List all investments.

**Parameters**:
- `limit` (optional, default: 100): Number of investments to return

**Example Request**:
```bash
curl http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/investments
```

**Response**:
```json
[
  {
    "investment_id": "inv-12345",
    "portfolio_id": "port-12345",
    "ticker_symbol": "AAPL",
    "quantity": 100,
    "purchase_price": 150.00,
    "current_price": 175.25,
    "current_value": 17525.00,
    "gain_loss": 2525.00,
    "gain_loss_percent": 16.83,
    "purchase_date": "2024-01-15",
    "last_updated": "2024-01-15T10:30:00Z",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

#### POST /investments
Create a new investment.

**Request Body**:
```json
{
  "portfolio_id": "port-12345",
  "ticker_symbol": "AAPL",
  "quantity": 100,
  "purchase_price": 150.00,
  "purchase_date": "2024-01-15"
}
```

**Example Request**:
```bash
curl -X POST http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/investments \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "port-12345",
    "ticker_symbol": "AAPL",
    "quantity": 100,
    "purchase_price": 150.00,
    "purchase_date": "2024-01-15"
  }'
```

#### GET /investments/{investment_id}
Get investment by ID.

**Example Request**:
```bash
curl http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/investments/inv-12345
```

#### PUT /investments/{investment_id}
Update investment information.

**Request Body**:
```json
{
  "quantity": 150,
  "purchase_price": 145.00
}
```

#### DELETE /investments/{investment_id}
Delete an investment.

**Example Request**:
```bash
curl -X DELETE http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/investments/inv-12345
```

#### GET /portfolios/{portfolio_id}/investments
Get all investments for a portfolio.

**Example Request**:
```bash
curl http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/portfolios/port-12345/investments
```

#### GET /portfolios/{portfolio_id}/investments/summary
Get investment summary for a portfolio.

**Example Request**:
```bash
curl http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/portfolios/port-12345/investments/summary
```

**Response**:
```json
{
  "portfolio_id": "port-12345",
  "investments": [
    {
      "investment_id": "inv-12345",
      "ticker_symbol": "AAPL",
      "quantity": 100,
      "current_value": 17525.00,
      "gain_loss": 2525.00,
      "gain_loss_percent": 16.83
    }
  ],
  "total_investments": 1,
  "total_value": 17525.00,
  "total_cost_basis": 15000.00,
  "total_gain_loss": 2525.00,
  "total_gain_loss_percent": 16.83
}
```

### Asset Pricing

#### GET /assets/{ticker_symbol}/price
Get current price for an asset.

**Parameters**:
- `use_cache` (optional, default: true): Whether to use cached price

**Example Request**:
```bash
curl http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/assets/AAPL/price
```

**Response**:
```json
{
  "ticker_symbol": "AAPL",
  "current_price": 175.25,
  "previous_close": 173.10,
  "change": 2.15,
  "change_percent": 1.24,
  "volume": 50000000,
  "market_cap": null,
  "timestamp": "2024-01-15T10:30:00Z",
  "source": "mock"
}
```

#### POST /assets/prices
Get current prices for multiple assets.

**Request Body**:
```json
{
  "ticker_symbols": ["AAPL", "GOOGL", "MSFT"]
}
```

**Example Request**:
```bash
curl -X POST http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/assets/prices \
  -H "Content-Type: application/json" \
  -d '{
    "ticker_symbols": ["AAPL", "GOOGL", "MSFT"]
  }'
```

**Response**:
```json
[
  {
    "ticker_symbol": "AAPL",
    "current_price": 175.25,
    "previous_close": 173.10,
    "change": 2.15,
    "change_percent": 1.24,
    "volume": 50000000,
    "timestamp": "2024-01-15T10:30:00Z",
    "source": "mock"
  },
  {
    "ticker_symbol": "GOOGL",
    "current_price": 2750.80,
    "previous_close": 2766.10,
    "change": -15.30,
    "change_percent": -0.55,
    "volume": 25000000,
    "timestamp": "2024-01-15T10:30:00Z",
    "source": "mock"
  }
]
```

#### POST /investments/update-prices
Update prices for all investments or specific tickers.

**Request Body** (optional):
```json
{
  "ticker_symbols": ["AAPL", "GOOGL"]
}
```

**Example Request**:
```bash
# Update all investment prices
curl -X POST http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/investments/update-prices

# Update specific tickers
curl -X POST http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/investments/update-prices \
  -H "Content-Type: application/json" \
  -d '{
    "ticker_symbols": ["AAPL", "GOOGL"]
  }'
```

**Response**:
```json
{
  "updated_prices": [
    {
      "ticker_symbol": "AAPL",
      "current_price": 175.25,
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "updated_investments": 5,
  "errors": []
}
```

#### DELETE /cache/prices
Clear all cached prices.

**Example Request**:
```bash
curl -X DELETE http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/cache/prices
```

### Portfolio Synchronization

#### POST /portfolios/{portfolio_id}/sync-values
Synchronize portfolio values with current investment data.

**Example Request**:
```bash
curl -X POST http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/portfolios/port-12345/sync-values
```

**Response**:
```json
{
  "message": "Portfolio values synced successfully",
  "portfolio_id": "port-12345",
  "total_value": 175250.00,
  "investment_count": 5
}
```

## Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | VALIDATION_ERROR | Invalid request data |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Resource already exists |
| 500 | INTERNAL_ERROR | Server error |
| 503 | SERVICE_UNAVAILABLE | External service unavailable |

## Rate Limits

- **Customer Service**: 1000 requests per minute
- **Portfolio Service**: 500 requests per minute
- **Asset Service**: 200 requests per minute (due to external API limits)

## Sample Integration Workflows

### Complete Portfolio Setup

```bash
# 1. Create customer
CUSTOMER_ID=$(curl -s -X POST http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/customers \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com", "phone": "+1-555-0123", "address": "123 Main St"}' \
  | jq -r '.customer_id')

# 2. Create portfolio
PORTFOLIO_ID=$(curl -s -X POST http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/portfolios \
  -H "Content-Type: application/json" \
  -d "{\"customer_id\": \"$CUSTOMER_ID\", \"portfolio_name\": \"My Portfolio\", \"portfolio_type\": \"IRA\"}" \
  | jq -r '.portfolio_id')

# 3. Add investment
curl -X POST http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/investments \
  -H "Content-Type: application/json" \
  -d "{\"portfolio_id\": \"$PORTFOLIO_ID\", \"ticker_symbol\": \"AAPL\", \"quantity\": 100, \"purchase_price\": 150.00, \"purchase_date\": \"2024-01-15\"}"

# 4. Update prices
curl -X POST http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/investments/update-prices

# 5. Get portfolio summary
curl http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/portfolios/$PORTFOLIO_ID/investments/summary
```

### Price Monitoring

```bash
# Monitor specific assets
curl -X POST http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/assets/prices \
  -H "Content-Type: application/json" \
  -d '{"ticker_symbols": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]}'

# Clear cache for fresh data
curl -X DELETE http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/cache/prices

# Update all investment prices
curl -X POST http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/investments/update-prices
```

## Testing with Postman

A Postman collection is available in the `docs/` directory with pre-configured requests for all endpoints.

## WebSocket Support (Future)

Future versions will include WebSocket support for real-time price updates:

```javascript
// Example WebSocket connection
const ws = new WebSocket('wss://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/ws');

ws.onmessage = function(event) {
  const priceUpdate = JSON.parse(event.data);
  console.log('Price update:', priceUpdate);
};
```

## GraphQL Support (Future)

Future versions will include GraphQL endpoints for more flexible querying:

```graphql
query GetPortfolioSummary($portfolioId: ID!) {
  portfolio(id: $portfolioId) {
    id
    name
    type
    totalValue
    investments {
      id
      tickerSymbol
      quantity
      currentPrice
      gainLoss
    }
  }
}
```
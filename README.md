# AWS Portfolio Services Demo

A complete microservices architecture for investment portfolio tracking, built with Python FastAPI, AWS ECS, and infrastructure as code.

## 🏗️ Architecture Overview

This project implements a distributed microservices architecture for managing investment portfolios with real-time asset pricing and portfolio analytics.

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │ Application     │    │   ECS Fargate   │
│                 │────│ Load Balancer   │────│   Services      │
│  (Mock Routes)  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────────────────────────────────────┐
                    │              Service Layer                      │
                    │                                                 │
                    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
                    │  │  Customer   │  │ Portfolio   │  │   Asset     │  │
                    │  │  Service    │  │  Service    │  │  Service    │  │
                    │  │    :8000    │  │    :8001    │  │    :8002    │  │
                    │  └─────────────┘  └─────────────┘  └─────────────┘  │
                    └─────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌─────────────────────────────────────────────────┐
                    │              Data Layer                         │
                    │                                                 │
                    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
                    │  │  Customer   │  │ Portfolio   │  │Investment   │  │
                    │  │   Table     │  │   Table     │  │   Table     │  │
                    │  │ (DynamoDB)  │  │ (DynamoDB)  │  │ (DynamoDB)  │  │
                    │  └─────────────┘  └─────────────┘  └─────────────┘  │
                    └─────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌─────────────────────────────────────────────────┐
                    │            External Services                    │
                    │                                                 │
                    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
                    │  │ Alpha       │  │   Redis     │  │ CloudWatch  │  │
                    │  │ Vantage     │  │   Cache     │  │   Logs      │  │
                    │  │ Price API   │  │ (Optional)  │  │             │  │
                    │  └─────────────┘  └─────────────┘  └─────────────┘  │
                    └─────────────────────────────────────────────────┘
```

### Technology Stack

- **Runtime**: Python 3.11
- **Framework**: FastAPI with Pydantic
- **Container**: Docker + ECS Fargate
- **Database**: Amazon DynamoDB
- **Load Balancer**: Application Load Balancer (ALB)
- **Cache**: Redis (optional) / In-memory fallback
- **Infrastructure**: AWS CDK (Python)
- **Logging**: CloudWatch Logs
- **External APIs**: Alpha Vantage (market data)

## 🔧 Infrastructure Components

### AWS Services Used

1. **ECS Fargate**: Container orchestration for microservices
2. **Application Load Balancer**: Traffic distribution and path-based routing
3. **ECR**: Container image registry
4. **DynamoDB**: NoSQL database with GSI for efficient queries
5. **VPC**: Network isolation with public/private subnets
6. **CloudWatch**: Logging and monitoring
7. **IAM**: Role-based access control
8. **API Gateway**: RESTful API endpoints (with mock integrations)

### Network Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              VPC                                        │
│                                                                         │
│  ┌─────────────────────────┐       ┌─────────────────────────┐          │
│  │     Public Subnet       │       │     Public Subnet       │          │
│  │         AZ-1a           │       │         AZ-1b           │          │
│  │                         │       │                         │          │
│  │  ┌─────────────────┐    │       │  ┌─────────────────┐    │          │
│  │  │       ALB       │    │       │  │   NAT Gateway   │    │          │
│  │  └─────────────────┘    │       │  └─────────────────┘    │          │
│  └─────────────────────────┘       └─────────────────────────┘          │
│                                                                         │
│  ┌─────────────────────────┐       ┌─────────────────────────┐          │
│  │    Private Subnet       │       │    Private Subnet       │          │
│  │         AZ-1a           │       │         AZ-1b           │          │
│  │                         │       │                         │          │
│  │  ┌─────────────────┐    │       │  ┌─────────────────┐    │          │
│  │  │ ECS Tasks       │    │       │  │ ECS Tasks       │    │          │
│  │  │ (Services)      │    │       │  │ (Services)      │    │          │
│  │  └─────────────────┘    │       │  └─────────────────┘    │          │
│  └─────────────────────────┘       └─────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 🚀 Services Overview

### 1. Customer Service (Port 8000)

**Purpose**: Manages customer information and authentication

**Key Features**:
- Customer registration and profile management
- CRUD operations for customer data
- Email-based customer lookup
- Customer validation and data integrity

**Database Schema**:
```python
Customer {
    customer_id: str (PK)
    name: str
    email: str
    phone: str
    address: str
    created_at: datetime
    updated_at: datetime
}
```

### 2. Portfolio Service (Port 8001)

**Purpose**: Manages investment portfolios and portfolio analytics

**Key Features**:
- Portfolio creation and management
- Portfolio types (IRA, Brokerage, 401k, etc.)
- Customer-portfolio associations
- Portfolio performance tracking
- Value synchronization with Asset Service

**Database Schema**:
```python
Portfolio {
    portfolio_id: str (PK)
    customer_id: str (GSI)
    portfolio_name: str
    portfolio_type: PortfolioType
    total_value: float
    created_at: datetime
    updated_at: datetime
}
```

### 3. Asset Service (Port 8002)

**Purpose**: Manages investments and real-time asset pricing

**Key Features**:
- Investment tracking and management
- Real-time asset price fetching
- Portfolio value calculation
- Price caching and rate limiting
- External API integration (Alpha Vantage)
- Background price updates

**Database Schema**:
```python
Investment {
    investment_id: str (PK)
    portfolio_id: str (GSI)
    ticker_symbol: str
    quantity: float
    purchase_price: float
    current_price: float
    current_value: float
    gain_loss: float
    gain_loss_percent: float
    purchase_date: date
    last_updated: datetime
    created_at: datetime
    updated_at: datetime
}
```

## 🌐 API Endpoints

### Load Balancer URL
**Base URL**: `http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com`

### Customer Service Endpoints

#### Health Check
```http
GET /health
```

#### Customer Management
```http
GET /customers                    # List all customers
POST /customers                   # Create new customer
GET /customers/{customer_id}      # Get customer by ID
PUT /customers/{customer_id}      # Update customer
DELETE /customers/{customer_id}   # Delete customer
GET /customers/email/{email}      # Get customer by email
```

#### Example: Create Customer
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

### Portfolio Service Endpoints

#### Portfolio Management
```http
GET /portfolios                              # List all portfolios
POST /portfolios                             # Create new portfolio
GET /portfolios/{portfolio_id}               # Get portfolio by ID
PUT /portfolios/{portfolio_id}               # Update portfolio
DELETE /portfolios/{portfolio_id}            # Delete portfolio
GET /customers/{customer_id}/portfolios      # Get customer's portfolios
GET /customers/{customer_id}/portfolios/summary  # Get portfolio summary
```

#### Example: Create Portfolio
```bash
curl -X POST http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/portfolios \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust-12345",
    "portfolio_name": "My Retirement Portfolio",
    "portfolio_type": "IRA"
  }'
```

### Asset Service Endpoints

#### Investment Management
```http
GET /investments                             # List all investments
POST /investments                            # Create new investment
GET /investments/{investment_id}             # Get investment by ID
PUT /investments/{investment_id}             # Update investment
DELETE /investments/{investment_id}          # Delete investment
GET /portfolios/{portfolio_id}/investments  # Get portfolio investments
GET /portfolios/{portfolio_id}/investments/summary  # Get investment summary
```

#### Asset Pricing
```http
GET /assets/{ticker_symbol}/price           # Get current asset price
POST /assets/prices                         # Get multiple asset prices
POST /investments/update-prices             # Update investment prices
DELETE /cache/prices                        # Clear price cache
```

#### Portfolio Synchronization
```http
POST /portfolios/{portfolio_id}/sync-values # Sync portfolio values
```

#### Example: Create Investment
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

#### Example: Get Asset Price
```bash
curl http://portfolio-tracker-alb-426131923.us-east-1.elb.amazonaws.com/assets/AAPL/price
```

## 🔧 Configuration

### Environment Variables

Each service supports the following environment variables:

```bash
# Common
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Asset Service Specific
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key  # Optional
REDIS_URL=redis://localhost:6379              # Optional
PORTFOLIO_SERVICE_URL=http://portfolio-service:8001
```

### DynamoDB Tables

1. **portfolio-tracker-customers**
   - Partition Key: `customer_id`
   - Point-in-time recovery enabled

2. **portfolio-tracker-portfolios**
   - Partition Key: `portfolio_id`
   - GSI: `customer-index` (partition key: `customer_id`)

3. **portfolio-tracker-investments**
   - Partition Key: `investment_id`
   - GSI: `portfolio-index` (partition key: `portfolio_id`)

## 📊 Monitoring and Logging

### CloudWatch Log Groups

- `/ecs/customer-service` - Customer service logs
- `/ecs/portfolio-service` - Portfolio service logs  
- `/ecs/asset-service` - Asset service logs

### Health Checks

All services expose `/health` endpoints for monitoring:
- Returns HTTP 200 with service status
- Used by ALB target group health checks
- Monitored every 10 seconds

### Metrics Available

- ECS service metrics (CPU, memory, task count)
- ALB metrics (request count, latency, errors)
- DynamoDB metrics (read/write capacity, throttles)
- Custom application metrics via CloudWatch

## 🚦 Data Flow Examples

### Complete Investment Workflow

1. **Create Customer**
   ```bash
   POST /customers
   → Returns customer_id
   ```

2. **Create Portfolio**
   ```bash
   POST /portfolios
   → Links to customer_id
   → Returns portfolio_id
   ```

3. **Add Investment**
   ```bash
   POST /investments
   → Links to portfolio_id
   → Fetches current price
   → Calculates gains/losses
   ```

4. **Update Prices**
   ```bash
   POST /investments/update-prices
   → Fetches latest prices
   → Updates all investments
   → Synchronizes portfolio values
   ```

5. **View Portfolio Summary**
   ```bash
   GET /portfolios/{portfolio_id}/investments/summary
   → Returns aggregated portfolio metrics
   ```

### Service Communication Flow

```
Client Request → ALB → ECS Service → DynamoDB
                            ↓
                     External Price API
                            ↓
                        Redis Cache
                            ↓
                   Portfolio Service (sync)
```

## 🛠️ Development Setup

### Prerequisites

- Python 3.11+
- Docker
- AWS CLI configured
- Node.js (for CDK)

### Local Development

1. **Clone Repository**
   ```bash
   git clone https://github.com/jimcor101/awsPortfolioServicesDemo.git
   cd awsPortfolioServicesDemo
   ```

2. **Deploy Infrastructure**
   ```bash
   cd infrastructure
   pip install -r requirements.txt
   cdk deploy
   ```

3. **Build and Deploy Services**
   ```bash
   # Build all services
   ./scripts/build-all.sh
   
   # Deploy to ECS
   ./scripts/deploy-all.sh
   ```

### Testing

Each service includes unit tests and integration tests:

```bash
# Run tests for a specific service
cd services/customer-service
pytest tests/

# Run all tests
./scripts/run-tests.sh
```

## 🔐 Security Considerations

### Network Security
- Services run in private subnets
- ALB in public subnets with security groups
- No direct internet access to services

### IAM Roles
- Least privilege access
- Service-specific roles
- DynamoDB table-level permissions

### Data Protection
- Encryption at rest (DynamoDB)
- HTTPS termination at ALB
- No sensitive data in logs

## 🚀 Deployment Guide

### Production Deployment

1. **Configure Environment**
   ```bash
   export AWS_DEFAULT_REGION=us-east-1
   export ALPHA_VANTAGE_API_KEY=your-key
   ```

2. **Deploy Infrastructure**
   ```bash
   cd infrastructure
   cdk deploy --require-approval never
   ```

3. **Push Images to ECR**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin {account}.dkr.ecr.us-east-1.amazonaws.com
   
   # Build and push each service
   ./scripts/build-and-push.sh
   ```

4. **Verify Deployment**
   ```bash
   # Check service health
   curl http://your-alb-dns/health
   
   # Check ECS services
   aws ecs describe-services --cluster portfolio-tracker-cluster --services customer-service portfolio-service asset-service
   ```

## 📈 Performance Characteristics

### Expected Throughput
- **Customer Service**: 1000 requests/second
- **Portfolio Service**: 500 requests/second  
- **Asset Service**: 200 requests/second (due to external API limits)

### Latency Targets
- **Health checks**: < 100ms
- **CRUD operations**: < 200ms
- **Price fetching**: < 500ms (cached), < 2s (fresh)

### Scaling
- Auto-scaling configured for ECS services
- DynamoDB on-demand pricing
- ALB handles traffic distribution

## 🔍 Troubleshooting

### Common Issues

1. **Service Unhealthy**
   - Check CloudWatch logs
   - Verify security group rules
   - Confirm task definition ports

2. **Price API Failures**
   - Verify Alpha Vantage API key
   - Check rate limiting
   - Review cache configuration

3. **Database Connection Issues**
   - Verify IAM permissions
   - Check VPC endpoints
   - Review DynamoDB table configuration

### Debug Commands

```bash
# Check service logs
aws logs tail /ecs/customer-service --follow

# Check ECS task status
aws ecs describe-tasks --cluster portfolio-tracker-cluster --tasks {task-id}

# Check ALB target health
aws elbv2 describe-target-health --target-group-arn {target-group-arn}
```

## 📚 Additional Resources

- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [CDK Python Reference](https://docs.aws.amazon.com/cdk/api/v2/python/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
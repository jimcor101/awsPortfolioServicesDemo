# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Investment Portfolio Tracker** project that implements a microservices architecture for managing customer portfolios and financial assets. The system is designed to be deployed on AWS using modern containerized services.

## Architecture

The project follows a microservices pattern with three core services:

1. **Customer Service** - Handles user registration and customer profile management using DynamoDB
2. **Portfolio Service** - Maps customers to their investment portfolios using DynamoDB  
3. **Asset Service** - Retrieves real-time asset prices from external APIs with caching

### Data Model

The system uses the following core entities:
- **Customer**: User profile with contact information and address
- **Portfolio**: Customer's investment accounts (e.g., IRA, Brokerage, 401k)
- **Investment**: Individual holdings within portfolios (ticker, quantity, purchase info)
- **Instrument**: Optional normalized ticker/asset metadata

Relationships: Customer 1→N Portfolio 1→N Investment N→1 Instrument

## Technology Stack

### AWS Services
- **Amazon ECS (Fargate)** for container orchestration
- **API Gateway** for service routing
- **DynamoDB** for data persistence
- **EventBridge/SNS/SQS** for event-driven communication
- **Secrets Manager/Parameter Store** for configuration
- **CloudWatch + X-Ray + OpenTelemetry** for monitoring
- **IAM** for access control

### Development Stack
- **Python** microservices
- **Docker** containerization
- **AWS CDK** for Infrastructure as Code
- **GitHub Actions** for CI/CD
- **CloudFormation/CDK** for infrastructure deployment

## Development

The project is now fully deployed and operational:

### Live Environment
- **Base URL**: `http://portfolio-tracker-alb-184744493.us-east-1.elb.amazonaws.com`
- **ECS Cluster**: `portfolio-tracker-cluster`
- **Services**: customer-service, portfolio-service, asset-service (all running)

### Sample Data
The database is populated with sample data:
- 3 customers (John Smith, Sarah Johnson, Michael Davis)
- 4 portfolios (IRA, Brokerage, Roth IRA, 401k)
- 5 investments (AAPL, MSFT, GOOGL, TSLA, SPY)

### Build and Deployment
- Build images: `./scripts/build-and-push.sh`
- Deploy infrastructure: `./scripts/deploy-infrastructure.sh`
- Configure load balancer: `./scripts/configure-load-balancer.sh`

## Future Enhancements

The project roadmap includes:
- Terraform as an additional IaC option
- AWS CodePipeline integration
- Enhanced CI/CD workflows
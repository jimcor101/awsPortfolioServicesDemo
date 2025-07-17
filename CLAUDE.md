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

Since this appears to be a requirements/planning document, there are no build, test, or lint commands yet. The project is structured to implement:

- 3 Python microservices
- Docker containerization
- AWS CDK infrastructure
- CI/CD via GitHub Actions

## Future Enhancements

The project roadmap includes:
- Terraform as an additional IaC option
- AWS CodePipeline integration
- Enhanced CI/CD workflows
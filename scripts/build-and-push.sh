#!/bin/bash

# Build and Push All Services to ECR
# This script builds Docker images for all services and pushes them to ECR

set -e

# Get AWS account ID and region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_DEFAULT_REGION:-us-east-1}

echo "Building and pushing images to ECR..."
echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"

# Authenticate Docker with ECR
echo "Authenticating Docker with ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Function to build and push service
build_and_push_service() {
    local service_name=$1
    local service_dir=$2
    
    echo "Building $service_name..."
    
    # Navigate to service directory
    cd $service_dir
    
    # Build Docker image
    docker build -t $service_name .
    
    # Tag for ECR
    docker tag $service_name:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/portfolio-tracker/$service_name:latest
    
    # Push to ECR
    echo "Pushing $service_name to ECR..."
    docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/portfolio-tracker/$service_name:latest
    
    echo "✓ $service_name built and pushed successfully"
    
    # Return to original directory
    cd ..
}

# Navigate to services directory
cd services

# Build and push each service
build_and_push_service "customer-service" "customer-service"
build_and_push_service "portfolio-service" "portfolio-service"
build_and_push_service "asset-service" "asset-service"

echo "All services built and pushed successfully!"

# Verify images in ECR
echo "Verifying images in ECR..."
aws ecr list-images --repository-name portfolio-tracker/customer-service --query 'imageIds[?imageTag==`latest`]' --output table
aws ecr list-images --repository-name portfolio-tracker/portfolio-service --query 'imageIds[?imageTag==`latest`]' --output table
aws ecr list-images --repository-name portfolio-tracker/asset-service --query 'imageIds[?imageTag==`latest`]' --output table

echo "Build and push complete!"
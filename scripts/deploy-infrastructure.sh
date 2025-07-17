#!/bin/bash

# Deploy Infrastructure with CDK
# This script deploys the complete infrastructure stack

set -e

echo "Deploying infrastructure with CDK..."

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo "CDK is not installed. Installing..."
    npm install -g aws-cdk
fi

# Check CDK version
echo "CDK version: $(cdk --version)"

# Get AWS account info
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_DEFAULT_REGION:-us-east-1}

echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"

# Navigate to infrastructure directory
cd infrastructure

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Bootstrap CDK if not already done
echo "Checking CDK bootstrap status..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region $AWS_REGION &> /dev/null; then
    echo "Bootstrapping CDK..."
    cdk bootstrap aws://$AWS_ACCOUNT_ID/$AWS_REGION
else
    echo "CDK already bootstrapped"
fi

# Synthesize CDK app
echo "Synthesizing CDK app..."
cdk synth

# Deploy infrastructure
echo "Deploying infrastructure..."
cdk deploy --require-approval never

# Verify deployment
echo "Verifying deployment..."
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name InfrastructureStack --query 'Stacks[0].StackStatus' --output text)

if [ "$STACK_STATUS" = "CREATE_COMPLETE" ] || [ "$STACK_STATUS" = "UPDATE_COMPLETE" ]; then
    echo "✓ Infrastructure deployment successful!"
    
    # Display key outputs
    echo "Getting infrastructure details..."
    
    # ECS cluster
    ECS_CLUSTER=$(aws ecs describe-clusters --clusters portfolio-tracker-cluster --query 'clusters[0].clusterName' --output text)
    echo "ECS Cluster: $ECS_CLUSTER"
    
    # ALB DNS
    ALB_DNS=$(aws elbv2 describe-load-balancers --names portfolio-tracker-alb --query 'LoadBalancers[0].DNSName' --output text)
    echo "ALB DNS: $ALB_DNS"
    
    # VPC ID
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=InfrastructureStack/PortfolioTrackerVpc" --query 'Vpcs[0].VpcId' --output text)
    echo "VPC ID: $VPC_ID"
    
    # DynamoDB tables
    echo "DynamoDB Tables:"
    aws dynamodb list-tables --query 'TableNames' --output table
    
    # ECR repositories
    echo "ECR Repositories:"
    aws ecr describe-repositories --query 'repositories[*].repositoryName' --output table
    
else
    echo "✗ Infrastructure deployment failed with status: $STACK_STATUS"
    exit 1
fi

echo "Infrastructure deployment complete!"
echo "Next steps:"
echo "1. Run ./scripts/build-and-push.sh to build and push service images"
echo "2. Run ./scripts/configure-load-balancer.sh to configure routing"
echo "3. Test the deployment with curl http://$ALB_DNS/health"
# Deployment Guide

This guide provides step-by-step instructions for deploying the AWS Portfolio Services Demo to your AWS environment.

## Prerequisites

### Required Tools

1. **AWS CLI** (v2.0+)
   ```bash
   # Install AWS CLI
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   
   # Configure AWS CLI
   aws configure
   ```

2. **Docker** (v20.0+)
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   # Start Docker service
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

3. **Node.js** (v16+) and AWS CDK
   ```bash
   # Install Node.js
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   
   # Install AWS CDK
   npm install -g aws-cdk
   ```

4. **Python** (v3.11+)
   ```bash
   # Install Python 3.11
   sudo apt-get update
   sudo apt-get install python3.11 python3.11-venv python3.11-dev
   ```

5. **Git**
   ```bash
   sudo apt-get install git
   ```

### AWS Account Setup

1. **AWS Account**: Active AWS account with appropriate permissions
2. **IAM User**: User with the following permissions:
   - `AmazonECS_FullAccess`
   - `AmazonDynamoDBFullAccess`
   - `AmazonEC2ContainerRegistryFullAccess`
   - `ElasticLoadBalancingFullAccess`
   - `AmazonVPCFullAccess`
   - `IAMFullAccess`
   - `CloudWatchLogsFullAccess`
   - `AmazonAPIGatewayAdministrator`

3. **AWS Region**: Choose your preferred region (default: us-east-1)

## Step 1: Clone Repository

```bash
git clone https://github.com/jimcor101/awsPortfolioServicesDemo.git
cd awsPortfolioServicesDemo
```

## Step 2: Environment Configuration

### Configure AWS CLI

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your default region (e.g., us-east-1)
# Enter your default output format (json)
```

### Verify AWS Configuration

```bash
# Test AWS connectivity
aws sts get-caller-identity

# Check available regions
aws ec2 describe-regions --query 'Regions[*].RegionName' --output table
```

### Set Environment Variables

```bash
# Create environment file
cat > .env << EOF
AWS_DEFAULT_REGION=us-east-1
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key-here
REDIS_URL=redis://localhost:6379
EOF

# Source the environment
source .env
```

## Step 3: Bootstrap CDK

```bash
# Bootstrap CDK in your AWS account
cdk bootstrap aws://${AWS_ACCOUNT_ID}/${AWS_DEFAULT_REGION}

# Verify bootstrap was successful
aws cloudformation describe-stacks --stack-name CDKToolkit --query 'Stacks[0].StackStatus'
```

## Step 4: Deploy Infrastructure

### Install CDK Dependencies

```bash
cd infrastructure
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Deploy Base Infrastructure

```bash
# Deploy DynamoDB tables, VPC, ECS cluster, ECR repositories
cdk deploy --require-approval never

# Verify deployment
aws cloudformation describe-stacks --stack-name InfrastructureStack --query 'Stacks[0].StackStatus'
```

### Verify Infrastructure Components

```bash
# Check ECS cluster
aws ecs describe-clusters --clusters portfolio-tracker-cluster

# Check DynamoDB tables
aws dynamodb list-tables --query 'TableNames' --output table

# Check ECR repositories
aws ecr describe-repositories --query 'repositories[*].repositoryName' --output table

# Check VPC
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=InfrastructureStack/PortfolioTrackerVpc" --query 'Vpcs[0].VpcId' --output text
```

## Step 5: Build and Push Docker Images

### Authenticate Docker with ECR

```bash
# Get ECR login token
aws ecr get-login-password --region ${AWS_DEFAULT_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com
```

### Build Customer Service

```bash
cd ../services/customer-service

# Build Docker image
docker build -t customer-service .

# Tag for ECR
docker tag customer-service:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/portfolio-tracker/customer-service:latest

# Push to ECR
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/portfolio-tracker/customer-service:latest
```

### Build Portfolio Service

```bash
cd ../portfolio-service

# Build Docker image
docker build -t portfolio-service .

# Tag for ECR
docker tag portfolio-service:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/portfolio-tracker/portfolio-service:latest

# Push to ECR
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/portfolio-tracker/portfolio-service:latest
```

### Build Asset Service

```bash
cd ../asset-service

# Build Docker image
docker build -t asset-service .

# Tag for ECR
docker tag asset-service:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/portfolio-tracker/asset-service:latest

# Push to ECR
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/portfolio-tracker/asset-service:latest
```

### Verify Images in ECR

```bash
# List images in each repository
aws ecr list-images --repository-name portfolio-tracker/customer-service
aws ecr list-images --repository-name portfolio-tracker/portfolio-service
aws ecr list-images --repository-name portfolio-tracker/asset-service
```

## Step 6: Deploy ECS Services

### Update CDK to Enable Services

```bash
cd ../../infrastructure

# Enable ECS services in CDK code
# (This step enables the service creation code that was commented out)

# Deploy ECS services
cdk deploy --require-approval never
```

### Verify ECS Services

```bash
# Check service status
aws ecs describe-services --cluster portfolio-tracker-cluster --services customer-service portfolio-service asset-service --query 'services[*].[serviceName,status,runningCount,desiredCount]' --output table

# Check task status
aws ecs list-tasks --cluster portfolio-tracker-cluster --query 'taskArns' --output table
```

## Step 7: Configure Load Balancer

### Get Infrastructure Details

```bash
# Get VPC ID
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=InfrastructureStack/PortfolioTrackerVpc" --query 'Vpcs[0].VpcId' --output text)

# Get ALB ARN
ALB_ARN=$(aws elbv2 describe-load-balancers --names portfolio-tracker-alb --query 'LoadBalancers[0].LoadBalancerArn' --output text)

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers --names portfolio-tracker-alb --query 'LoadBalancers[0].DNSName' --output text)

echo "VPC ID: $VPC_ID"
echo "ALB ARN: $ALB_ARN"
echo "ALB DNS: $ALB_DNS"
```

### Create Target Groups

```bash
# Create Customer Service target group
CUSTOMER_TG_ARN=$(aws elbv2 create-target-group --name customer-service-tg --protocol HTTP --port 8000 --vpc-id $VPC_ID --target-type ip --health-check-path /health --health-check-protocol HTTP --health-check-port 8000 --query 'TargetGroups[0].TargetGroupArn' --output text)

# Create Portfolio Service target group
PORTFOLIO_TG_ARN=$(aws elbv2 create-target-group --name portfolio-service-tg --protocol HTTP --port 8001 --vpc-id $VPC_ID --target-type ip --health-check-path /health --health-check-protocol HTTP --health-check-port 8001 --query 'TargetGroups[0].TargetGroupArn' --output text)

# Create Asset Service target group
ASSET_TG_ARN=$(aws elbv2 create-target-group --name asset-service-tg --protocol HTTP --port 8002 --vpc-id $VPC_ID --target-type ip --health-check-path /health --health-check-protocol HTTP --health-check-port 8002 --query 'TargetGroups[0].TargetGroupArn' --output text)

echo "Customer TG ARN: $CUSTOMER_TG_ARN"
echo "Portfolio TG ARN: $PORTFOLIO_TG_ARN"
echo "Asset TG ARN: $ASSET_TG_ARN"
```

### Register ECS Tasks with Target Groups

```bash
# Get ECS task IPs
CUSTOMER_IP=$(aws ecs describe-tasks --cluster portfolio-tracker-cluster --tasks $(aws ecs list-tasks --cluster portfolio-tracker-cluster --service-name customer-service --query 'taskArns[0]' --output text) --query 'tasks[0].attachments[0].details[?name==`privateIPv4Address`].value' --output text)

PORTFOLIO_IP=$(aws ecs describe-tasks --cluster portfolio-tracker-cluster --tasks $(aws ecs list-tasks --cluster portfolio-tracker-cluster --service-name portfolio-service --query 'taskArns[0]' --output text) --query 'tasks[0].attachments[0].details[?name==`privateIPv4Address`].value' --output text)

ASSET_IP=$(aws ecs describe-tasks --cluster portfolio-tracker-cluster --tasks $(aws ecs list-tasks --cluster portfolio-tracker-cluster --service-name asset-service --query 'taskArns[0]' --output text) --query 'tasks[0].attachments[0].details[?name==`privateIPv4Address`].value' --output text)

# Register targets
aws elbv2 register-targets --target-group-arn $CUSTOMER_TG_ARN --targets Id=$CUSTOMER_IP,Port=8000
aws elbv2 register-targets --target-group-arn $PORTFOLIO_TG_ARN --targets Id=$PORTFOLIO_IP,Port=8001
aws elbv2 register-targets --target-group-arn $ASSET_TG_ARN --targets Id=$ASSET_IP,Port=8002
```

### Configure Load Balancer Routing

```bash
# Get listener ARN
LISTENER_ARN=$(aws elbv2 describe-listeners --load-balancer-arn $ALB_ARN --query 'Listeners[0].ListenerArn' --output text)

# Create routing rules
aws elbv2 create-rule --listener-arn $LISTENER_ARN --priority 100 --conditions Field=path-pattern,Values="/customers*" --actions Type=forward,TargetGroupArn=$CUSTOMER_TG_ARN

aws elbv2 create-rule --listener-arn $LISTENER_ARN --priority 200 --conditions Field=path-pattern,Values="/portfolios*" --actions Type=forward,TargetGroupArn=$PORTFOLIO_TG_ARN

aws elbv2 create-rule --listener-arn $LISTENER_ARN --priority 300 --conditions Field=path-pattern,Values="/investments*" --actions Type=forward,TargetGroupArn=$ASSET_TG_ARN

aws elbv2 create-rule --listener-arn $LISTENER_ARN --priority 400 --conditions Field=path-pattern,Values="/assets*" --actions Type=forward,TargetGroupArn=$ASSET_TG_ARN
```

### Configure Security Groups

```bash
# Get security group IDs
ALB_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=InfrastructureStack-PortfolioTrackerALB*" --query 'SecurityGroups[0].GroupId' --output text)
CUSTOMER_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=InfrastructureStack-CustomerServiceSecurityGroup*" --query 'SecurityGroups[0].GroupId' --output text)
PORTFOLIO_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=InfrastructureStack-PortfolioServiceSecurityGroup*" --query 'SecurityGroups[0].GroupId' --output text)
ASSET_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=InfrastructureStack-AssetServiceSecurityGroup*" --query 'SecurityGroups[0].GroupId' --output text)

# Allow ALB to reach services
aws ec2 authorize-security-group-ingress --group-id $CUSTOMER_SG --protocol tcp --port 8000 --source-group $ALB_SG
aws ec2 authorize-security-group-ingress --group-id $PORTFOLIO_SG --protocol tcp --port 8001 --source-group $ALB_SG
aws ec2 authorize-security-group-ingress --group-id $ASSET_SG --protocol tcp --port 8002 --source-group $ALB_SG
```

## Step 8: Verify Deployment

### Check Target Group Health

```bash
# Wait for health checks to pass
sleep 30

# Check target group health
aws elbv2 describe-target-health --target-group-arn $CUSTOMER_TG_ARN --query 'TargetHealthDescriptions[0].TargetHealth.State' --output text
aws elbv2 describe-target-health --target-group-arn $PORTFOLIO_TG_ARN --query 'TargetHealthDescriptions[0].TargetHealth.State' --output text
aws elbv2 describe-target-health --target-group-arn $ASSET_TG_ARN --query 'TargetHealthDescriptions[0].TargetHealth.State' --output text
```

### Test API Endpoints

```bash
# Test health endpoints
curl http://$ALB_DNS/health

# Test service endpoints
curl http://$ALB_DNS/customers
curl http://$ALB_DNS/portfolios
curl http://$ALB_DNS/assets/AAPL/price
```

### Verify Logs

```bash
# Check service logs
aws logs describe-log-groups --log-group-name-prefix "/ecs/"

# View recent logs
aws logs tail /ecs/customer-service --follow --start-time -1h
aws logs tail /ecs/portfolio-service --follow --start-time -1h
aws logs tail /ecs/asset-service --follow --start-time -1h
```

## Step 9: Optional Configuration

### Configure Alpha Vantage API Key

```bash
# Update ECS task definitions with Alpha Vantage API key
# This enables real-time stock price data instead of mock data

# Get current task definition
aws ecs describe-task-definition --task-definition asset-service --query 'taskDefinition.containerDefinitions[0].environment' --output table

# Update task definition (requires CDK redeployment with environment variable)
```

### Configure Redis Cache

```bash
# Deploy Redis instance (optional)
# This improves price lookup performance

# Create Redis cluster
aws elasticache create-cache-cluster --cache-cluster-id portfolio-cache --cache-node-type cache.t3.micro --engine redis --num-cache-nodes 1

# Update ECS task definition with Redis URL
```

## Step 10: Production Considerations

### Security Hardening

```bash
# Enable VPC Flow Logs
aws ec2 create-flow-logs --resource-type VPC --resource-ids $VPC_ID --traffic-type ALL --log-destination-type cloud-watch-logs --log-group-name VPCFlowLogs

# Enable DynamoDB encryption at rest
aws dynamodb update-table --table-name portfolio-tracker-customers --sse-specification Enabled=true,SSEType=KMS

# Enable ALB access logs
aws elbv2 modify-load-balancer-attributes --load-balancer-arn $ALB_ARN --attributes Key=access_logs.s3.enabled,Value=true Key=access_logs.s3.bucket,Value=your-log-bucket
```

### Monitoring Setup

```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard --dashboard-name "Portfolio-Services" --dashboard-body file://cloudwatch-dashboard.json

# Create CloudWatch alarms
aws cloudwatch put-metric-alarm --alarm-name "High-CPU-Customer-Service" --alarm-description "High CPU usage on Customer Service" --metric-name CPUUtilization --namespace AWS/ECS --statistic Average --period 300 --threshold 80 --comparison-operator GreaterThanThreshold --evaluation-periods 2
```

### Backup Configuration

```bash
# Enable DynamoDB Point-in-Time Recovery
aws dynamodb update-continuous-backups --table-name portfolio-tracker-customers --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
aws dynamodb update-continuous-backups --table-name portfolio-tracker-portfolios --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
aws dynamodb update-continuous-backups --table-name portfolio-tracker-investments --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

# Create backup plan
aws backup create-backup-plan --backup-plan file://backup-plan.json
```

## Troubleshooting

### Common Issues

1. **CDK Bootstrap Errors**
   ```bash
   # Check CDK version
   cdk --version
   
   # Update CDK
   npm install -g aws-cdk@latest
   
   # Re-bootstrap
   cdk bootstrap --force
   ```

2. **Docker Build Failures**
   ```bash
   # Check Docker daemon
   docker info
   
   # Restart Docker
   sudo systemctl restart docker
   
   # Clear Docker cache
   docker system prune -a
   ```

3. **ECS Task Failures**
   ```bash
   # Check task logs
   aws ecs describe-tasks --cluster portfolio-tracker-cluster --tasks [task-id] --query 'tasks[0].stoppedReason'
   
   # Check service events
   aws ecs describe-services --cluster portfolio-tracker-cluster --services customer-service --query 'services[0].events[0:5]'
   ```

4. **Target Group Health Issues**
   ```bash
   # Check security group rules
   aws ec2 describe-security-groups --group-ids $CUSTOMER_SG --query 'SecurityGroups[0].IpPermissions'
   
   # Check target health
   aws elbv2 describe-target-health --target-group-arn $CUSTOMER_TG_ARN
   ```

### Debugging Commands

```bash
# ECS service logs
aws logs get-log-events --log-group-name /ecs/customer-service --log-stream-name [stream-name] --limit 10

# ECS task details
aws ecs describe-tasks --cluster portfolio-tracker-cluster --tasks [task-id] --query 'tasks[0].containers[0].lastStatus'

# ALB listener rules
aws elbv2 describe-rules --listener-arn $LISTENER_ARN --query 'Rules[*].[Priority,Conditions[0].Values[0]]' --output table

# Network connectivity
aws ec2 describe-network-interfaces --network-interface-ids [eni-id] --query 'NetworkInterfaces[0].PrivateIpAddress'
```

## Cleanup

### Remove Resources

```bash
# Delete ECS services
aws ecs delete-service --cluster portfolio-tracker-cluster --service customer-service --force
aws ecs delete-service --cluster portfolio-tracker-cluster --service portfolio-service --force
aws ecs delete-service --cluster portfolio-tracker-cluster --service asset-service --force

# Delete target groups
aws elbv2 delete-target-group --target-group-arn $CUSTOMER_TG_ARN
aws elbv2 delete-target-group --target-group-arn $PORTFOLIO_TG_ARN
aws elbv2 delete-target-group --target-group-arn $ASSET_TG_ARN

# Delete CDK stack
cdk destroy --force
```

### Clean Up ECR Images

```bash
# Delete all images in ECR repositories
aws ecr batch-delete-image --repository-name portfolio-tracker/customer-service --image-ids imageTag=latest
aws ecr batch-delete-image --repository-name portfolio-tracker/portfolio-service --image-ids imageTag=latest
aws ecr batch-delete-image --repository-name portfolio-tracker/asset-service --image-ids imageTag=latest
```

## Next Steps

1. **Set up CI/CD pipeline** with AWS CodePipeline
2. **Configure monitoring** with CloudWatch and X-Ray
3. **Implement authentication** with Amazon Cognito
4. **Add API rate limiting** with AWS API Gateway
5. **Set up automated testing** with AWS CodeBuild
6. **Configure disaster recovery** with multi-region deployment

For additional help, refer to the [API Reference](API_REFERENCE.md) and [README](../README.md) documentation.
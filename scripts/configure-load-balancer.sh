#!/bin/bash

# Configure Load Balancer and Target Groups
# This script sets up ALB routing for all services

set -e

echo "Configuring load balancer and target groups..."

# Get infrastructure details
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=InfrastructureStack/PortfolioTrackerVpc" --query 'Vpcs[0].VpcId' --output text)
ALB_ARN=$(aws elbv2 describe-load-balancers --names portfolio-tracker-alb --query 'LoadBalancers[0].LoadBalancerArn' --output text)
ALB_DNS=$(aws elbv2 describe-load-balancers --names portfolio-tracker-alb --query 'LoadBalancers[0].DNSName' --output text)

echo "VPC ID: $VPC_ID"
echo "ALB ARN: $ALB_ARN"
echo "ALB DNS: $ALB_DNS"

# Function to create target group if it doesn't exist
create_target_group() {
    local name=$1
    local port=$2
    
    if aws elbv2 describe-target-groups --names $name &> /dev/null; then
        echo "Target group $name already exists"
        TG_ARN=$(aws elbv2 describe-target-groups --names $name --query 'TargetGroups[0].TargetGroupArn' --output text)
    else
        echo "Creating target group $name..."
        TG_ARN=$(aws elbv2 create-target-group --name $name --protocol HTTP --port $port --vpc-id $VPC_ID --target-type ip --health-check-path /health --health-check-protocol HTTP --health-check-port $port --query 'TargetGroups[0].TargetGroupArn' --output text)
    fi
    
    echo "Target group $name ARN: $TG_ARN"
}

# Create target groups
create_target_group "customer-service-tg" 8000
CUSTOMER_TG_ARN=$TG_ARN

create_target_group "portfolio-service-tg" 8001
PORTFOLIO_TG_ARN=$TG_ARN

create_target_group "asset-service-tg" 8002
ASSET_TG_ARN=$TG_ARN

# Wait for ECS services to be running
echo "Waiting for ECS services to be running..."
sleep 30

# Function to get ECS task IP
get_task_ip() {
    local service_name=$1
    local task_arn=$(aws ecs list-tasks --cluster portfolio-tracker-cluster --service-name $service_name --query 'taskArns[0]' --output text)
    
    if [ "$task_arn" != "None" ] && [ "$task_arn" != "null" ]; then
        aws ecs describe-tasks --cluster portfolio-tracker-cluster --tasks $task_arn --query 'tasks[0].attachments[0].details[?name==`privateIPv4Address`].value' --output text
    else
        echo "No tasks found for service $service_name"
        return 1
    fi
}

# Get ECS task IPs
echo "Getting ECS task IPs..."
CUSTOMER_IP=$(get_task_ip "customer-service")
PORTFOLIO_IP=$(get_task_ip "portfolio-service")
ASSET_IP=$(get_task_ip "asset-service")

echo "Customer Service IP: $CUSTOMER_IP"
echo "Portfolio Service IP: $PORTFOLIO_IP"
echo "Asset Service IP: $ASSET_IP"

# Register targets
if [ "$CUSTOMER_IP" != "" ]; then
    echo "Registering customer service target..."
    aws elbv2 register-targets --target-group-arn $CUSTOMER_TG_ARN --targets Id=$CUSTOMER_IP,Port=8000
fi

if [ "$PORTFOLIO_IP" != "" ]; then
    echo "Registering portfolio service target..."
    aws elbv2 register-targets --target-group-arn $PORTFOLIO_TG_ARN --targets Id=$PORTFOLIO_IP,Port=8001
fi

if [ "$ASSET_IP" != "" ]; then
    echo "Registering asset service target..."
    aws elbv2 register-targets --target-group-arn $ASSET_TG_ARN --targets Id=$ASSET_IP,Port=8002
fi

# Get listener ARN
LISTENER_ARN=$(aws elbv2 describe-listeners --load-balancer-arn $ALB_ARN --query 'Listeners[0].ListenerArn' --output text)

# Function to create listener rule if it doesn't exist
create_listener_rule() {
    local priority=$1
    local path_pattern=$2
    local target_group_arn=$3
    
    # Check if rule already exists
    if aws elbv2 describe-rules --listener-arn $LISTENER_ARN --query "Rules[?Priority=='$priority']" --output text | grep -q "$priority"; then
        echo "Listener rule with priority $priority already exists"
    else
        echo "Creating listener rule for $path_pattern..."
        aws elbv2 create-rule --listener-arn $LISTENER_ARN --priority $priority --conditions Field=path-pattern,Values="$path_pattern" --actions Type=forward,TargetGroupArn=$target_group_arn
    fi
}

# Create listener rules
create_listener_rule 100 "/customers*" $CUSTOMER_TG_ARN
create_listener_rule 200 "/portfolios*" $PORTFOLIO_TG_ARN
create_listener_rule 300 "/investments*" $ASSET_TG_ARN
create_listener_rule 400 "/assets*" $ASSET_TG_ARN

# Configure security groups
echo "Configuring security groups..."
ALB_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=InfrastructureStack-PortfolioTrackerALB*" --query 'SecurityGroups[0].GroupId' --output text)
CUSTOMER_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=InfrastructureStack-CustomerServiceSecurityGroup*" --query 'SecurityGroups[0].GroupId' --output text)
PORTFOLIO_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=InfrastructureStack-PortfolioServiceSecurityGroup*" --query 'SecurityGroups[0].GroupId' --output text)
ASSET_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=InfrastructureStack-AssetServiceSecurityGroup*" --query 'SecurityGroups[0].GroupId' --output text)

# Function to add security group rule if it doesn't exist
add_sg_rule() {
    local sg_id=$1
    local port=$2
    local source_sg=$3
    
    if aws ec2 describe-security-groups --group-ids $sg_id --query "SecurityGroups[0].IpPermissions[?FromPort==\`$port\` && UserIdGroupPairs[?GroupId==\`$source_sg\`]]" --output text | grep -q "$port"; then
        echo "Security group rule already exists for port $port"
    else
        echo "Adding security group rule for port $port..."
        aws ec2 authorize-security-group-ingress --group-id $sg_id --protocol tcp --port $port --source-group $source_sg
    fi
}

# Add security group rules
add_sg_rule $CUSTOMER_SG 8000 $ALB_SG
add_sg_rule $PORTFOLIO_SG 8001 $ALB_SG
add_sg_rule $ASSET_SG 8002 $ALB_SG

# Wait for health checks
echo "Waiting for health checks to pass..."
sleep 30

# Check target group health
echo "Checking target group health..."
aws elbv2 describe-target-health --target-group-arn $CUSTOMER_TG_ARN --query 'TargetHealthDescriptions[0].TargetHealth.State' --output text
aws elbv2 describe-target-health --target-group-arn $PORTFOLIO_TG_ARN --query 'TargetHealthDescriptions[0].TargetHealth.State' --output text
aws elbv2 describe-target-health --target-group-arn $ASSET_TG_ARN --query 'TargetHealthDescriptions[0].TargetHealth.State' --output text

echo "Load balancer configuration complete!"
echo "ALB DNS: $ALB_DNS"
echo "Test endpoints:"
echo "  Health: curl http://$ALB_DNS/health"
echo "  Customers: curl http://$ALB_DNS/customers"
echo "  Portfolios: curl http://$ALB_DNS/portfolios"
echo "  Assets: curl http://$ALB_DNS/assets/AAPL/price"
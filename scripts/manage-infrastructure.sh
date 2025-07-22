#!/bin/bash

# AWS Infrastructure Management Script
# This script can shutdown or startup the AWS infrastructure to save costs

set -e

# Configuration
CLUSTER_NAME="portfolio-tracker-cluster"
SERVICES=("customer-service" "portfolio-service" "asset-service")
REGION=${AWS_DEFAULT_REGION:-us-east-1}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if AWS CLI is configured
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed"
        exit 1
    fi

    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS CLI is not configured or credentials are invalid"
        exit 1
    fi
}

# Function to get current service status
get_service_status() {
    local service=$1
    local status=$(aws ecs describe-services \
        --cluster $CLUSTER_NAME \
        --services $service \
        --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}' \
        --output json 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo $status
    else
        echo '{"Status": "NOT_FOUND", "Running": 0, "Desired": 0}'
    fi
}

# Function to shutdown infrastructure
shutdown_infrastructure() {
    print_status "Starting infrastructure shutdown..."
    
    # Stop ECS services
    print_status "Stopping ECS services..."
    for service in "${SERVICES[@]}"; do
        print_status "Stopping service: $service"
        
        # Get current status
        status=$(get_service_status $service)
        current_desired=$(echo $status | jq -r '.Desired')
        
        if [ "$current_desired" -gt 0 ]; then
            # Scale service to 0
            aws ecs update-service \
                --cluster $CLUSTER_NAME \
                --service $service \
                --desired-count 0 \
                --no-cli-pager
            
            print_status "Service $service scaled to 0 (was $current_desired)"
        else
            print_warning "Service $service is already stopped"
        fi
    done
    
    # Wait for services to stop
    print_status "Waiting for services to stop completely..."
    sleep 30
    
    # Verify all services are stopped
    print_status "Verifying service shutdown status..."
    for service in "${SERVICES[@]}"; do
        status=$(get_service_status $service)
        running=$(echo $status | jq -r '.Running')
        desired=$(echo $status | jq -r '.Desired')
        
        if [ "$running" -eq 0 ] && [ "$desired" -eq 0 ]; then
            print_status "✓ $service: Stopped (Running: $running, Desired: $desired)"
        else
            print_warning "⚠ $service: Still running (Running: $running, Desired: $desired)"
        fi
    done
    
    print_status "Infrastructure shutdown complete!"
    print_warning "Note: DynamoDB tables and other resources remain active and will continue to incur minimal charges"
    print_status "ECS services are stopped and will not incur compute charges"
}

# Function to startup infrastructure
startup_infrastructure() {
    print_status "Starting infrastructure startup..."
    
    # Start ECS services
    print_status "Starting ECS services..."
    for service in "${SERVICES[@]}"; do
        print_status "Starting service: $service"
        
        # Scale service to 1 (or desired count)
        aws ecs update-service \
            --cluster $CLUSTER_NAME \
            --service $service \
            --desired-count 1 \
            --no-cli-pager
        
        print_status "Service $service scaled to 1"
    done
    
    # Wait for services to start
    print_status "Waiting for services to start..."
    sleep 60
    
    # Wait for services to become healthy
    print_status "Waiting for services to become healthy..."
    for service in "${SERVICES[@]}"; do
        print_status "Checking health status of $service..."
        
        # Wait up to 5 minutes for service to become healthy
        timeout=300
        elapsed=0
        
        while [ $elapsed -lt $timeout ]; do
            status=$(get_service_status $service)
            running=$(echo $status | jq -r '.Running')
            desired=$(echo $status | jq -r '.Desired')
            
            if [ "$running" -eq "$desired" ] && [ "$running" -gt 0 ]; then
                print_status "✓ $service: Healthy (Running: $running, Desired: $desired)"
                break
            else
                print_status "Waiting for $service... (Running: $running, Desired: $desired)"
                sleep 15
                elapsed=$((elapsed + 15))
            fi
        done
        
        if [ $elapsed -ge $timeout ]; then
            print_warning "⚠ $service: Timeout waiting for healthy status"
        fi
    done
    
    print_status "Infrastructure startup complete!"
    
    # Get ALB DNS name
    ALB_DNS=$(aws elbv2 describe-load-balancers \
        --names portfolio-tracker-alb \
        --query 'LoadBalancers[0].DNSName' \
        --output text 2>/dev/null || echo "ALB not found")
    
    if [ "$ALB_DNS" != "ALB not found" ]; then
        print_status "Application Load Balancer: http://$ALB_DNS"
        print_status "Health Check: curl http://$ALB_DNS/health"
    fi
}

# Function to show current status
show_status() {
    print_status "Current Infrastructure Status:"
    print_status "=============================="
    
    # Check ECS services
    print_status "ECS Services:"
    for service in "${SERVICES[@]}"; do
        status=$(get_service_status $service)
        service_status=$(echo $status | jq -r '.Status')
        running=$(echo $status | jq -r '.Running')
        desired=$(echo $status | jq -r '.Desired')
        
        if [ "$service_status" = "NOT_FOUND" ]; then
            print_error "  $service: NOT FOUND"
        elif [ "$running" -eq 0 ]; then
            print_warning "  $service: STOPPED (Running: $running, Desired: $desired)"
        else
            print_status "  $service: RUNNING (Running: $running, Desired: $desired)"
        fi
    done
    
    # Check ALB
    print_status ""
    ALB_STATUS=$(aws elbv2 describe-load-balancers \
        --names portfolio-tracker-alb \
        --query 'LoadBalancers[0].State.Code' \
        --output text 2>/dev/null || echo "not_found")
    
    if [ "$ALB_STATUS" = "active" ]; then
        ALB_DNS=$(aws elbv2 describe-load-balancers \
            --names portfolio-tracker-alb \
            --query 'LoadBalancers[0].DNSName' \
            --output text)
        print_status "Load Balancer: ACTIVE"
        print_status "  URL: http://$ALB_DNS"
    elif [ "$ALB_STATUS" = "not_found" ]; then
        print_error "Load Balancer: NOT FOUND"
    else
        print_warning "Load Balancer: $ALB_STATUS"
    fi
    
    # Check DynamoDB tables
    print_status ""
    print_status "DynamoDB Tables:"
    TABLES=$(aws dynamodb list-tables --query 'TableNames[?contains(@, `portfolio-tracker`)]' --output json)
    table_count=$(echo $TABLES | jq length)
    
    if [ "$table_count" -gt 0 ]; then
        echo $TABLES | jq -r '.[]' | while read table; do
            print_status "  $table: ACTIVE"
        done
    else
        print_warning "  No portfolio-tracker tables found"
    fi
}

# Function to show usage
show_usage() {
    echo "AWS Infrastructure Management Script"
    echo ""
    echo "Usage: $0 {shutdown|startup|status|help}"
    echo ""
    echo "Commands:"
    echo "  shutdown  - Stop all ECS services (saves compute costs)"
    echo "  startup   - Start all ECS services"
    echo "  status    - Show current infrastructure status"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 shutdown    # Stop all services to save costs"
    echo "  $0 startup     # Start all services"
    echo "  $0 status      # Check current status"
    echo ""
    echo "Note: This script only manages ECS services. DynamoDB, ALB, and other"
    echo "      infrastructure components remain active to preserve data and configuration."
}

# Main script logic
main() {
    # Check prerequisites
    check_aws_cli
    
    case "$1" in
        shutdown)
            shutdown_infrastructure
            ;;
        startup)
            startup_infrastructure
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Invalid command: $1"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
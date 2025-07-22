# Infrastructure Management Scripts

This directory contains scripts to manage the AWS Portfolio Services Demo infrastructure.

## 📋 Available Scripts

### `manage-infrastructure.sh`
**Purpose**: Start/stop AWS infrastructure to manage costs

**Usage**:
```bash
./scripts/manage-infrastructure.sh {shutdown|startup|status|help}
```

**Commands**:

#### `shutdown` - Stop All Services
```bash
./scripts/manage-infrastructure.sh shutdown
```
- Stops all ECS services (scales to 0)
- Saves compute costs while preserving data
- DynamoDB tables remain active
- Load balancer remains active

#### `startup` - Start All Services  
```bash
./scripts/manage-infrastructure.sh startup
```
- Starts all ECS services (scales to 1)
- Waits for services to become healthy
- Verifies deployment status

#### `status` - Check Current Status
```bash
./scripts/manage-infrastructure.sh status
```
- Shows ECS service status
- Shows Load Balancer status
- Shows DynamoDB table status
- Displays API endpoint URL

#### `help` - Show Usage Information
```bash
./scripts/manage-infrastructure.sh help
```

## 💰 Cost Management

### When to Shutdown
- **After development sessions**: Save ~$50-100/month on ECS compute costs
- **Overnight/weekends**: When not actively testing
- **Extended breaks**: During vacations or project pauses

### What Happens During Shutdown
- ✅ **ECS Services**: Stopped (no compute charges)
- ✅ **Data**: Preserved in DynamoDB
- ✅ **Configuration**: Load balancer and networking preserved
- ✅ **Images**: Remain in ECR repositories

### Minimal Ongoing Costs
Even when shutdown, these services incur minimal costs:
- DynamoDB: ~$1-5/month (pay-per-request)
- Load Balancer: ~$16/month
- ECR Storage: ~$1-2/month
- VPC/Networking: Usually free tier

## 🔧 Other Infrastructure Scripts

### `build-and-push.sh`
Build and push all service Docker images to ECR
```bash
./scripts/build-and-push.sh
```

### `deploy-infrastructure.sh` 
Deploy complete infrastructure using CDK
```bash
./scripts/deploy-infrastructure.sh
```

### `configure-load-balancer.sh`
Configure ALB routing and health checks
```bash
./scripts/configure-load-balancer.sh
```

## 📊 Example Workflow

### Daily Development
```bash
# Morning: Start infrastructure
./scripts/manage-infrastructure.sh startup

# Work on development...
curl http://portfolio-tracker-alb-184744493.us-east-1.elb.amazonaws.com/health

# Evening: Stop to save costs
./scripts/manage-infrastructure.sh shutdown
```

### Check Status Anytime
```bash
./scripts/manage-infrastructure.sh status
```

### Full Redeploy (if needed)
```bash
# 1. Deploy infrastructure
./scripts/deploy-infrastructure.sh

# 2. Build and push images  
./scripts/build-and-push.sh

# 3. Configure load balancer
./scripts/configure-load-balancer.sh

# 4. Check status
./scripts/manage-infrastructure.sh status
```

## ⚠️ Important Notes

1. **Data Safety**: Shutdown only stops compute services, data is preserved
2. **Startup Time**: Allow 2-3 minutes for services to become fully healthy
3. **Dependencies**: Requires AWS CLI configured with appropriate permissions
4. **Region**: Uses `AWS_DEFAULT_REGION` or defaults to `us-east-1`

## 🆘 Troubleshooting

### Services Won't Start
```bash
# Check ECS task logs
aws logs tail /ecs/customer-service --follow

# Check service events
aws ecs describe-services --cluster portfolio-tracker-cluster --services customer-service
```

### Load Balancer Issues
```bash
# Check target group health
aws elbv2 describe-target-health --target-group-arn <target-group-arn>
```

### Permission Issues
Ensure your AWS credentials have permissions for:
- ECS (describe-services, update-service)
- ELBv2 (describe-load-balancers, describe-target-health)
- DynamoDB (list-tables)
- Logs (describe-log-groups, get-log-events)
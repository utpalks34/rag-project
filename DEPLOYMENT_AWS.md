# Deployment Guide: AWS

This guide covers deploying the AI Study Notes Assistant on AWS.

## Prerequisites

- AWS account with appropriate permissions
- AWS CLI installed and configured
- Docker installed locally
- OpenAI API key

## Architecture

```
┌─────────────────────────────────────────┐
│         AWS Application                 │
├─────────────────────────────────────────┤
│  Route 53 (DNS) → CloudFront (CDN)     │
│         ↓                               │
│  ALB (Application Load Balancer)        │
│   ├─ Port 8000 (Backend API)            │
│   └─ Port 8501 (Frontend)               │
├─────────────────────────────────────────┤
│  ECS (Elastic Container Service)        │
│   ├─ Task 1: FastAPI Backend            │
│   └─ Task 2: Streamlit Frontend         │
├─────────────────────────────────────────┤
│  EBS (Elastic Block Store)              │
│   ├─ ChromaDB Vector Store              │
│   └─ Uploaded PDFs                      │
├─────────────────────────────────────────┤
│  RDS (Optional: for metadata)           │
└─────────────────────────────────────────┘
```

## Step 1: Prepare Docker Images

1. Build images:
```bash
docker build -f docker/Dockerfile -t ai-study-backend:latest .
docker build -f docker/Dockerfile.frontend -t ai-study-frontend:latest .
```

2. Push to ECR (Elastic Container Registry):
```bash
# Create ECR repositories
aws ecr create-repository --repository-name ai-study-backend --region us-east-1
aws ecr create-repository --repository-name ai-study-frontend --region us-east-1

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag ai-study-backend:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-study-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-study-backend:latest

# Repeat for frontend
docker tag ai-study-frontend:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-study-frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-study-frontend:latest
```

## Step 2: Create VPC and Networking

1. Create VPC:
```bash
aws ec2 create-vpc --cidr-block 10.0.0.0/16
```

2. Create subnets:
```bash
# Public subnet 1
aws ec2 create-subnet --vpc-id vpc-xxx \
  --cidr-block 10.0.1.0/24 --availability-zone us-east-1a

# Public subnet 2
aws ec2 create-subnet --vpc-id vpc-xxx \
  --cidr-block 10.0.2.0/24 --availability-zone us-east-1b

# Private subnet for database
aws ec2 create-subnet --vpc-id vpc-xxx \
  --cidr-block 10.0.3.0/24 --availability-zone us-east-1a
```

3. Create Internet Gateway and routes
4. Create NAT Gateway for private subnets

## Step 3: Create ECS Cluster

1. Create cluster:
```bash
aws ecs create-cluster --cluster-name ai-study-cluster
```

2. Register task definitions:

**Backend Task Definition:**
```json
{
  "family": "ai-study-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-study-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENAI_API_KEY",
          "value": "${OPENAI_API_KEY}"
        },
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-study-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "mountPoints": [
        {
          "sourceVolume": "ebs-data",
          "containerPath": "/app/data"
        }
      ]
    }
  ],
  "volumes": [
    {
      "name": "ebs-data",
      "ebs": {
        "size": 50,
        "deleteOnTermination": false,
        "volumeType": "gp3"
      }
    }
  ]
}
```

## Step 4: Configure Load Balancer

1. Create Application Load Balancer:
```bash
aws elbv2 create-load-balancer \
  --name ai-study-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx \
  --scheme internet-facing
```

2. Create target groups:
```bash
# Backend target group
aws elbv2 create-target-group \
  --name ai-study-backend-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxx \
  --target-type ip

# Frontend target group
aws elbv2 create-target-group \
  --name ai-study-frontend-tg \
  --protocol HTTP \
  --port 8501 \
  --vpc-id vpc-xxx \
  --target-type ip
```

3. Create listener rules
4. Configure health checks

## Step 5: Create Services

1. Create backend service:
```bash
aws ecs create-service \
  --cluster ai-study-cluster \
  --service-name ai-study-backend-service \
  --task-definition ai-study-backend:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=backend,containerPort=8000"
```

2. Create frontend service (similar)

## Step 6: Configure Auto Scaling

1. Create Auto Scaling policy:
```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/ai-study-cluster/ai-study-backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 10
```

2. Create scaling policy:
```bash
aws application-autoscaling put-scaling-policy \
  --policy-name ai-study-scale-up \
  --service-namespace ecs \
  --resource-id service/ai-study-cluster/ai-study-backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration \
  "TargetValue=70.0,PredefinedMetricSpecification={PredefinedMetricType=ECSServiceAverageCPUUtilization}"
```

## Step 7: Set Up Monitoring

1. Enable CloudWatch:
```bash
# Logs group already created by ECS
aws logs create-log-group --log-group-name /ecs/ai-study-backend
aws logs create-log-group --log-group-name /ecs/ai-study-frontend
```

2. Create CloudWatch Alarms for:
   - CPU utilization
   - Memory usage
   - Request latency
   - Error rates

3. Set up SNS for notifications

## Step 8: Configure Route 53

1. Create hosted zone
2. Create A records pointing to ALB
3. Set up SSL/TLS certificates (ACM)

## Step 9: Enable RDS (Optional)

For production with metadata storage:

```bash
aws rds create-db-instance \
  --db-instance-identifier ai-study-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password "<strong-password>" \
  --allocated-storage 20 \
  --publicly-accessible false \
  --multi-az
```

## Cost Estimation

- ECS Fargate: $20-50/month
- EBS Storage: $5-10/month
- Load Balancer: $20/month
- Data Transfer: $0.02-0.05/GB
- **Total: $45-85/month** (medium usage)

## Monitoring

Monitor using CloudWatch:
- Average response time should be <2s
- Error rate <1%
- CPU usage 30-70%

## Backup Strategy

1. Use AWS Backup for EBS volumes
2. Automated snapshots daily
3. Cross-region replication

## Security

1. Use IAM roles for services
2. Enable VPC Flow Logs
3. Use AWS Secrets Manager for API keys
4. Enable encryption at rest and in transit
5. Regular security audits

## Troubleshooting

```bash
# Check service logs
aws logs tail /ecs/ai-study-backend --follow

# Check service status
aws ecs describe-services --cluster ai-study-cluster \
  --services ai-study-backend-service

# Scale up/down
aws ecs update-service --cluster ai-study-cluster \
  --service ai-study-backend-service \
  --desired-count 3
```

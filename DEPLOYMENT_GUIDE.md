# 🚀 LegalizeMe AI Agent - Production Deployment Guide

## 🎯 Deployment Target
- **Domain**: https://www.legalizeme.site/counsel
- **AWS Region**: us-east-1
- **Environment**: Production
- **Service**: Multi-LLM AI Agent with 6 model support

## ⚡ Quick Deploy (One Command)

```bash
./deploy-production.sh
```

This script handles the complete production deployment automatically.

## 📋 Prerequisites

### 1. AWS Credentials
Ensure you have AWS credentials configured with appropriate permissions:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

### 2. Required Permissions
Your AWS user/role needs these permissions:
- **Copilot**: Full access to ECS, ALB, CloudFormation, IAM
- **Bedrock**: Model access for Claude 4
- **Secrets Manager**: Create/read secrets
- **Certificate Manager**: SSL certificate management
- **Route53**: DNS management (if using AWS DNS)

### 3. API Keys (Optional)
Set these in your `.env` file for enhanced functionality:
```bash
HUGGINGFACE_API_KEY=your_hf_key
OPENAI_API_KEY=your_openai_key
```

## 🏗️ Architecture Overview

```
Internet → Route53 → Certificate Manager → Application Load Balancer → ECS Fargate
                                                         ↓
                                             LegalizeMe AI Service
                                                         ↓
                                        Amazon Bedrock (Claude 4) + Other LLMs
```

### Infrastructure Components
- **ECS Fargate**: Serverless container hosting
- **Application Load Balancer**: Traffic distribution and SSL termination
- **AWS Secrets Manager**: Secure API key storage
- **CloudWatch**: Monitoring and logging
- **Amazon Bedrock**: Claude 4 model access

## 🔧 Manual Deployment Steps

If you prefer manual control, follow these steps:

### Step 1: Initialize Copilot Application
```bash
copilot app init legalizeme-ai --domain legalizeme.site
```

### Step 2: Create Production Environment
```bash
copilot env init --name prod
copilot env deploy --name prod
```

### Step 3: Deploy Service
```bash
copilot svc deploy --name api --env prod
```

### Step 4: Configure SSL Certificate
1. Go to AWS Certificate Manager
2. Request certificate for `www.legalizeme.site`
3. Validate domain ownership
4. Update manifest with certificate ARN

### Step 5: Configure DNS
Add CNAME record in your DNS provider:
```
www.legalizeme.site → your-alb-dns-name.us-east-1.elb.amazonaws.com
```

## 🌐 Domain Configuration

### DNS Settings
Configure these DNS records with your provider:

| Type  | Name | Value | TTL |
|-------|------|-------|-----|
| CNAME | www  | your-alb-dns-name.us-east-1.elb.amazonaws.com | 300 |
| A     | @    | your-alb-ip-address | 300 |

### SSL Certificate
1. **Request**: AWS Certificate Manager → Request certificate
2. **Domain**: `www.legalizeme.site` and `legalizeme.site`
3. **Validation**: DNS validation (recommended)
4. **Status**: Wait for "Issued" status

## 📊 Monitoring & Management

### CloudWatch Dashboards
Monitor these key metrics:
- **Request Count**: API calls per minute
- **Response Time**: Average latency
- **Error Rate**: 4xx/5xx responses
- **CPU/Memory**: Container resource usage

### Log Groups
- `/copilot/legalizeme-ai-prod-api`: Application logs
- `/aws/ecs/legalizeme-ai`: Container logs

### Useful Commands
```bash
# View service status
copilot svc show --name api --env prod

# View real-time logs
copilot svc logs --name api --env prod --follow

# Redeploy service
copilot svc deploy --name api --env prod

# Scale service
# Edit copilot/api/manifest.yml count settings, then redeploy
```

## 🧪 Testing Deployment

### Health Check
```bash
curl https://www.legalizeme.site/health
```

### API Endpoints
```bash
# Get available models
curl https://www.legalizeme.site/counsel/models

# Test query endpoint
curl -X POST https://www.legalizeme.site/counsel/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the employment laws in Kenya?", "model": "claude-4"}'
```

### Load Testing
```bash
# Install artillery for load testing
npm install -g artillery

# Run load test
artillery quick --count 10 --num 100 https://www.legalizeme.site/counsel/health
```

## 🔐 Security Configuration

### Secrets Management
All sensitive data is stored in AWS Secrets Manager:
- `legalizeme-ai-prod-HUGGINGFACE_API_KEY`
- `legalizeme-ai-prod-OPENAI_API_KEY`

### Network Security
- **VPC**: Private subnets for containers
- **Security Groups**: Restricted access rules
- **ALB**: Public-facing load balancer only

### IAM Policies
Service has minimal required permissions:
- Bedrock model access
- Secrets Manager read access
- CloudWatch logging
- S3 bucket access (for model cache)

## 📈 Scaling Configuration

### Auto Scaling Settings
```yaml
# copilot/api/manifest.yml
count:
  min: 2          # Minimum instances
  max: 10         # Maximum instances
  scale_in_cooldown: 300s   # Scale down delay
  scale_out_cooldown: 60s   # Scale up delay
  target_cpu: 70           # CPU threshold
  target_memory: 80        # Memory threshold
```

### Manual Scaling
```bash
# Edit manifest.yml count settings
copilot svc deploy --name api --env prod
```

## 💰 Cost Optimization

### Development vs Production
| Resource | Development | Production |
|----------|-------------|------------|
| **ECS Tasks** | 1 task | 2-10 tasks |
| **CPU** | 512 CPU | 1024+ CPU |
| **Memory** | 1GB | 2-4GB |
| **Estimated Cost** | $30-50/month | $100-300/month |

### Cost Monitoring
- Set up AWS Budgets for cost alerts
- Monitor CloudWatch metrics for optimization
- Use Bedrock pricing calculator for model costs

## 🚨 Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check service logs
copilot svc logs --name api --env prod

# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name legalizeme-ai-prod-api
```

#### 2. Domain Not Accessible
- Verify DNS propagation: `dig www.legalizeme.site`
- Check certificate status in ACM
- Verify security group rules

#### 3. High Latency
- Check CloudWatch metrics
- Consider increasing CPU/memory
- Enable response caching
- Use lighter models for development

#### 4. Model Access Denied
```bash
# Check Bedrock permissions
aws bedrock list-foundation-models --region us-east-1

# Verify IAM policies
aws iam get-policy-version --policy-arn arn:aws:iam::ACCOUNT:policy/BedrockAccess
```

## 🔄 CI/CD Integration

### GitHub Actions Workflow
The deployment is automated via GitHub Actions:
```yaml
# .github/workflows/backend-ci.yml
- name: Deploy to AWS Copilot
  run: copilot svc deploy --name api --env prod
```

### Manual Deploy from Local
```bash
# Ensure you're on main branch
git checkout main
git pull origin main

# Deploy
./deploy-production.sh
```

## 📞 Support & Maintenance

### Regular Maintenance
- **Weekly**: Check CloudWatch metrics and logs
- **Monthly**: Review costs and optimize resources
- **Quarterly**: Update dependencies and security patches

### Emergency Procedures
```bash
# Rollback deployment
copilot svc deploy --name api --env prod --image PREVIOUS_TAG

# Scale down for maintenance
# Update manifest.yml count to 0, then redeploy

# Emergency stop
copilot svc delete --name api --env prod
```

---

## 🎉 Deployment Complete!

Your LegalizeMe AI Agent is now live at:
**https://www.legalizeme.site/counsel**

### Next Steps:
1. **Test all endpoints** using the testing commands above
2. **Monitor performance** in CloudWatch
3. **Set up alerts** for critical metrics
4. **Configure backup procedures** for data persistence
5. **Plan scaling strategy** based on usage patterns

**🚀 Your production-grade, multi-LLM legal AI assistant is ready to serve users worldwide!**
# AWS Copilot Deployment Guide

This guide explains how to deploy the Multi-LLM AI Agent using AWS Copilot.

## Prerequisites

1. **AWS CLI** configured with appropriate permissions
2. **AWS Copilot CLI** installed ([Installation Guide](https://aws.github.io/copilot-cli/docs/getting-started/install/))
3. **Docker** installed and running
4. **AWS Account** with permissions for:
   - ECS, VPC, Application Load Balancer
   - Amazon Bedrock access
   - S3, CloudWatch, Systems Manager

## Initial Setup

### 1. Initialize Copilot Application

```bash
# Initialize the application (run once)
copilot app init counsel-ai
cd counsel-ai
```

### 2. Set Up Secrets

Store your API keys in AWS Secrets Manager:

```bash
# Store HuggingFace API key
aws secretsmanager create-secret \
  --name "/copilot/counsel-ai/production/secrets/HUGGINGFACE_API_KEY" \
  --secret-string "your-huggingface-api-key"

# Optional: Store OpenAI API key for future use
aws secretsmanager create-secret \
  --name "/copilot/counsel-ai/production/secrets/OPENAI_API_KEY" \
  --secret-string "your-openai-api-key"
```

### 3. Enable Amazon Bedrock

Ensure you have access to Claude models in Amazon Bedrock:

```bash
# Check available models (should include Claude)
aws bedrock list-foundation-models --region us-east-1
```

If you don't have access, request it through the AWS Console:
1. Go to Amazon Bedrock console
2. Navigate to "Model access"
3. Request access to Anthropic Claude models

## Deployment

### 1. Deploy to Development Environment

```bash
# Deploy the service to dev environment
copilot svc deploy --name api --env dev
```

### 2. Deploy to Staging Environment

```bash
# Create staging environment
copilot env init --name staging

# Deploy staging environment
copilot env deploy --name staging

# Deploy service to staging
copilot svc deploy --name api --env staging
```

### 3. Deploy to Production Environment

```bash
# Create production environment
copilot env init --name prod

# Deploy production environment
copilot env deploy --name prod

# Deploy service to production
copilot svc deploy --name api --env prod
```

## Environment Configuration

### Development
- **Resources**: 512 MB RAM, 0.5 vCPU
- **Scaling**: Fixed 1 instance
- **Model**: FLAN-T5 (lightweight)
- **Debug**: Enabled

### Staging
- **Resources**: 2 GB RAM, 1 vCPU
- **Scaling**: 1-2 instances
- **Model**: Claude 4
- **Debug**: Disabled

### Production
- **Resources**: 4 GB RAM, 2 vCPU
- **Scaling**: 2-5 instances
- **Model**: Claude 4
- **Features**: All optimizations enabled

## Testing Deployments

### Health Check
```bash
# Get service URL
copilot svc show --name api

# Test health endpoint
curl https://your-service-url/health
```

### API Testing
```bash
# Test model listing
curl https://your-service-url/models

# Test query with model selection
curl -X POST https://your-service-url/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the employment rights in Kenya?",
    "model": "claude-4",
    "temperature": 0.3,
    "max_tokens": 2048
  }'
```

## Monitoring and Logs

### View Logs
```bash
# View service logs
copilot svc logs --name api --env prod --follow

# View specific container logs
copilot task exec --name api --env prod
```

### CloudWatch Monitoring
- Navigate to CloudWatch in AWS Console
- Look for log groups: `/copilot/counsel-ai-prod-api`
- Set up alarms for CPU, memory, and error rates

## Model Management

### Supported Models
- `claude-4`: Claude 3.5 Sonnet via Bedrock
- `hunyuan-a13b`: Tencent Hunyuan (self-hosted)
- `flan-t5`: Google FLAN-T5 (lightweight)
- `mixtral`: Mixtral 8x7B
- `llama`: Meta LLaMA 3

### Model Selection
Use the `model` parameter in API requests:

```json
{
  "query": "Your legal question",
  "model": "claude-4",
  "temperature": 0.3,
  "max_tokens": 2048
}
```

## Troubleshooting

### Common Issues

1. **Bedrock Access Denied**
   - Ensure you've requested model access in Bedrock console
   - Check IAM permissions for bedrock:InvokeModel

2. **Out of Memory Errors**
   - Increase memory allocation in manifest.yml
   - Use lighter models (flan-t5) for development

3. **Slow Cold Starts**
   - Consider increasing minimum instance count
   - Use lighter base models for faster initialization

4. **High Costs**
   - Monitor Bedrock usage in AWS Cost Explorer
   - Use FLAN-T5 for development/testing
   - Implement caching (already included)

### Scaling Issues

If you encounter scaling issues:

1. **Check CloudWatch metrics**
2. **Adjust scaling thresholds** in manifest.yml
3. **Monitor memory/CPU usage**
4. **Consider model optimization**

## Cost Optimization

### Tips to Reduce Costs
1. **Use appropriate instance sizes** per environment
2. **Enable caching** (already configured)
3. **Use lighter models for development**
4. **Monitor Bedrock usage**
5. **Set up billing alerts**

### Estimated Monthly Costs (us-east-1)
- **Development**: $50-100/month
- **Staging**: $100-200/month  
- **Production**: $300-500/month (excluding Bedrock usage)

*Note: Bedrock costs depend on usage volume*

## Security

### Best Practices Implemented
- **Private VPC placement**
- **Secrets in AWS Secrets Manager**
- **IAM least privilege permissions**
- **CloudWatch logging enabled**
- **Health checks configured**

### Additional Security
Consider implementing:
- WAF for API protection
- VPC endpoints for AWS services
- Enhanced monitoring with GuardDuty
- Regular security scanning

## Updating the Service

### Code Updates
```bash
# Build and deploy new version
copilot svc deploy --name api --env prod
```

### Configuration Updates
```bash
# Update environment variables in manifest.yml
# Then redeploy
copilot svc deploy --name api --env prod
```

### Rolling Back
```bash
# View deployment history
copilot svc history --name api --env prod

# Deploy specific version (if needed)
copilot svc deploy --name api --env prod --tag previous-version
```

## Support

For issues with:
- **AWS Copilot**: [Copilot Documentation](https://aws.github.io/copilot-cli/)
- **Amazon Bedrock**: [Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- **Application Issues**: Check CloudWatch logs and service metrics
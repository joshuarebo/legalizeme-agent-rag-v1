#!/bin/bash

# ===========================================
# LegalizeMe AI Agent - Production Deployment
# ===========================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Configuration
APP_NAME="legalizeme-ai"
SERVICE_NAME="api"
ENVIRONMENT="prod"
AWS_REGION="us-east-1"
DOMAIN="legalizeme.site"
SUBDOMAIN="www.legalizeme.site"
API_PATH="/counsel"

print_header "🚀 LegalizeMe AI Agent - Production Deployment"

# Step 1: Environment Setup
print_status "Setting up deployment environment..."
export AWS_REGION=$AWS_REGION
export AWS_DEFAULT_REGION=$AWS_REGION

# Load environment variables
if [ -f ".env" ]; then
    print_status "Loading environment variables..."
    export $(grep -v '^#' .env | xargs)
    print_success "Environment variables loaded"
else
    print_warning "No .env file found. Please ensure AWS credentials are configured."
fi

# Step 2: Verify AWS Authentication
print_status "Verifying AWS authentication..."
if aws sts get-caller-identity >/dev/null 2>&1; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    print_success "AWS authentication successful. Account ID: $ACCOUNT_ID"
else
    print_error "AWS authentication failed. Please configure credentials:"
    echo "  1. Set AWS_ACCESS_KEY_ID environment variable"
    echo "  2. Set AWS_SECRET_ACCESS_KEY environment variable"
    echo "  3. Set AWS_REGION environment variable"
    exit 1
fi

# Step 3: Initialize Copilot Application
print_status "Initializing Copilot application..."
if [ ! -f "copilot/.copilot/config.yml" ]; then
    print_status "Creating new Copilot application: $APP_NAME"
    copilot app init $APP_NAME --domain $DOMAIN
    print_success "Copilot application initialized"
else
    print_success "Copilot application already exists"
fi

# Step 4: Create Production Environment
print_status "Setting up production environment..."
if [ ! -d "copilot/environments/$ENVIRONMENT" ]; then
    print_status "Creating production environment..."
    copilot env init --name $ENVIRONMENT
    print_success "Production environment created"
else
    print_success "Production environment already exists"
fi

# Step 5: Deploy Environment Infrastructure
print_status "Deploying environment infrastructure..."
copilot env deploy --name $ENVIRONMENT
print_success "Environment infrastructure deployed"

# Step 6: Create Secrets in AWS Secrets Manager
print_status "Setting up secrets in AWS Secrets Manager..."

# Create secrets for API keys
if [ ! -z "$HUGGINGFACE_API_KEY" ]; then
    aws secretsmanager create-secret \
        --name "legalizeme-ai-prod-HUGGINGFACE_API_KEY" \
        --description "Hugging Face API Key for LegalizeMe AI" \
        --secret-string "$HUGGINGFACE_API_KEY" \
        --region $AWS_REGION >/dev/null 2>&1 || \
    aws secretsmanager update-secret \
        --secret-id "legalizeme-ai-prod-HUGGINGFACE_API_KEY" \
        --secret-string "$HUGGINGFACE_API_KEY" \
        --region $AWS_REGION >/dev/null 2>&1
    print_success "Hugging Face API key stored in Secrets Manager"
fi

if [ ! -z "$OPENAI_API_KEY" ]; then
    aws secretsmanager create-secret \
        --name "legalizeme-ai-prod-OPENAI_API_KEY" \
        --description "OpenAI API Key for LegalizeMe AI" \
        --secret-string "$OPENAI_API_KEY" \
        --region $AWS_REGION >/dev/null 2>&1 || \
    aws secretsmanager update-secret \
        --secret-id "legalizeme-ai-prod-OPENAI_API_KEY" \
        --secret-string "$OPENAI_API_KEY" \
        --region $AWS_REGION >/dev/null 2>&1
    print_success "OpenAI API key stored in Secrets Manager"
fi

# Step 7: Deploy the Service
print_status "Deploying LegalizeMe AI service..."
copilot svc deploy --name $SERVICE_NAME --env $ENVIRONMENT
print_success "Service deployed successfully"

# Step 8: Get Service Information
print_status "Retrieving service information..."
SERVICE_URL=$(copilot svc show --name $SERVICE_NAME --env $ENVIRONMENT --json | jq -r '.routes[0].url' 2>/dev/null || echo "")

if [ ! -z "$SERVICE_URL" ]; then
    print_success "Service deployed at: $SERVICE_URL"
else
    print_warning "Could not retrieve service URL. Use 'copilot svc show' to get details."
fi

# Step 9: Configure Domain and SSL
print_status "Configuring custom domain..."
print_warning "Manual domain configuration required:"
echo "  1. Go to AWS Certificate Manager and request SSL certificate for $SUBDOMAIN"
echo "  2. Add CNAME records to your DNS provider:"
echo "     - Point $SUBDOMAIN to the service URL"
echo "     - Configure SSL certificate validation"
echo "  3. Update the Copilot manifest with custom domain configuration"

# Step 10: Health Check
print_status "Performing health check..."
sleep 30  # Wait for service to be ready

if [ ! -z "$SERVICE_URL" ]; then
    if curl -f "$SERVICE_URL/health" >/dev/null 2>&1; then
        print_success "Health check passed"
    else
        print_warning "Health check failed. Service may still be starting up."
    fi
fi

# Step 11: Enable Monitoring
print_status "Enabling monitoring and logging..."
print_success "CloudWatch monitoring is enabled by default"
print_success "Application logs are available in CloudWatch Logs"

# Step 12: Final Configuration
print_header "🎉 Deployment Complete!"
echo
print_success "LegalizeMe AI Agent has been deployed to production!"
echo
echo "📊 Deployment Summary:"
echo "  Application: $APP_NAME"
echo "  Service: $SERVICE_NAME"
echo "  Environment: $ENVIRONMENT"
echo "  Region: $AWS_REGION"
echo "  Account: $ACCOUNT_ID"
if [ ! -z "$SERVICE_URL" ]; then
    echo "  Service URL: $SERVICE_URL"
fi
echo
echo "🔗 Next Steps:"
echo "  1. Configure custom domain: https://$SUBDOMAIN$API_PATH"
echo "  2. Test API endpoints: curl $SERVICE_URL/models"
echo "  3. Monitor logs: copilot svc logs --name $SERVICE_NAME --env $ENVIRONMENT"
echo "  4. Scale if needed: Update count in copilot/api/manifest.yml"
echo
echo "📚 Management Commands:"
echo "  View service: copilot svc show --name $SERVICE_NAME --env $ENVIRONMENT"
echo "  View logs: copilot svc logs --name $SERVICE_NAME --env $ENVIRONMENT"
echo "  Redeploy: copilot svc deploy --name $SERVICE_NAME --env $ENVIRONMENT"
echo "  Delete: copilot app delete $APP_NAME"
echo
print_success "🚀 Your AI-powered legal assistant is now live!"
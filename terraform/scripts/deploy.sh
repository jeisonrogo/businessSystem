#!/bin/bash

# =============================================================================
# AWS BUSINESS SYSTEM DEPLOYMENT SCRIPT
# Automated deployment for multi-tenant business system
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$TERRAFORM_DIR")"

# Default values
ENVIRONMENT="${1:-dev}"
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_PROFILE="${AWS_PROFILE:-personal}"
PROJECT_NAME="business-system"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

check_prerequisites() {
    log "Checking prerequisites..."

    # Check if required tools are installed
    local tools=("terraform" "aws" "docker" "jq")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error "$tool is required but not installed."
        fi
    done

    # Run AWS profile validation
    log "Validating AWS profile configuration..."
    if [[ -f "$SCRIPT_DIR/validate-aws-profile.sh" ]]; then
        AWS_PROFILE="$AWS_PROFILE" "$SCRIPT_DIR/validate-aws-profile.sh"
    else
        # Fallback to basic check
        log "Using AWS profile: $AWS_PROFILE"
        if ! aws sts get-caller-identity --profile "$AWS_PROFILE" &> /dev/null; then
            error "AWS credentials not configured for profile '$AWS_PROFILE'. Run 'aws configure --profile $AWS_PROFILE' first."
        fi
    fi

    # Check Terraform version
    local tf_version
    tf_version=$(terraform version -json | jq -r '.terraform_version')
    log "Using Terraform version: $tf_version"

    success "All prerequisites check passed"
}

validate_environment() {
    log "Validating environment: $ENVIRONMENT"

    if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
        error "Invalid environment. Must be one of: dev, staging, prod"
    fi

    local tfvars_file="$TERRAFORM_DIR/environments/$ENVIRONMENT/terraform.tfvars"
    if [[ ! -f "$tfvars_file" ]]; then
        error "Terraform variables file not found: $tfvars_file"
    fi

    success "Environment validation passed"
}

build_backend_image() {
    log "Building backend Docker image..."

    local backend_dir="$PROJECT_ROOT/backend"
    local image_name="$PROJECT_NAME-backend"
    local image_tag="$ENVIRONMENT-$(date +%Y%m%d-%H%M%S)"

    if [[ ! -f "$backend_dir/Dockerfile" ]]; then
        warning "Dockerfile not found in backend directory. Creating basic Dockerfile..."
        create_basic_dockerfile "$backend_dir"
    fi

    cd "$backend_dir"

    # Build the image
    log "Building Docker image: $image_name:$image_tag"
    docker build -t "$image_name:$image_tag" .
    docker tag "$image_name:$image_tag" "$image_name:latest"

    success "Backend image built successfully"

    # Return to original directory
    cd "$SCRIPT_DIR"

    echo "$image_name:$image_tag"
}

create_basic_dockerfile() {
    local backend_dir="$1"

    cat > "$backend_dir/Dockerfile" << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    success "Created basic Dockerfile in $backend_dir"
}

build_frontend() {
    log "Building frontend application..."

    local frontend_dir="$PROJECT_ROOT/frontend"

    if [[ ! -d "$frontend_dir" ]]; then
        warning "Frontend directory not found. Skipping frontend build."
        return 0
    fi

    cd "$frontend_dir"

    # Install dependencies
    if [[ -f "package.json" ]]; then
        log "Installing frontend dependencies..."
        npm ci
    else
        warning "package.json not found. Skipping frontend build."
        return 0
    fi

    # Build frontend
    log "Building frontend for production..."
    npm run build

    success "Frontend built successfully"

    # Return to original directory
    cd "$SCRIPT_DIR"
}

deploy_infrastructure() {
    log "Deploying infrastructure with Terraform..."

    cd "$TERRAFORM_DIR"

    local tfvars_file="environments/$ENVIRONMENT/terraform.tfvars"

    # Initialize Terraform
    log "Initializing Terraform..."
    terraform init

    # Validate configuration
    log "Validating Terraform configuration..."
    terraform validate

    # Plan deployment
    log "Creating Terraform plan..."
    terraform plan -var-file="$tfvars_file" -out="$ENVIRONMENT.tfplan"

    # Apply deployment
    log "Applying Terraform plan..."
    terraform apply "$ENVIRONMENT.tfplan"

    # Clean up plan file
    rm -f "$ENVIRONMENT.tfplan"

    success "Infrastructure deployed successfully"

    # Return to original directory
    cd "$SCRIPT_DIR"
}

upload_frontend() {
    log "Uploading frontend to S3..."

    local frontend_dir="$PROJECT_ROOT/frontend"
    local build_dir="$frontend_dir/build"

    if [[ ! -d "$build_dir" ]]; then
        warning "Frontend build directory not found. Skipping frontend upload."
        return 0
    fi

    cd "$TERRAFORM_DIR"

    # Get S3 bucket name from Terraform output
    local bucket_name
    bucket_name=$(terraform output -raw s3_frontend_bucket_name 2>/dev/null || echo "")

    if [[ -z "$bucket_name" ]]; then
        warning "Could not get S3 bucket name from Terraform outputs. Skipping frontend upload."
        return 0
    fi

    log "Uploading frontend to S3 bucket: $bucket_name"

    # Sync build directory to S3
    aws s3 sync "$build_dir" "s3://$bucket_name" --delete --profile "$AWS_PROFILE"

    # Get CloudFront distribution ID and create invalidation
    local distribution_id
    distribution_id=$(terraform output -raw cloudfront_distribution_id 2>/dev/null || echo "")

    if [[ -n "$distribution_id" ]]; then
        log "Creating CloudFront invalidation for distribution: $distribution_id"
        aws cloudfront create-invalidation --distribution-id "$distribution_id" --paths "/*" --profile "$AWS_PROFILE" > /dev/null
        success "CloudFront invalidation created"
    fi

    success "Frontend uploaded successfully"

    # Return to original directory
    cd "$SCRIPT_DIR"
}

run_database_migrations() {
    log "Running database migrations..."

    cd "$TERRAFORM_DIR"

    # Get database connection info from Terraform outputs
    local db_endpoint
    local db_name
    local secret_name

    db_endpoint=$(terraform output -raw rds_endpoint 2>/dev/null || echo "")
    db_name=$(terraform output -raw rds_database_name 2>/dev/null || echo "")
    secret_name=$(terraform output -raw secrets_manager_secret_name 2>/dev/null || echo "")

    if [[ -z "$db_endpoint" || -z "$db_name" || -z "$secret_name" ]]; then
        warning "Could not get database connection info. Skipping migrations."
        return 0
    fi

    # Get database credentials from Secrets Manager
    local db_credentials
    db_credentials=$(aws secretsmanager get-secret-value --secret-id "$secret_name" --query SecretString --output text --profile "$AWS_PROFILE")

    local db_username
    local db_password

    db_username=$(echo "$db_credentials" | jq -r '.username')
    db_password=$(echo "$db_credentials" | jq -r '.password')

    # Set environment variables for migration
    export DATABASE_URL="postgresql://$db_username:$db_password@$db_endpoint:5432/$db_name"

    # Run Alembic migrations if available
    local backend_dir="$PROJECT_ROOT/backend"
    if [[ -f "$backend_dir/alembic.ini" ]]; then
        cd "$backend_dir"
        log "Running Alembic migrations..."

        # Activate virtual environment if it exists
        if [[ -d "venv" ]]; then
            source venv/bin/activate
        fi

        python -m alembic upgrade head
        success "Database migrations completed"
    else
        warning "Alembic configuration not found. Skipping migrations."
    fi

    # Return to original directory
    cd "$SCRIPT_DIR"
}

show_deployment_summary() {
    log "Deployment Summary"
    echo "=================="

    cd "$TERRAFORM_DIR"

    # Get deployment info
    local app_urls
    app_urls=$(terraform output -json application_urls 2>/dev/null || echo '{}')

    local frontend_url
    local backend_url

    frontend_url=$(echo "$app_urls" | jq -r '.frontend_cloudfront // "Not available"')
    backend_url=$(echo "$app_urls" | jq -r '.backend_app_runner // "Not available"')

    echo ""
    echo "🌐 Application URLs:"
    echo "   Frontend: https://$frontend_url"
    echo "   Backend:  https://$backend_url"
    echo ""

    # Get cost estimate
    local cost_info
    cost_info=$(terraform output -json estimated_monthly_cost 2>/dev/null || echo '{}')

    if [[ "$cost_info" != '{}' ]]; then
        echo "💰 Estimated Monthly Costs:"
        echo "$cost_info" | jq -r 'to_entries[] | "   \(.key): \(.value)"'
        echo ""
    fi

    # Get useful commands
    local useful_commands
    useful_commands=$(terraform output -json deployment_info 2>/dev/null || echo '{}')

    if [[ "$useful_commands" != '{}' ]]; then
        echo "🔧 Useful Commands:"
        echo "$useful_commands" | jq -r '.useful_commands | to_entries[] | "   \(.key): \(.value)"'
        echo ""
    fi

    success "Deployment completed successfully!"

    # Return to original directory
    cd "$SCRIPT_DIR"
}

# =============================================================================
# MAIN DEPLOYMENT FLOW
# =============================================================================

main() {
    log "Starting deployment for environment: $ENVIRONMENT"
    echo "============================================================="

    # Step 1: Prerequisites and validation
    check_prerequisites
    validate_environment

    # Step 2: Build applications
    build_backend_image
    build_frontend

    # Step 3: Deploy infrastructure
    deploy_infrastructure

    # Step 4: Upload frontend
    upload_frontend

    # Step 5: Run database migrations
    run_database_migrations

    # Step 6: Show summary
    show_deployment_summary

    log "Deployment process completed!"
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

# Show usage if requested
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: $0 [ENVIRONMENT]"
    echo ""
    echo "ENVIRONMENT: dev, staging, or prod (default: dev)"
    echo ""
    echo "Prerequisites:"
    echo "  - AWS CLI configured with appropriate credentials"
    echo "  - Terraform >= 1.0 installed"
    echo "  - Docker installed"
    echo "  - jq installed"
    echo ""
    echo "Example:"
    echo "  $0 dev"
    echo "  $0 prod"
    exit 0
fi

# Run main function
main "$@"